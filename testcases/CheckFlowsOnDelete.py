'''
Created on Oct 25, 2016

@author: edesai
'''
from testcases.BaseTest import BaseTest
from nodes.Controller import Controller
from nodes.Compute import Compute
import time
import sys
from common.utils import SSHConnection
from common.MySqlConnection import MySqlConnection
import subprocess
import re


class CheckFlowsOnDelete(object):
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
        self.new_subnw = "20.20.30.0/24"
        
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
                                                   self.new_tenant,self.new_user, self.new_password,
                                                   self.new_subnw)
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
        

        print "Connecting to database"
        #Connect to database
        mysql_db = MySqlConnection(self.args)
        
        with MySqlConnection(self.args) as mysql_connection:
            try:
                data = mysql_db.get_instances(mysql_connection, "autohost1")
                print "Instance name:", data[1], ", Instance IP:", data[6], ", vdp_vlan:", data[11] 
                vdpVlan = data[11]   
            except Exception as e:
                print "Created Exception: ",e
                print "Cleanup: "
                self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
                self.cleanup(new_network, new_user, new_project)
                return 1 #TODO: Return correct retval
                
        with SSHConnection(address=self.controller.ip, username=self.controller.sys_username, password = self.controller.password) as client:
            stdin, stdout, stderr = client.exec_command("sudo ovs-ofctl dump-flows br-ethd")
            
            output = "".join(stdout.readlines())
            error_output = "".join(stderr.readlines()).strip()
            if error_output:
                print "br-ethd Error:", error_output 
                print "Cleanup: "
                self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
                self.cleanup(new_network, new_user, new_project)    
                return 1 #TODO: Return correct retval
            print "Output:", output

            for line in output.splitlines():
                line = line.rstrip()
                x = re.search('(?<=mod_vlan_vid:)\d+', line)
                if x:
                    print "VDP VLAN is:", x.group(0) 
                    if long(x.group(0)) == vdpVlan:
                        print "VDP VLAN found:", vdpVlan
                        break
            if error_output:
                print "br-ethd Error:", error_output 
                print "Cleanup: "
                self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
                self.cleanup(new_network, new_user, new_project)
                return 1 #TODO: Return correct retval 
            stdin, stdout, stderr = client.exec_command("sudo ovs-ofctl dump-flows br-int")
            
            output = "".join(stdout.readlines())
            error_output = "".join(stderr.readlines()).strip()
            if error_output:
                print "br-int Error:", error_output  
                print "Cleanup: "
                self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
                self.cleanup(new_network, new_user, new_project)   
                return 1 #TODO: Return correct retval
            
            print "Output:", output

            for line in output.splitlines():
                line = line.rstrip()
                x = re.search('(?<=mod_vlan_vid:)\d+', line)
                if x:
                    print "VDP VLAN is:", x.group(0) 
                    if long(x.group(0)) == vdpVlan:
                        print "VDP VLAN found:", vdpVlan
                        break
            if error_output:
                print "br-int Error:", error_output  
                print "Cleanup: "
                self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
                self.cleanup(new_network, new_user, new_project)   
                return 1 #TODO: Return correct retval
            
        self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
        print "Deleting Instance autohost1..."
        self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
        
        '''max_retries = 4
        for i in range(max_retries):
            try:
                time.sleep (5)
                break
            except Exception as e:
                print "Created Exception: Timeout Error ", e
                print "Cleanup: "
                self.cleanup(new_network, new_user, new_project)
                return 1 #TODO: Return correct retval'''
            
        with SSHConnection(address=self.controller.ip, username=self.controller.sys_username, password = self.controller.password) as client:
            stdin, stdout, stderr = client.exec_command("sudo ovs-ofctl dump-flows br-ethd")
            
            output = "".join(stdout.readlines())
            error_output = "".join(stderr.readlines()).strip()
            if error_output:
                print "Error:", error_output  
                print "Cleanup: "
                self.cleanup(new_network, new_user, new_project)   
                return 1 #TODO: Return correct retval
            print "Output:", output

            for line in output.splitlines():
                line = line.rstrip()
                x = re.search('(?<=mod_vlan_vid:)\d+', line)
                if x:
                    if long(x.group(0)) == vdpVlan:
                        print "VDP VLAN found:", vdpVlan
                        print "Flows not deleted from br-ethd...Failing the test case..."
                        print "Cleanup: "
                        self.cleanup(new_network, new_user, new_project)
                        return 1 #TODO: Return correct retval
                        break
            stdin, stdout, stderr = client.exec_command("sudo ovs-ofctl dump-flows br-int")
            
            output = "".join(stdout.readlines())
            error_output = "".join(stderr.readlines()).strip()
            if error_output:
                print "Error:", error_output     
                print "Cleanup: "
                self.cleanup(new_network, new_user, new_project)
                return 1 #TODO: Return correct retval
            print "Output:", output

            for line in output.splitlines():
                line = line.rstrip()
                x = re.search('(?<=mod_vlan_vid:)\d+', line)
                if x:
                    if long(x.group(0)) == vdpVlan:
                        print "VDP VLAN found:", vdpVlan
                        print "Flows not deleted from br-int...Failing the test case..."
                        print "Cleanup: "
                        self.cleanup(new_network, new_user, new_project)
                        return 1 #TODO: Return correct retval
                        break
        print "Cleanup: "
        self.cleanup(new_network, new_user, new_project)
        print "Done"
        return 0
                
    def cleanup(self, new_network, new_user, new_project):                
        self.controller.deleteNetwork(new_network.get('network').get('id'), self.new_tenant, 
                                      self.new_user, self.new_password)
        new_user.delete()
        new_project.delete()
        return 0
         
        
        