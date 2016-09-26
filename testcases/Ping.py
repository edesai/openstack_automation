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
        try:
            print "[debug] I'm overriding my parent runTest"
            self.controller.createProject(self.new_tenant)
            self.controller.createUser(new_tenant = self.new_tenant, 
                                       new_username = self.new_user, 
                                       new_password = self.new_password)
            
            #Create network
            self.controller.createNetwork(self.new_tenant,self.new_nw, self.new_user, self.new_password)
        
        finally:
            # Cleanup
            print "Deleting user:"
            #keystone = self.controller.get_keystone_client("admin", 'RegionOne')
            #keystone.users.delete(self.new_user)
            #keystone.tenants.delete(self.new_tenant)
