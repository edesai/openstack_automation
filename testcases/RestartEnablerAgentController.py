'''
Created on Dec 21, 2016

@author: edesai
'''

from testcases.RestartService import RestartService


class RestartEnablerAgentController(object):
    '''
    classdocs
    '''
    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self.config_dict = config_dict 
    
    def runTest(self):   
        return RestartService(self.config_dict).runTest(service="enabler-agent") 