'''
Created on Sep 22, 2016

@author: edesai
'''
import paramiko

class SSHConnection(object):
    """"Wrapper"""
    def __init__(self, address, username, password):
        self.address = address
        self.username = username
        self.password = password
        
    def __enter__(self):
        """ """
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.address, username = self.username, password = self.password,
                            allow_agent=False, look_for_keys=False)
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        
        