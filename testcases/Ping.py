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
        print "[debug] I'm overriding my parent runTest"
        self.controller.createProject()

