'''
Created on Dec 1, 2016

@author: edesai
'''

from nodes.Controller import Controller
from nodes.Compute import Compute
import time
from common.Utils import SSHConnection
from common.MySqlConnection import MySqlConnection
from common.ReturnValue import ReturnValue
from common.MySqlDbTables import MySqlDbTables
from common.Ping import Ping
from common.CheckStatusOfServices import CheckStatusOfServices
from constants import resultConstants

class SameSubnetSameComputePing(object):
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
            self.computeHosts.append(Compute(compute['hostname'], compute['ip'], compute['username'], compute['password']))
        
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
        self.new_inst1 = self.new_tenant+"inst1"
        self.new_inst2 = self.new_tenant+"inst2"
        self.config_dict = config_dict

             
    def runTest(self):
        
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

            #Create key-pair & security groups and rules
            keypair_secgrp = self.controller.createKeyPairSecurityGroup(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password)
            
            
            #Create an aggregate with availability zone
            hosts_list = self.computeHosts
            zone1 = self.new_tenant+"_az_"+hosts_list[0]['hostname']
            agg_name=self.new_tenant+"_agg_"+hosts_list[0]['hostname']
            aggregate1 = self.controller.createAggregate(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password, agg_name, 
                                                   availability_zone = zone1)
            
            if hosts_list:
                aggregate1.add_host(hosts_list[0].hostname)                
            else:
                raise Exception("No hosts found")

            #Create instance
            host1 = self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                               self.new_password, new_network_inst1.network.get('network').get('id'),
                                               self.new_inst1, key_name=keypair_secgrp.key_pair, availability_zone=zone1)
            print "Host1:", host1
            host2 = self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                               self.new_password, new_network_inst1.get('network').get('id'),
                                               self.new_inst2, key_name=keypair_secgrp.key_pair, availability_zone=zone1)
            print "Host2:", host2
            
                
            ip_host1 = str((host1[0].networks[self.new_network1])[0])
            ip_host2 = str((host2[0].networks[self.new_network1])[0])    
            
            
            #Verify Ping using DHCP namespace on controller
            pingObj = Ping()
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                        new_network_inst1.network.get('network').get('id'), ip_host1)
            if not result:
                raise Exception("Ping failed...Failing test case\n")
            
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                        new_network_inst1.network.get('network').get('id'), ip_host2)
            if not result:
                raise Exception("Ping failed...Failing test case\n") 
            
            dhcp_ip = self.new_subnw1[:-4]+"2"
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                        new_network_inst1.network.get('network').get('id'), dhcp_ip)
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
        skip_proj = False
        hosts_list = []
        
        try:
            new_project_user = self.controller.getProjectUser(self.new_tenant, self.new_user)
            if not new_project_user:
                print "Project/User not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e
    
        try:
            agg1 = self.new_tenant+"_agg_"+self.config_dict['computes'][0]['hostname'] 
            hosts_list = self.computeHosts
            
            self.controller.deleteAggregate(self.controller, new_project_user.tenant.id, 
                                            self.new_user, self.new_password, agg1, hosts_list[0])
        except Exception as e:
            print "Error:", e       
                
        if skip_proj is False:    
            try:
                self.controller.deleteInstance(new_project_user.tenant.id, self.new_user, self.new_password, self.new_inst1)
            except Exception as e:
                print "Error:", e
            
            try:
                self.controller.deleteInstance(new_project_user.tenant.id, self.new_user, self.new_password, self.new_inst2)
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
            self.controller.deleteProjectUser(self.controller, new_project_user)
        except Exception as e:
            print "Error:", e 
        
        print "Done cleaning"
        return ReturnValue.SUCCESS
        
        
      
        