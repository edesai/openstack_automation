'''
Created on Nov 14, 2016

@author: edesai
'''
from testcases.BaseTest import BaseTest
from nodes.Controller import Controller
from nodes.Compute import Compute
import time
import sys
from common.Utils import SSHConnection
from common.MySqlConnection import MySqlConnection


class VlanTranslation(object):
    '''
    classdocs
    '''

    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self.config_dict = config_dict
        self.controller = Controller(config_dict['controller']['address'], config_dict['controller']['ip'], config_dict['controller']['username'],
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
                data = mysql_db.get_instances(mysql_db, "autohost1")