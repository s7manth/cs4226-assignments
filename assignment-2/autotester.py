import json
import os
import re
from argparse import ArgumentParser
from dataclasses import dataclass
from importlib import import_module
from time import sleep

import router
from features import (
    EXPECTED_ASNS,
    EXPECTED_BGP_NEIGHBORS,
    EXPECTED_HOSTS,
    EXPECTED_PING_RESULTS,
    EXPECTED_PROTOCOLS,
    RESTRICTED_COMMANDS,
)
from mininet.link import Link
from mininet.log import error, info
from mininet.log import output as out
from mininet.log import setLogLevel, warn
from mininet.net import Mininet


@dataclass
class Settings:
    id: str
    show_output: bool


def expect(net, host, command, message, present=True) -> bool:
    node = net.getNodeByName(host)
    output = node.cmd(command)
    out(output)
    if isinstance(message, str):
        found = output.find(message) != -1
        return found ^ (not present)
    found = True ^ (not present)
    for msg in message:
        found = found and output.find(msg) != -1
    return found ^ (not present)


def check_loopback(expected, actual) -> bool:
    result = True
    if "loopback" not in expected and hasattr(actual, "loopback"):
        result = False
        warn(f"({actual.name}) should not have configured loopback\n")
        return result
    if "loopback" not in expected:
        return result
    if not hasattr(actual, "loopback"):
        result = False
        warn(f"({actual.name}) should have configured loopback\n")
        return result

    if actual.loopback != expected["loopback"]:
        result = False
        warn(f"({actual.name}) should have loopback configured as {expected['loopback']}\n")
    return result


def check_interface(expected_interface, actual_interface) -> bool:
    result = True
    address = f"{actual_interface.ip}/{actual_interface.prefixLen}"
    if address != expected_interface[1]:
        result = False
        warn(f"({actual_interface}) should have address {expected_interface[1]}\n")
    return result


def check_host_configuration(expected_host, actual_host) -> bool:
    result = True
    result = check_loopback(expected_host, actual_host)
    expected_interfaces = set(expected_host["interfaces"].keys())
    actual_interfaces = set(map(lambda interface: interface.name, actual_host.intfs.values()))
    if len(actual_interfaces.difference(expected_interfaces)) > 0:
        result = False
        warn(f"({actual_host.name}) additional interface: {actual_interfaces.difference(expected_interfaces)}\n")
    if len(expected_interfaces.difference(actual_interfaces)) > 0:
        result = False
        warn(f"({actual_host.name}) missing interface: {expected_interfaces.difference(actual_interfaces)}\n")
    common = expected_interfaces.intersection(actual_interfaces)
    for name in common:
        expected = next((interface for interface in list(expected_host["interfaces"].items()) if interface[0] == name))
        actual = next((interface for interface in list(actual_host.intfs.values()) if interface.name == name))
        result = check_interface(expected, actual)
    return result


def check_topology(net: Mininet) -> bool:
    result = True
    hosts = net.hosts
    hosts.sort(key=lambda item: item.name)
    expected = set(map(lambda host: host["name"], EXPECTED_HOSTS))
    actual = set(map(lambda host: host.name, hosts))
    if len(actual.difference(expected)) > 0:
        result = False
        warn(f"additional hosts: {actual.difference(expected)}\n")
    if len(expected.difference(actual)) > 0:
        result = False
        warn(f"missing hosts: {expected.difference(actual)}\n")
    common = expected.intersection(actual)
    for hostname in common:
        expected = next((host for host in list(EXPECTED_HOSTS) if host["name"] == hostname))
        actual = next((host for host in list(hosts) if host.name == hostname))
        check_host_configuration(expected, actual)
    return result


def check_active_protocols(net: Mininet) -> bool:
    result = True
    for entry in EXPECTED_PROTOCOLS:
        for protocol in entry["protocols"]:
            protocol_name = protocol["type"].upper()
            command = f'vtysh -c "show ip {protocol["type"]}"'
            expected = f"{protocol_name} instance not found"
            warn("++++++ check_active_protocols: " + entry["node"] + " command: " + command + " expected (is instance found): " + str(protocol["status"]) + "\n")
            if expect(net, entry["node"], command, expected, False) != protocol["status"]:
                result = False
                warn(f'({entry["node"]}) {protocol_name} should{" not" if not protocol["status"] else ""} be active\n')
    return result


