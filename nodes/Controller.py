'''
Created on Sep 22, 2016

@author: edesai
'''
from common.utils import SSHConnection

class Controller(object):
    '''
    classdocs
    '''


    def __init__(self, ip, username, password):
        '''
        Constructor
        '''
        self.ip = ip
        self.username = username
        self.password = password
        
    def createProject(self):
        '''
        '''
        with SSHConnection(address=self.ip, username=self.username, password = self.password) as client:
            stdin, stdout, stderr = client.exec_command("uname -a")
            print "uname: " + stdout
        # Use sshHandle to run create project command