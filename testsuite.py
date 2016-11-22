#!/usr/bin/python
import argparse
from testcases.Ping import Ping
from testcases.CheckFlowsOnDelete import CheckFlowsOnDelete
from testcases.CheckFlowsOnDeleteOneInst import CheckFlowsOnDeleteOneInst
from testcases.VdpAssoc import VdpAssoc
from testcases.VdpDeassoc import VdpDeassoc
import sys
import yaml

TEST_CASE_MAP = {
    "1" : Ping,
    "2" : CheckFlowsOnDelete,
    "3" : CheckFlowsOnDeleteOneInst,
    "4" : VdpAssoc,
    "5" : VdpDeassoc
    #"6" : VlanTranslation
    
    }


'''
class BaseTestCase():
    def runTest():
'''    

def main():
    parser = argparse.ArgumentParser(description='This is OpenStack TestSuite')
    parser.add_argument('-f','--testbed_file', help = 'Provide the testbed file', required=True)
    '''parser.add_argument('--tests', help = 'Provide the test case', required=True)
    parser.add_argument('--dcnm', help = 'Provide the DCNM IP Address', required=True)
    parser.add_argument('--dcnmSysUsername', help = 'Provide the system user name of the dcnm', default = "root")
    parser.add_argument('--dcnmSysPassword', help = 'Provide the system password of the dcnm', default = "cisco123")
    parser.add_argument('--dcnmGuiUsername', help = 'Provide the GUI user name of the dcnm', default = "admin")
    parser.add_argument('--dcnmGuiPassword', help = 'Provide the GUI password of the dcnm', default = "cisco123")
    parser.add_argument('--computeHosts', help = 'Provide the Compute node IP Address', required=True)
    parser.add_argument('--computeUsername', help = 'Provide the user name of the compute node', default = "localadmin")
    parser.add_argument('--computePassword', help = 'Provide the password of the compute node', default = "cisco123")
    parser.add_argument('--controller', help = 'Provide the Controller node IP Address', required=True)
    parser.add_argument('--controllerUsername', help = 'Provide the user name of the controller node', default = "admin")
    parser.add_argument('--controllerSysUsername', help = 'Provide the system user name of the controller node', default = "localadmin")
    parser.add_argument('--controllerPassword', help = 'Provide the password of the controller node', default = "cisco123")
    parser.add_argument('--dbUsername', help = 'Provide the Mysql db  user name of the controller node', default = "root")
    parser.add_argument('--dbPassword', help = 'Provide the Mysql password of the controller node', default = "cisco123")'''
    args = parser.parse_args()
    file_handle = open(args.testbed_file)
    config_dict = yaml.safe_load(file_handle)
    file_handle.close()
    
    
    requestedTests = config_dict['tests']
    
    testCasesToRun = []
    for test in requestedTests:
        if TEST_CASE_MAP.has_key(str(test)):
            #print "Test Case:", test, "\n"
            testCasesToRun.append(TEST_CASE_MAP[str(test)](config_dict))
        else:
            print "Invalid test case request: " + str(test)
    print "TestCases requested by User: ", testCasesToRun
        
    result_list = []
    # Run all the tests
    for testCase in testCasesToRun:
        print "Running test case: ", testCase
        result = testCase.runTest()
        result_list.append(result)
    print "Results are:", result_list

if __name__ == "__main__":
    main()
