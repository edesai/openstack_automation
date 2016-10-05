#!/usr/bin/python
import argparse
from testcases.Ping import Ping

TEST_CASE_MAP = {
    "1" : Ping
}


'''
class BaseTestCase():
    def runTest():
'''    

def main():
    parser = argparse.ArgumentParser(description='This is OpenStack TestSuite')
    parser.add_argument('--tests', help = 'Provide the test case', required=True)
    parser.add_argument('--computeHosts', help = 'Provide the Compute node IP Address', required=True)
    parser.add_argument('--computeUsername', help = 'Provide the user name of the compute node', default = "localadmin")
    parser.add_argument('--computePassword', help = 'Provide the user name of the compute node', default = "cisco123")
    parser.add_argument('--controller', help = 'Provide the Controller node IP Address', required=True)
    parser.add_argument('--controllerUsername', help = 'Provide the user name of the controller node', default = "admin")
    parser.add_argument('--controllerSysUsername', help = 'Provide the system user name of the controller node', default = "localadmin")
    parser.add_argument('--controllerPassword', help = 'Provide the user name of the controller node', default = "cisco123")
    args = parser.parse_args()
    
    requestedTests = args.tests.split(',')

    testCasesToRun = []
    for test in requestedTests:
        if TEST_CASE_MAP.has_key(test):
            print "Test Case:", test, "\n"
            testCasesToRun.append(TEST_CASE_MAP[test](args))
        else:
            print "Invalid test case request: " + test
        
    
    # Run all the tests
    for testCase in testCasesToRun:
        testCase.runTest()
    

if __name__ == "__main__":
    main()
