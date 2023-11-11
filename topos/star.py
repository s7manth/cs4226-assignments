#!/usr/bin/python

import os, sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.node import Host, RemoteController

class TreeTopo(Topo):
  """
  Tree topology
  """

  def __init__(self):
    Topo.__init__(self)

  def build(self):
    infileName = "star.in"
    
    # Read input file
    with open(infileName) as f:
      lines = f.readlines()
    
    config = [int(x) for x in lines[0].split()]
    print("config", config)
    nHosts = config[0]
    nSwitches = config[1]
    nLinks = config[2]
    links = [tuple(x.split(',')) for x in lines[1:]]

    # Add hosts
    for h in range(1, nHosts + 1):
      host = self.addHost('h%d' % h)
        
    # Add switches 
    for s in range(1, nSwitches + 1):
      sconfig = {
        'dpid': "%016x" % s
      }
      switch = self.addSwitch('s%d' % s, **sconfig)
        
    # Add links
    for link in links:
      self.addLink(link[0], link[1])
        
                    
topos = { 
  'sdnip' : (lambda: TreeTopo()) 
}

if __name__ == '__main__':
  sys.path.insert(1, '/home/sdn/onos/topos')
  from onosnet import run
  run(TreeTopo())

