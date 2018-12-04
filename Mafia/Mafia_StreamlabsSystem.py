#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
from enum import Enum
import math
import time
import random
sys.path.append(os.path.join(os.path.dirname(__file__), "lib")) #point at lib folder for classes / references

#import clr
#clr.AddReference("IronPython.SQLite.dll")
#clr.AddReference("IronPython.Modules.dll")

#   Import your Settings class
from Settings_Module import MySettings

#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "mafia"
Website = "www.twitch.tv/solsticeshard"
Description = ""
Creator = "SolsticeShard"
Version = "1.0.0.0"

#---------------------------
#   Define Global Variables
#---------------------------
global SettingsFile
SettingsFile = ""
global ScriptSettings
ScriptSettings = MySettings()
global TestMessage
TestMessage = ""

global PlayerQueue
PlayerQueue = []

global GameIsRunning
GameIsRunning = False

global Players
Players = {}

global IsDay
IsDay = False

global Votes
Votes = {}

global Accused
Accused = ""

global ProtectTarget
ProtectTarget = ""

global CopInvestigated
CopInvestigated = False

global VotesMatch
VotesMatch = False

#Classes

class Role(Enum):
    VILLAGER = 1
    DOCTOR = 2
    COP = 3
    MAFIA = 10

class Team(Enum):
    VILLAGE = 1
    MAFIA = 2

class Player():
    username = ""
    alive = True
    role = Role.VILLAGER
    team = Team.VILLAGE

    def __init__(self, username, role, team):
        self.username = username
        self.role = role
        self.team = team

#---------------------------
#   [Required] Initialize Data (Only called on load)
#---------------------------
def Init():
    #   Create Settings Directory
    directory = os.path.join(os.path.dirname(__file__), "Settings")
    if not os.path.exists(directory):
        os.makedirs(directory)

    #   Load settings
    SettingsFile = os.path.join(os.path.dirname(__file__), "Settings\settings.json")
    ScriptSettings = MySettings(SettingsFile)
    ScriptSettings.Response = "Overwritten pong! ^_^"
    return

