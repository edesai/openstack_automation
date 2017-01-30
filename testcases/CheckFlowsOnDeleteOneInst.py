'''
Created on Nov 18, 2016

@author: edesai
'''
from nodes.Controller import Controller
from nodes.Compute import Compute
import time
from common.MySqlConnection import MySqlConnection
from common.OvsFlowsCli import OvsFlowsCli
from common.ReturnValue import ReturnValue
from common.MySqlDbTables import MySqlDbTables
from common.CheckStatusOfServices import CheckStatusOfServices
from constants import resultConstants


class CheckFlowsOnDeleteOneInst(object):
    '''
    classdocs
    '''

    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self.config_dict = config_dict
        self.controller = Controller(
            config_dict['controller']['hostname'],
            config_dict['controller']['ip'],
            config_dict['controller']['username'],
            config_dict['controller']['password'],
            config_dict['controller']['sys_username'])

        self.computeHosts = []
        for compute in config_dict['computes']:
            self.computeHosts.append(
                Compute(
                    compute['hostname'],
                    compute['ip'],
                    compute['username'],
                    compute['password']))

        self.new_tenant = config_dict[
            'openstack_tenant_details']['tenant_name']

        if "tenant_username" in config_dict["openstack_tenant_details"] and config_dict[
                'openstack_tenant_details']['tenant_username'] is not None:
            self.new_user = config_dict[
                'openstack_tenant_details']['tenant_username']
        else:
            self.new_user = "auto_user"
        if "tenant_password" in config_dict["openstack_tenant_details"] and config_dict[
                'openstack_tenant_details']['tenant_password'] is not None:
            self.new_password = config_dict[
                'openstack_tenant_details']['tenant_password']
        else:
            self.new_password = "cisco123"
        self.new_network1 = self.new_tenant + "nw1"
        self.new_subnw1 = "10.11.12.0/24"
        self.new_inst1 = self.new_tenant + "inst1"
        self.new_inst2 = self.new_tenant + "inst2"
        self.config_dict = config_dict

    def runTest(self):
        del_inst = False
        try:
            # Basic checks for status of services
            status_inst = CheckStatusOfServices(self.config_dict)
            status = CheckStatusOfServices.check(status_inst)
            if not status:
                print "Some service/s not running...Unable to run testcase"
                return resultConstants.RESULT_ABORT

            # Create project & user
            new_project_user = self.controller.createProjectUser(
                self.new_tenant, self.new_user, self.new_password)

            # Create network and subnetwork
            new_network_inst1 = self.controller.createNetworkSubNetwork(
                self.new_tenant,
                self.new_network1,
                self.new_subnw1,
                self.new_user,
                self.new_password)

            # Create key-pair & security groups and rules
            keypair_secgrp = self.controller.createKeyPairSecurityGroup(
                new_project_user.tenant.id, self.new_user, self.new_password)

            # Create instance
            host1 = self.controller.createInstance(
                new_project_user.tenant.id,
                self.new_user,
                self.new_password,
                new_network_inst1.network.get('network').get('id'),
                self.new_inst1,
                key_name=keypair_secgrp.key_pair,
                availability_zone=None)
            del_inst = True
            print "Host1:", host1

            # Create instance
            host2 = self.controller.createInstance(
                new_project_user.tenant.id,
                self.new_user,
                self.new_password,
                new_network_inst1.network.get('network').get('id'),
                self.new_inst2,
                key_name=keypair_secgrp.key_pair,
                availability_zone=None)
            print "Host2:", host2

            time.sleep(20)  # wait for flows to be added

            # Verify Flows
            vdptool_inst = OvsFlowsCli()
            result = OvsFlowsCli.check_if_exists_in_both_br_flows(
                vdptool_inst,
                self.config_dict,
                self.controller.ip,
                self.controller.sys_username,
                self.controller.password,
                host1[0].name)
            if not result:
                raise Exception("Incorrect OVS flows")

            # Verify that flows are not deleted after deleting one instance on
            # Controller+Compute
            self.controller.deleteKeyPair(
                new_project_user.tenant.id,
                self.new_user,
                self.new_password)
            print "Deleting only 1 Instance - " + self.new_inst1 + "..."
            self.controller.deleteInstance(
                new_project_user.tenant.id,
                self.new_user,
                self.new_password,
                self.new_inst1)
            del_inst = False

            print "Waiting before checking the flows\n"
            time.sleep(20)  # wait for flows to be deleted

            # Verify if DB has the instance info (Expected : Not found)
            mysql_db = MySqlConnection(self.config_dict)

            with MySqlConnection(self.config_dict) as mysql_connection:
                data = mysql_db.get_instances(mysql_connection, host1[0].name)
            
            if data is not None:
                raise Exception("DB not cleared for the instance")    
                '''
                result = OvsFlowsCli.check_if_exists_in_both_br_flows(
                vdptool_inst,
                self.config_dict,
                self.controller.ip,
                self.controller.sys_username,
                self.controller.password,
                host1[0].name)
            if not result:
                raise Exception("Incorrect OVS flows")'''

        except Exception as e:
            print "Exception:", e
            return resultConstants.RESULT_ABORT
            if del_inst:
                # Deleting instance and network
                self.controller.deleteKeyPair(new_project_user.tenant.id,
                                              self.new_user, self.new_password)
                print "Deleting Instance " + self.new_inst1 + "..."
                self.controller.deleteInstance(
                    new_project_user.tenant.id,
                    self.new_user,
                    self.new_password,
                    self.new_inst1)
            self.cleanup()
            return ReturnValue.FAILURE

        self.cleanup()
        print "Done"
        return ReturnValue.SUCCESS

    def cleanup(self):
        print "Cleanup:"
        skip_proj = False

        try:
            new_project_user = self.controller.getProjectUser(
                self.new_tenant, self.new_user)
            if not new_project_user:
                print "Project/User not found during cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e

        if skip_proj is False:

            try:
                self.controller.deleteInstance(
                    new_project_user.tenant.id,
                    self.new_user,
                    self.new_password,
                    self.new_inst2)
            except Exception as e:
                print "Error:", e

        try:
            self.controller.deleteNetwork(
                self.controller,
                self.new_network1,
                self.new_tenant,
                self.new_user,
                self.new_password)
        except Exception as e:
            print "Error:", e

        try:
            self.controller.deleteProjectUser(
                self.controller, new_project_user)
        except Exception as e:
            print "Error:", e

        print "Done"
        return ReturnValue.SUCCESS
