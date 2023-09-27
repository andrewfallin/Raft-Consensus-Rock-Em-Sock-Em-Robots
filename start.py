# ________________________________________________________________
# --------- START-UP FUNCTION & PROCESS INITIALIZATION -----------
# ================================================================
"""
LOCAL RUN COMMAND:
    python PycharmProjects/520-DS_Proj2/start.py
"""
import os

from Client import Client
from Server import Server


def processStartup() -> None:
    """Function to take user input and read from a configuration file to initialize a specific process node"""
    # Greet and get input
    print("=========================================================================================================")
    print("Hello! Welcome to a Raft consensus implementation of Rock-Em-Sock-Em Robots over multiple game servers...")
    print("=========================================================================================================\n")
    print("Is this process node running locally or on Amazon Web Services?")
    awsOrLocal = input("Type 'local' or 'AWS'\n-> ")
    while awsOrLocal not in ["local", "LOCAL", "l", "L", "aws", "AWS", "a", "A"]:
        awsOrLocal = input("Invalid! Please type 'local' or 'AWS'\n-> ")
    processID = int(input("Provide the Process ID as an integer:\n-> "))
    while processID not in range(7):
        processID = int(input("Invalid! Provide the Process ID as an integer:\n-> "))
    # Set the absolute path to the configuration file
    workingDir = os.getcwd()
    configFilePath = ""
    if awsOrLocal == "local" or awsOrLocal == "Local" or awsOrLocal == "LOCAL" or awsOrLocal == "l" or awsOrLocal == "L":
        configFilePath = os.path.join(workingDir, "config.txt")
    elif awsOrLocal == "aws" or awsOrLocal == "Aws" or awsOrLocal == "AWS" or awsOrLocal == "a" or awsOrLocal == "A":
        configFilePath = "/home/ec2-user/520-DS_Proj2/config.txt"
    # Read config file and split on lines
    with open(configFilePath, "r") as config:
        configAsString = config.read()
    configLines = configAsString.split("\n")
    # Get configurations
    configurations = []
    for line in range(len(configLines)):
        if configLines[line] == "$LOCAL$" and (
                awsOrLocal == "local" or awsOrLocal == "Local" or awsOrLocal == "LOCAL" or awsOrLocal == "l" or awsOrLocal == "L"):
            for processLine in range(1, 8):
                processConfigs = configLines[line + processLine].split(" ")
                configurations.append(processConfigs)
        elif configLines[line] == "$AWS$" and (
                awsOrLocal == "aws" or awsOrLocal == "Aws" or awsOrLocal == "AWS" or awsOrLocal == "a" or awsOrLocal == "A"):
            for processLine in range(1, 8):
                processConfigs = configLines[line + processLine].split(" ")
                configurations.append(processConfigs)
    # Parse out this process's configurations and form node group
    name = ""
    publicIP = ""
    port = -1
    privateIP = ""
    backupPath = ""
    group = []
    for process in configurations:
        if int(process[0]) == processID:
            name = process[1]
            publicIP = process[2]
            port = int(process[3])
            privateIP = process[4]
            backupPath = os.path.join(workingDir, process[5])
        elif int(process[0]) != processID:
            processNetworking = (process[1], process[2], int(process[3]))
            group.append(processNetworking)
    # Print initialization data
    print("Process Name: " + name)
    print("Public IP: " + publicIP)
    print("Port: " + str(port))
    print("Private IP: " + privateIP)
    print("Backup Path: " + backupPath)
    print("Group: ")
    for process in group:
        print(str(process))
    print("\n")
    # Initialize process based on type and launch threads
    if name[0] == "C":
        thisClient = Client(processID, name, privateIP, port, group, backupPath)
        thisClient.startThreads()
    elif name[0] == "S":
        thisServer = Server(processID, name, privateIP, port, group, backupPath)
        thisServer.startThreads()


# START-UP SCRIPT
if __name__ == "__main__":
    processStartup()
