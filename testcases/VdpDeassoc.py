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
 



class VdpDeassoc(object):
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
            self.computeHosts.append(Compute(compute['address'], compute['username'], compute['password']))

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
            #Create project
            new_project = self.controller.createProject(self.new_tenant)
    
            #Create user
            new_user = self.controller.createUser(new_project, 
                                       new_username = self.new_user, 
                                       new_password = self.new_password)
    
            #Create network
            new_network1 = self.controller.createNetwork(self.new_tenant,self.new_network1, 
                                          self.new_user, self.new_password)
            print "New Network:", new_network1  

            #Create subnet
            new_subnet = self.controller.createSubnet(new_network1.get('network').get('id'), 
                                                       self.new_tenant,self.new_user, self.new_password,
                                                       self.new_subnw1)
            print "New Subnetwork:", new_subnet

            #Create key-pair
            key_pair = self.controller.createKeyPair(new_project.id, self.new_user, 
                                                   self.new_password)
    
            #Create security groups and rules
            self.controller.createSecurityGroup(new_project.id, self.new_user, 
                                                   self.new_password)

            #Create instance
            host1 = self.controller.createInstance(new_project.id, self.new_user, 
                                                   self.new_password, new_network1.get('network').get('id'),
                                                   self.new_inst1, key_name=key_pair, availability_zone=None)
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
                   
            self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
            self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, self.new_inst1)
            
            time.sleep(10) #Wait for flows to be deleted
            
            inst_str =  str((host1[0].networks[self.new_network1])[0])
            vdptool_inst = VdpToolCli()
            result = VdpToolCli.check_output(vdptool_inst, self.controller.ip, self.controller.sys_username, 
                                     self.controller.password, uplink_info.vethInterface, inst_str)
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
        skip_proj = False
        skip_nw = False
        
        try:
            new_project = self.controller.getProject(self.new_tenant)
            if not new_project:
                print "Project not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e
        
        try:
            new_network1 = self.controller.getNetwork(self.new_tenant,self.new_network1, 
                                                         self.new_user, self.new_password)
            if not new_network1:
                skip_nw = True
                print("Network not found during cleanup")
        except Exception as e:
            print "Error:", e
        
        if skip_nw is False:    
            try:
                self.controller.deleteNetwork(new_network1['id'], self.new_tenant, 
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
        
        if skip_proj is False:    
            try:
                new_project.delete()
            except Exception as e:
                print "Error:", e
            
        print "Done cleaning"
        return ReturnValue.SUCCESS