def check_connectivity(net: Mininet) -> bool:
    result = True
    connectivity = net.pingAll(1)
    warn("++++++ check_connectivity: " + "pingall" + " expected: " + "all sucess\n")
    if connectivity != 0:
        result = False
        warn("all nodes should be able to ping each other\n")
    warn("++++++ check_connectivity: " + "check AS100 RIP connectivity" + " expected: " + "all success\n")
    for entry in EXPECTED_PING_RESULTS["success"]:
        source = entry["source"]
        target = entry["target"]
        warn("++++++ check_bgp_asn: " + source + " command: " + f"ping {target} -W 1 -w 1 -c 1" + " expected: " + "0% packet loss\n")
        if not expect(net, source, f"ping {target} -W 1 -w 1 -c 1", "0% packet loss"):
            result = False
            warn(f"({source}) failed to ping {target}\n")
    warn("++++++ check_connectivity: " + "check other AS RIP connectivity" + " expected: " + "all fail\n")
    for entry in EXPECTED_PING_RESULTS["failure"]:
        source = entry["source"]
        target = entry["target"]
        warn("++++++ check_bgp_asn: " + source + " command: " + f"ping {target} -W 1 -w 1 -c 1" + " expected: " + "Network is unreachable\n")
        if not expect(net, source, f"ping {target} -W 1 -w 1 -c 1", "Network is unreachable"):
            result = False
            warn(f"({source}) should fail to ping {target}\n")
    return result


def check_commands(net: Mininet) -> bool:
    result = True
    hosts = net.hosts
    hosts.sort(key=lambda item: item.name)
    routers = filter(lambda host: host.name.startswith("r"), hosts)
    for router in routers:
        for entry in RESTRICTED_COMMANDS:
            command = 'vtysh -c "show running-config"'
            expected = router.name in entry["nodes"]
            if not expect(net, router.name, command, entry["command"], expected):
                result = False
                warn(f'({router.name}) {"does not use" if expected else "uses"} {entry["command"]}\n')
    return result


def check_bgp_asn(net: Mininet) -> bool:
    result = True
    for entry in EXPECTED_ASNS:
        node = entry["node"]
        asn = entry["asn"]
        warn("++++++ check_bgp_asn: " + node + " command: " + 'vtysh -c "show bgp summary"' + " expected: " + f"local AS number {asn}\n")
        if not expect(net, node, 'vtysh -c "show bgp summary"', f"local AS number {asn}"):
            result = False
            warn(f"({node}) incorrect ASN\n")
    return result


def check_bgp_neighbors(net: Mininet) -> bool:
    result = True
    for entry in EXPECTED_BGP_NEIGHBORS:
        node = entry["node"]
        warn("++++++ check_bgp_neighbors: " + node + " command: " + 'vtysh -c "show bgp summary"' + " expected: include " + ','.join(entry["include"]) + "\n")
        if "exclude" in entry:
            warn("++++++ check_bgp_neighbors: " + node + " command: " + 'vtysh -c "show bgp summary"' + " expected: exclude " + ','.join(entry["exclude"]) + "\n")
        if not expect(net, node, 'vtysh -c "show bgp summary"', entry["include"]):
            result = False
            warn(f'({node}) should be neighbours with {entry["include"]}\n')
        if "exclude" in entry and not expect(net, node, 'vtysh -c "show bgp summary"', entry["exclude"], False):
            result = False
            warn(f'({node}) should not be neighbours with {entry["exclude"]}\n')
    return result


