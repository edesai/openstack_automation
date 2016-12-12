#!/usr/bin/python
import argparse
from testcases.SameSubnetDiffComputePing import SameSubnetDiffComputePing 
from testcases.CheckFlowsOnDelete import CheckFlowsOnDelete
from testcases.CheckFlowsOnDeleteOneInst import CheckFlowsOnDeleteOneInst
from testcases.VdpAssoc import VdpAssoc
from testcases.VdpDeassoc import VdpDeassoc
from testcases.CheckVdpKeepAlive import CheckVdpKeepAlive
from testcases.DiffSubnetSameComputePing import DiffSubnetSameComputePing
from testcases.DiffSubnetDiffComputePing import DiffSubnetDiffComputePing
from testcases.SameSubnetSameComputePing import SameSubnetSameComputePing
from testcases.CheckDCNM import CheckDCNM
import yaml


TEST_CASE_MAP = {
    "1" : SameSubnetDiffComputePing,
    "2" : SameSubnetSameComputePing,
    "3" : DiffSubnetSameComputePing,
    "4" : DiffSubnetDiffComputePing,
    "5" : CheckFlowsOnDelete,
    "6" : CheckFlowsOnDeleteOneInst,
    "7" : VdpAssoc,
    "8" : VdpDeassoc,
    "9" : CheckVdpKeepAlive,
    "10": CheckDCNM  
    }


'''
class BaseTestCase():
    def runTest():
'''    

def main():
    parser = argparse.ArgumentParser(description='This is OpenStack TestSuite')
    parser.add_argument('-f','--testbed_file', help = 'Provide the testbed file', required=True)
    parser.add_argument('--tests', help = 'Provide comma-separated list of test cases to run (e.g 1,2)', required=True)

    args = parser.parse_args()
    file_handle = open(args.testbed_file)
    config_dict = yaml.safe_load(file_handle)
    file_handle.close()
    
    requestedTests = args.tests.split(',')
    #requestedTests = config_dict['tests']
    
    testCasesToRun = []
    for test in requestedTests:
        if TEST_CASE_MAP.has_key(str(test)):
            #print "Test Case:", test, "\n"
            testCasesToRun.append(TEST_CASE_MAP[str(test)](config_dict))
        else:
            print "Invalid test case request: " + str(test)
    print "TestCases requested by User: ", requestedTests
        
    result_list = []
    # Run all the tests
    for testCase in testCasesToRun:
        print "Running test case: ", testCase
        result = testCase.runTest()
        result_list.append(result)
    print "Results are:", result_list
    
if __name__ == "__main__":
    main()
