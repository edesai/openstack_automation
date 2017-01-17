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
        self.new_network2 = self.new_tenant+"nw2"
        self.new_subnw2 = "10.13.14.0/24"
        self.new_inst1 = self.new_tenant+"inst1"
        self.new_inst2 = self.new_tenant+"inst2"
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
            
            #Create project
            new_project = self.controller.createProject(self.new_tenant)
            
            
            nova = self.controller.get_nova_client(new_project.id, self.new_user, self.new_password)  
            if not nova:
                raise Exception("Nova client not found")
    
            #Create user
            new_user = self.controller.createUser(new_project, 
                                       new_username = self.new_user, 
                                       new_password = self.new_password)
    
            #Create 1st network
            new_network1 = self.controller.createNetwork(self.new_tenant,self.new_network1, 
                                          self.new_user, self.new_password)
            print "New Network:", new_network1   

            #Create subnet
            new_subnet1 = self.controller.createSubnet(new_network1.get('network').get('id'), 
                                                       self.new_tenant,self.new_user, self.new_password,
                                                       self.new_subnw1)
            print "New Subnetwork:", new_subnet1
    
            #Create 2nd network
            new_network2 = self.controller.createNetwork(self.new_tenant, self.new_network2, 
                                          self.new_user, self.new_password)
            print "New Network:", new_network2   

            #Create subnet
            new_subnet2 = self.controller.createSubnet(new_network2.get('network').get('id'), 
                                                       self.new_tenant,self.new_user, self.new_password,
                                                       self.new_subnw2)
            print "New Subnetwork:", new_subnet2

            #Create key-pair
            key_pair = self.controller.createKeyPair(new_project.id, self.new_user, 
                                                   self.new_password)
    
            #Create security groups and rules
            self.controller.createSecurityGroup(new_project.id, self.new_user, 
                                                   self.new_password)
  
        
            hosts = nova.hosts.list()
            hosts_list = [h for h in hosts if h.zone == "nova"]
            #print "Hosts list:", hosts_list
              
        
            #Create an aggregate with availability zone
            agg1 = self.new_tenant+"_agg_"+self.config_dict['computes'][0]['hostname']
            zone1 =  self.new_tenant+"_az_"+self.config_dict['computes'][0]['hostname']
            aggregate1 = self.controller.createAggregate(new_project.id, self.new_user, 
                                                   self.new_password, agg_name=agg1, 
                                               availability_zone=zone1)
            
            if hosts_list:
                aggregate1.add_host(hosts_list[0].host_name)                
            else:
                raise Exception("No hosts found")

            agg2 = self.new_tenant+"_agg_"+self.config_dict['computes'][1]['hostname']
            zone2 =  self.new_tenant+"_az_"+self.config_dict['computes'][1]['hostname']
            aggregate2 = self.controller.createAggregate(new_project.id, self.new_user, 
                                                   self.new_password, agg_name=agg2, 
                                               availability_zone=zone2)
            
            if hosts_list:
                aggregate2.add_host(hosts_list[1].host_name)                
            else:
                raise Exception("No hosts found")

            #Create 5 instances on two different computes (total 10 instances)
            zones = nova.availability_zones.list()    
            for zone in zones:
                zone_name = str(zone.zoneName)
                if zone_name == zone1:
                    print "Launching instance in zone: ", zone_name
                    host1 = self.controller.createInstance(new_project.id, self.new_user, 
                                                   self.new_password, new_network1.get('network').get('id'),
                                                   self.new_inst1, key_name=key_pair, availability_zone=zone_name,
                                                   count = 5)
            #print "Host1:", host1

            zones = nova.availability_zones.list()  
            for zone in zones:
                zone_name = str(zone.zoneName)
                if zone_name == zone2:
                    print "Launching instance in zone: ", zone_name    
                    host2 = self.controller.createInstance(new_project.id, self.new_user, 
                                                   self.new_password, new_network2.get('network').get('id'),
                                                   self.new_inst2, key_name=key_pair, availability_zone=zone_name,
                                                   count = 5)
            #print "Host2:", host2


            #Verify Ping, ovs flows and uplink & vdptool output using DHCP namespace on controller (before restart)
            pingObj = Ping()

            dhcp_ip1 = self.new_subnw1[:-4]+"2"
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                        new_network2.get('network').get('id'), dhcp_ip1)
            
            if not result:
                raise Exception("Ping failed...Failing test case\n") 
            
            dhcp_ip2 = self.new_subnw2[:-4]+"2"
            result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                        new_network1.get('network').get('id'), dhcp_ip2)
            
            if not result:
                raise Exception("Ping failed...Failing test case\n")
                        
            inst_ip_list = []
            print "before for loop"
            for inst in range(5):
                print "loop:", inst
                instObj = Instance(ip = str((host1[inst].networks[self.new_network1])[0]), 
                                   instname = str(host1[inst].name), hostname = hosts_list[0].host_name)
                print "InstObj1:", instObj
                inst_ip_list.append(instObj)
                print "inst_ip_list1:", inst_ip_list
                instObj = Instance(ip = str((host2[inst].networks[self.new_network2])[0]), 
                                   instname = str(host2[inst].name), hostname = hosts_list[1].host_name)
                print "InstObj2:", instObj
                inst_ip_list.append(instObj)
                print "inst_ip_list2:", inst_ip_list
            print "after for loop"
            for inst in inst_ip_list:
                #Verify Ping
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network1.get('network').get('id'), inst.ip)
                print "network_id is:", new_network1.get('network').get('id')
                if not result:
                    raise Exception("Ping failed...Failing test case\n")    
            
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network2.get('network').get('id'), inst.ip)
                print "network_id is:", new_network2.get('network').get('id')
                if not result:
                    raise Exception("Ping failed...Failing test case\n")    
                
                #Verify Flows
                vdptool_inst = OvsFlowsCli()
                result = OvsFlowsCli.check_if_exists_in_both_br_flows(vdptool_inst, self.config_dict, self.controller.ip, self.controller.sys_username, 
                                     self.controller.password, inst.instname)
                if not result:
                    raise Exception("Incorrect OVS flows")
                
                #Verify vdptool output
                vdptool_inst = VdpToolCli()
                result = VdpToolCli.check_uplink_and_output(vdptool_inst, self.config_dict, inst.ip, inst.instname, inst.hostname)
                if not result:
                    raise Exception("Incorrect VDPTool output")
                
            if service == "enabler-server":
                #Restart Enabler server on controller   
                enabler_inst = EnablerService(self.controller.ip, self.controller.sys_username, self.controller.password)
                result = EnablerService.take_action(enabler_inst, "restart", "server")   
                if not result:
                    raise Exception("Error while restarting enabler server")
            
            elif service == "enabler-agent":    
                #Restart Enabler agent on controller   
                enabler_inst = EnablerService(self.controller.ip, self.controller.sys_username, self.controller.password)
                result = EnablerService.take_action(enabler_inst, "restart", "agent")   
                if not result:
                    raise Exception("Error while restarting enabler agent")
            
            elif service == "lldpad":    
                #Restart lldpad on controller   
                lldpad_inst = LldpadService(self.controller.ip, self.controller.sys_username, self.controller.password)
                result = LldpadService.take_action(lldpad_inst, "restart")   
                if not result:
                    raise Exception("Error while restarting lldpad")
                
            
            #Verify Ping, ovs flows and uplink & vdptool output using DHCP namespace on controller (after restart)
            for inst in inst_ip_list:
                #Verify Ping
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network1.get('network').get('id'), inst.ip)
                print "network_id is:", new_network1.get('network').get('id')
                if not result:
                    raise Exception("Ping failed...Failing test case\n")    
            
                result = pingObj.verify_ping_qdhcpns(self.controller.ip, self.controller.sys_username, self.controller.password,
                                            new_network2.get('network').get('id'), inst.ip)
                print "network_id is:", new_network2.get('network').get('id')
                if not result:
                    raise Exception("Ping failed...Failing test case\n")    
                
                #Verify Flows
                vdptool_inst = OvsFlowsCli()
                result = OvsFlowsCli.check_if_exists_in_both_br_flows(vdptool_inst, self.config_dict, self.controller.ip, self.controller.sys_username, 
                                     self.controller.password, inst.instname)
                if not result:
                    raise Exception("Incorrect OVS flows")
                
                #Verify vdptool output
                vdptool_inst = VdpToolCli()
                result = VdpToolCli.check_uplink_and_output(vdptool_inst, self.config_dict, inst.ip, inst.instname, inst.hostname)
                if not result:
                    raise Exception("Incorrect VDPTool output")
            
            
        except Exception as e:
            print "Created Exception: ",e 
            self.cleanup()
            return ReturnValue.FAILURE
   
        self.cleanup()
        return ReturnValue.SUCCESS
    
    def cleanup(self):
        
        print "Cleanup:"
        skip_nova = False
        skip_proj = False
        
        try:
            new_project = self.controller.getProject(self.new_tenant)
            if not new_project:
                print "Project not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e
        
        try: 
            nova = self.controller.get_nova_client(new_project.id, self.new_user, self.new_password)  
            if not nova:
                print("Nova client not found during cleanup")
                skip_nova = True
        except Exception as e:
            print "Error:", e
            
        if skip_nova is False and skip_proj is False:        
            try:
                agg1 = self.new_tenant+"_agg_"+self.config_dict['computes'][0]['hostname']    
                aggregate1 = self.controller.getAggregate(new_project.id, self.new_user, self.new_password,
                                                         agg_name=agg1)    
                if not aggregate1:
                    print("Aggregate1 not found during cleanup")
                else:
                    hosts = nova.hosts.list()
                    zone1 = self.new_tenant+"_az_"+self.config_dict['computes'][0]['hostname']
                    host1 = [h for h in hosts if h.zone == zone1]    
                    if host1 and aggregate1:
                        aggregate1.remove_host(host1[0].host_name)
                    else:
                        print("Hosts not found during cleanup")    
            except Exception as e:
                print "Error:", e
                
            try:
                if aggregate1:             
                    nova.aggregates.delete(aggregate1) 
            except Exception as e:
                print "Error:", e

            try:
                agg2 = self.new_tenant+"_agg_"+self.config_dict['computes'][1]['hostname']    
                aggregate2 = self.controller.getAggregate(new_project.id, self.new_user, self.new_password,
                                                         agg_name=agg2)    
                if not aggregate2:
                    print("Aggregate2 not found during cleanup")
                else:
                    zone2 = self.new_tenant+"_az_"+self.config_dict['computes'][1]['hostname']
                    host2 = [h for h in hosts if h.zone == zone2]    
                    if host2 and aggregate2:
                        aggregate2.remove_host(host2[0].host_name)
                    else:
                        print("Hosts not found during cleanup")    
            except Exception as e:
                print "Error:", e
                
            try: 
                if aggregate2:            
                    nova.aggregates.delete(aggregate2) 
            except Exception as e:
                print "Error:", e
                
        if skip_proj is False:    
            try:
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, self.new_inst1, count = 5)
            except Exception as e:
                print "Error:", e
            
            try:
                self.controller.deleteInstance(new_project.id, self.new_user, self.new_password, self.new_inst2, count = 5)
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
        except Exception as e:
            print "Error:", e
            
        try:
            self.controller.deleteNetwork(new_network1['id'], self.new_tenant, 
                                      self.new_user, self.new_password)
        except Exception as e:
            print "Error:", e
            
        try:
            new_network2 = self.controller.getNetwork(self.new_tenant,self.new_network2, 
                                                         self.new_user, self.new_password)
            if not new_network2:
                print("Network not found during cleanup")
        except Exception as e:
            print "Error:", e
            
        try:
            self.controller.deleteNetwork(new_network2['id'], self.new_tenant, 
                                      self.new_user, self.new_password)
        except Exception as e:
            print "Error:", e    
        
        try:
            new_user = self.controller.getUser(self.new_user)
            if not new_user:
                print("User not found during cleanup")
            else:
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
        

    



        