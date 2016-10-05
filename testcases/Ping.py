'''
Created on Sep 22, 2016

@author: edesai
'''
from testcases.BaseTest import BaseTest
from nodes.Controller import Controller
from nodes.Compute import Compute
import time
import subprocess
from subprocess import call
import sys
from common.utils import SSHConnection



class Ping(BaseTest):
    '''
    classdocs
    '''

    
    def __init__(self, args):
        '''
        Constructor
        '''
        
        self.args = args
        self.controller = Controller(args.controller, self.args.controllerUsername, self.args.controllerSysUsername, self.args.controllerPassword)

        self.computeHosts = []
        for compute in args.computeHosts.split(','):
            self.computeHosts.append(Compute(compute, self.args.computeUsername, self.args.computePassword))
        
        self.new_tenant = "auto"
        self.new_user = "auto_user"
        self.new_password = "cisco123"
        self.new_network = "auto_nw"
             
    # TODO: enforce this
    def runTest(self):
        
        #Create project
        new_project = self.controller.createProject(self.new_tenant)
        
        
        #Create user
        new_user = self.controller.createUser(new_project, 
                                   new_username = self.new_user, 
                                   new_password = self.new_password)
        
        #Create network
        new_network = self.controller.createNetwork(self.new_tenant,self.new_network, 
                                      self.new_user, self.new_password)
        print "New Network:", new_network
    
        #Create subnet
        new_subnet = self.controller.createSubnet(new_network.get('network').get('id'), 
                                                   self.new_tenant,self.new_user, self.new_password)
        print "New Subnetwork:", new_subnet

        #Create key-pair
        key_pair = self.controller.createKeyPair(new_project.id, self.new_user, 
                                               self.new_password)        
        
        #Create security groups and rules
        self.controller.createSecurityGroup(new_project.id, self.new_user, 
                                               self.new_password)
        
        
        #Create instance
        host1 = self.controller.createInstance(new_project.id, self.new_user, 
                                               self.new_password, new_network.get('network').get('id'),
                                               "autohost1", key_name=key_pair)
        print "Host1:", host1
        
        host2 = self.controller.createInstance(new_project.id, self.new_user, 
                                               self.new_password, new_network.get('network').get('id'),
                                               "autohost2", key_name=key_pair)
        print "Host2:", host2

        
        with SSHConnection(address=self.controller.ip, username=self.controller.sys_username, password = self.controller.password) as client:
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network.get('network').get('id')+" ping -c 3 20.20.30.4")
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            print "Error:", error_output
            
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network.get('network').get('id')+" ping -c 3 20.20.30.3")
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            print "Error:", error_output
            
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network.get('network').get('id')+" ping -c 3 20.20.30.2")
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            print "Error:", error_output

        #call(["sudo","ip","netns","exec","qdhcp-"+new_network.get('network').get('id'), "ping", ])
        

        '''    
        # Cleanup
        print "Cleanup:"
        self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
        self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost2")
        self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
        time.sleep(5)
        self.controller.deleteNetwork(new_network.get('network').get('id'), self.new_tenant, 
                                      self.new_user, self.new_password)
        new_user.delete()
        new_project.delete()
        '''
        print "Done"
        
