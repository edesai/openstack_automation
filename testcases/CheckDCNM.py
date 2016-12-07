'''
Created on Dec 5, 2016

@author: edesai
'''
from nodes.Controller import Controller
from nodes.Compute import Compute
import time
from common.Utils import SSHConnection

class CheckDCNM(object):
    '''
    classdocs
    '''


    def __init__(self, config_dict):
        '''
        Constructor
        '''
        
        self.controller = Controller(config_dict['controller']['address'], config_dict['controller']['ip'],
                                     config_dict['controller']['username'],
                                     config_dict['controller']['password'], config_dict['controller']['sys_username'])

        self.computeHosts = []
        for compute in config_dict['computes']:
            self.computeHosts.append(Compute(compute['address'], compute['username'], compute['password']))
        
        self.new_tenant = "auto"
        self.new_user = "auto_user"
        self.new_password = "cisco123"
        self.new_network1 = "auto_nw"
        self.new_subnw1 = "20.20.30.0/24"
        self.dcnm_ip = config_dict['testbed']['dcnm']['address']
        self.dcnm_sys_username = config_dict['testbed']['dcnm']['sys_username']
        self.dcnm_sys_password = config_dict['testbed']['dcnm']['sys_password']
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
                                                       "20.20.30.0/24")
            print "New Subnetwork:", new_subnet
        except Exception as e:
            print "Error:", e                
            self.cleanup()
            return 1
        
        time.sleep(5) #This is because results were different without adding delay
        
        with SSHConnection(address=self.dcnm_ip, username=self.dcnm_sys_username, password = self.dcnm_sys_password) as client:
            stdin, stdout, stderr = client.exec_command("ldapsearch -x -v -D 'cn=admin,dc=cisco,dc=com' -w 'cisco123' -b 'dc=cisco,dc=com'")
            output = stdout.readlines()
            
            found = False
            #print output
            org_str = "orgName: "+self.new_tenant
            for line in output:
                line = line.strip()
                if org_str in line:
                    print "Organization "+self.new_tenant+" created on DCNM"
                    found = True
                    break
            if found is False:
                "Organization "+self.new_tenant+" NOT found on DCNM" 
                self.cleanup()
                return 1
            
            found = False
            part_str = "vrfName: "+self.new_tenant+":CTX"
            for line in output:
                line = line.strip()
                if part_str in line:
                    print "Partition CTX created on DCNM"
                    found = True
                    break
            if found is False:        
                print "Partition CTX NOT found on DCNM"  
                self.cleanup()
                return 1
            
            found = False
            net_str =  "networkName: "+self.new_network1
            print net_str
            for line in output:
                line = line.strip()
                if net_str in line:
                    print "Network "+self.new_network1+" created on DCNM"
                    found = True
                    break
            if found is False:
                print "Network "+self.new_network1+" NOT found on DCNM"     
                self.cleanup()
                return 1
        
        self.cleanup()
        return 0
    
    def cleanup(self):
        print "Cleanup:"
        skip_nw = False
        try:
            new_project = self.controller.getProject(self.new_tenant)
            if not new_project:
                print "Project not found during cleanup"
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
            
        try:
            new_project.delete()
        except Exception as e:
            print "Error:", e
        
        print "Done"
        
        return 0       
            