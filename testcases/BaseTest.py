'''
Created on Sep 22, 2016

@author: edesai
'''

class BaseTest(object):
    '''
    classdocs
    '''
    def __init__(self, args):
        '''
        Constructor
        '''
        self.args = args
        
    def runTest(self):
        '''
        '''
        print "Parent run test"   