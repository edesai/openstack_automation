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
            self.computeHosts.append(Compute(compute['address'], compute['username'], compute['password']))
        
        self.new_tenant = "auto"
        self.new_user = "auto_user"
        self.new_password = "cisco123"
        self.new_network = "auto_nw"
        self.new_subnw = "20.20.30.0/24"
        
    # TODO: enforce this
    def runTest(self):  
          
        #Create project
        new_project = self.controller.createProject(self.new_tenant)
        
        
        #Create user
        new_user = self.controller.createUser(new_project, 
                                   new_username = self.new_user, 
                                   new_password = self.new_password)
        
        #Create network
        new_network = self.controller.createNetwork(self.new_tenant,self.new_network, 
                                      self.new_user, self.new_password)
        print "New Network:", new_network
    
        #Create subnet
        new_subnet = self.controller.createSubnet(new_network.get('network').get('id'), 
                                                   self.new_tenant,self.new_user, self.new_password,
                                                   self.new_subnw)
        print "New Subnetwork:", new_subnet

        #Create key-pair
        key_pair = self.controller.createKeyPair(new_project.id, self.new_user, 
                                               self.new_password)        
        
        #Create security groups and rules
        self.controller.createSecurityGroup(new_project.id, self.new_user, 
                                               self.new_password)
        
        
        #Create instance
        host1 = self.controller.createInstance(new_project.id, self.new_user, 
                                               self.new_password, new_network.get('network').get('id'),
                                               "autohost1", key_name=key_pair)
        print "Host1:", host1
        
        print "Connecting to database"
        #Connect to database
        mysql_db = MySqlConnection(self.config_dict)
        
        with MySqlConnection(self.config_dict) as mysql_connection:
            try:
                data = mysql_db.get_instances(mysql_connection, "autohost1")
                print "Host name is:", data[10]
                host_name = data[10]
            except Exception as e:
                print "Created Exception: ",e
                print "Cleanup: "
                self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
                self.cleanup(new_network, new_user, new_project)
                return 1 #TODO: Return correct retval
        
        print "Getting uplink info...\n"
        try:
            uplinkInst = Uplink(self.config_dict)
            uplink_info = UplinkInfo()
            uplink_info = Uplink.get_info(uplinkInst, host_name)
            print "uplink switchIp:", uplink_info.switchIp
            
            fabricSwInst = FabricSwitch(self.config_dict)            
            fabric_sw_info = FabricSwitchInfo()
            fabric_sw_info = FabricSwitch.get_info(fabricSwInst, uplink_info.switchIp, self.config_dict)
            
        except Exception as e:
            print "Created Exception: ",e
            print "Cleanup: "
            self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
            self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
            self.cleanup(new_network, new_user, new_project)
            return 1 #TODO: Return correct retval
        
        print "Checking for VDP Keep alive on the fabric connection...\n"
        
        with SSHConnection(address=uplink_info.switchIp, username=fabric_sw_info.username, password = fabric_sw_info.password) as client:
            stdin, stdout, stderr = client.exec_command("show run vlan")
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
    
    
    def cleanup(self, new_network, new_user, new_project):
        print "Cleanup:"
        self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
        #self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost2")
        self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
        time.sleep(5)                
        self.controller.deleteNetwork(new_network.get('network').get('id'), self.new_tenant, 
                                      self.new_user, self.new_password)
        new_user.delete()
        new_project.delete()
        print "Done"
        return 0        