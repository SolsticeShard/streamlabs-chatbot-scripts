#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
import math
from datetime import datetime, timedelta
from enum import Enum
import random
sys.path.append(os.path.join(os.path.dirname(__file__), "lib")) #point at lib folder for classes / references


#   Import your Settings class
from BlackJack_Settings_Module import BlackJackSettings
#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "blackjack"
Website = "www.github.com/SolsticeShard"
Description = "A simple blackjack implementation. Can be a little bit spammy!"
Creator = "SolsticeShard"
Version = "1.0.0.0"

#Classes
class Suits(Enum):
    DIAMONDS = 1
    HEARTS = 2
    CLUBS = 3
    SPADES = 4

class Values(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 12
    QUEEN = 13
    KING = 14
    ACE = 11
    
class Card:
    value = Values.ACE
    suit = Suits.SPADES
    
    def __init__(self, value, suit):
        self.suit = suit
        self.value = value
        return

    def printCard(self):
        return self.value.name + ' of ' + self.suit.name

    def points(self):
        if self.value in [Values.JACK, Values.QUEEN, Values.KING]:
            return 10
        
        if self.value == Values.ACE:
            return 11
        
        return self.value.value

#---------------------------
#   Define Global Variables
#---------------------------
global SettingsFile
SettingsFile = ""
global ScriptSettings
ScriptSettings = BlackJackSettings()

global GameIsRunning
GameIsRunning = False

global ActingPlayer
ActingPlayer = ''

global Hands
Hands = {}

global DoubledDownCards
DoubledDownCards = {}

global Deck
Deck = []

global Bets
Bets = {}

global PlayersInQueue
PlayersInQueue = []

global TurnEndTime
TurnEndTime = datetime.now()
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
    ScriptSettings = BlackJackSettings(SettingsFile)
    ScriptSettings.Command = "!blackjack"
    return

#---------------------------
#   [Required] Execute Data / Process messages
#---------------------------
def Execute(data):
    global Deck
    global ActingPlayer
    global GameIsRunning
    global Hands
    global Bets
    global PlayersInQueue
    global DoubledDownCards
    global ScriptSettings
    global TurnEndTime

    if data.GetParam(0).lower() != ScriptSettings.Command:
        return

    #reminder commands
    if GameIsRunning == True and data.GetParamCount() == 2:
        if data.GetParam(1).lower() == "cards":
            msg = data.User + ", your cards are "
            for card in Hands[data.User]:
                msg += card.printCard() + "; "
            msg += "(" + str(EvaluateHand(data.User)) + " points)."
            if data.User in DoubledDownCards:
                msg += ". You also have a face down doubled down card."
            Parent.SendTwitchMessage(msg)
            return
        if data.GetParam(1).lower() == "dealer":
            Parent.SendTwitchMessage("The dealer's face-up card is " + Hands["DEALER"][0].printCard())
            return
        if data.GetParam(1).lower() == "turn":
            Parent.SendTwitchMessage("It is " + ActingPlayer + "'s turn.")
            return

    if GameIsRunning == True and Hands != {} and data.User.lower() not in map(str.lower, PlayersInQueue):
        SendMessage(data, data.User + ", a game is currently running. Feel free to join the next one!")
        return

    #someone playing out of turn        
    if GameIsRunning == True and Hands != {} and data.User.lower() != ActingPlayer.lower():
        SendMessage(data, data.User + ", it is not your turn! It's " + ActingPlayer + "'s turn.")
        return
    #start queue
    if GameIsRunning == False:
        if data.GetParamCount() < 2:
            Parent.SendTwitchMessage(data.User + ", you have to declare a bet when starting a hand of blackjack between " + str(ScriptSettings.MinimumBet) + " and " + str(ScriptSettings.MaximumBet))
            return
        try:
            bet = int(data.GetParam(1))
        except ValueError:
            Parent.SendTwitchMessage(data.User + ", your bet must be an integer value.")
            return
        if bet > ScriptSettings.MaximumBet or bet < ScriptSettings.MinimumBet:
            Parent.SendTwitchMessage(data.User + ", your bet must be between " + str(ScriptSettings.MinimumBet) + " and " + str(ScriptSettings.MaximumBet))
            return
        if Parent.GetPoints(data.User) < bet:
            Parent.SendTwitchMessage(data.User + ", you do not have " + str(bet) + " points to bet, sorry!")
            return
        GameIsRunning = True
        StartQueue(data.User, bet)
        if len(PlayersInQueue) >= ScriptSettings.MaximumPlayers:
            StartGame()
    #join queue
    if data.GetParam(1).lower() == 'join':
        if data.GetParamCount() < 3:
            Parent.SendTwitchMessage(data.User + ", you have to declare a bet when joining a hand of blackjack between " + str(ScriptSettings.MinimumBet) + " and " + str(ScriptSettings.MaximumBet))
            return
        try:
            bet = int(data.GetParam(2))
        except ValueError:
            Parent.SendTwitchMessage(data.User + ", your bet must be an integer value.")
            return
        if bet > ScriptSettings.MaximumBet or bet < ScriptSettings.MinimumBet:
            Parent.SendTwitchMessage(data.User + ", your bet must be between " + str(ScriptSettings.MinimumBet) + " and " + str(ScriptSettings.MaximumBet))
            return
        if Parent.GetPoints(data.User) < bet:
            Parent.SendTwitchMessage(data.User + ", you do not have " + str(bet) + " points to be, sorry!")
            return
        JoinQueue(data.User, bet)
        if len(PlayersInQueue) >= ScriptSettings.MaximumPlayers:
            StartGame()
        return
    #start game
    if data.GetParam(1).lower() == 'start':
        StartGame()
        return
    #player actions
    if data.GetParam(1).lower() == 'stand':
        TurnEndTime = datetime.now() + timedelta(seconds = ScriptSettings.TurnTimeout)
        Parent.SendTwitchMessage(data.User + " stands with " + str(EvaluateHand(data.User)) + " points.")
        index = PlayersInQueue.index(ActingPlayer)
        if index == len(PlayersInQueue) - 1:
            TakeDealerTurn()
        else:
            ActingPlayer = PlayersInQueue[index+1]
            Parent.SendTwitchMessage(ActingPlayer + ", it is now your turn.")
            TurnEndTime = datetime.now() + timedelta(seconds = ScriptSettings.TurnTimeout)
        return

    if data.GetParam(1).lower() == 'doubledown':
        TurnEndTime = datetime.now() + timedelta(seconds = ScriptSettings.TurnTimeout)
        if not CanDoubleDown(data.User):
            Parent.SendTwitchMessage("You can only double down if your original two cards total 9, 10, or 11.")
            return
        newCard = Deck.pop()
        DoubledDownCards[data.User] = newCard
        Bets[data.User] *= 2
        Parent.SendTwitchMessage("You have been dealt a facedown card and your bet is doubled.")
        index = PlayersInQueue.index(ActingPlayer)
        if index == len(PlayersInQueue) - 1:
            TakeDealerTurn()
        else:
            ActingPlayer = PlayersInQueue[index+1]
            Parent.SendTwitchMessage(ActingPlayer + ", it is now your turn.")
        return

    if data.GetParam(1).lower() == 'hit':
        TurnEndTime = datetime.now() + timedelta(seconds = ScriptSettings.TurnTimeout)
        if Hit(ActingPlayer):
            index = PlayersInQueue.index(ActingPlayer)
            Parent.SendTwitchMessage("You bust! Sorry, you lose " + str(Bets[data.User]) + " points :(.")
            Parent.RemovePoints(data.User, Bets[data.User])
            RemovePlayer(data.User)
            if index == len(PlayersInQueue):
                TakeDealerTurn()
            else:
                ActingPlayer = PlayersInQueue[index]
                Parent.SendTwitchMessage(ActingPlayer + ", it is now your turn.")
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
    global ActingPlayer
    global TurnEndTime
    global PlayersInQueue
    global Hands

    if ScriptSettings.TurnTimeout > 0 and GameIsRunning and len(Hands) > 0 and datetime.now() > TurnEndTime:
        index = PlayersInQueue.index(ActingPlayer)
        player_to_remove = ActingPlayer
        ActingPlayer = None
        Parent.SendTwitchMessage("Sorry " + player_to_remove + ", you took too long on your turn.")
        RemovePlayer(player_to_remove)
        if index == len(PlayersInQueue):
            TakeDealerTurn()
        else:
            ActingPlayer = PlayersInQueue[index]
            Parent.SendTwitchMesssage(ActingPlayer + ", it is now your turn.")

    return

def TakeDealerTurn():
    global Hands
    global Bets
    global DoubledDownCards
    global PlayersInQueue
    global GameIsRunning

    if len(PlayersInQueue) == 0:
        Parent.SendTwitchMessage("Everyone busted, lame! Game's over. The dealer's facedown card was " + Hands["DEALER"][1].printCard())
        GameIsRunning = False
        return

    for player in DoubledDownCards:
        Parent.SendTwitchMessage(player + " flips up their double down card. It's the " + DoubledDownCards[player].printCard())
        Hands[player].append(DoubledDownCards[player])
        if EvaluateHand(player) > 21:
            Parent.SendTwitchMessage("With their new card, they bust :(")
            RemovePlayer(player)

    Parent.SendTwitchMessage("It's the dealer's turn. He flips his face down card to reveal the " + Hands["DEALER"][1].printCard() + " (with the " + Hands["DEALER"][0].printCard() + ").")
    while EvaluateHand("DEALER") < 17:
        Parent.SendTwitchMessage("The dealer hits.")
        Hit("DEALER")
    dealerValue = EvaluateHand("DEALER")
    if dealerValue > 21:
        Parent.SendTwitchMessage("The dealer busts! Everyone still in wins their bet.")
        for player in Bets:
            Parent.SendTwitchMessage(player + " wins " + str(Bets[player]))
            Parent.AddPoints(player.lower(), Bets[player])
    else:
        Parent.SendTwitchMessage("The dealer stands with " + str(EvaluateHand("DEALER")) + " points.")
        for player in Hands:
            playerValue = EvaluateHand(player)
            if player == "DEALER":
                continue
            if playerValue > dealerValue:
                Parent.SendTwitchMessage(player + " beats the dealer and wins " + str(Bets[player]))
                Parent.AddPoints(player, Bets[player])
            elif playerValue == dealerValue:
                Parent.SendTwitchMessage(player + " ties the dealer.")
            elif playerValue < dealerValue:
                Parent.SendTwitchMessage(player + " loses to the dealer and loses " + str(Bets[player]))
                Parent.RemovePoints(player, Bets[player])

    Parent.SendTwitchMessage("Thanks for playing everyone!")
    GameIsRunning = False
    return

def Hit(player):
    global Deck
    global Hands
    global Bets
    
    newCard = Deck.pop()
    Hands[player].append(newCard)
    Parent.SendTwitchMessage("You are dealt " + newCard.printCard())
    
    newValue = EvaluateHand(player)

    if newValue > 21 and player != "DEALER":
        return True

    return False

def CanDoubleDown(player):
    global Hands

    if EvaluateHand(player) in [9, 10, 11] or ((EvaluateHand(player) - 10) in [9, 10, 11] and (Hands[player][0].value == Values.ACE or Hands[player][1].value == Values.ACE)):
        return True
    return False

def EvaluateHand(player):
    global Hands

    indicesOfAcesCountedAsOne = []

    while True:
        total = 0
        for card in Hands[player]:
            if card.value == Values.ACE and Hands[player].index(card) in indicesOfAcesCountedAsOne:
                total += 1
            else:
                total += card.points()

        if total > 21:
            foundNewAce = False
            for card in Hands[player]:
                if card.value == Values.ACE and Hands[player].index(card) not in indicesOfAcesCountedAsOne:
                    indicesOfAcesCountedAsOne.append(Hands[player].index(card))
                    foundNewAce = True
                    break
            if foundNewAce:
                continue
            return 22
        else:
            return total
        


def StartQueue(startingUser, bet):
    global PlayersInQueue
    global Bets
    global Hands
    global ScriptSettings

    Hands = {}
    PlayersInQueue = [startingUser]
    Bets = {startingUser: bet}
    Parent.SendTwitchMessage(startingUser + ' has started a hand of blackjack! Type "!blackjack join (bet)" to join or "!blackjack start" to start. Up to ' + str(ScriptSettings.MaximumPlayers) + ' may play.')
    return

def JoinQueue(user, bet):
    global PlayersInQueue
    global Bets

    if user.lower() not in map(str.lower, PlayersInQueue):
        PlayersInQueue.append(user)
        Bets[user] = bet
        Parent.SendTwitchMessage(user + ' has joined!')
        return
    
    Parent.SendTwitchMessage(user + ', you are already signed up. Use "!blackjack start" to start.')
    return

def StartGame():
    global PlayersInQueue
    global Deck
    global Hands
    global DoubledDownCards
    global ActingPlayer
    global GameIsRunning
    global TurnEndTime
    global ScriptSettings

    Hands = {}
    DoubledDownCards = {}
    Parent.SendTwitchMessage("The game begins! Time to deal out cards.")
    for suit in Suits:
        for val in Values:
            Deck.append(Card(val, suit))
    random.shuffle(Deck)
    for player in PlayersInQueue:
        card1 = Deck.pop()
        card2 = Deck.pop()
        Hands[player] = [card1, card2]
    #dealer
    card1 = Deck.pop()
    card2 = Deck.pop()
    Hands["DEALER"] = [card1, card2]
    Parent.SendTwitchMessage("Here are the hands:")
    for player in PlayersInQueue:
        Parent.SendTwitchMessage(player + ": " + Hands[player][0].printCard() + ", " + Hands[player][1].printCard())
    Parent.SendTwitchMessage("Dealer: " + Hands["DEALER"][0].printCard() + ", face-down card.")
    CheckNaturals()
    if len(PlayersInQueue) == 0:
        GameIsRunning = False
        Parent.SendTwitchMessage("Game over!")
        return
    Parent.SendTwitchMessage('Use "!blackjack cards" to read your cards, "!blackjack dealer" for the dealer''s cards, or "!blackjack turn" for whose turn it is.')
    ActingPlayer = PlayersInQueue[0]
    Parent.SendTwitchMessage(ActingPlayer + ', it''s your turn. Your options: "!blackjack hit", "!blackjack stand", "!blackjack doubledown". (split and insurance will be implemented later)')
    TurnEndTime = datetime.now() + timedelta(seconds = ScriptSettings.TurnTimeout)
    return

def CheckNaturals():
    global GameIsRunning
    global Bets
    global PlayersInQueue
    dealerHasBlackJack = HasNaturalBlackJack("DEALER")

    playersToRemove = []
    if dealerHasBlackJack:
        Parent.SendTwitchMessage("The dealer has blackjack, sorry!")
        for player in PlayersInQueue:
            if HasNaturalBlackJack(player):
                Parent.SendTwitchMessage(player + " also has blackjack, tie!")
            else:
                Parent.SendTwitchMessage(player + " lost their bet of " + str(Bets[player]))
                Parent.RemovePoints(player.lower(), long(Bets[player]))
            playersToRemove.append(player)
    else:
        for player in PlayersInQueue:
            if HasNaturalBlackJack(player):
                reward = math.ceil(float(Bets[player]) * 1.5)
                Parent.SendTwitchMessage(player + " has a blackjack! They win " + str(reward) + " points.")
                Parent.AddPoints(player.lower(), reward)
                playersToRemove.append(player)
    for player in playersToRemove:
        RemovePlayer(player)

    return


def RemovePlayer(player):
    global PlayersInQueue
    global Hands
    global Bets

    PlayersInQueue.remove(player)
    del Hands[player]
    del Bets[player]
    return


def HasNaturalBlackJack(player):
    global Hands

    tens = [Values.KING, Values.QUEEN, Values.JACK, Values.TEN]

    if (Hands[player][0].value == Values.ACE and Hands[player][1].value in tens) or (Hands[player][0].value in tens and Hands[player][1].value == Values.ACE):
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
    global ScriptSettings
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
