'''
Created on Dec 7, 2016

@author: edesai
'''
from common.Utils import SSHConnection
from common.MySqlConnection import MySqlConnection
from common.MySqlDbTables import MySqlDbTables
from common.VdpToolCli import VdpToolCli


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

        with SSHConnection(address=node_ip, username=node_username, password=node_password) as client:

            stdin, stdout, stderr = client.exec_command(
                "sudo ovs-ofctl dump-flows " + bridge_name)
            output = "".join(stdout.readlines())
            error_output = "".join(stderr.readlines()).strip()
            if error_output:
                raise Exception(bridge_name + " Error:", error_output)

            print "Output:", output

            if search_str in output:
                print search_str + " found in " + bridge_name + " flows\n"
                return True

            else:
                print search_str + " not found in " + bridge_name + " flows\n"
                return False

    def check_if_exists_in_both_br_flows(
            self,
            config_dict,
            node_ip,
            node_username,
            node_password,
            instname):
        # Connect to database
        mysql_db = MySqlConnection(config_dict)

        with MySqlConnection(config_dict) as mysql_connection:
            data = mysql_db.get_instances(mysql_connection, instname)
            if data is None:
                print ("No data found in mysql db")
                return False

            print "Instance name:", data[MySqlDbTables.INSTANCES_INSTANCE_NAME], ", Instance IP:", data[MySqlDbTables.INSTANCES_INSTANCE_IP], ", vdp_vlan:", data[MySqlDbTables.INSTANCES_VDP_VLAN]
            vdp_vlan = str(data[MySqlDbTables.INSTANCES_VDP_VLAN])

        if vdp_vlan == 0:
            print "VDP VLAN is 0 which is unexpected."
            raise Exception("Incorrect VDP Vlan.\n")

        search_str = "dl_vlan=" + vdp_vlan
        vdptool_inst = OvsFlowsCli()
        result1 = OvsFlowsCli.check_output(
            vdptool_inst,
            node_ip,
            node_username,
            node_password,
            "br-int",
            search_str)

        search_str = "mod_vlan_vid:" + vdp_vlan
        vdptool_inst = OvsFlowsCli()
        result2 = OvsFlowsCli.check_output(
            vdptool_inst,
            node_ip,
            node_username,
            node_password,
            "br-ethd",
            search_str)
        return result1 and result2

    def verify_ovs_and_vdp(self, config_dict, node_ip, node_username,
                           node_password, inst_name, inst_ip, inst_hostname):

        result1 = OvsFlowsCli.check_if_exists_in_both_br_flows(
            self, config_dict, node_ip, node_username, node_password, inst_name)

        # Verify vdptool output
        vdptool_inst = VdpToolCli()
        result2 = VdpToolCli.check_uplink_and_output(
            vdptool_inst, config_dict, inst_ip, inst_name, inst_hostname)

        return (result1 and result2)
