'''
Created on Dec 15, 2016

@author: edesai
'''
from common.Utils import SSHConnection


class Ping(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''

    def verify_ping_qdhcpns(
            self,
            node_address,
            username,
            password,
            network_id,
            dest_ip):
        with SSHConnection(address=node_address, username=username, password=password) as client:
            failure_list = ["unreachable", "100% packet loss", "0 received"]
            stdin, stdout, stderr = client.exec_command(
                "sudo ip netns exec qdhcp-" + network_id + " ping -c 3 " + dest_ip)
            cmd = "sudo ip netns exec qdhcp-" + network_id + " ping -c 3 " + dest_ip
            print "Command is:", cmd
            output = "".join(stdout.readlines()).strip()
            error_output = "".join(stderr.readlines()).strip()
            print "Output:", output
            if error_output:
                print "Error:", error_output
                raise Exception("Ping failed...Failing test case\n")
            for word in failure_list:
                if word in output:
                    raise Exception("Ping failed...Failing test case\n")
            return True
