'''
Created on Sep 22, 2016

@author: edesai
'''
#from common.utils import SSHConnection
import os_client_config
from keystoneauth1.identity import v2
from keystoneauth1 import session
from keystoneauth1 import loading
from keystoneclient.v2_0 import client as keystone_client
import sys
from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client





class Controller(object):
    '''
    classdocs
    '''
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
 
    def __init__(self, ip, username, password):
        '''
        Constructor
        '''
        self.ip = ip
        self.username = username
        self.password = password
        
    def createProject(self, tenant_name):
        '''
        '''
        keystone = self.get_keystone_client('admin', 'RegionOne')

        # Creating tenant/project
        new_tenant = keystone.tenants.create(tenant_name,
                                             description="Automation tenant",
                                             enabled=True)
        return new_tenant
    
    def createUser(self, new_tenant, new_username, new_password):  
        
        keystone = self.get_keystone_client('admin', 'RegionOne')  
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
            print "Created user:"
            print new_user
        else:
            print "Role not found !!"
            sys.exit(-1) #TODO: Return specific codes

        return new_user
        
        
    def createNetwork(self, tenant, name, new_username, new_password):
        neutron = self.get_neutron_client(tenant, new_username, new_password)
        body = {"network": {"name": name,
                   "admin_state_up": "True"}}
        new_network = neutron.create_network(body=body)
        new_network_id = new_network.get('network').get('id')
        print "Created network:", new_network, "network_id:", new_network_id, "\n"
        return new_network
    
     
    def createSubnet(self, new_network_id,tenant, new_username, new_password): 
        neutron = self.get_neutron_client(tenant, new_username, new_password)   
        sub_body = {'subnets': [{'cidr': '51.50.49.0/24',
                          'ip_version': 4, 'network_id': new_network_id}]}
        new_subnet = neutron.create_subnet(body=sub_body)
        print "Created subnet:", new_subnet
        return new_subnet
    
    def deleteNetwork(self, new_network_id, tenant, new_username, new_password):
        neutron = self.get_neutron_client(tenant, new_username, new_password)
        neutron.delete_network(new_network_id)
        # List projects
        #with SSHConnection(address=self.ip, username=self.username, password = self.password) as client:
        #   stdin, stdout, stderr = client.exec_command("uname -a")
        #    print "uname: " + stdout
        # Use sshHandle to run create project command
        '''Create client'''
        
    def createInstance(self, tenant_id, username, password, network_id, hostname):
        nova = self.get_nova_client(tenant_id, username, password)
        print nova.servers.list()
        nics = [{'net-id':network_id}]
        image = nova.images.find(name="cirros-0.3.4-x86_64-uec")
        flavor = nova.flavors.find(name="m1.tiny")
        if image and flavor:
            instance = nova.servers.create(name=hostname, image=image, 
                                           flavor=flavor, nics=nics)
        else:
            print "Error creating instance"
            print "image:", image, "flavor:", flavor
            sys.exit(-1) #TODO: Return specific codes   
            
        return instance
