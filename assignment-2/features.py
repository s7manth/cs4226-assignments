EXPECTED_HOSTS = [
    {
        "name": "h211",
        "interfaces": {"h211-eth0": "10.2.1.1/24"},
    },
    {
        "name": "h311",
        "interfaces": {"h311-eth0": "10.3.1.1/24"},
    },
    {
        "name": "h411",
        "interfaces": {"h411-eth0": "10.4.1.1/25"},
    },
    {
        "name": "h412",
        "interfaces": {"h412-eth0": "10.4.1.129/25"},
    },
    {
        "name": "r110",
        "loopback": "100.100.1.1/32",
        "interfaces": {"r110-eth1": "192.168.1.0/31", "r110-eth2": "172.17.1.0/31", "r110-eth3": "172.17.3.0/31"},
    },
    {
        "name": "r120",
        "loopback": "100.100.1.2/32",
        "interfaces": {"r120-eth1": "192.168.1.1/31", "r120-eth2": "192.168.1.2/31"},
    },
    {
        "name": "r130",
        "loopback": "100.100.1.3/32",
        "interfaces": {"r130-eth1": "192.168.1.3/31", "r130-eth2": "172.17.2.0/31", "r130-eth3": "172.17.4.0/31"},
    },
    {
        "name": "r210",
        "loopback": "100.100.2.1/32",
        "interfaces": {"r210-eth0": "10.2.1.254/24", "r210-eth1": "172.17.1.1/31"},
    },
    {
        "name": "r310",
        "loopback": "100.100.3.1/32",
        "interfaces": {"r310-eth0": "10.3.1.254/24", "r310-eth1": "172.17.2.1/31"},
    },
    {
        "name": "r410",
        "loopback": "100.100.4.1/32",
        "interfaces": {
            "r410-eth0": "10.4.1.126/25",
            "r410-eth1": "10.4.1.254/25",
            "r410-eth2": "172.17.3.1/31",
            "r410-eth3": "172.17.4.1/31",
        },
    },
]

EXPECTED_PROTOCOLS = [
    {"node": "r110", "protocols": [{"type": "rip", "status": True}, {"type": "bgp", "status": True}]},
    {"node": "r120", "protocols": [{"type": "rip", "status": True}, {"type": "bgp", "status": True}]},
    {"node": "r130", "protocols": [{"type": "rip", "status": True}, {"type": "bgp", "status": True}]},
    {"node": "r210", "protocols": [{"type": "rip", "status": False}, {"type": "bgp", "status": True}]},
    {"node": "r310", "protocols": [{"type": "rip", "status": False}, {"type": "bgp", "status": True}]},
    {"node": "r410", "protocols": [{"type": "rip", "status": False}, {"type": "bgp", "status": True}]},
]

EXPECTED_ASNS = [
    {"node": "r110", "asn": "100"},
    {"node": "r120", "asn": "100"},
    {"node": "r130", "asn": "100"},
    {"node": "r210", "asn": "200"},
    {"node": "r310", "asn": "300"},
    {"node": "r410", "asn": "400"},
]

EXPECTED_BGP_NEIGHBORS = [
    {"node": "r110", "include": ["100.100.1.2", "100.100.1.3", "172.17.1.1", "172.17.3.1"], "exclude": ["192.168.1.1"]},
    {"node": "r120", "include": ["100.100.1.1", "100.100.1.3"], "exclude": ["192.168.1.0", "192.168.1.3"]},
    {"node": "r130", "include": ["100.100.1.1", "100.100.1.2", "172.17.2.1", "172.17.4.1"], "exclude": ["192.168.1.2"]},
    {"node": "r210", "include": ["172.17.1.0"]},
    {"node": "r310", "include": ["172.17.2.0"]},
    {"node": "r410", "include": ["172.17.3.0", "172.17.4.0"]},
]

EXPECTED_PING_RESULTS = {
    "success": [
        {"source": "r110", "target": "100.100.1.2"},
        {"source": "r110", "target": "100.100.1.3"},
        {"source": "r120", "target": "100.100.1.1"},
        {"source": "r120", "target": "100.100.1.3"},
        {"source": "r130", "target": "100.100.1.1"},
        {"source": "r130", "target": "100.100.1.2"},
    ],
    "failure": [
        {"source": "r120", "target": "100.100.1.4"},
        {"source": "r120", "target": "100.100.1.5"},
        {"source": "r120", "target": "100.100.1.6"},
        {"source": "r210", "target": "100.100.1.1"},
        {"source": "r210", "target": "100.100.1.2"},
        {"source": "r210", "target": "100.100.1.3"},
        {"source": "r310", "target": "100.100.1.1"},
        {"source": "r310", "target": "100.100.1.2"},
        {"source": "r310", "target": "100.100.1.3"},
        {"source": "r410", "target": "100.100.1.1"},
        {"source": "r410", "target": "100.100.1.2"},
        {"source": "r410", "target": "100.100.1.3"},
    ],
}

RESTRICTED_COMMANDS = [
    {"command": "redistribute", "nodes": []},
    {"command": "match community", "nodes": ["r110", "r130"]},
    {"command": "match ip address", "nodes": ["r410"]},
    {"command": "set community", "nodes": ["r410"]},
    {"command": "set local-preference", "nodes": ["r110", "r130"]},
    {"command": "set metric", "nodes": ["r110", "r130"]},
]
