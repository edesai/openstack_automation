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

class DiffSubnetSameComputePing(object):
    '''
    classdocs
    '''


    def __init__(self, config_dict):
        '''
        Constructor
        '''
        
        self.controller = Controller(config_dict['controller']['hostname'], config_dict['controller']['ip'], config_dict['controller']['username'],
                                    config_dict['controller']['password'], config_dict['controller']['sys_username'])

        self.computeHosts = []
        for compute in config_dict['computes']:
            self.computeHosts.append(Compute(compute['address'], compute['username'], compute['password']))
        
        self.admin_username = config_dict['controller']['username']
        self.admin_password = config_dict['controller']['password']
        self.new_tenant = config_dict['openstack_tenant_details']['tenant_name']
        self.new_user = config_dict['openstack_tenant_details']['tenant_username']
        self.new_password = config_dict['openstack_tenant_details']['tenant_password']
        self.new_network1 = config_dict['openstack_tenant_details']['tenant_network1']
        self.new_subnw1 = config_dict['openstack_tenant_details']['tenant_subnw1']
        self.new_network2 = config_dict['openstack_tenant_details']['tenant_network2']
        self.new_subnw2 = config_dict['openstack_tenant_details']['tenant_subnw2']
        self.new_inst1 = config_dict['openstack_tenant_details']['tenant_inst1']
        self.new_inst2 = config_dict['openstack_tenant_details']['tenant_inst2']
        self.config_dict = config_dict
                          
    # TODO: enforce this
    def runTest(self):
        try:
            #Create project
            new_project = self.controller.createProject(self.new_tenant)
            
        except Exception as e:
            print "Error:", e 
            return 1
        
        try: 
            nova = self.controller.get_nova_client(new_project.id, self.new_user, self.new_password)  
            if not nova:
                raise Exception("Nova client not found")
        except Exception as e:
            print "Error:", e
            self.cleanup()
            return 1     

        try:    
            #Create user
            new_user = self.controller.createUser(new_project, 
                                       new_username = self.new_user, 
                                       new_password = self.new_password)
        except Exception as e:
            print "Error:", e
            self.cleanup()
            return 1
        
        try:    
            #Create 1st network
            new_network1 = self.controller.createNetwork(self.new_tenant,self.new_network1, 
                                          self.new_user, self.new_password)
            print "New Network:", new_network1   
        except Exception as e:
            print "Error:", e
            self.cleanup() 
            return 1
           
        try:
            #Create subnet
            new_subnet1 = self.controller.createSubnet(new_network1.get('network').get('id'), 
                                                       self.new_tenant,self.new_user, self.new_password,
                                                       self.new_subnw1)
            print "New Subnetwork:", new_subnet1
        except Exception as e:
            print "Error:", e                
            self.cleanup()
            return 1
        
        try:    
            #Create 2nd network
            new_network2 = self.controller.createNetwork(self.new_tenant, self.new_network2, 
                                          self.new_user, self.new_password)
            print "New Network:", new_network2   
        except Exception as e:
            print "Error:", e
            self.cleanup() 
            return 1
           
        try:
            #Create subnet
            new_subnet2 = self.controller.createSubnet(new_network2.get('network').get('id'), 
                                                       self.new_tenant,self.new_user, self.new_password,
                                                       self.new_subnw2)
            print "New Subnetwork:", new_subnet2
        except Exception as e:
            print "Error:", e 
            self.cleanup()
            return 1
            
        try:
            #Create key-pair
            key_pair = self.controller.createKeyPair(new_project.id, self.new_user, 
                                                   self.new_password)
        except Exception as e:
            print "Error:", e                
            self.cleanup()
            return 1             
        
        try:    
            #Create security groups and rules
            self.controller.createSecurityGroup(new_project.id, self.new_user, 
                                                   self.new_password)
        except Exception as e:
            print "Error:", e
            self.cleanup()
            return 1
        
        try:
            agg1 = self.new_tenant+"_agg_"+self.config_dict['computes'][0]['address']
            zone1 = self.new_tenant+"_az_"+self.config_dict['computes'][0]['address']
            aggregate = self.controller.createAggregate(new_project.id, self.new_user, 
                                                   self.new_password, agg_name=agg1, 
                                                   availability_zone = zone1)
            hosts = nova.hosts.list()
            hosts_list = [h for h in hosts if h.zone == "nova"]
            if hosts_list:
                aggregate.add_host(hosts_list[0].host_name)                
            else:
                raise Exception("No hosts found")
        except Exception as e:
            print "Error:", e
            self.cleanup()
            return 1
        
        try:
            #Create instance
            zone1 = self.new_tenant+"_az_"+self.config_dict['computes'][0]['address']
            zones = nova.availability_zones.list()    
            for zone in zones:
                zone_name = str(zone.zoneName)
                if zone_name == zone1:
                    print "Launching instance in zone: ", zone_name 
                    host1 = self.controller.createInstance(new_project.id, self.new_user, 
                                                           self.new_password, new_network1.get('network').get('id'),
                                                           self.new_inst1, key_name=key_pair, availability_zone=zone_name)
                    print "Host1:", host1
                    break
                
        except Exception as e:
            print "Error:", e
            self.cleanup()
            return 1
        
        try:
            #Create instance
            zones = nova.availability_zones.list()    
            for zone in zones:
                zone_name = str(zone.zoneName)
                if zone_name == zone1:
                    print "Launching instance in zone: ", zone_name        
                    host2 = self.controller.createInstance(new_project.id, self.new_user, 
                                                           self.new_password, new_network2.get('network').get('id'),
                                                           self.new_inst2, key_name=key_pair, availability_zone=zone_name)
                    print "Host2:", host2
                    break
                
        except Exception as e:
            print "Error:", e
            self.cleanup()
            return 1
        
        print "Connecting to database"
        #Connect to database
        mysql_db = MySqlConnection(self.config_dict)
        
        with MySqlConnection(self.config_dict) as mysql_connection:
            try:
                data = mysql_db.get_instances(mysql_connection, self.new_inst1)
                ip_host1 = data[6]
                print "Ip of "+self.new_inst1+" is:"+ip_host1
                data = mysql_db.get_instances(mysql_connection, self.new_inst2)
                ip_host2 = data[6]
                print "Ip of "+self.new_inst2+" is:"+ip_host2
                
            except Exception as e:
                print "Created Exception: ",e
                print "Cleanup: " 
                self.cleanup()
                return 1
        
            
        with SSHConnection(address=self.controller.ip, username=self.controller.sys_username, password = self.controller.password) as client:
            failure_list = ["unreachable","100% packet loss","0 received"]
            
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network1.get('network').get('id')+" ping -c 3 "+ip_host1)
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            if error_output:
                print "Error:", error_output
            for word in failure_list:
                if word in output:
                    print "Ping failed...Failing test case\n"
                    self.cleanup()
                    return 1
                
            dhcp_ip1 = self.new_subnw1[:-4]+"2"
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network1.get('network').get('id')+" ping -c 3 "+dhcp_ip1)
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            if error_output:
                print "Error:", error_output
            for word in failure_list:
                if word in output:
                    print "Ping failed...Failing test case\n"
                    self.cleanup()
                    return 1
            
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network1.get('network').get('id')+" ping -c 3 "+ip_host2)
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            if error_output:
                print "Error:", error_output
            for word in failure_list:
                if word in output:
                    print "Ping failed...Failing test case\n"
                    self.cleanup()
                    return 1
                
            dhcp_ip2 = self.new_subnw2[:-4]+"2"
            stdin, stdout, stderr = client.exec_command("sudo ip netns exec qdhcp-"+new_network1.get('network').get('id')+" ping -c 3 "+dhcp_ip2)
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            if error_output:
                print "Error:", error_output
            for word in failure_list:
                if word in output:
                    print "Ping failed...Failing test case\n"
                    self.cleanup()
                    return 1 
                    
        self.cleanup()
        return 0

    
    def cleanup(self):
        
        print "Cleanup:"
        skip_nova = False
        skip_proj = False
        
        try:
            new_project = self.controller.getProject(self.new_tenant)
            if not new_project:
                print "Project not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e
        
        try: 
            nova = self.controller.get_nova_client(new_project.id, self.new_user, self.new_password)  
            if not nova:
                print("Nova client not found during cleanup")
                skip_nova = True
        except Exception as e:
            print "Error:", e
            
        if skip_nova is False:        
            try:
                agg1 = self.new_tenant+"_agg_"+self.config_dict['computes'][0]['address']    
                aggregate1 = self.controller.getAggregate(new_project.id, self.new_user, self.new_password,
                                                         agg_name=agg1)    
                if not aggregate1:
                    print("Aggregate1 not found during cleanup")
            except Exception as e:
                print "Error:", e
            
            try:
                hosts = nova.hosts.list()
                zone1 = self.new_tenant+"_az_"+self.config_dict['computes'][0]['address']
                host1 = [h for h in hosts if h.zone == zone1]    
                if host1 and aggregate1:
                    aggregate1.remove_host(host1[0].host_name)
                else:
                    print("Hosts not found during cleanup")
            except Exception as e:
                print "Error:", e
                
            try:             
                nova.aggregates.delete(aggregate1) 
            except Exception as e:
                print "Error:", e
                
        if skip_proj is False:    
            try:
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, self.new_inst1)
            except Exception as e:
                print "Error:", e
            
            try:
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, self.new_inst2)
            except Exception as e:
                print "Error:", e
            
            try:
                self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                time.sleep(5)                
            except Exception as e:
                print "Error:", e
        try:
            new_network1 = self.controller.getNetwork(self.new_tenant,self.new_network1, 
                                                         self.new_user, self.new_password)
            if not new_network1:
                print("Network not found during cleanup")
        except Exception as e:
            print "Error:", e
            
        try:
            self.controller.deleteNetwork(new_network1['id'], self.new_tenant, 
                                      self.new_user, self.new_password)
        except Exception as e:
            print "Error:", e
        
        try:
            new_network2 = self.controller.getNetwork(self.new_tenant,self.new_network2, 
                                                         self.new_user, self.new_password)
            if not new_network2:
                print("Network not found during cleanup")
        except Exception as e:
            print "Error:", e
            
        try:
            self.controller.deleteNetwork(new_network2['id'], self.new_tenant, 
                                      self.new_user, self.new_password)
        except Exception as e:
            print "Error:", e
        
        try:
            new_user = self.controller.getUser(self.new_user)
            if not new_user:
                print("User not found during cleanup")
        except Exception as e:
            print "Error:", e
            
        try:
            new_user.delete()
        except Exception as e:
            print "Error:", e
            
        try:
            new_project.delete()
        except Exception as e:
            print "Error:", e
        
        print "Done"
        return 0    