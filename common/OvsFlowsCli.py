'''
Created on Dec 7, 2016

@author: edesai
'''
from common.Utils import SSHConnection

class OvsFlowsCli(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
    def check_output(self, node_ip, node_username, 
                     node_password, bridge_name, search_str):
                     
        with SSHConnection(address=node_ip, username = node_username, password = node_password) as client:
            
            stdin, stdout, stderr = client.exec_command("sudo ovs-ofctl dump-flows "+bridge_name)
            output = "".join(stdout.readlines())
            error_output = "".join(stderr.readlines()).strip()
            if error_output:
                raise Exception(bridge_name+" Error:", error_output)   
            
            print "Output:", output

            if search_str in output:
                print search_str+" found in "+bridge_name+" flows\n"
                return True
            
            else:
                print search_str+" not found in "+bridge_name+" flows\n"  
                return False
                
