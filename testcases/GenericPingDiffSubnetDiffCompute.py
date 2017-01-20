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
from common.CheckStatusOfServices import CheckStatusOfServices
from constants import resultConstants

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
            #Basic checks for status of services
            status_inst = CheckStatusOfServices(self.config_dict)
            status = CheckStatusOfServices.check(status_inst)
            if not status:
                print "Some service/s not running...Unable to run testcase"
                return resultConstants.RESULT_ABORT
            
            #Create project & user
            new_project_user = self.controller.createProjectUser(self.new_tenant, 
                                                            self.new_user,
                                                            self.new_password)
            
            #Create network and subnetwork
            new_network_inst1 = self.controller.createNetworkSubNetwork(self.new_tenant,self.new_network1,  
                                          self.new_subnw1, self.new_user, self.new_password)

            new_network_inst2 = self.controller.createNetworkSubNetwork(self.new_tenant,self.new_network2,  
                                          self.new_subnw2, self.new_user, self.new_password)
            #Create key-pair & security groups and rules
            keypair_secgrp = self.controller.createKeyPairSecurityGroup(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password)

            hosts_list = self.computeHosts
            nw1_compute_count = math.floor(self.computeCount)
            
            #Put first half computes on nw1
            for host in range(int(nw1_compute_count)):
                #Create an aggregate with availability zone per compute/host
                agg.append(self.new_tenant+"_agg_" + hosts_list[host].hostname)
                zone.append(self.new_tenant+"_az_"+ hosts_list[host].hostname)
                aggregate.append(self.controller.createAggregate(new_project_user.tenant.id, self.new_user, 
                                                       self.new_password, agg_name=agg[host], 
                                                       availability_zone=zone[host]))
                aggregate[host].add_host(hosts_list[host].hostname)
                
                #Create instance
                vm.append(self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                                           self.new_password, new_network_inst1.network.get('network').get('id'),
                                                           self.new_inst+str(host), key_name=keypair_secgrp.key_pair, availability_zone=zone[host]))            

                print "VM["+str(host)+"]:", vm[host] 
                ip_vm.append(str((vm[host][0].networks[self.new_network1])[0]))
                print "IP of VM["+str(host)+"]:", ip_vm[host]
            
            for host in range(int(nw1_compute_count), int(self.computeCount - 1)):
                #Create an aggregate with availability zone per compute/host
                agg.append(self.new_tenant+"_agg_" + hosts_list[host].hostname)
                zone.append(self.new_tenant+"_az_"+ hosts_list[host].hostname)
                aggregate.append(self.controller.createAggregate(new_project_user.tenant.id, self.new_user, 
                                                       self.new_password, agg_name=agg[host], 
                                                       availability_zone=zone[host]))
                aggregate[host].add_host(hosts_list[host].hostname)
                #Create instance
                vm.append(self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                                           self.new_password, new_network_inst2.network.get('network').get('id'),
                                                           self.new_inst+str(host), key_name=keypair_secgrp.key_pair, availability_zone=zone[host]))            

                print "VM["+str(host)+"]:", vm[host] 
                ip_vm.append(str((vm[host][0].networks[self.new_network2])[0]))
                print "IP of VM["+str(host)+"]:", ip_vm[host] 

            pingObj = Ping()
            dhcp_ip1 = self.new_subnw1[:-4]+"2"
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                        new_network_inst1.network.get('network').get('id'), dhcp_ip1)
            dhcp_ip2 = self.new_subnw2[:-4]+"2"
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                        new_network_inst1.network.get('network').get('id'), dhcp_ip2)
            if not result:
                raise Exception("Ping failed...Failing test case\n")
            
            for host in range(int(nw1_compute_count)):
                #Verify Ping using DHCP namespace
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network_inst1.network.get('network').get('id'), ip_vm[host])                
                if not result:
                    raise Exception("Ping failed...Failing test case\n")
                
            for host in range(int(nw1_compute_count), int(self.computeCount - 1)):
                #Verify Ping using DHCP namespace
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network_inst2.network.get('network').get('id'), ip_vm[host])                
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
        agg_list = []
        skip_proj = False
        
        
        hosts_list = self.computeHosts
        try:
            new_project_user = self.controller.getProjectUser(self.new_tenant, self.new_user)
            if not new_project_user:
                print "Project/User not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e
            
        nw1_compute_count = math.floor(self.computeCount)
        if skip_proj is False:        
            try:
                for host in range(self.computeCount):
                    #Create an aggregate with availability zone per compute/host
                    agg_list.append(self.new_tenant+"_agg_" + hosts_list[host].hostname)

                self.controller.deleteAggregateList(self.controller, new_project_user.tenant.id, self.new_user, 
                                                self.new_password, agg_list, hosts_list)
            except Exception as e:
                print "Error:", e
    
        if skip_proj is False:    
            
            for host in range(self.computeCount):
                try:
                    self.controller.deleteInstance(new_project_user.tenant.id, self.new_user, self.new_password, self.new_inst+str(host))
                except Exception as e:
                    print "Error:", e

            try:
                self.controller.deleteKeyPair(new_project_user.tenant.id, self.new_user, self.new_password)
                time.sleep(5)                
            except Exception as e:
                print "Error:", e
        try:
            self.controller.deleteNetwork(self.controller, self.new_network1, self.new_tenant, 
                                      self.new_user, self.new_password)
        except Exception as e:
            print "Error:", e
        
        try:
            self.controller.deleteNetwork(self.controller, self.new_network2, self.new_tenant, 
                                      self.new_user, self.new_password)
        except Exception as e:
            print "Error:", e
        
        try:
            self.controller.deleteProjectUser(self.controller, new_project_user)
        except Exception as e:
            print "Error:", e
        
        print "Done"
        return ReturnValue.SUCCESS
    

        