#!/usr/bin/python
import argparse
from testcases.Ping import Ping
from testcases.CheckFlowsOnDelete import CheckFlowsOnDelete
from testcases.CheckFlowsOnDeleteOneInst import CheckFlowsOnDeleteOneInst
from testcases.VdpAssoc import VdpAssoc
from testcases.VdpDeassoc import VdpDeassoc
from testcases.CheckVdpKeepAlive import CheckVdpKeepAlive
from testcases.DiffSubnetSameComputePing import DiffSubnetSameComputePing
from testcases.DiffSubnetDiffComputePing import DiffSubnetDiffComputePing
from testcases.SameSubnetSameComputePing import SameSubnetSameComputePing
import sys
import yaml


TEST_CASE_MAP = {
    "1" : Ping,
    "2" : CheckFlowsOnDelete,
    "3" : CheckFlowsOnDeleteOneInst,
    "4" : VdpAssoc,
    "5" : VdpDeassoc,
    "6" : CheckVdpKeepAlive,
    "7" : SameSubnetSameComputePing,
    "8" : DiffSubnetSameComputePing,
    "9" : DiffSubnetDiffComputePing      
    }


'''
class BaseTestCase():
    def runTest():
'''    

def main():
    parser = argparse.ArgumentParser(description='This is OpenStack TestSuite')
    parser.add_argument('-f','--testbed_file', help = 'Provide the testbed file', required=True)

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
