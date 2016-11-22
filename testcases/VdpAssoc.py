'''
Created on Nov 21, 2016

@author: edesai
'''

from nodes.Controller import Controller
from nodes.Compute import Compute
from common.utils import SSHConnection
from common.MySqlConnection import MySqlConnection
from common.Uplink import Uplink, UplinkInfo



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
        
        print "Check for looping...hostname:", host_name    
        try:
            uplinkInst = Uplink(self.args)
            
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
                    print "Cleanup: "
                    self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
                    self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
                    self.cleanup(new_network, new_user, new_project)
                    return 1 #TODO: Return correct retval
                
                
                inst_str =  str((host1.networks["auto_nw"])[0])
                if inst_str in output:
                    print "Instance found in vdptool cmd output.\n"
                else:
                    print "Error:Instance not found in vdptool cmd output.\n", error_output     
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
        
        print "Cleanup: "
        self.controller.deleteKeyPair(new_project.id, self.new_user, self.new_password)
        self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, "autohost1")
        self.cleanup(new_network, new_user, new_project)
        print "Done"   
        return 0 
    
    def cleanup(self, new_network, new_user, new_project):                
        self.controller.deleteNetwork(new_network.get('network').get('id'), self.new_tenant, 
                                      self.new_user, self.new_password)
        new_user.delete()
        new_project.delete()
        return 0    