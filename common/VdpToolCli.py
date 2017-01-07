'''
Created on Dec 7, 2016

@author: edesai
'''
from common.Utils import SSHConnection
from common.MySqlConnection import MySqlConnection
from common.MySqlDbTables import MySqlDbTables
from common.Uplink import Uplink

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
                     
        with SSHConnection(address=node_ip, username = node_username, password = node_password) as client:
            stdin, stdout, stderr = client.exec_command("sudo vdptool -t -i "+uplink_interface+" -V assoc -c mode=assoc")
            output = "".join(stdout.readlines())
            print "VDPTOOL command output:", output
            error_output = "".join(stderr.readlines()).strip()
            if error_output:
                raise Exception("Error:", error_output)     

            inst_str =  str_to_search
            if inst_str in output:
                print "String found in vdptool cmd output.\n"
                return True
            else:
                print "String not found in vdptool cmd output.\n" 
                return False #TODO: Return correct retval  
    
    def check_uplink_and_output(self, config_dict, inst_ip, instname, host_name):
        print "Connecting to database"
        #Connect to database
        mysql_db = MySqlConnection(config_dict)
        
        with MySqlConnection(config_dict) as mysql_connection:
        
            data = mysql_db.get_instances(mysql_connection, instname)
            print "Host name is:", data[MySqlDbTables.INSTANCES_HOST_NAME]
            host_name = data[MySqlDbTables.INSTANCES_HOST_NAME]

        uplinkInst = Uplink(config_dict)
        uplink_info = Uplink.get_info(uplinkInst, host_name)
        print "uplink veth:", uplink_info.vethInterface
        print "remote_port",  uplink_info.remotePort
        
        inst_str =  (inst_ip)
        
        for compute in config_dict['computes']:
            if compute['hostname'] == host_name:
                vdptool_inst = VdpToolCli()
                result = VdpToolCli.check_output(vdptool_inst, compute['ip'], compute['username'], compute['password'], uplink_info.vethInterface, inst_str)
        return result