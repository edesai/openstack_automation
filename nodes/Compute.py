'''
Created on Sep 22, 2016

@author: edesai
'''


class Compute(object):
    '''
    classdocs
    '''

    def __init__(self, hostname, ip, username, password):
        '''
        Constructor
        '''
        self.hostname = hostname
        self.ip = ip
        self.username = username
        self.password = password

    def ping(self):
        '''
            Logic to reboot a compute
        '''
