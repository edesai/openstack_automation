'''
Created on Nov 21, 2016

@author: edesai
'''

from nodes.Controller import Controller
from nodes.Compute import Compute
from common.Utils import SSHConnection
from common.MySqlConnection import MySqlConnection
from common.Uplink import Uplink, UplinkInfo
import time



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
            self.computeHosts.append(Compute(compute['address'], compute['username'], compute['password']))
        
        self.admin_username = config_dict['controller']['username']
        self.admin_password = config_dict['controller']['password']
        self.new_tenant = config_dict['openstack_tenant_details']['tenant_name']
        self.new_user = config_dict['openstack_tenant_details']['tenant_username']
        self.new_password = config_dict['openstack_tenant_details']['tenant_password']
        self.new_network1 = config_dict['openstack_tenant_details']['tenant_network1']
        self.new_subnw1 = config_dict['openstack_tenant_details']['tenant_subnw1']
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
            #Create user
            new_user = self.controller.createUser(new_project, 
                                       new_username = self.new_user, 
                                       new_password = self.new_password)
        except Exception as e:
            print "Error:", e
            self.cleanup()
            return 1
        
        try:    
            #Create network
            new_network1 = self.controller.createNetwork(self.new_tenant,self.new_network1, 
                                          self.new_user, self.new_password)
            print "New Network:", new_network1  
        except Exception as e:
            print "Error:", e
            self.cleanup() 
            return 1
           
        try:
            #Create subnet
            new_subnet = self.controller.createSubnet(new_network1.get('network').get('id'), 
                                                       self.new_tenant,self.new_user, self.new_password,
                                                       self.new_subnw1)
            print "New Subnetwork:", new_subnet
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
            #Create instance
            host1 = self.controller.createInstance(new_project.id, self.new_user, 
                                                   self.new_password, new_network1.get('network').get('id'),
                                                   self.new_inst1, key_name=key_pair, availability_zone=None)
            print "Host1:", host1
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
                print "Host name is:", data[10]
                host_name = data[10]
            except Exception as e:
                print "Created Exception: ",e
                self.cleanup()
                return 1 #TODO: Return correct retval 
        
            
        try:
            uplinkInst = Uplink(self.config_dict)
            
            uplink_info = UplinkInfo()
            uplink_info = Uplink.get_info(uplinkInst, host_name)
            print "uplink veth:", uplink_info.vethInterface
            print "remote_port",  uplink_info.remotePort
            with SSHConnection(address=self.controller.ip, username=self.controller.sys_username, password = self.controller.password) as client:
                stdin, stdout, stderr = client.exec_command("sudo vdptool -t -i "+uplink_info.vethInterface+" -V assoc -c mode=assoc")
                output = "".join(stdout.readlines())
                print "VDPTOOL command output:", output
                error_output = "".join(stderr.readlines()).strip()
                if error_output:
                    print "Error:", error_output     
                    self.cleanup()
                    return 1 #TODO: Return correct retval

                inst_str =  str((host1.networks[self.new_network1])[0])
                if inst_str in output:
                    print "Instance found in vdptool cmd output.\n"
                else:
                    print "Error:Instance not found in vdptool cmd output.\n", error_output   
                    self.cleanup()
                    return 1 #TODO: Return correct retval       
        except Exception as e:
            print "Created Exception: ",e
            self.cleanup()
            return 1 #TODO: Return correct retval    
        
        self.cleanup()
        print "Done"   
        return 0 
    
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
        return 0
         
         