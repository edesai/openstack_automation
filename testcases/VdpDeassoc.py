'''
Created on Nov 21, 2016

@author: edesai
'''

from nodes.Controller import Controller
from nodes.Compute import Compute
from common.MySqlConnection import MySqlConnection
from common.Uplink import Uplink
from common.VdpToolCli import VdpToolCli
import time
from common.ReturnValue import ReturnValue
from common.MySqlDbTables import MySqlDbTables
from common.CheckStatusOfServices import CheckStatusOfServices
from constants import resultConstants
 



class VdpDeassoc(object):
    '''
    classdocs
    '''
    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self.config_dict = config_dict
        self.controller = Controller(config_dict['controller']['hostname'], 
                                     config_dict['controller']['ip'], 
                                     config_dict['controller']['username'],
                                     config_dict['controller']['password'], 
                                     config_dict['controller']['sys_username'])

        self.computeHosts = []
        for compute in config_dict['computes']:
            self.computeHosts.append(Compute(compute['hostname'], 
                                             compute['ip'], compute['username'], 
                                             compute['password']))

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


            #Create instance
            host1 = self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password, new_network_inst1.network.get('network').get('id'),
                                                   self.new_inst1, key_name=keypair_secgrp.key_pair, availability_zone=None)
            print "Host1:", host1
        
            time.sleep(20) #Wait for flows to be added
        
            vdptool_inst = VdpToolCli()
            result = VdpToolCli.check_uplink_and_output(vdptool_inst, self.config_dict,
                                                        str((host1.networks[self.new_network1])[0]), 
                                                        host1.name, host1.host_name)
            if result is False:
                raise Exception("Incorrect vdptool cmd output.\n") 
                   
            self.controller.deleteKeyPair(new_project_user.tenant.id, self.new_user, self.new_password)
            self.controller.deleteInstance(new_project_user.tenant.id, 
                                           self.new_user, self.new_password, self.new_inst1)
            
            time.sleep(20) #Wait for flows to be deleted
            
            vdptool_inst = VdpToolCli()
            result = VdpToolCli.check_uplink_and_output(vdptool_inst, self.config_dict,
                                                        str((host1.networks[self.new_network1])[0]), 
                                                        host1.name, host1.host_name)
            if result is True:
                raise Exception("Incorrect vdptool cmd output.\n")
                    
            else:
                print "Instance NOT found in vdptool cmd output. Passing the testcase.\n"
                         
                
        except Exception as e:
            print "Created Exception: ",e
            self.cleanup()
            return ReturnValue.FAILURE        
        
        
        self.cleanup()
        print "Done"   
        return ReturnValue.SUCCESS
    
    def cleanup(self):                
        print "Cleanup:"
        
        try:
            new_project_user = self.controller.getProjectUser(self.new_tenant, self.new_user)
            if not new_project_user:
                print "Project/User not found during cleanup"
                
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
    