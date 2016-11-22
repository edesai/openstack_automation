'''
Created on Nov 21, 2016

@author: edesai
'''

from common.MySqlConnection import MySqlConnection
import json

class UplinkInfo:
    interface = ''
    vethInterface = ''
    switchIp = ''
    switchName = ''
    remotePort = ''
    
    
class Uplink(object):
    '''
    classdocs
    '''
    def __init__(self, args):
        '''
        Constructor
        '''
        self.args = args
        
    def get_info(self, host_name): 
        print "Connecting to database"
        #Connect to database
        mysql_db = MySqlConnection(self.args)
        with MySqlConnection(self.args) as mysql_connection:
            try:
                data = mysql_db.get_agent_info(mysql_connection, host_name)
                print "Agent info is:", data[3]
                info = json.loads(data[3])
                uplink_info = UplinkInfo()
                uplink_info.interface = info["uplink"]
                uplink_info.vethInterface = info["veth_intf"]
                print "veth_intf", uplink_info.vethInterface
                uplink_info.switchIp = info["topo"][uplink_info.vethInterface]["remote_mgmt_addr"]
                uplink_info.switchName = info["topo"][uplink_info.vethInterface]["remote_system_name"]
                uplink_info.remotePort = info["topo"][uplink_info.vethInterface]["remote_port"]
                return uplink_info       
            except Exception as e:
                print "Created Exception: ",e 
                return 1
        return 1  