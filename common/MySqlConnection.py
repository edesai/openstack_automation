'''
Created on Oct 26, 2016

@author: edesai
'''
import MySQLdb
from common.MySqlDbTables import MySqlDbTables


class MySqlConnection(object):
    '''
    classdocs
    '''

    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self.host = config_dict['controller']['ip']
        self.user = config_dict['controller']['db']['username']
        self.password = config_dict['controller']['db']['password']
        self.dbName = "cisco_dfa"

    def __enter__(self):
        self.connection = MySQLdb.connect(host=self.host, user=self.user,
                                          passwd=self.password, db=self.dbName)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

    def get_instances(self, connection, instance_name):
        # prepare a cursor object using cursor() method
        cursor = connection.cursor()

        # execute the SQL query using execute() method.
        cursor.execute("select * from instances")

        # fetch all of the rows from the query
        data = cursor.fetchall()

        result = None
        for row in data:
            if(row[MySqlDbTables.INSTANCES_INSTANCE_NAME] == instance_name):
                result = row
                break

        # close the cursor object
        cursor.close()

        # print "Data after closing connection:", data
        return result

    def get_agent_info(self, connection, host_name):
        # prepare a cursor object using cursor() method
        cursor = connection.cursor()

        # execute the SQL query using execute() method.
        cursor.execute("select * from agents")

        # fetch all of the rows from the query
        data = cursor.fetchall()

        print "In get_agent_info_method, printing data:", data
        result = None
        for row in data:
            if(row[MySqlDbTables.AGENTS_HOST_NAME] == host_name):
                result = row
                break

        # close the cursor object
        cursor.close()

        # print "Data after closing connection:", data
        return result
