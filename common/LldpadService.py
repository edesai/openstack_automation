'''
Created on Dec 20, 2016

@author: edesai
'''
from common.Utils import SSHConnection
import time


class LldpadService(object):
    '''
    classdocs
    '''

    def __init__(self, node_ip, node_username, node_password):
        '''
        Constructor
        '''
        self.ip = node_ip
        self.username = node_username
        self.password = node_password

    def take_action(self, action):
        with SSHConnection(address=self.ip, username=self.username, password=self.password) as client:
            stdin, stdout, stderr = client.exec_command(
                "sudo service lldpad " + action)
            output = "".join(stdout.readlines())
            error_output = "".join(stderr.readlines()).strip()
            if error_output:
                raise Exception("Error starting lldpad:", error_output)
            print "Waiting for things to get settled"
            time.sleep(200)
        return True

    def check_status(self):
        with SSHConnection(address=self.ip, username=self.username, password=self.password) as client:
            stdin, stdout, stderr = client.exec_command(
                "sudo service lldpad status")
            output = "".join(stdout.readlines())
            error_output = "".join(stderr.readlines()).strip()
            if error_output:
                raise Exception("Error while checking status of lldapd")
            failure_list = ["stop/waiting"]
            for word in failure_list:
                if word in output:
                    print ("Alert: Process lldpad not running")
                    return False
        return True
