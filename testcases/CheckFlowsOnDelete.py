'''
Created on Oct 25, 2016

@author: edesai
'''

from nodes.Controller import Controller
from nodes.Compute import Compute
import time
from common.MySqlConnection import MySqlConnection
from common.OvsFlowsCli import OvsFlowsCli
from common.ReturnValue import ReturnValue
from common.MySqlDbTables import MySqlDbTables
from common.CheckStatusOfServices import CheckStatusOfServices
from constants import resultConstants


class CheckFlowsOnDelete(object):
    '''
    classdocs
    '''
    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self.config_dict = config_dict
        self.controller = Controller(config_dict['controller']['hostname'], config_dict['controller']['ip'] ,self.config_dict['controller']['username'], 
                                     self.config_dict['controller']['password'], config_dict['controller']['sys_username'])

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
                                                   self.new_password, new_network_inst1.get('network').get('id'),
                                                   self.new_inst1, key_name=keypair_secgrp.key_pair, availability_zone=None)
            print "Host1:", host1
        
            time.sleep(5)
            
            print "Connecting to database"
            #Connect to database
            mysql_db = MySqlConnection(self.config_dict)
            
            with MySqlConnection(self.config_dict) as mysql_connection:
            
                data = mysql_db.get_instances(mysql_connection, self.new_inst1)
                print "Instance name:", data[MySqlDbTables.INSTANCES_INSTANCE_NAME], ", Instance IP:", data[MySqlDbTables.INSTANCES_INSTANCE_IP], ", vdp_vlan:", data[MySqlDbTables.INSTANCES_VDP_VLAN] 
                vdp_vlan = str(data[MySqlDbTables.INSTANCES_VDP_VLAN])
                
            time.sleep(15) # wait for flows to be added

            search_str =  "dl_vlan="+vdp_vlan
            vdptool_inst = OvsFlowsCli()
            result = OvsFlowsCli.check_output(vdptool_inst, self.controller.ip, self.controller.sys_username, 
                                     self.controller.password, "br-int", search_str)
            if not result:
                raise Exception("Incorrect ovs flows output.\n")
            
            search_str = "mod_vlan_vid:"+vdp_vlan
            vdptool_inst = OvsFlowsCli()
            result = OvsFlowsCli.check_output(vdptool_inst, self.controller.ip, self.controller.sys_username, 
                                     self.controller.password, "br-ethd", search_str)
            if not result:
                raise Exception("Incorrect ovs flows output.\n") 
            
            #Deleting instance and network
            self.controller.deleteKeyPair(new_project_user.tenant.id, self.new_user, self.new_password)
            print "Deleting Instance "+self.new_inst1+"..."
            self.controller.deleteInstance(new_project_user.tenant.id, self.new_user, self.new_password, self.new_inst1)
            self.controller.deleteNetwork(new_network_inst1.network.get('network').get('id'), self.new_tenant, 
                                      self.new_user, self.new_password)
            print "Waiting for flows to be deleted\n"
            time.sleep(15)

            search_str =  "dl_vlan="+vdp_vlan
            vdptool_inst = OvsFlowsCli()
            result = OvsFlowsCli.check_output(vdptool_inst, self.controller.ip, self.controller.sys_username, 
                                     self.controller.password, "br-int", search_str)
            if result:
                raise Exception("Incorrect ovs flows output. Flows still present. Failing the test case...\n")
            
            search_str = "mod_vlan_vid:"+vdp_vlan
            vdptool_inst = OvsFlowsCli()
            result = OvsFlowsCli.check_output(vdptool_inst, self.controller.ip, self.controller.sys_username, 
                                     self.controller.password, "br-ethd", search_str)
            if result:
                raise Exception("Incorrect ovs flows output. Flows still present. Failing the test case...\n") 
        
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
        try:
            new_project = self.controller.getProject(self.new_tenant)
            if not new_project:
                print "Project not found during cleanup"
                skip_proj = True
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
        
        if skip_proj is False:    
            try:
                new_project.delete()
            except Exception as e:
                print "Error:", e
        
        print "Done cleaning"
        return ReturnValue.SUCCESS     
        
        