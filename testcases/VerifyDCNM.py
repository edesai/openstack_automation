'''
Created on Dec 5, 2016

@author: edesai
'''
from nodes.Controller import Controller
from nodes.Compute import Compute
import time
from common.Utils import SSHConnection
from common.ReturnValue import ReturnValue
from common.CheckStatusOfServices import CheckStatusOfServices
from constants import resultConstants

class VerifyDCNM(object):
    '''
    classdocs
    '''


    def __init__(self, config_dict):
        '''
        Constructor
        '''
        
        self.controller = Controller(config_dict['controller']['hostname'], 
                                     config_dict['controller']['ip'],
                                     config_dict['controller']['username'],
                                     config_dict['controller']['password'], 
                                     config_dict['controller']['sys_username'])

        self.computeHosts = []
        for compute in config_dict['computes']:
            self.computeHosts.append(Compute(compute['hostname'], compute['ip'], 
                                             compute['username'], compute['password']))
        

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
        self.dcnm_ip = config_dict['testbed']['dcnm']['address']
        self.dcnm_sys_username = config_dict['testbed']['dcnm']['sys_username']
        self.dcnm_sys_password = config_dict['testbed']['dcnm']['sys_password']
        self.ldap_username = config_dict['testbed']['dcnm']['ldap_username']
        self.ldap_password = config_dict['testbed']['dcnm']['ldap_password']
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

        
            time.sleep(5) #This is because results were different without adding delay
            
            with SSHConnection(address=self.dcnm_ip, username=self.dcnm_sys_username, password = self.dcnm_sys_password) as client:
                stdin, stdout, stderr = client.exec_command("ldapsearch -x -v -D 'cn="+self.ldap_username+",dc=cisco,dc=com' -w '"+self.ldap_password+"' -b 'dc=cisco,dc=com'")
                output = stdout.readlines()
                
                #print output
                org_str = "orgName: "+self.new_tenant
                org_found = False
                part_str = "vrfName: "+self.new_tenant+":CTX"
                part_found = False
                net_str =  "networkName: "+self.new_network1
                net_found = False
                for line in output:
                    line = line.strip()
                    if not org_found and org_str in line:
                        print "Organization  created on DCNM"
                        org_found = True
                    if not part_found and part_str in line:
                        print "Partition CTX created on DCNM"
                        part_found = True    
                    if not net_found and net_str in line:
                        print "Network  created on DCNM"
                        net_found = True    
                if not org_found:
                    raise Exception("Organization NOT found on DCNM")
                elif not part_found:
                    raise Exception("Partition NOT found on DCNM")
                elif not net_found:
                    raise Exception("Network NOT found on DCNM")                
    
        
        except Exception as e:
            print "Error:", e                
            self.cleanup()
            return ReturnValue.FAILURE
        
        self.cleanup()
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
            