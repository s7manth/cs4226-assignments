import atexit

from mininet.cli import CLI
from mininet.link import Link
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from router import FRRRouter

net = None


class Topology(Topo):
    def build(self):
        # Add Routers
        r110 = self.addNode('r110', cls=FRRRouter)
        r120 = self.addNode('r120', cls=FRRRouter)
        r130 = self.addNode('r130', cls=FRRRouter)
        r210 = self.addNode('r210', cls=FRRRouter)
        r310 = self.addNode('r310', cls=FRRRouter)
        r410 = self.addNode('r410', cls=FRRRouter)

        # Add Hosts
        h211 = self.addHost('h211')
        h311 = self.addHost('h311')
        h411 = self.addHost('h411')
        h412 = self.addHost('h412')

        # Add Links
        self.addLink(r110, h211, intfName1='r110-eth1', params1={'ip': '192.168.1.0/31'}, intfName2='h211-eth0', params2={'ip': '192.168.1.1/31'})
        self.addLink(r110, r120, intfName1='r110-eth2', params1={'ip': '172.17.1.0/31'}, intfName2='r120-eth1', params2={'ip': '172.17.1.1/31'})
        self.addLink(r110, r130, intfName1='r110-eth3', params1={'ip': '172.17.3.0/31'}, intfName2='r130-eth2', params2={'ip': '172.17.3.1/31'})

        pass


def startNetwork():
    info("*** Creating the network\n")
    topology = Topology()

    global net
    net = Mininet(topo=topology, link=Link, autoSetMacs=True)

    info("*** Starting the network\n")
    net.start()
    info("*** Running CLI\n")
    CLI(net)


def stopNetwork():
    if net is not None:
        net.stop()


if __name__ == "__main__":
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel("info")
    startNetwork()
