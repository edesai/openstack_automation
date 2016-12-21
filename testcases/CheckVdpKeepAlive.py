'''
Created on Nov 30, 2016

@author: edesai
'''
from nodes.Controller import Controller
from nodes.Compute import Compute
from common.Utils import SSHConnection
from common.Uplink import Uplink, UplinkInfo
from common.MySqlConnection import MySqlConnection
from common.FabricSwitch import FabricSwitch, FabricSwitchInfo
import time
from common.ReturnValue import ReturnValue
from common.MySqlDbTables import MySqlDbTables

class CheckVdpKeepAlive(object):
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

        
            print "Getting uplink info...\n"
        
            uplinkInst = Uplink(self.config_dict)
            uplink_info = UplinkInfo()
            uplink_info = Uplink.get_info(uplinkInst, host_name)
            print "uplink switchIp:", uplink_info.switchIp
            
            fabricSwInst = FabricSwitch(self.config_dict)            
            fabric_sw_info = FabricSwitchInfo()
            fabric_sw_info = FabricSwitch.get_info(fabricSwInst, uplink_info.switchIp, self.config_dict)
            

        
            print "Checking for VDP Keep alive on the fabric connection...\n"
            
            with SSHConnection(address=uplink_info.switchIp, username=fabric_sw_info.username, password = fabric_sw_info.password) as client:
                stdin, stdout, stderr = client.exec_command("show run vlan")
                output = "".join(stdout.readlines()).strip()
                error_output = "".join(stderr.readlines()).strip()
                print "Output:", output
        
        except Exception as e:
            print "Created Exception: ",e
            self.cleanup()
            return ReturnValue.FAILURE
        
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
                
        if skip_proj is False:    
            
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
                skip_nw = True
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
        
        print "Done"
        return ReturnValue.SUCCESS
         
                