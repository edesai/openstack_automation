#!/usr/bin/python
import argparse
import yaml
import os.path

from testcases.SameSubnetDiffComputePing import SameSubnetDiffComputePing 
from testcases.CheckFlowsOnDelete import CheckFlowsOnDelete
from testcases.CheckFlowsOnComputeOnDelete import CheckFlowsOnComputeOnDelete
from testcases.CheckFlowsOnDeleteOneInst import CheckFlowsOnDeleteOneInst
from testcases.VdpAssoc import VdpAssoc
from testcases.VdpDeassoc import VdpDeassoc
from testcases.CheckVdpKeepAlive import CheckVdpKeepAlive
from testcases.DiffSubnetSameComputePing import DiffSubnetSameComputePing
from testcases.DiffSubnetDiffComputePing import DiffSubnetDiffComputePing
from testcases.SameSubnetSameComputePing import SameSubnetSameComputePing
from testcases.RestartEnablerServer import RestartEnablerServer
from testcases.RestartEnablerAgentController import RestartEnablerAgentController
from testcases.RestartLldpadController import RestartLldpadController
from testcases.VerifyDCNM import VerifyDCNM
from testcases.GenericPingSameSubnetDiffCompute import GenericPingSameSubnetDiffCompute
from testcases.GenericPingDiffSubnetDiffCompute import GenericPingDiffSubnetDiffCompute
from constants import resultConstants


TEST_CASE_MAP = {
    "1" : GenericPingSameSubnetDiffCompute,
    "2" : SameSubnetSameComputePing,
    "3" : DiffSubnetSameComputePing,
    "4" : GenericPingDiffSubnetDiffCompute,
    "5" : CheckFlowsOnDelete,
    "6" : CheckFlowsOnDeleteOneInst,
    "7" : CheckFlowsOnComputeOnDelete,
    "8" : VdpAssoc,
    "9" : VdpDeassoc,
    "10": VerifyDCNM,
    "11" : RestartEnablerServer,
    "12" : RestartEnablerAgentController, 
    "13" : RestartLldpadController,
    "14" : CheckVdpKeepAlive  
    }


def main():
    try:
        parser = argparse.ArgumentParser(description='This is OpenStack TestSuite')
        parser.add_argument('-f','--testbed_file', help = 'Provide the testbed file', required=True)
        parser.add_argument('--tests', help = 'Provide comma-separated list of test cases to run (e.g 1,2)', required=True)
    
        args = parser.parse_args()
        
        with open(args.testbed_file) as file_handle:
            config_dict = yaml.safe_load(file_handle)
        
    
        requestedTests = args.tests.split(',')
        
        testCasesToRun = []
        for test in requestedTests:
            if TEST_CASE_MAP.has_key(str(test)):
                testCasesToRun.append(TEST_CASE_MAP[str(test)](config_dict))
            else:
                print "Invalid test case request: " + str(test)
        print "TestCases requested by User: ", requestedTests
        
        result_list = []
        # Run all the tests
        for testCase in testCasesToRun:
            print "Running test case: ", testCase
            result = testCase.runTest()
            if result == resultConstants.RESULT_ABORT:
                result_list.append(result)
                raise Exception("Aborting testsuite")
            else:
                result_list.append(result)
        print "Results are:", result_list
        
    except Exception as e:
        print "Exception created", e
        print "Results are:", result_list   
         
if __name__ == "__main__":
    main()