def check_fault_tolerance(net: Mininet) -> bool:
    result = True
    warn("++++++ check_fault_tolerance: " + "r410" + " command: " + "traceroute 192.168.1.1" + " expected: " + "172.17.3.0\n")
    if not expect(net, "r410", "traceroute 192.168.1.1", "172.17.3.0"):
        result = False
        warn("(r410) route to r120 does not pass through r110\n")
    net.configLinkStatus("r110", "r410", "down")
    sleep(5)
    warn("++++++ check_fault_tolerance: " + "r410" + " command (after link r110 r410 down): " + "traceroute 192.168.1.1" + " expected: " + "172.17.4.0\n")
    if not expect(net, "r410", "traceroute 192.168.1.1", "172.17.4.0"):
        result = False
        warn("(r410) route to r120 does not pass through r130 [link down]\n")
    connectivity = net.pingAll(1)
    warn("++++++ check_fault_tolerance: " + "pingall" + " expected: " + "all sucess\n")
    if connectivity != 0:
        result = False
        warn("failed to maintain connectivity [link down]\n")
    net.configLinkStatus("r110", "r410", "up")
    sleep(5)
    warn("++++++ check_fault_tolerance: " + "r410" + " command (after link r110 r410 up): " + "traceroute 192.168.1.1" + " expected: " + "172.17.3.0\n")
    if not expect(net, "r410", "traceroute 192.168.1.1", "172.17.3.0"):
        result = False
        warn("(r410) route to r120 does not pass through r110 [link up]\n")
    warn("++++++ check_fault_tolerance: " + "pingall" + " expected: " + "all sucess\n")
    connectivity = net.pingAll(1)
    if connectivity != 0:
        result = False
        warn("failed to maintain connectivity [link up]\n")
    return result


def check_metric_values(net: Mininet) -> bool:
    result = True
    command = 'vtysh -c "show bgp ipv4 unicast all"'
    warn("++++++ check_metric_values: " + "r410" + " command: " + 'vtysh -c "show bgp ipv4 unicast all"' + " expected: " + "172.17.3.0               0\n")
    if not expect(net, "r410", command, "172.17.3.0               0", False):
        result = False
        warn("(r410) received route with unset metric from r110\n")
    warn("++++++ check_metric_values: " + "r410" + " command: " + 'vtysh -c "show bgp ipv4 unicast all"' + " expected: " + "172.17.4.0               0\n")
    if not expect(net, "r410", command, "172.17.4.0               0", False):
        result = False
        warn("(r410) received route with unset metric from r130\n")
    warn("++++++ check_metric_values: " + "r210" + " command: " + 'vtysh -c "show bgp ipv4 unicast all"' + " expected: " + "172.17.1.0               0\n")
    if not expect(net, "r210", command, "172.17.1.0               0"):
        result = False
        warn("(r210) received route with set metric from r110\n")
    warn("++++++ check_metric_values: " + "r310" + " command: " + 'vtysh -c "show bgp ipv4 unicast all"' + " expected: " + "172.17.2.0               0\n")
    if not expect(net, "r310", command, "172.17.2.0               0"):
        result = False
        warn("(r310) received route with set metric from r130\n")
    return result


def check_route_properties(net: Mininet, node, subnet, next_hop, community, local_preference) -> bool:
    result = True
    output = net.getNodeByName(node).cmd(f'vtysh -c "show bgp ipv4 unicast {subnet} json"')
    out(output)
    data = json.loads(output)
    route = next(filter(lambda path: path["nexthops"][0]["ip"] == next_hop, data["paths"]))
    if route["community"]["string"] != community:
        result = False
        warn(f"({node}) incorrect community value received for {subnet}\n")
    if route["locPrf"] != local_preference:
        result = False
        warn(f"({node}) incorrect local preference value set for {subnet}\n")
    return result


def check_route(net: Mininet) -> bool:
    result = True

    result = check_route_properties(net, "r110", "10.4.1.0", "172.17.3.1", "400:300", 300)
    result = check_route_properties(net, "r110", "10.4.1.128", "172.17.3.1", "400:100", 100)
    result = check_route_properties(net, "r130", "10.4.1.0", "172.17.4.1", "400:100", 100)
    result = check_route_properties(net, "r130", "10.4.1.128", "172.17.4.1", "400:300", 300)

    warn("++++++ check_route: " + "r120" + " command: " + 'r120 ip route' + " expected: " + "output match reg 10.4.1.0\/25 nhid \d+ via 192.168.1.0\n")
    warn("++++++ check_route: " + "r120" + " command: " + 'r120 ip route' + " expected: " + "output match reg 10.4.1.128\/25 nhid \d+ via 192.168.1.3\n")

    output = net.getNodeByName("r120").cmd("ip route")
    out(output)
    if re.search("10.4.1.0\/25 nhid \d+ via 192.168.1.0", output) is None:
        result = False
        warn("(r120) route to 10.4.1.0/25 does not pass through r110\n")
    if re.search("10.4.1.128\/25 nhid \d+ via 192.168.1.3", output) is None:
        result = False
        warn("(r120) route to 10.4.1.128/25 does not pass through r130\n")
    return result


