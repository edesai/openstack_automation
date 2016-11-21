'''
Created on Nov 21, 2016

@author: edesai
'''

from nodes.Controller import Controller
from nodes.Compute import Compute
import time
from common.utils import SSHConnection
from common.MySqlConnection import MySqlConnection
import json


class VdpAssoc(object):
    '''
    classdocs
    '''
    def __init__(self, args):
        '''
        Constructor
        '''
        self.args = args
        self.controller = Controller(args.controller, self.args.controllerUsername, self.args.controllerSysUsername, self.args.controllerPassword)

        self.computeHosts = []
        for compute in args.computeHosts.split(','):
            self.computeHosts.append(Compute(compute, self.args.computeUsername, self.args.computePassword))
        
        self.new_tenant = "auto"
        self.new_user = "auto_user"
        self.new_password = "cisco123"
        self.new_network = "auto_nw"
        
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
                                                   self.new_tenant,self.new_user, self.new_password)
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
        mysql_db = MySqlConnection(self.args)
        
        with MySqlConnection(self.args) as mysql_connection:
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
            
            try:
                data = mysql_db.get_agent_info(mysql_connection, host_name)
                print "Agent info is:", data[3]
                info = json.loads(data[3])
                print "Uplink:",info["uplink"]
                remote_switch_ip = info["topo"]["LLDPLeth3"]["remote_mgmt_addr"]
                print "Remote Switch Ip:", remote_switch_ip
                with SSHConnection(address=self.controller.ip, username=self.controller.sys_username, password = self.controller.password) as client:
                    stdin, stdout, stderr = client.exec_command("sudo vdptool -t -i LLDPLeth3 -V assoc -c mode=assoc")
                    output = "".join(stdout.readlines())
                    print "VDPTOOL command output:", output
                    error_output = "".join(stderr.readlines()).strip()
                    if error_output:
                        print "Error:", error_output     
                        print "Cleanup: "
                        self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                        self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
                        self.cleanup(new_network, new_user, new_project)
                        return 1 #TODO: Return correct retval
                        
                        
            except Exception as e:
                print "Created Exception: ",e
                print "Cleanup: "
                self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
                self.cleanup(new_network, new_user, new_project)
                return 1 #TODO: Return correct retval    
                
        return 0 
    
    def cleanup(self, new_network, new_user, new_project):                
        self.controller.deleteNetwork(new_network.get('network').get('id'), self.new_tenant, 
                                      self.new_user, self.new_password)
        new_user.delete()
        new_project.delete()
        return 0    