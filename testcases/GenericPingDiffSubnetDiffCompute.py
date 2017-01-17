'''
Created on Jan 12, 2017

@author: edesai
'''

from nodes.Controller import Controller
from nodes.Compute import Compute
import time
from common.ReturnValue import ReturnValue
from common.Ping import Ping
import math

class GenericPingDiffSubnetDiffCompute(object):
    '''
    classdocs
    '''

    def __init__(self, config_dict):
        '''
        Constructor
        '''
        
        self.controller = Controller(config_dict['controller']['hostname'], config_dict['controller']['ip'], config_dict['controller']['username'],
                                    config_dict['controller']['password'], config_dict['controller']['sys_username'])
        
        self.computeCount = 0
        self.computeHosts = []
        for compute in config_dict['computes']:
            self.computeHosts.append(Compute(compute['hostname'], compute['ip'], compute['username'], compute['password']))
            self.computeCount = self.computeCount + 1
        
        self.new_tenant = config_dict['openstack_tenant_details']['tenant_name']
        
        if "tenant_username" in config_dict["openstack_tenant_details"] and config_dict['openstack_tenant_details']['tenant_username'] != None:
            self.new_user = config_dict['openstack_tenant_details']['tenant_username']
        else:
            self.new_user = "auto_user"    
        if "tenant_password" in config_dict["openstack_tenant_details"] and config_dict['openstack_tenant_details']['tenant_password'] != None:
            self.new_password = config_dict['openstack_tenant_details']['tenant_password']
        else:
            self.new_password = "cisco123"
        self.new_network1 = self.new_tenant+"nw1"
        self.new_subnw1 = "10.11.12.0/24"
        self.new_network2 = self.new_tenant+"nw2"
        self.new_subnw2 = "10.13.14.0/24"
        self.new_inst = self.new_tenant+"inst"
        self.config_dict = config_dict
             
    
    def runTest(self):
        
        agg = []
        aggregate = []
        zone = []
        vm = []
        ip_vm = []
    
        try:
            
            #Create project
            new_project = self.controller.createProject(self.new_tenant)
            
            nova = self.controller.get_nova_client(new_project.id, self.new_user, self.new_password)  
            if not nova:
                raise Exception("Nova client not found")
            
            #Create user
            new_user = self.controller.createUser(new_project, 
                                       new_username = self.new_user, 
                                       new_password = self.new_password)
            
            #Create 1st network
            new_network1 = self.controller.createNetwork(self.new_tenant,self.new_network1, 
                                          self.new_user, self.new_password)
            print "New Network:", new_network1   
            
            #Create subnet
            new_subnet1 = self.controller.createSubnet(new_network1.get('network').get('id'), 
                                                       self.new_tenant,self.new_user, self.new_password,
                                                       self.new_subnw1)
            print "New Subnetwork:", new_subnet1
            
            #Create 2nd network
            new_network2 = self.controller.createNetwork(self.new_tenant, self.new_network2, 
                                          self.new_user, self.new_password)
            print "New Network:", new_network2   

            #Create subnet
            new_subnet2 = self.controller.createSubnet(new_network2.get('network').get('id'), 
                                                       self.new_tenant,self.new_user, self.new_password,
                                                       self.new_subnw2)
            print "New Subnetwork:", new_subnet2
            
            #Create key-pair
            key_pair = self.controller.createKeyPair(new_project.id, self.new_user, 
                                                   self.new_password)
    
            #Create security groups and rules
            self.controller.createSecurityGroup(new_project.id, self.new_user, 
                                                   self.new_password)

            hosts_list = self.computeHosts
            nw1_compute_count = math.floor(self.computeCount)
            
            #Put first half computes on nw1
            for host in range(int(nw1_compute_count)):
                #Create an aggregate with availability zone per compute/host
                agg.append(self.new_tenant+"_agg_" + hosts_list[host].hostname)
                zone.append(self.new_tenant+"_az_"+ hosts_list[host].hostname)
                aggregate.append(self.controller.createAggregate(new_project.id, self.new_user, 
                                                       self.new_password, agg_name=agg[host], 
                                                       availability_zone=zone[host]))
                aggregate[host].add_host(hosts_list[host].hostname)
                #Create instance
                vm.append(self.controller.createInstance(new_project.id, self.new_user, 
                                                           self.new_password, new_network1.get('network').get('id'),
                                                           self.new_inst+str(host), key_name=key_pair, availability_zone=zone[host]))            

                print "VM["+str(host)+"]:", vm[host] 
                ip_vm.append(str((vm[host][0].networks[self.new_network1])[0]))
                print "IP of VM["+str(host)+"]:", ip_vm[host]
            
            for host in range(int(nw1_compute_count), int(self.computeCount - 1)):
                #Create an aggregate with availability zone per compute/host
                agg.append(self.new_tenant+"_agg_" + hosts_list[host].hostname)
                zone.append(self.new_tenant+"_az_"+ hosts_list[host].hostname)
                aggregate.append(self.controller.createAggregate(new_project.id, self.new_user, 
                                                       self.new_password, agg_name=agg[host], 
                                                       availability_zone=zone[host]))
                aggregate[host].add_host(hosts_list[host].hostname)
                #Create instance
                vm.append(self.controller.createInstance(new_project.id, self.new_user, 
                                                           self.new_password, new_network2.get('network').get('id'),
                                                           self.new_inst+str(host), key_name=key_pair, availability_zone=zone[host]))            

                print "VM["+str(host)+"]:", vm[host] 
                ip_vm.append(str((vm[host][0].networks[self.new_network2])[0]))
                print "IP of VM["+str(host)+"]:", ip_vm[host] 

            pingObj = Ping()
            dhcp_ip1 = self.new_subnw1[:-4]+"2"
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                        new_network1.get('network').get('id'), dhcp_ip1)
            dhcp_ip2 = self.new_subnw2[:-4]+"2"
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                        new_network1.get('network').get('id'), dhcp_ip2)
            if not result:
                raise Exception("Ping failed...Failing test case\n")
            
            for host in range(int(nw1_compute_count)):
                #Verify Ping using DHCP namespace
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network1.get('network').get('id'), ip_vm[host])                
                if not result:
                    raise Exception("Ping failed...Failing test case\n")
                
            for host in range(int(nw1_compute_count), int(self.computeCount - 1)):
                #Verify Ping using DHCP namespace
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network2.get('network').get('id'), ip_vm[host])                
                if not result:
                    raise Exception("Ping failed...Failing test case\n")
                
        except Exception as e:
            print "Created Exception: ",e
            self.cleanup()
            return ReturnValue.FAILURE
        
        self.cleanup()
        return ReturnValue.SUCCESS
    
        
    
    def cleanup(self):
        
        print "Cleanup:"
        
        agg = []
        aggregate = []
        zone = []
        skip_nova = False
        skip_proj = False
        
        
        hosts_list = self.computeHosts
        try:
            new_project = self.controller.getProject(self.new_tenant)
            if not new_project:
                print "Project not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e
        
        if skip_proj is False:
            try: 
                nova = self.controller.get_nova_client(new_project.id, self.new_user, self.new_password)  
                if not nova:
                    print("Nova client not found during cleanup")
                    skip_nova = True
            except Exception as e:
                print "Error:", e
            
        nw1_compute_count = math.floor(self.computeCount)
        if skip_nova is False and skip_proj is False:        
            try:
                for host in range(int(nw1_compute_count)):
                    agg.append(self.new_tenant+"_agg_" + hosts_list[host].hostname) 
                    aggregate.append(self.controller.getAggregate(new_project.id, self.new_user, self.new_password,
                                                                   agg_name=agg[host]))
                    zone.append(self.new_tenant+"_az_"+hosts_list[host].hostname)  
                    aggregate[host].remove_host(hosts_list[host].hostname)   
 
            except Exception as e:
                print "Error:", e
                
            try:
                for host in range(int(nw1_compute_count)):
                    if aggregate[host]:             
                        nova.aggregates.delete(aggregate[host]) 
            except Exception as e:
                print "Error:", e
            
            try:
                for host in range(int(nw1_compute_count), int(self.computeCount - 1)):
                    agg.append(self.new_tenant+"_agg_" + hosts_list[host].hostname) 
                    aggregate.append(self.controller.getAggregate(new_project.id, self.new_user, self.new_password,
                                                                   agg_name=agg[host]))
                    zone.append(self.new_tenant+"_az_"+hosts_list[host].hostname)  
                    aggregate[host].remove_host(hosts_list[host].hostname)   
 
            except Exception as e:
                print "Error:", e
                
            try:
                for host in range(int(nw1_compute_count), int(self.computeCount - 1)):
                    if aggregate[host]:             
                        nova.aggregates.delete(aggregate[host]) 
            except Exception as e:
                print "Error:", e
        if skip_proj is False:    
            
            for host in range(self.computeCount):
                try:
                    self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, self.new_inst+str(host))
                except Exception as e:
                    print "Error:", e

            try:
                self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                time.sleep(5)                
            except Exception as e:
                print "Error:", e
        try:
            new_network1 = self.controller.getNetwork(self.new_tenant, self.new_network1, 
                                                         self.new_user, self.new_password)
            if not new_network1:
                print("Network not found during cleanup")
            else:
                self.controller.deleteNetwork(new_network1['id'], self.new_tenant, 
                                      self.new_user, self.new_password)    
        except Exception as e:
            print "Error:", e
        
        try:
            new_network2 = self.controller.getNetwork(self.new_tenant, self.new_network2, 
                                                         self.new_user, self.new_password)
            if not new_network2:
                print("Network not found during cleanup")
            else:
                self.controller.deleteNetwork(new_network2['id'], self.new_tenant, 
                                      self.new_user, self.new_password)    
        except Exception as e:
            print "Error:", e
        
        try:
            new_user = self.controller.getUser(self.new_user)
            if not new_user:
                print("User not found during cleanup")
            else:
                new_user.delete()    
        except Exception as e:
            print "Error:", e
        
        if skip_proj is False:    
            try:
                new_project.delete()
            except Exception as e:
                print "Error:", e
        
        print "Done"
        return ReturnValue.SUCCESS
    

        