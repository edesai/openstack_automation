'''
Created on Dec 21, 2016

@author: edesai
'''
from nodes.Controller import Controller
from nodes.Compute import Compute
from common.Ping import Ping
from common.ReturnValue import ReturnValue
import time
from common.Instance import Instance
from common.OvsFlowsCli import OvsFlowsCli
from common.VdpToolCli import VdpToolCli
from common.EnablerService import EnablerService
from common.LldpadService import LldpadService
from common.CheckStatusOfServices import CheckStatusOfServices
from constants import resultConstants

class RestartService(object):
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
        self.new_network2 = self.new_tenant+"nw2"
        self.new_subnw2 = "10.13.14.0/24"
        self.new_inst1 = self.new_tenant+"inst1"
        self.new_inst2 = self.new_tenant+"inst2"
        self.num_inst = 5
        self.config_dict = config_dict 
    
    def runTest(self, service):
          
        print "Service to be restarted is:", service
        
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

            new_network_inst2 = self.controller.createNetworkSubNetwork(self.new_tenant,self.new_network2,  
                                          self.new_subnw2, self.new_user, self.new_password)
            #Create key-pair & security groups and rules
            keypair_secgrp = self.controller.createKeyPairSecurityGroup(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password)
    
            hosts_list = self.computeHosts

            #Create an aggregate with availability zone
            agg1 = self.new_tenant+"_agg_"+hosts_list[0].hostname
            zone1 =  self.new_tenant+"_az_"+hosts_list[0].hostname
            aggregate1 = self.controller.createAggregate(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password, agg_name=agg1, 
                                                   availability_zone=zone1)
            
            if hosts_list:
                aggregate1.add_host(hosts_list[0].hostname)                
            else:
                raise Exception("No hosts found")

            agg2 = self.new_tenant+"_agg_"+hosts_list[1].hostname
            zone2 =  self.new_tenant+"_az_"+hosts_list[1].hostname
            aggregate2 = self.controller.createAggregate(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password, agg_name=agg2, 
                                                   availability_zone=zone2)
            
            if hosts_list:
                aggregate2.add_host(hosts_list[1].hostname)                
            else:
                raise Exception("No hosts found")

            #Create 5 instances on two different computes (total 10 instances)
            host1 = self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password, 
                                                   new_network_inst1.network.get('network').get('id'),
                                                   self.new_inst1, key_name=keypair_secgrp.key_pair, 
                                                   availability_zone=zone1, count = self.num_inst)
            
            host2 = self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password, 
                                                   new_network_inst2.network.get('network').get('id'),
                                                   self.new_inst2, key_name=keypair_secgrp.key_pair, 
                                                   availability_zone=zone2, count = self.num_inst)
            

            
            #Verify Ping, ovs flows and uplink & vdptool output using DHCP namespace on controller (before restart)
            pingObj = Ping()
            
            dhcp_ip1 = self.new_subnw1[:-4]+"2"
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, 
                                                 self.controller.password,
                                                 new_network_inst2.network.get('network').get('id'), 
                                                 dhcp_ip1)
            
            if not result:
                raise Exception("Ping failed...Failing test case\n") 
            
            dhcp_ip2 = self.new_subnw2[:-4]+"2"
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, 
                                                 self.controller.password,
                                                 new_network_inst1.network.get('network').get('id'), 
                                                 dhcp_ip2)
            
            if not result:
                raise Exception("Ping failed...Failing test case\n")
                      
            inst_ip_list = []
            
            #Gathering instances information
            for inst in range(self.num_inst):
                print "loop:", inst
                instObj = Instance(ip = str((host1[inst].networks[self.new_network1])[0]), 
                                   instname = str(host1[inst].name), hostname = hosts_list[0].hostname)
                print "InstObj1:", instObj
                inst_ip_list.append(instObj)
                print "inst_ip_list1:", inst_ip_list
                instObj = Instance(ip = str((host2[inst].networks[self.new_network2])[0]), 
                                   instname = str(host2[inst].name), hostname = hosts_list[1].hostname)
                print "InstObj2:", instObj
                inst_ip_list.append(instObj)
                print "inst_ip_list2:", inst_ip_list
            
            #Verify ping, ovs and vdp results 
            for inst in inst_ip_list:
                #Verify Ping
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network_inst1.network.get('network').get('id'), inst.ip)
                print "network_id is:", new_network_inst1.network.get('network').get('id')
                if not result:
                    raise Exception("Ping failed...Failing test case\n")    
            
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network_inst2.network.get('network').get('id'), inst.ip)
                print "network_id is:", new_network_inst2.network.get('network').get('id')
                if not result:
                    raise Exception("Ping failed...Failing test case\n")    
                
                OvsFlowsCli().verify_ovs_and_vdp(self.config_dict, self.controller.ip, self.controller.sys_username, 
                                                 self.controller.password, inst.instname, 
                                                 inst.ip, inst.instname, inst.hostname)
                if not result:
                    raise Exception("Incorrect VDPTool/OVS output")

            
            #Restart service    
            if service == "enabler-server":
                #Restart Enabler server on controller   
                enabler_inst = EnablerService(self.controller.ip, 
                                              self.controller.sys_username, self.controller.password)
                result = EnablerService.take_action(enabler_inst, "restart", "server")   
                if not result:
                    raise Exception("Error while restarting enabler server")
            
            elif service == "enabler-agent":    
                #Restart Enabler agent on controller   
                enabler_inst = EnablerService(self.controller.ip, 
                                              self.controller.sys_username, self.controller.password)
                result = EnablerService.take_action(enabler_inst, "restart", "agent")   
                if not result:
                    raise Exception("Error while restarting enabler agent")
            
            elif service == "lldpad":    
                #Restart lldpad on controller   
                lldpad_inst = LldpadService(self.controller.ip, 
                                            self.controller.sys_username, self.controller.password)
                result = LldpadService.take_action(lldpad_inst, "restart")   
                if not result:
                    raise Exception("Error while restarting lldpad")
                
            
            #Verify Ping, ovs flows and uplink & vdptool output using DHCP namespace on controller (after restart)
            for inst in inst_ip_list:
                #Verify Ping
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network_inst1.network.get('network').get('id'), inst.ip)
                print "network_id is:", new_network_inst1.network.get('network').get('id')
                if not result:
                    raise Exception("Ping failed...Failing test case\n")    
            
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network_inst2.network.get('network').get('id'), inst.ip)
                print "network_id is:", new_network_inst2.network.get('network').get('id')
                if not result:
                    raise Exception("Ping failed...Failing test case\n")    
                
                OvsFlowsCli().verify_ovs_and_vdp(self.config_dict, self.controller.ip, self.controller.sys_username, 
                                                 self.controller.password, inst.instname, 
                                                 inst.ip, inst.hostname)
                if not result:
                    raise Exception("Incorrect VDPTool/OVS output")
                

            
        except Exception as e:
            print "Created Exception: ",e 
            self.cleanup()
            return ReturnValue.FAILURE
   
        self.cleanup()
        return ReturnValue.SUCCESS
    
    def cleanup(self):
        
        print "Cleanup:"
        agg_list = []
        hosts_list = self.computeHosts
        hosts = []
        skip_proj = False
        
        try:
            new_project_user = self.controller.getProjectUser(self.new_tenant, self.new_user)
            if not new_project_user:
                print "Project/User not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e
        
            
        if skip_proj is False:
            try:
                for var in range(self.num_inst):        
                    agg_list.append(self.new_tenant+"_agg_" + hosts_list[var].hostname)
                    hosts.append(hosts_list[var])
                self.controller.deleteAggregateList(self.controller, new_project_user.tenant.id, 
                                                    self.new_user, self.new_password, 
                                                    agg_list, hosts)       
            except Exception as e:
                print "Error:", e
                
        if skip_proj is False:    
            try:
                self.controller.deleteInstance(new_project_user.tenant.id, self.new_user, 
                                               self.new_password, self.new_inst1, count = self.num_inst)
            except Exception as e:
                print "Error:", e
            
            try:
                self.controller.deleteInstance(new_project_user.tenant.id, self.new_user, 
                                               self.new_password, self.new_inst2, count = self.num_inst)
            except Exception as e:
                print "Error:", e
            
            try:
                self.controller.deleteKeyPair(new_project_user.tenant.id, self.new_user, self.new_password)
                time.sleep(5)                
            except Exception as e:
                print "Error:", e
        try:
            self.controller.deleteNetwork(self.controller, self.new_network1, self.new_tenant, 
                                      self.new_user, self.new_password)
        except Exception as e:
            print "Error:", e
        
        try:
            self.controller.deleteNetwork(self.controller, self.new_network2, self.new_tenant, 
                                      self.new_user, self.new_password)
        except Exception as e:
            print "Error:", e
        
        try:
            self.controller.deleteProjectUser(self.controller, new_project_user)
        except Exception as e:
            print "Error:", e
        
        print "Done"
        return ReturnValue.SUCCESS
        

    



        