#---------------------------
#   [Required] Execute Data / Process messages
#---------------------------
def Execute(data):
    global PlayerQueue
    global GameIsRunning
    global Players
    global Accused
    global Votes
    global IsDay
    global CopInvestigated
    global ProtectTarget
    global VotesMatch

    if data.GetParam(0).lower() != "!mafia":
        return

    if GameIsRunning == False and PlayerQueue == []:
        PlayerQueue = [data.User.lower()]
        Parent.SendTwitchMessage(data.User + " has started a game of mafia! Type !mafia join to join and !mafia start to begin")
        return
    
    if GameIsRunning == False and data.GetParam(1).lower() == "join":
        if data.User.lower() not in PlayerQueue:
            PlayerQueue.append(data.User.lower())
            #Should maybe be a whisper?
            Parent.SendTwitchMessage(data.User + " has joined the game.")
        return
    
    if GameIsRunning == False and data.GetParam(1).lower() == "start":
        if len(PlayerQueue) < 3:
            Parent.SendTwitchMessage("You need at least 3 people to play mafia!")
            return
        else:
            StartGame()
            return
    
    if data.GetParam(1).lower() == "alive":
        alivePeople = ""
        for player in Players:
            if Players[player].alive:
                alivePeople += player + " "
        Parent.SendTwitchWhisper(data.User, "These are the people still alive: " + alivePeople)
        return

    if GameIsRunning == True and (data.User.lower() not in Players or Players[data.User.lower()].alive == False):
        Parent.SendTwitchWhisper(data.User, "Sorry, the game is currently running and you are either dead or did not join")
        return

    if IsDay:
        if data.IsWhisper():
            Parent.SendTwitchWhisper(data.User, "All commands must be public during the day!")
            return
        
        if data.GetParam(1).lower() == "accuse" and Accused != "":
            Parent.SendTwitchWhisper(data.User, "Sorry, but " + Accused + " is already being accused. Please resolve the vote first.")
            return
        
        if data.GetParam(1).lower() == "vote" and Accused == "":
            Parent.SendTwitchWhisper(data.User, "Sorry, but you can only vote if someone has been accused")
            return
        
        if data.GetParam(1).lower() == "accuse":
            if data.GetParamCount() < 3:
                Parent.SendTwitchWhisper(data.User, "Please provide a person to accuse")
                return
    
            accuseTarget = data.GetParam(2).lower()
            
            if accuseTarget not in Players or Players[accuseTarget].alive == False:
                Parent.SendTwitchWhisper(data.User, "Sorry, " + accuseTarget + " is already dead or not a valid player in this game.")
                return
            
            #TODO: prevent one person from spam accusing
            Accused = accuseTarget
            Votes = {}
            Votes[data.User.lower()] = True
            Votes[accuseTarget] = False

            Parent.SendTwitchMessage(data.User + " has accused " + accuseTarget + "! Use !mafia vote (yes|no) to vote. All players must vote before a decision is made.")
            return

        if data.GetParam(1).lower() == "vote":
            #TODO: consider abstention
            if data.GetParamCount() < 3 or data.GetParam(2) not in ["yes", "no"]:
                Parent.SendTwitchWhisper(data.User, "You must vote yes or no")
                return
            if data.GetParam(2) == "yes":
                Votes[data.User.lower()] = True
            else:
                Votes[data.User.lower()] = False
            
            yesVotes = 0
            noVotes = 0
            everyoneVoted = True

            for player in Players:
                if Players[player].alive:
                    if player not in Votes:
                        everyoneVoted = False
                        break
                    if Votes[player] == True:
                        yesVotes += 1
                    elif Votes[player] == False:
                        noVotes += 1
            
            if everyoneVoted:
                if yesVotes > noVotes:
                    Parent.SendTwitchMessage("There was a majority vote to execute " + Accused + "!")
            
                    #if PlayerRoles[Accused] == Role.MAFIA:
                    #    Parent.SendTwitchMesssage(Accused + " was a mafia member!")
                    #else:
                    #    Parent.SendTwitchMessage(Accused + " was an innocent villager :(.")
                    Players[Accused].alive = False
                    Accused = ""
                    if not CheckForEndOfGame():
                        StartNightPhase()
                else:
                    #TODO prevent the same person from being accused multiple times?
                    Parent.SendTwitchMessage("There was not a majority vote to execute " + Accused + ", so they go free. Use !mafia accuse (player) to accuse someone else.")
                    Accused = ""
                    return

    else: #if night time
        if not data.IsWhisper():
            Parent.SendTwitchWhisper(data.User, "During the night phase, all commands must be in a direct whisper to me.")
            return
        
        if data.GetParam(1).lower() == "vote":
            if Players[data.User.lower()].team != Team.MAFIA:
                Parent.SendTwitchWhisper(data.User, "Only mafia can vote at night")
                return
            
            voteTarget = data.GetParam(2).lower()
            if voteTarget not in Players or Players[voteTarget].alive == False:
                Parent.SendTwitchMessage(data.User, "Sorry, " + voteTarget + " is already dead or not a valid player in this game.")
                return
            
            Votes[data.User.lower()] = voteTarget

            VotesMatch = True
            Parent.SendTwitchWhisper(data.User, "Thanks for your vote! All mafia must unanimously vote for their target.")
            for player in Players:
                if Players[player].team == Team.MAFIA and Players[player].alive == True and (player not in Votes or Votes[player] != voteTarget):
                    VotesMatch = False
        
        if data.GetParam(1).lower() == "protect":
            if Players[data.User.lower()].role != Role.DOCTOR:
                Parent.SendTwitchWhisper(data.User, "Only the doctor can protect people!")
                return
            if ProtectTarget != "":
                Parent.SendTwitchWhisper(data.User, "You have already decided to protect " + ProtectTarget + " this round.")
                return
            target = data.GetParam(2)
            if target not in Players or Players[target].alive == False:
                Parent.SendTwitchWhisper(data.User, target + " is not a valid, living player.")
                return
            ProtectTarget = target
            Parent.SendTwitchWhisper(data.User, "You are protecting " + target + " tonight.")

        if data.GetParam(1).lower() == "investigate":

            target = data.GetParam(2).lower()

            if Players[data.User.lower()].role != Role.COP:
                Parent.SendTwitchWhisper(data.User, "Only the cop can investigate people!")
                return
            if CopInvestigated:
                Parent.SendTwitchWhisper(data.User, "You have already investigated someone this round!")
                return
            if target not in Players or Players[target].alive == False:
                Parent.SendTwitchWhisper(data.User, target + " is not a valid, living player.")
                return
            
            Parent.SendTwitchWhisper(data.User, target + " belongs to the " + str(Players[target].team))
            CopInvestigated = True

        doctor_alive = False
        cop_alive = False

        for player in Players:
            if Players[player].role == Role.DOCTOR and Players[player].alive:
                doctor_alive = True
            elif Players[player].role == Role.COP and Players[player].alive:
                cop_alive = True

        
        if VotesMatch and (not doctor_alive or ProtectTarget != "") and (not cop_alive or CopInvestigated == True):
            if not CheckForEndOfGame():
                for vote in Votes:
                    victim = Votes[vote]
                    break
                StartDayPhase(victim, ProtectTarget)
            return
        else:
            #TODO: let the mafia collectively know when they disagree on their votes
            
            return

    return

