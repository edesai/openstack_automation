'''
Created on Jan 17, 2017

@author: edesai
'''
from common.EnablerService import EnablerService
from common.LldpadService import LldpadService

class CheckStatusOfServices(object):
    '''
    classdocs
    '''

    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self.config_dict = config_dict
    
    def check(self):  
        enabler_inst = EnablerService(self.config_dict['controller']['ip'], 
                                      self.config_dict['controller']['sys_username'], 
                                      self.config_dict['controller']['password'])
        
        result = EnablerService.check_status(enabler_inst, "agent")   
        if not result:  
            return False
        
        result = EnablerService.check_status(enabler_inst, "server")   
        if not result:  
            return False
        
        lldpad_inst = LldpadService(self.config_dict['controller']['ip'], 
                                    self.config_dict['controller']['sys_username'], 
                                    self.config_dict['controller']['password'])
        result = LldpadService.check_status(lldpad_inst)   
        if not result:
            return False
        
        return True
        