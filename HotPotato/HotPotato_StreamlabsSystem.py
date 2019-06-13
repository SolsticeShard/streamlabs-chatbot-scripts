#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
import math
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), "lib")) #point at lib folder for classes / references

#   Import your Settings class
from Settings_Module import MySettings
#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "hotpotato"
Website = "www.github.com/solsticeshard"
Description = "simple chatbot implementation of a hot potato game. Active viewers take turns throwing a potato back and forth with a decreasing timer until it is dropped."
Creator = "SolsticeShard"
Version = "1.0.0.0"

#---------------------------
#   Define Global Variables
#---------------------------
global SettingsFile
SettingsFile = ""
global ScriptSettings
ScriptSettings = MySettings()

global GameIsRunning
GameIsRunning = False

global GameEndTime
GameEndTime = datetime.now()

global GameStartTime
GameStartTime = datetime.now()

global TimeToHold
TimeToHold = 0

global PeopleWhoHaveHeldThePotato
PeopleWhoHaveHeldThePotato = []

global PotatoHolder
PotatoHolder = ""

#---------------------------
#   [Required] Initialize Data (Only called on load)
#---------------------------
def Init():
    global ScriptSettings
    #   Create Settings Directory
    directory = os.path.join(os.path.dirname(__file__), "Settings")
    if not os.path.exists(directory):
        os.makedirs(directory)

    #   Load settings
    SettingsFile = os.path.join(os.path.dirname(__file__), "Settings\settings.json")
    ScriptSettings = MySettings(SettingsFile)
    
    return

#---------------------------
#   [Required] Execute Data / Process messages
#---------------------------
def Execute(data):
    global GameIsRunning
    global PotatoHolder
    global GameStartTime
    global GameEndTime
    global TimeToHold
    global ScriptSettings
    global PeopleWhoHaveHeldThePotato
    global ScriptSettings
    
    if data.IsChatMessage() and data.GetParam(0).lower() == ScriptSettings.Command and Parent.IsOnCooldown(ScriptName,ScriptSettings.Command):
        SendMessage(data, "The potato is still warming up! Come back in " + str(Parent.GetCooldownDuration(ScriptName,ScriptSettings.Command)) + " seconds!")
        return

    if data.GetParamCount() != 2:
        SendMessage(data, "To use" + ScriptSettings.Command + ", please provide a username to throw the potato to.")
        return
    
    targetUser = data.GetParam(1)
    if targetUser.lower() == data.User.lower():
        SendMessage(data, "You can't throw the potato to yourself, silly!")
        return

    if targetUser.lower() == ScriptSettings.StreamerUsername.lower() or targetUser.lower() == ScriptSettings.BotUsername.lower():
        SendMessage(data, "No throwing the potato to the streamer or a bot, silly.")
        return    

    if targetUser.lower() not in map(str.lower, Parent.GetViewerList()):
        SendMessage(data, "Sorry " + data.User + ", it looks like " + targetUser + " is not an active viewer.")
        return

    #If the game is not running, let's start it!
    if GameIsRunning == False:
        GameIsRunning = True
        GameStartTime = datetime.now()
        GameEndTime = datetime.now() + timedelta(minutes=5)
        PotatoHolder = targetUser
        TimeToHold = ScriptSettings.SecondsToHold
        PeopleWhoHaveHeldThePotato = [data.User, targetUser]
        SendMessage(data, "The potato is in the air! It's in your hands, " + targetUser + "!")
        return
    
    if data.User.lower() != PotatoHolder.lower():
        SendMessage(data, "The potato is in someone else's hands, " + data.User)
        return
    
    if data.User.lower() not in map(str.lower, PeopleWhoHaveHeldThePotato):
        PeopleWhoHaveHeldThePotato.append(data.User.lower())
    PotatoHolder = targetUser.lower()
    if TimeToHold > ScriptSettings.TimeDecrement:
        TimeToHold -= ScriptSettings.TimeDecrement
    GameEndTime = datetime.now() + timedelta(seconds = TimeToHold)
    SendMessage(data, data.User + " throws the potato to " + targetUser + "! They only have " + str(TimeToHold) + " seconds to throw it!")

    return

def SendMessage(data, msg):
    if data.IsFromTwitch():
        Parent.SendTwitchMessage(msg)
    else:
        Parent.SendDiscordMessage(msg)

#---------------------------
#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
#---------------------------
def Tick():
    global GameIsRunning
    global GameStartTime
    global GameEndTime
    global PotatoHolder
    global PeopleWhoHaveHeldThePotato

    if GameIsRunning == True and datetime.now() > GameEndTime:
        GameIsRunning = False
        Parent.AddCooldown(ScriptName,ScriptSettings.Command, 1800)
        Parent.SendTwitchMessage(PotatoHolder + " dropped the potato! Sorry, everyone else gets rewards.")
        if PotatoHolder in PeopleWhoHaveHeldThePotato:
            PeopleWhoHaveHeldThePotato.remove(PotatoHolder)
        datedifference = GameEndTime - GameStartTime
        reward = math.ceil(float(datedifference.seconds) / 60.0)
        rewardDict = {}
        rewardMsg = "The potato stayed up for " + str(reward) + " minutes, so the following users get " + str(reward) + " points! "
        for winner in PeopleWhoHaveHeldThePotato:
            rewardDict[winner.lower()] = reward
            rewardMsg += winner + " "
        Parent.AddPointsAll(rewardDict)
        Parent.SendTwitchMessage(rewardMsg)
        
    return

#---------------------------
#   [Optional] Parse method (Allows you to create your own custom $parameters) 
#---------------------------
def Parse(parseString, userid, username, targetid, targetname, message):
    
    if "$myparameter" in parseString:
        return parseString.replace("$myparameter","I am a cat!")
    
    return parseString

#---------------------------
#   [Optional] Reload Settings (Called when a user clicks the Save Settings button in the Chatbot UI)
#---------------------------
def ReloadSettings(jsonData):
    # Execute json reloading here
    ScriptSettings.__dict__ = json.loads(jsonData)
    ScriptSettings.Save(SettingsFile)
    return

#---------------------------
#   [Optional] Unload (Called when a user reloads their scripts or closes the bot / cleanup stuff)
#---------------------------
def Unload():
    return

#---------------------------
#   [Optional] ScriptToggled (Notifies you when a user disables your script or enables it)
#---------------------------
def ScriptToggled(state):
    return
