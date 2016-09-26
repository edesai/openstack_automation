'''
Created on Sep 22, 2016

@author: edesai
'''
from testcases.BaseTest import BaseTest
from nodes.Controller import Controller
from nodes.Compute import Compute

class Ping(BaseTest):
    '''
    classdocs
    '''

    
    def __init__(self, args):
        '''
        Constructor
        '''
        
        self.args = args
        self.controller = Controller(args.controller, self.args.controllerUsername, self.args.controllerPassword)

        self.computeHosts = []
        for compute in args.computeHosts.split(','):
            self.computeHosts.append(Compute(compute, self.args.computeUsername, self.args.computePassword))
        
        self.new_tenant = "auto"
        self.new_user = "auto_user"
        self.new_password = "cisco123"
        self.new_network = "auto_nw"
             
    # TODO: enforce this
    def runTest(self):
        
        new_project = self.controller.createProject(self.new_tenant)
        new_user = self.controller.createUser(new_project, 
                                   new_username = self.new_user, 
                                   new_password = self.new_password)
        
        #Create network
        new_network = self.controller.createNetwork(self.new_tenant,self.new_network, 
                                      self.new_user, self.new_password)
        print "new network:", new_network
    
        # Cleanup
        print "Cleanup:"
        self.controller.deleteNetwork(new_network.get('network').get('id'), self.new_tenant, 
                                      self.new_user, self.new_password)
        new_user.delete()
        new_project.delete()
