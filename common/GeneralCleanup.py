'''
Created on Jan 9, 2017

@author: edesai
'''
from nodes.Controller import Controller


class GeneralCleanup(object):
    '''
    classdocs
    '''

    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self.controller = Controller(
            config_dict['controller']['hostname'],
            config_dict['controller']['ip'],
            config_dict['controller']['username'],
            config_dict['controller']['password'],
            config_dict['controller']['sys_username'])

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

        self.config_dict = config_dict

    def start(self):
        print "In start()..."
        skip_nova = False
        skip_proj = False

        try:
            new_project = self.controller.getProject("admin")
            if not new_project:
                print "Project not found during general cleanup"
                skip_proj = True
        except Exception as e:
            print "Error:", e

        if skip_proj is False:
            try:
                nova = self.controller.get_nova_client(
                    new_project.id, self.new_user, self.new_password)
                if not nova:
                    print("Nova client not found during cleanup")
                    skip_nova = True
            except Exception as e:
                print "Error:", e

        if skip_nova is False and skip_proj is False:
            '''
            try:
                aggregates = self.controller.listAggregates(new_project.id, self.new_user, self.new_password)
                hosts = nova.hosts.list()
                #here assumption is each aggregate has one host
                for agg in aggregates:
                    for host in hosts:
                        agg.remove_host(host)
                for agg in aggregates:
                    nova.aggregates.delete(agg)

            except Exception as e:
                print "Error:", e
            '''
            try:
                instances = self.controller.listInstances(
                    new_project.id, "admin", "cisco123")
                return
                for instance in instances:
                    self.controller.deleteInstance(
                        new_project.id, self.new_user, self.new_password, instance.name)
            except Exception as e:
                print "Error:", e

            try:
                networks = self.controller.listNetworks(
                    new_project.id, self.new_user, self.new_password)
                for network in networks:
                    self.controller.deleteNetwork(
                        network['id'], self.new_tenant, self.new_user, self.new_password)
            except Exception as e:
                print "Error:", e

        try:
            new_user = self.controller.getUser(self.new_user)
            if not new_user:
                print("User not found during cleanup")
            else:
                new_user.delete()
        except Exception as e:
            print "Error:", e
