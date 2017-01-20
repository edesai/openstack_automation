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

class ProjectUser:
    tenant = ''
    user = ''

class NetworkSubNetwork:
    network = ''
    sub_network = '' 
    
class KeyPairSecGroup:
    key_pair = ''
    sec_grp = ''       
    
class Controller(object):
    '''
    classdocs
    '''
    def __init__(self, hostname, ip, username, password, sys_username):
        '''
        Constructor
        '''
        self.address = hostname
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
        print "Projects are:", tenants
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
            print "Created user:", new_username
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
    
    def createProjectUser(self, tenant_name, new_username, new_password):
        keystone = self.get_keystone_client(self.username, 'RegionOne')
        # Creating tenant/project
        new_tenant = keystone.tenants.create(tenant_name,
                                             description="Automation tenant",
                                             enabled=True)
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
            print "Created user:", new_username
        else:
            print "Role not found !!"
            sys.exit(-1) #TODO: Return specific codes
        
        projUserInst = ProjectUser()
        projUserInst.tenant = new_tenant
        projUserInst.user = new_user
        
        return projUserInst
            
    def getProjectUser(self, tenant_name, username):
        tenant_found = None
        keystone = self.get_keystone_client(self.username, 'RegionOne')
        tenants = keystone.tenants.list()
        print "Projects are:", tenants
        for tenant in tenants:
            if tenant.name == tenant_name:
                tenant_found = tenant
        if tenant_found == None:
            print "Project not found"
            return None
        users = keystone.users.list() 
        for user in users:
            if user.name == username:
                user_found = user 
        if user_found == None:
            print "User not found !!" 
            return None              
        projUserInst = ProjectUser()
        projUserInst.tenant = tenant_found
        projUserInst.user = user_found
        return projUserInst
    
    def deleteProjectUser(self, controller, project_user):
        try:
            user = controller.getUser(project_user.user.username)
            user.delete()
            tenant = controller.getProject(project_user.tenant.name)
            tenant.delete()
        except Exception as e:
            raise Exception("Exception during delete of project/user")
        
    def createNetwork(self, tenant, name, new_username, new_password):
        neutron = self.get_neutron_client(tenant, new_username, new_password)
        body = {"network": {"name": name,
                   "admin_state_up": "True"}}
        new_network = neutron.create_network(body=body)
        new_network_id = new_network.get('network').get('id')
        print "Created network:", name, "network_id:", new_network_id, "\n"
        return new_network
    
    def getNetwork(self, tenant, name, new_username, new_password):
        neutron = self.get_neutron_client(tenant, new_username, new_password)
        networks_dict = neutron.list_networks(retrieve_all=True)
        networks = networks_dict['networks']
        for nw in networks:
            if nw['name'] == name:
                return nw
        return None    
    
    def listNetworks(self, tenant, new_username, new_password):   
        neutron = self.get_neutron_client(tenant, new_username, new_password)
        networks_dict = neutron.list_networks(retrieve_all=True)
        networks = networks_dict['networks']
        return networks 
     
    def createSubnet(self, new_network_id, tenant, new_username, new_password, subnet_range): 
        #neutron = self.get_neutron_client(tenant, new_username, new_password)   
        neutron = self.get_neutron_client(tenant, new_username, new_password)
        sub_body = {'subnets': [{'cidr': subnet_range,
                          'ip_version': 4, 'network_id': new_network_id}]}
        new_subnet = neutron.create_subnet(body=sub_body)
        print "Created subnet:", subnet_range
        return new_subnet
    
    def deleteNetwork(self, controller, new_network, tenant, new_username, new_password):
        try:
            neutron = self.get_neutron_client(tenant, new_username, new_password)
            network = controller.getNetwork(tenant, new_network, new_username, new_password)
            neutron.delete_network(network.get('id'))
            time.sleep(90)
        except Exception as e:
            print "Exception found:", e
        return
    
    def createNetworkSubNetwork(self, tenant, name, subnet_range, new_username, new_password):
        neutron = self.get_neutron_client(tenant, new_username, new_password)        
        body = {"network": {"name": name,
                   "admin_state_up": "True"}}
        new_network = neutron.create_network(body=body)
        new_network_id = new_network.get('network').get('id')
        print "Created network:", name, "network_id:", new_network_id, "\n"
        sub_body = {'subnets': [{'cidr': subnet_range,
                          'ip_version': 4, 'network_id': new_network_id}]}
        new_subnet = neutron.create_subnet(body=sub_body)
        print "Created subnet:", subnet_range
        network_inst = NetworkSubNetwork()
        network_inst.network = new_network
        network_inst.sub_network = new_subnet
        return network_inst
        

    '''Create client'''
        
    def createInstance(self, tenant_id, new_username, new_password, network_id, 
                       inst_name, key_name, availability_zone=None, count = 1):
        nova = self.get_nova_client(tenant_id, new_username, new_password)
        print nova.servers.list()
        nics = [{'net-id':network_id}]
        image = nova.images.find(name="cirros-0.3.4-x86_64-uec")
        flavor = nova.flavors.find(name="m1.tiny")
        instance_list = []
        if image and flavor:
            for x in range(count):
                instance = nova.servers.create(name = (inst_name+"-"+str(x+1) if (count > 1) else inst_name), 
                                               image=image,flavor=flavor, nics=nics, 
                                               key_name=key_name.name, availability_zone = availability_zone)
                instance_list.append(instance)
                print "Waiting for Instance to boot up..."
                time.sleep(100)
            
            #time.sleep(100)
            
        else:
            print "Error creating instance"
            sys.exit(-1) #TODO: Return specific codes   
            
        return instance_list
    
    
    def deleteInstance(self, tenant_id, username, password, inst_name, count = 1):
        for x in range(count):
            nova = self.get_nova_client(tenant_id, username, password)
            servers_list = nova.servers.list()
            server_del = inst_name+"-"+str(x+1) if (count > 1) else inst_name
            
            for s in servers_list:
                if s.name == server_del:
                    print("This server %s exists, so delete" % server_del)
                    nova.servers.delete(s)
                    time.sleep(90)
                    break
            
        #time.sleep(90)
        return
    
    def listInstances(self, tenant_id, username, password): 
        nova = self.get_nova_client(tenant_id, username, password)
        servers_list = nova.servers.list()
        return servers_list
    
    def createKeyPair(self, tenant_id, new_username, new_password):
        with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as f:
            public_key = f.read()
          
        nova = self.get_nova_client(tenant_id, new_username, new_password)
        key = nova.keypairs.create('mykey', public_key)
         
        return key
    
    
    def deleteKeyPair(self, tenant_id, username, password):
        nova = self.get_nova_client(tenant_id, username, password)
        nova.keypairs.delete('mykey')
        return
        
    def createSecurityGroup(self, tenant_id, new_username, new_password):   
        nova = self.get_nova_client(tenant_id, new_username, new_password)
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
    
    def createKeyPairSecurityGroup(self, tenant_id, new_username, new_password):
        nova = self.get_nova_client(tenant_id, new_username, new_password)
        with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as f:
            public_key = f.read()
        group = nova.security_groups.find(name="default")  
        if not group:
            group = nova.security_groups.create(name="default")
        
        key = nova.keypairs.create('mykey', public_key)
        
        nova.security_group_rules.create(group.id, ip_protocol="icmp",
                                         cidr="0.0.0.0/0",
                                         from_port=-1, to_port=-1)
        nova.security_group_rules.create(group.id, ip_protocol="tcp",
                                         cidr="0.0.0.0/0",
                                         from_port=22, to_port=22)   
        
        keypair_secgroup = KeyPairSecGroup()
        keypair_secgroup.key_pair = key
        keypair_secgroup.sec_grp = group
        return keypair_secgroup     
   
    def createAggregate(self, tenant_id, new_username, new_password, agg_name, availability_zone): 
        nova = self.get_nova_client(tenant_id, new_username, new_password)        
        aggregate = nova.aggregates.create(agg_name, availability_zone)
        return aggregate
    
    def deleteAggregate(self, controller, tenant_id, username, password, 
                        agg_name, host_list):
        try:
            nova = self.get_nova_client(tenant_id, username, password)
            aggregate = controller.getAggregate(tenant_id, username, password,
                                             agg_name=agg_name)
            if not aggregate:
                print "Aggregate"+aggregate+"not found"
                return False
            else:
                for host in host_list:
                    aggregate.remove_host(host.hostname)
                    nova.aggregates.delete(agg_name)
            return True
        except Exception as e:
            print "Error:", e
            
    def deleteAggregateList(self, controller, tenant_id, username, password, 
                        agg_list, host_list):        
        if(len(agg_list) != len(host_list)):
            raise Exception ("Length of host_list and aggregate_list "
                             "is not same.Consider using deleteAggregate Api instead")
            
        try:
            nova = self.get_nova_client(tenant_id, username, password)
            
            for var in range(len(host_list)):
                aggregate = controller.getAggregate(tenant_id, username, password,
                                             agg_list[var])
                if aggregate is None:
                    print "Aggregate"+agg_list[var]+"not found"
                    return False
                else:
                    aggregate.remove_host(host_list[var].hostname)
                    nova.aggregates.delete(aggregate)
            return True
        except Exception as e:
            print "Error:", e                
                
            
    
    def getAggregate(self, tenant_id, username, password, agg_name):
        nova = self.get_nova_client(tenant_id, username, password)
        aggregates = nova.aggregates.list()
        for aggregate in aggregates:
            if aggregate.name == agg_name:
                return aggregate    
        return None 
    
    def listAggregates(self, tenant_id, username, password): 
        nova = self.get_nova_client(tenant_id, username, password)
        aggregates = nova.aggregates.list()  
        return aggregates