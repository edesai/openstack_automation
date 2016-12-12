'''
Created on Dec 7, 2016

@author: edesai
'''
from common.Utils import SSHConnection

class VdpToolCli(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
    
    def check_output(self, node_ip, node_username, 
                     node_password, uplink_interface, str_to_search):
        try:             
            with SSHConnection(address=node_ip, username = node_username, password = node_password) as client:
                stdin, stdout, stderr = client.exec_command("sudo vdptool -t -i "+uplink_interface+" -V assoc -c mode=assoc")
                output = "".join(stdout.readlines())
                print "VDPTOOL command output:", output
                error_output = "".join(stderr.readlines()).strip()
                if error_output:
                    print "Error:", error_output     
                    return False
    
                inst_str =  str_to_search
                if inst_str in output:
                    print "String found in vdptool cmd output.\n"
                    return True
                else:
                    print "Error:String not found in vdptool cmd output.\n", error_output 
                    return False #TODO: Return correct retval  
        except Exception as e:
            print "Error:", e
            return False           