'''
Created on Nov 22, 2016

@author: edesai
'''

class FabricSwitchInfo:
    username = ''
    password = ''
    address = ''

class FabricSwitch(object):
    '''
    classdocs
    '''
    def __init__(self, mgmt_ip, config_dict):
        '''
        Constructor
        '''
        self.config_dict = config_dict
        
    def get_info(self, mgmt_ip):    
        fabric_sw_info = FabricSwitchInfo()
        fabric_sw_info.address = mgmt_ip
        for item in self.config_dict['fabric_switch']:
            if (item['address'] == mgmt_ip):
                fabric_sw_info.username = item['username']
                fabric_sw_info.password = item['password']
                break
        return fabric_sw_info
        
                