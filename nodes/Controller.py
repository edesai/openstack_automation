'''
Created on Sep 22, 2016

@author: edesai
'''

import os_client_config
import os.path
from keystoneauth1.identity import v2
from keystoneauth1 import session
from keystoneauth1 import loading
from keystoneclient.v2_0 import client as keystone_client
import sys
from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client
import time

class Controller(object):
    '''
    classdocs
    '''
    def __init__(self, ip, username, password, sys_username):
        '''
        Constructor
        '''
        self.ip = ip
        self.username = username
        self.sys_username = sys_username
        self.password = password
        
    def get_nova_client(self, tenant_id, username, password):
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(auth_url='http://' + self.ip + ':5000/v2.0',
                                        username=username,
                                        password=password,
                                        project_id=tenant_id)
        sess = session.Session(auth=auth)
        return nova_client.Client(2, session=sess)
    
    def get_neutron_client(self, tenant_name, username, password): #TODO: Remove 
        '''
        creates a neutron client
        '''
        auth = v2.Password(auth_url='http://' + self.ip + ':5000/v2.0',
                                 username=username,
                                 password=password,
                                 tenant_name=tenant_name)
        sess = session.Session(auth=auth)
        return neutron_client.Client(session=sess)
        
    
    def get_keystone_client(self, project_name, region_name):
        '''
        creates a keystone client
        '''
        auth = v2.Password(auth_url='http://' + self.ip + ':5000/v2.0',
                           username= self.username,
                           password=self.password,
                           tenant_name=project_name)
        sess = session.Session(auth=auth)
        return keystone_client.Client(session=sess)
        
    def get_client(self, client_type, project_name, region_name):
        return os_client_config.make_client(
            client_type,
            auth_url='http://' + self.ip + ':5000/v2.0',
            username= self.username,
            password=self.password,
            project_name=project_name,
            region_name=region_name)
 

    def createProject(self, tenant_name):
        keystone = self.get_keystone_client(self.username, 'RegionOne')
        # Creating tenant/project
        new_tenant = keystone.tenants.create(tenant_name,
                                             description="Automation tenant",
                                             enabled=True)
        return new_tenant
    
    def getProject(self, tenant_name):
        keystone = self.get_keystone_client(self.username, 'RegionOne')
        tenants = keystone.tenants.list()
        for tenant in tenants:
            if tenant.name == tenant_name:
                return tenant
        return None
    
    def createUser(self, new_tenant, new_username, new_password):  
        keystone = self.get_keystone_client(self.username, 'RegionOne')  
        # Creating new user
        roleToUse = None
        for role in keystone.roles.list():
            if role.name == 'admin':
                print "Using admin role:"
                roleToUse = role
                break

        #new_user = None
        if roleToUse:
            new_user = keystone.users.create(new_username,
                                new_password,
                                tenant_id = new_tenant.id)
            keystone.roles.add_user_role(new_user, roleToUse, new_tenant)
            print "Created user:", new_user
        else:
            print "Role not found !!"
            sys.exit(-1) #TODO: Return specific codes

        return new_user
    
    def getUser(self, user_name):
        keystone = self.get_keystone_client(self.username, 'RegionOne')
        users = keystone.users.list() 
        for user in users:
            if user.name == user_name:
                return user    
        return None
    
    def createNetwork(self, tenant, name, new_username, new_password):
        neutron = self.get_neutron_client(tenant, new_username, new_password)
        body = {"network": {"name": name,
                   "admin_state_up": "True"}}
        new_network = neutron.create_network(body=body)
        new_network_id = new_network.get('network').get('id')
        print "Created network:", new_network, "network_id:", new_network_id, "\n"
        return new_network
    
    def getNetwork(self, tenant, name, new_username, new_password):
        neutron = self.get_neutron_client(tenant, new_username, new_password)
        networks_dict = neutron.list_networks(retrieve_all=True)
        networks = networks_dict['networks']
        for nw in networks:
            if nw['name'] == name:
                return nw
        return None    
        
     
    def createSubnet(self, new_network_id, tenant, new_username, new_password, subnet_range): 
        neutron = self.get_neutron_client(tenant, new_username, new_password)   
        sub_body = {'subnets': [{'cidr': subnet_range,
                          'ip_version': 4, 'network_id': new_network_id}]}
        new_subnet = neutron.create_subnet(body=sub_body)
        print "Created subnet:", new_subnet
        return new_subnet
    
    def deleteNetwork(self, new_network_id, tenant, new_username, new_password):
        neutron = self.get_neutron_client(tenant, new_username, new_password)
        neutron.delete_network(new_network_id)



    '''Create client'''
        
    def createInstance(self, tenant_id, username, password, network_id, 
                       hostname, key_name, availability_zone):
        nova = self.get_nova_client(tenant_id, username, password)
        print nova.servers.list()
        nics = [{'net-id':network_id}]
        image = nova.images.find(name="cirros-0.3.4-x86_64-uec")
        flavor = nova.flavors.find(name="m1.tiny")
        if image and flavor:
            instance = nova.servers.create(name=hostname, image=image, 
                                           flavor=flavor, nics=nics, 
                                           key_name=key_name.name, 
                                           availability_zone = availability_zone)
            print "Waiting for Instance to boot up..."
            time.sleep(100)

            print "Instance :", instance
            print "Instance:Networks :", instance.networks
            
        else:
            print "Error creating instance"
            print "image:", image, "flavor:", flavor
            sys.exit(-1) #TODO: Return specific codes   
            
        return instance
    
    
    def deleteInstance(self, tenant_id, username, password, hostname):
        nova = self.get_nova_client(tenant_id, username, password)
        servers_list = nova.servers.list()
        server_del = hostname
        
        for s in servers_list:
            if s.name == server_del:
                print("This server %s exists, so delete" % server_del)
                nova.servers.delete(s)
                break
            
        time.sleep(40)
        return
    
    
    def createKeyPair(self, tenant_id, username, password):
        with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as f:
            public_key = f.read()
          
        nova = self.get_nova_client(tenant_id, username, password)
        key = nova.keypairs.create('mykey', public_key)
         
        return key
    
    
    def deleteKeyPair(self, tenant_id, username, password):
        nova = self.get_nova_client(tenant_id, username, password)
        nova.keypairs.delete('mykey')
        return
        
    def createSecurityGroup(self, tenant_id, username, password):   
        nova = self.get_nova_client(tenant_id, username, password)
        group = nova.security_groups.find(name="default")
        if not group:
            group = nova.security_groups.create(name="default")
        
        nova.security_group_rules.create(group.id, ip_protocol="icmp",
                                         cidr="0.0.0.0/0",
                                         from_port=-1, to_port=-1)
        nova.security_group_rules.create(group.id, ip_protocol="tcp",
                                         cidr="0.0.0.0/0",
                                         from_port=22, to_port=22)   
        return group
         
   
    def createAggregate(self, tenant_id, username, password, agg_name, availability_zone): 
        nova = self.get_nova_client(tenant_id, username, password)        
        aggregate = nova.aggregates.create(agg_name, availability_zone)
        return aggregate
    
    def getAggregate(self, tenant_id, username, password, agg_name):
        nova = self.get_nova_client(tenant_id, username, password)
        aggregates = nova.aggregates.list()
        for aggregate in aggregates:
            if aggregate.name == agg_name:
                return aggregate    
        return None    