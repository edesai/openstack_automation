'''
Created on Dec 19, 2016

@author: edesai
'''
from nodes.Controller import Controller
from nodes.Compute import Compute
import time
from common.MySqlConnection import MySqlConnection
from common.OvsFlowsCli import OvsFlowsCli
from common.ReturnValue import ReturnValue
from common.MySqlDbTables import MySqlDbTables
from common.CheckStatusOfServices import CheckStatusOfServices
from constants import resultConstants
import math

class CheckFlowsOnComputeOnDelete(object):

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
        '''
        For this test case, instantiate a compute object which is not the same as controller
        '''
           
        for compute in config_dict['computes']:
            if compute['hostname'] != config_dict['controller']['hostname']:
                self.compute = Compute(compute['hostname'], compute['ip'], compute['username'], compute['password'])
        
               
        
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

            #Create key-pair & security groups and rules
            keypair_secgrp = self.controller.createKeyPairSecurityGroup(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password)
  
            nova = self.controller.get_nova_client(new_project_user.tenant.id, self.new_user, self.new_password)  
            if not nova:
                raise Exception("Nova client not found")
            
            
            hosts_list = self.computeHosts
            
            #Create an aggregate with availability zone
            agg1 = self.new_tenant+"_agg_"+ hosts_list[0].hostname
            zone1 =  self.new_tenant+"_az_"+ hosts_list[0].hostname
            aggregate1 = self.controller.createAggregate(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password, agg_name=agg1, 
                                                   availability_zone=zone1)
            
            if hosts_list:
                aggregate1.add_host(hosts_list[0].host_name)                
            else:
                raise Exception("No hosts found")

            agg2 = self.new_tenant+"_agg_"+ hosts_list[1].hostname
            zone2 =  self.new_tenant+"_az_"+ hosts_list[1].hostname
            aggregate2 = self.controller.createAggregate(new_project_user.tenant.id, self.new_user, 
                                                   self.new_password, agg_name=agg2, 
                                                   availability_zone=zone2)
            
            if hosts_list:
                aggregate2.add_host(hosts_list[1].host_name)                
            else:
                raise Exception("No hosts found")

            #Create instance
            zones = nova.availability_zones.list()    
            for zone in zones:
                zone_name = str(zone.zoneName)
                if zone_name == zone1:
                    print "Launching instance in zone: ", zone_name
                    host1 = self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                                           self.new_password, new_network_inst1.network.get('network').get('id'),
                                                   self.new_inst1, key_name=keypair_secgrp.keypair, availability_zone=zone_name)
            print "Host1:", host1
            
            zones = nova.availability_zones.list()    
            for zone in zones:
                zone_name = str(zone.zoneName)
                if zone_name == zone2:
                    print "Launching instance in zone: ", zone_name    
                    host2 = self.controller.createInstance(new_project_user.tenant.id, self.new_user, 
                                                           self.new_password, new_network_inst1.get('network').get('id'),
                                                   self.new_inst2, key_name=keypair_secgrp.keypair, availability_zone=zone_name)
            print "Host2:", host2
            
            
            print "Connecting to database"
            #Connect to database
            mysql_db = MySqlConnection(self.config_dict)
            
            with MySqlConnection(self.config_dict) as mysql_connection:
                
                data = mysql_db.get_instances(mysql_connection, self.new_inst1)
                print "Instance name:", data[MySqlDbTables.INSTANCES_INSTANCE_NAME], ", Instance IP:", data[MySqlDbTables.INSTANCES_INSTANCE_IP], ", vdp_vlan:", data[MySqlDbTables.INSTANCES_VDP_VLAN] 
                vdp_vlan = str(data[MySqlDbTables.INSTANCES_VDP_VLAN])   
        
            search_str =  "dl_vlan="+vdp_vlan
            vdptool_inst = OvsFlowsCli()
            result = OvsFlowsCli.check_output(vdptool_inst, self.compute.ip, self.compute.username, 
                                     self.compute.password, "br-int", search_str)
            if not result:
                raise Exception("Incorrect ovs flows output.\n")   

            search_str = "mod_vlan_vid:"+vdp_vlan
            vdptool_inst = OvsFlowsCli()
            result = OvsFlowsCli.check_output(vdptool_inst, self.compute.ip, self.compute.username, 
                                     self.compute.password, "br-ethd", search_str)
            if not result:
                raise Exception("Incorrect ovs flows output.\n")     
       
            #delete one instance 
            self.controller.deleteKeyPair(new_project_user.tenant.id, self.new_user, self.new_password)
            print "Deleting the Instance - "+self.new_inst2+" on "+self.compute.hostname+"..."
            self.controller.deleteInstance(new_project_user.tenant.id, self.new_user, self.new_password, self.new_inst2)
            

            #Check flows on that same compute (should not exist)
            search_str =  "dl_vlan="+vdp_vlan
            vdptool_inst = OvsFlowsCli()
            result = OvsFlowsCli.check_output(vdptool_inst, self.compute.ip, self.compute.username, 
                                     self.compute.password, "br-int", search_str)
            if result:
                raise Exception("Incorrect ovs flows output.\n")   
            
            search_str = "mod_vlan_vid:"+vdp_vlan
            vdptool_inst = OvsFlowsCli()
            result = OvsFlowsCli.check_output(vdptool_inst, self.compute.ip, self.compute.username, 
                                     self.compute.password, "br-ethd", search_str)
            if result:
                raise Exception("Incorrect ovs flows output.\n")
        
        except Exception as e:
            print "Error:", e
            self.cleanup()
            return ReturnValue.FAILURE
        
        self.cleanup()
        print "Done"
        return ReturnValue.SUCCESS
                
    def cleanup(self):
        print "Cleanup:"
        skip_proj = False
        skip_nova = False
        hosts_list = []
        try:
            new_project_user = self.controller.getProjectUser(self.new_tenant, self.new_user)
            if not new_project_user:
                print "Project/User not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e
               
        hosts_list = self.computeHosts    
        if skip_nova is False:        
            try:
                agg1 = self.new_tenant+"_agg_"+ hosts_list[0].hostname
                    
                hosts_list1 = []
                hosts_list1.append(hosts_list[0])
                self.controller.deleteAggregate(new_project_user.tenant.id, self.new_user, 
                                                self.new_password, agg1, hosts_list1)
            
            except Exception as e:
                print "Error:", e 

            try:
                agg2 = self.new_tenant+"_agg_"+hosts_list[1].hostname 
                
                hosts_list2 = []
                hosts_list2.append(hosts_list[1])
                self.controller.deleteAggregate(new_project_user.tenant.id, self.new_user,
                                                self.new_password, agg2, hosts_list2)
                
            except Exception as e:
                print "Error:", e    
                
        if skip_proj is False:    
            
            try:
                self.controller.deleteInstance(new_project_user.tenant.id, self.new_user,
                                               self.new_password, self.new_inst1)
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
            
        print "Done"
        return ReturnValue.SUCCESS
         
            