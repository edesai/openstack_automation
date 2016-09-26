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
            
            
    # TODO: enforce this
    def runTest(self):
        try:
            print "[debug] I'm overriding my parent runTest"
            new_tenant = self.controller.createProject()
            new_user = self.controller.createUser(new_tenant)
            
            #Create network
            new_network = self.controller.createNetwork(new_tenant,"auto_nw")
        
        finally:
            # Cleanup
            print "Deleting user:"
            #keystone = self.controller.get_keystone_client(new_tenant, 'RegionOne')
            #keystone.users.delete(new_user)
            #keystone.tenants.delete(new_tenant)
