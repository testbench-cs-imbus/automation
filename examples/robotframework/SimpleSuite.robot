*** Settings ***
Resource    /home/holger/repos/tbcs/automation/examples/robotframework/resources/simple.robot

*** Test Cases ***
Simple Test Case
	#    Test steps
	Magic Additon    a=4    b=2
	Magic Result Check    value=42
	Log Something    text=Is'nt it magic?
