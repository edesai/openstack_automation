'''
Created on Sep 22, 2016

@author: edesai
'''
#from common.utils import SSHConnection
import os_client_config
from keystoneauth1.identity import v2
from keystoneauth1 import session
from keystoneclient.v2_0 import client as keystone_client
import sys



class Controller(object):
    '''
    classdocs
    '''
    
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
        
    def createProject(self):
        '''
        '''
        keystone = self.get_keystone_client('admin', 'RegionOne')

        # Creating tenant/project
        new_tenant = keystone.tenants.create(tenant_name="automation-tenant",
                                             description="Automation tenant",
                                             enabled=True)
        
        
        # Creating new user
        roleToUse = None
        for role in keystone.roles.list():
            if role.name == 'admin':
                print "Using admin role:"
                roleToUse = role
                break

        new_user = None
        if roleToUse:
            new_user = keystone.users.create(name='auto_user',
                                password='cisco123',
                                tenant_id = new_tenant.id)
            keystone.roles.add_user_role(new_user, roleToUse, new_tenant)
            print "Created user:"
            print new_user
        else:
            print "Role not found !!"
            sys.exit(-1) #TODO: Return specific codes


        
        
        # Cleanup
        print "Deleting user:"
        keystone.users.delete(new_user)
        keystone.tenants.delete(new_tenant)
        
        
        # List projects
        #with SSHConnection(address=self.ip, username=self.username, password = self.password) as client:
        #   stdin, stdout, stderr = client.exec_command("uname -a")
        #    print "uname: " + stdout
        # Use sshHandle to run create project command
        '''Create client'''
        
    
