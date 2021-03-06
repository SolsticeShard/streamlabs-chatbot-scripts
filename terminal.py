import test
import sys
import os
from threading import Thread
import importlib
import importlib.util

from time import sleep


'''
This is a rudimentary terminal to simulate Twitch chat for the purposes of testing out Streamlabs chatbot scripts. It's a work in progress! To use, drop this file at the root of your scripts directory.

Type !cu to change your active user
Type !setpoints (user) (value) to set a user's points.
Type /w (message) to simulate sending a whisper to the bot
Type !import to load a named module from the terminal's directory
Type !quit to quit
'''

'''
This class simulates the Parent class available in chatbot scripts, effectively overloading the methods to work within the terminal.
'''
class Parent:
    Points = {}

    def __init__(self):
        return

    def AddPoints(self, user, amount):
        if user not in self.Points:
            self.Points[user.lower()] = amount
        else:
            self.Points[user.lower.lower()] = self.Points[user] + amount

        #TODO: check active viewer
        return True

    def AddPointsAll(self, data):
        for user in data:
            self.AddPoints(user.lower(), data[user])
        return []

    def RemovePointsAll(self, data):
        for user in data:
            self.RemovePoints(user.lower(), data[user])
        return []

    def RemovePoints(self, user, amount):
        if user.lower() not in self.Points:
            self.Points[user.lower()] = -amount
        else:
            self.Points[user.lower()] = self.Points[user.lower()] - amount
        
        return true

    def SendTwitchMessage(self, message):
        print("bot: " + message)

    def SendTwitchWhisper(self, user, message):
        print("bot >> " + user + ": " + message)

    def GetPoints(self, user):
        if user.lower() not in self.Points:
            self.Points[user.lower()] = 0
            return 0
        else:
            return self.Points[user.lower()]

    def IsOnCooldown(self, ScriptName, CommandName):
        #TODO: implement
        return False

'''
This class simulates the Data object passed into the script.
'''
class Data(object):
    User = ""
    Message = ""
    RawData = ""
    Whisper = ""
    Params = []
    
    def __init__(self, user, message, whisper):
        self.User = user
        self.Message = message
        self.Params = message.split(" ")
        self.Whisper = whisper

    def IsChatMessage(self):
        
        return not self.Whisper

    def IsRawData(self):
        #TODO Not sure what this is for.
        return True

    def IsFromTwitch(self):
        #TODO support discord vs twitch checking
        return True
    
    def IsFromDiscord(self):
        return False

    def IsWhisper(self):
        return self.Whisper
    
    def GetParam(self, id):
        return self.Params[id]
    
    def GetParamCount(self):
        return len(self.Params)

def GetInput(currentUser):
    return input(">>" + currentUser + ": ")

def execute_help(data):
    return


def tick_help(func):
    while True:
        func()
        sleep(1)

current_user = 'SolsticeShard'
command = ''
exec_funcs = []
parent = Parent()
starting_path = os.path.dirname(os.path.abspath(__file__))


for folder in os.listdir(starting_path):
    if os.path.isdir(os.path.join(starting_path, folder)):
        for filename in os.listdir(os.path.join(starting_path, folder)):
            if filename.endswith("_StreamlabsSystem.py"):
                module_name = filename.replace("_StreamlabsSystem.py", "")
                spec = importlib.util.spec_from_file_location(module_name, os.path.join(os.path.join(starting_path, folder), filename))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.Parent = parent
                exec_funcs.append(module.Execute)
                thread = Thread(target=tick_help, args=(module.Tick,))
                thread.daemon = True
                thread.start()
                print("META: Loaded script " + module_name)

while command != '!quit':
    command = GetInput(current_user)
    args = command.split(" ")
    if args[0] == '!import':
        active_script = importlib.import_module(command.replace("!import ", ""), "steve")
        active_script.Parent = Parent()
        active_script.Init()
        execute_help = active_script.Execute
        print("META: loaded script " + args[1])
    if args[0] == '!cu':
        current_user = args[1]
        print("META: Changed user to " + current_user)
        continue
    if args[0] == '!setpoints':
        parent.Points[args[1].lower()] = int(args[2])
        print("META: Set user " + str(args[1]) + " to " + str(args[2]) + " points.")
    else:
        if args[0] == '/w':
            data = Data(current_user, command.replace('/w ', ''), True)
        else:
            data = Data(current_user, command, False)
        for exec_func in exec_funcs:
            exec_func(data)

print("META: Exited!")