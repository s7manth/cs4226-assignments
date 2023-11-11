#!/usr/bin/python

import os, sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.node import Host, RemoteController

class TreeTopo( Topo ):
    "Tree topology"

    def build( self ):
        # Read ring.in
        # Load configuration of Hosts, Switches, and Links
        # You can write other functions as you need.

        # Add hosts
        # > self.addHost('h%d' % [HOST NUMBER])

        # Add switches
        # > sconfig = {'dpid': "%016x" % [SWITCH NUMBER]}
        # > self.addSwitch('s%d' % [SWITCH NUMBER], **sconfig)

        # Add links
        # > self.addLink([HOST1], [HOST2])
        
                    
topos = { 'sdnip' : ( lambda: TreeTopo() ) }

if __name__ == '__main__':
    sys.path.insert(1, '/home/sdn/onos/topos')
    from onosnet import run
    run( TreeTopo() )