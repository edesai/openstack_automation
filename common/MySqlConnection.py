'''
Created on Oct 26, 2016

@author: edesai
'''
import MySQLdb

class MySqlConnection(object):
    '''
    classdocs
    '''
    def __init__(self, args):
        '''
        Constructor
        '''
        self.args = args
        self.host = self.args.controller
        self.user = self.args.dbUsername
        self.password = self.args.dbPassword
        self.dbName = "cisco_dfa"
        
    def __enter__(self):
        self.connection = MySQLdb.connect (host = self.host, user = self.user, 
                                      passwd = self.password, db = self.dbName)
        return self.connection
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close ()
    
    def get_instances(self, connection, instance_name):
        # prepare a cursor object using cursor() method
        cursor = connection.cursor ()
        
        # execute the SQL query using execute() method.
        cursor.execute("select * from instances")
        
        # fetch all of the rows from the query
        data = cursor.fetchall ()
        
        result = 0
        for row in data :
            if(row[1] == instance_name):
                result = row
                break
        
        # close the cursor object
        cursor.close ()
        
        #print "Data after closing connection:", data         
        return result
    
    def get_agent_info(self, connection, host_name):
        # prepare a cursor object using cursor() method
        cursor = connection.cursor ()
        
        # execute the SQL query using execute() method.
        cursor.execute("select * from agents")
        
        # fetch all of the rows from the query
        data = cursor.fetchall ()
        
        print "In get_agent_info_method, printing data:", data
        result = 0
        for row in data :
            if(row[0] == host_name):
                result = row
                break
        
        # close the cursor object
        cursor.close ()
        
        #print "Data after closing connection:", data         
        return result
    