#---------------------------
#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
#---------------------------
def Tick():
    #todo: consider timing out public votes

    return



def StartGame():
    global GameIsRunning
    global PlayerQueue
    global Players
    global IsDay
    global CopAlive
    global DoctorAlive

    GameIsRunning = True

    number_of_mafia = math.floor(float(len(PlayerQueue)) / 3.0)
    number_of_villagers = len(PlayerQueue) - number_of_mafia
    random.shuffle(PlayerQueue)
    i = 0
    mafiaMembers = []

    Players = {}
    for player in PlayerQueue:
        if i == 0:
            Players[player] = Player(player, Role.DOCTOR, Team.VILLAGE)
            Parent.SendTwitchWhisper(player, "You are the doctor! During the night phase, you can protect another player from being murdered.")
        elif i == 1:
            Players[player] = Player(player, Role.COP, Team.VILLAGE)
            Parent.SendTwitchWhisper(player, "You are the cop! During the night phase, you can investigate another player's team.")
        elif i < number_of_villagers:
            Players[player] = Player(player, Role.VILLAGER, Team.VILLAGE)
            Parent.SendTwitchWhisper(player, "You are an ordinary villager! Try not to die!")
        else:
            Players[player] = Player(player, Role.MAFIA, Team.MAFIA)
            mafiaMembers.append(player)
        i += 1
    
    for mafia in mafiaMembers:
        Parent.SendTwitchWhisper(mafia, "You are a mafia member! The mafia members are " + str(mafiaMembers))
        time.sleep(3)

    Parent.SendTwitchMessage("The game has started! There are " + str(number_of_mafia) + " mafia and " + str(number_of_villagers) + " villagers.")
    PlayerQueue = []

    StartNightPhase()

    IsDay = False
    Votes = {}
    Parent.SendTwitchMessage("It is now the night phase. Mafia can vote for who to kill by whispering !mafia vote (player) to me. The votes must be unanimous!")

def StartDayPhase(victim, protect):
    global IsDay
    global Votes
    global Accused
    global Players

    IsDay = True
    Votes = {}
    Accused = ""

    if victim.lower() == protect.lower():
        Parent.SendTwitchMessage(protect + " was protected by the doctor!")
    else:
        Parent.SendTwitchMessage("The town awakens to find " + victim + " killed!")
        Players[victim].alive = False
    Parent.SendTwitchMessage("It is now the day phase. You can accuse a player with !mafia accuse (player).")

def StartNightPhase():
    global CopInvestigated
    global ProtectTarget
    global VotesMatch
    global Players
    global IsDay

    IsDay = False
    CopInvestigated = False
    ProtectTarget = ""
    VotesMatch = False

    for player in Players:
        if Players[player].role == Role.DOCTOR and Players[player].alive:
            Parent.SendTwitchWhisper(player, 'During the night phase, whisper "!mafia protect (player)" to protect someone from a mafia kill. You must do this at least once tonight!')
        if Players[player].role == Role.COP and Players[player].alive:
            Parent.SendTwitchWhisper(player, 'During the night phase, whisper "!mafia investigate (player)" to reveal a player''s identity. You must do this once tonight!')

def CheckForEndOfGame():
    global IsGameRunning
    global Players

    mafiaAlive = 0
    villagerAlive = 0
    mafiaMembers = ""

    for player in Players:
        if Players[player].team == Team.MAFIA:
            mafiaMembers += player + " "
        if Players[player].alive and Players[player].team == Team.MAFIA:
            mafiaAlive += 1

        elif Players[player].alive and Players[player].team == Team.VILLAGE:
            villagerAlive += 1
    
    if mafiaAlive == 0:
        Parent.SendTwitchMessage("All of the mafia are dead, the villagers win! The mafia members were " + mafiaMembers)
        GameIsRunning = False
        return True
        #TODO give awards
    if mafiaAlive > villagerAlive:
        Parent.SendTwitchMessage("The mafia have a majority and slowly kill everyone else off. The mafia members were " + mafiaMembers)
        GameIsRunning = False
        return True

    if mafiaAlive == 1 and villagerAlive == 1:
        Parent.SendTwitchMessage("There is a tie!")
        IsGameRunning = False
        return True
    
    return False
    
        



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