def check(id):
    # Modify search path for router configuration files.
    router.DIRECTORY = os.path.join(os.getcwd(), id)

    Topology = import_module(f"{id}.topology").Topology
    warn(f"({id}) GRADING\n")

    info("*** Creating the network\n")
    topology = Topology()
    net = Mininet(topo=topology, link=Link, autoSetMacs=True)

    info("*** Starting the network\n")
    net.start()

    sleep(10)  # Wait for all routes to converge.

    # Task 1
    warn("############################ Starting test cases for Task 1 ############################\n")
    topology_result = check_topology(net)
    if not topology_result:
        net.stop()
        warn("(topology) fail\n")
        error(f"({id}) incorrect topology\n")
        exit(255)
    else:
        warn(f"({id}) PASSED: Topology check\n")

    # Task 2
    warn("############################ Starting test cases for Task 2 ############################\n")

    protocol_result = check_active_protocols(net)
    if not protocol_result:
        warn(f"({id}) FAILED: Protocol check\n")
    else:
        warn(f"({id}) PASSED: Protocol check\n")

    asn_result = check_bgp_asn(net)
    if not asn_result:
        warn(f"({id}) FAILED: ASN check\n")
    else:
        warn(f"({id}) PASSED: ASN check\n")

    connectivity_result = check_connectivity(net)
    if not connectivity_result:
        warn(f"({id}) FAILED: Connectivity check\n")
    else:
        warn(f"({id}) PASSED: Connectivity check\n")

    neighbour_result = check_bgp_neighbors(net)
    if not neighbour_result:
        warn(f"({id}) FAILED: Neighbour check\n")
    else:
        warn(f"({id}) PASSED: Neighbour check\n")

    # Task 3
    warn("############################ Starting test cases for Task 3 ############################\n")
    fault_tolerance_result = check_fault_tolerance(net)
    if not fault_tolerance_result:
        warn(f"({id}) FAILED: Fault tolerance check\n")
    else:
        warn(f"({id}) PASSED: Fault tolerance check\n")

    metric_result = check_metric_values(net)
    if not metric_result:
        warn(f"({id}) FAILED: Metric value check\n")
    else:
        warn(f"({id}) PASSED: Metric value check\n")

    # Task 4
    warn("############################ Starting test cases for Task 4 ############################\n")
    route_result = check_route(net)
    if not route_result:
        warn(f"({id}) FAILED: Route check\n")
    else:
        warn(f"({id}) PASSED: Route check\n")
    # Others
    commands_result = check_commands(net)
    if not commands_result:
        warn(f"({id}) FAILED: Restricted commands check\n")
    else:
        warn(f"({id}) PASSED: Restricted commands check\n")


    warn(f"({id}) *** Summary ***\n")
    if not protocol_result:
        warn(f"({id}) FAILED: Protocol check\n")
    if not asn_result:
        warn(f"({id}) FAILED: ASN check\n")
    if not connectivity_result:
        warn(f"({id}) FAILED: Connectivity check\n")
    if not neighbour_result:
        warn(f"({id}) FAILED: Neighbour check\n")
    if not fault_tolerance_result:
        warn(f"({id}) FAILED: Fault tolerance check\n")
    if not metric_result:
        warn(f"({id}) FAILED: Metric value check\n")
    if not route_result:
        warn(f"({id}) FAILED: Route check\n")
    if not commands_result:
        warn(f"({id}) FAILED: Restricted commands check\n")

    net.stop()
    if (
        protocol_result
        and asn_result
        and connectivity_result
        and neighbour_result
        and fault_tolerance_result
        and metric_result
        and route_result
        and commands_result
    ):
        warn(f"({id}) ALL PASSED\n")
        exit(0)
    else:
        warn(f"({id}) FAILED\n")
        exit(1)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("id")
    parser.add_argument("--show-output", required=False, action="store_true")
    print(os.getcwd())

    settings = Settings(**vars(parser.parse_args()))
    setLogLevel("warn")
    if settings.show_output:
        setLogLevel("output")
    check(settings.id)
