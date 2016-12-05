'''
Created on Dec 1, 2016

@author: edesai
'''
from testcases.BaseTest import BaseTest
from nodes.Controller import Controller
from nodes.Compute import Compute
import time
from common.Utils import SSHConnection
from common.MySqlConnection import MySqlConnection
from novaclient import client as nova_client
from collections import OrderedDict
import json

class SameSubnetSameComputePing(object):
    '''
    classdocs
    '''


    def __init__(self, config_dict):
        '''
        Constructor
        '''
        
        self.controller = Controller(config_dict['controller']['address'], config_dict['controller']['username'],
                                    config_dict['controller']['password'], config_dict['controller']['sys_username'])

        self.computeHosts = []
        for compute in config_dict['computes']:
            self.computeHosts.append(Compute(compute['address'], compute['username'], compute['password']))
        
        self.admin_username = config_dict['controller']['username']
        self.admin_password = config_dict['controller']['password']
        self.new_tenant = "auto"
        self.new_user = "auto_user"
        self.new_password = "cisco123"
        self.new_network1 = "auto_nw1"
        self.new_subnw1 = "20.20.30.0/24"

             
    # TODO: enforce this
    def runTest(self):
        try:
            #Create project
            new_project = self.controller.createProject(self.new_tenant)
        except Exception as e:
            print "Error:", e 
            return 1
          
        try:    
            #Create user
            new_user = self.controller.createUser(new_project, 
                                       new_username = self.new_user, 
                                       new_password = self.new_password)
        except Exception as e:
            print "Error:", e
            new_project.delete()
            return 1
        
        try:    
            #Create 1st network
            new_network1 = self.controller.createNetwork(self.new_tenant,self.new_network1, 
                                          self.new_user, self.new_password)
            print "New Network:", new_network1   
        except Exception as e:
            print "Error:", e
            new_user.delete()
            new_project.delete() 
            return 1
           
        try:
            #Create subnet
            new_subnet1 = self.controller.createSubnet(new_network1.get('network').get('id'), 
                                                       self.new_tenant,self.new_user, self.new_password,
                                                       self.new_subnw1)
            print "New Subnetwork:", new_subnet1
        except Exception as e:
            print "Error:", e                
            self.controller.deleteNetwork(new_network1.get('network').get('id'), self.new_tenant, 
                                          self.new_user, self.new_password)
            new_user.delete()
            new_project.delete()
            return 1
        
        
        try:
            #Create key-pair
            key_pair = self.controller.createKeyPair(new_project.id, self.new_user, 
                                                   self.new_password)
        except Exception as e:
            print "Error:", e                
            self.controller.deleteNetwork(new_network1.get('network').get('id'), self.new_tenant, 
                                          self.new_user, self.new_password)           
            new_user.delete()
            new_project.delete()
            return 1             
        
        try:    
            #Create security groups and rules
            self.controller.createSecurityGroup(new_project.id, self.new_user, 
                                                   self.new_password)
        except Exception as e:
            print "Error:", e
            self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
            time.sleep(5)                
            self.controller.deleteNetwork(new_network1.get('network').get('id'), self.new_tenant, 
                                          self.new_user, self.new_password)            
            new_user.delete()
            new_project.delete()
            return 1
        
        try:
            nova = self.controller.get_nova_client(new_project.id, self.new_user, self.new_password)
            aggregate = nova.aggregates.create(name="auto_agg", availability_zone = "az_auto_agg")
            aggregate.add_host("edesai-ucs-110")                
           
        except Exception as e:
            print "Error:", e
            self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
            time.sleep(5)                
            self.controller.deleteNetwork(new_network1.get('network').get('id'), self.new_tenant, 
                                          self.new_user, self.new_password)        
            new_user.delete()
            new_project.delete()
            return 1

        try:
            #Create instance
            nova = self.controller.get_nova_client(new_project.id, self.new_user , self.new_password)
            zones = nova.availability_zones.list()    
            for zone in zones:
                zone_name = str(zone.zoneName)
                if zone_name == "az_auto_agg":
                    print "Launching instance in zone: ", zone_name 
                    host1 = self.controller.createInstance(new_project.id, self.new_user, 
                                                           self.new_password, new_network1.get('network').get('id'),
                                                           "autohost1", key_name=key_pair, availability_zone=zone_name)
                    print "Host1:", host1
                    break
                
        except Exception as e:
            print "Error:", e
            aggregate.remove_host("edesai-ucs-110")
            nova.aggregates.delete(aggregate)
            self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
            time.sleep(5)                
            self.controller.deleteNetwork(new_network1.get('network').get('id'), self.new_tenant, 
                                          self.new_user, self.new_password)        
            new_user.delete()
            new_project.delete()
            return 1
        
        try:
            #Create instance
            nova = self.controller.get_nova_client(new_project.id, self.new_user , self.new_password)
            zones = nova.availability_zones.list()    
            for zone in zones:
                zone_name = str(zone.zoneName)
                if zone_name == "az_auto_agg":
                    print "Launching instance in zone: ", zone_name        
                    host2 = self.controller.createInstance(new_project.id, self.new_user, 
                                                           self.new_password, new_network1.get('network').get('id'),
                                                           "autohost2", key_name=key_pair, availability_zone=zone_name)
                    print "Host2:", host2
                    break
                
        except Exception as e:
            print "Error:", e
            aggregate.remove_host("edesai-ucs-110")
            nova.aggregates.delete(aggregate)
            self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
            self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
            time.sleep(5)
            self.controller.deleteNetwork(new_network1.get('network').get('id'), self.new_tenant, 
                              self.new_user, self.new_password)
            new_user.delete()
            new_project.delete()
            return 1
            
        with SSHConnection(address=self.controller.ip, username=self.controller.sys_username, password = self.controller.password) as client:
            failure_list = ["unreachable","100% packet loss","0 received"]
            
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network1.get('network').get('id')+" ping -c 3 20.20.30.4")
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            if error_output:
                print "Error:", error_output
            for word in failure_list:
                if word in output:
                    print "Ping failed...Failing test case\n"
                    self.cleanup(new_network1, new_user, new_project)
                    return 1
            
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network1.get('network').get('id')+" ping -c 3 20.20.30.3")
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            if error_output:
                print "Error:", error_output
            for word in failure_list:
                if word in output:
                    print "Ping failed...Failing test case\n"
                    self.cleanup(new_network1, new_user, new_project)
                    return 1
            
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network1.get('network').get('id')+" ping -c 3 20.20.30.2")
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            if error_output:
                print "Error:", error_output
            for word in failure_list:
                if word in output:
                    print "Ping failed...Failing test case\n"
                    self.cleanup(new_network1, new_user, new_project)
                    return 1
        aggregate.remove_host("edesai-ucs-110")        
        nova.aggregates.delete(aggregate)       
        self.cleanup(new_network1, new_user, new_project)
        
        return 0
        
    def cleanup(self, new_network1, new_user, new_project):
        print "Cleanup:"
        self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
        self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost2")
        self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
        time.sleep(5)                
        self.controller.deleteNetwork(new_network1.get('network').get('id'), self.new_tenant, 
                                      self.new_user, self.new_password)
        new_user.delete()
        new_project.delete()
        print "Done"
        return 0

        
      
        