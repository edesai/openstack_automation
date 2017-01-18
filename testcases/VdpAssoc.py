'''
Created on Nov 21, 2016

@author: edesai
'''

from nodes.Controller import Controller
from nodes.Compute import Compute
from common.MySqlConnection import MySqlConnection
from common.Uplink import Uplink
import time
from common.VdpToolCli import VdpToolCli
from common.ReturnValue import ReturnValue
from common.MySqlDbTables import MySqlDbTables
from common.CheckStatusOfServices import CheckStatusOfServices
from constants import resultConstants



class VdpAssoc(object):
    '''
    classdocs
    '''
    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self.config_dict = config_dict
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


            #Create instance
            host1 = self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password, new_network_inst1.network.get('network').get('id'),
                                                   self.new_inst1, key_name=keypair_secgrp.key_pair, availability_zone=None)
            print "Host1:", host1

            print "Connecting to database"
            #Connect to database
            mysql_db = MySqlConnection(self.config_dict)
            
            with MySqlConnection(self.config_dict) as mysql_connection:
            
                data = mysql_db.get_instances(mysql_connection, self.new_inst1)
                print "Host name is:", data[MySqlDbTables.INSTANCES_HOST_NAME]
                host_name = data[MySqlDbTables.INSTANCES_HOST_NAME]

            uplinkInst = Uplink(self.config_dict)
            uplink_info = Uplink.get_info(uplinkInst, host_name)
            print "uplink veth:", uplink_info.vethInterface
            print "remote_port",  uplink_info.remotePort
            
            inst_str =  str((host1[0].networks[self.new_network1])[0])
            
            vdptool_inst = VdpToolCli()
            result = VdpToolCli.check_output(vdptool_inst, self.controller.ip, self.controller.sys_username, 
                                     self.controller.password, uplink_info.vethInterface, inst_str)
            if result is False:
                raise Exception("Incorrect vdptool cmd output.\n")
     
        except Exception as e:
            print "Created Exception: ",e
            self.cleanup()
            return ReturnValue.FAILURE    
        
        self.cleanup()
        print "Done"   
        return ReturnValue.SUCCESS 
    
    def cleanup(self):                
        print "Cleanup:"
        skip_proj = False
        skip_nw = False
        
        try:
            new_project_user = self.controller.getProjectUser(self.new_tenant, self.new_user)
            if not new_project_user:
                print "Project/User not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e
                
        if skip_proj is False:    
            try:
                self.controller.deleteInstance(new_project_user.tenant.id, self.new_user, self.new_password, self.new_inst1)
            except Exception as e:
                print "Error:", e
            
            try:
                self.controller.deleteKeyPair(new_project_user.tenant.id, self.new_user, self.new_password)
                time.sleep(5)                
            except Exception as e:
                print "Error:", e   
        
        if not(skip_nw and skip_proj):    
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
         
