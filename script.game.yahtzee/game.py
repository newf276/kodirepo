#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2021 Mark König (mark.koenig@kleiner-schelm.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os
import random
from random import randint
import time
import threading
import string
import sys

import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui

addon = xbmcaddon.Addon()

ADDON_NAME = addon.getAddonInfo('name')
ADDON_PATH = addon.getAddonInfo('path')
MEDIA_PATH = os.path.join(
    xbmcvfs.translatePath(ADDON_PATH),
    'resources',
    'skins',
    'default',
    'media'
)
LIB_PATH = os.path.join(
    xbmcvfs.translatePath(ADDON_PATH),
    'resources',
    'lib'
)

SPEED = addon.getSetting('speed')
NOTIFY = addon.getSetting('notify') == "true"

libs  = xbmcvfs.translatePath(os.path.join(ADDON_PATH, 'resources', 'lib'))
sys.path.append(libs)

import yahtzee_points
import yahtzee_logic

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92

class Game(xbmcgui.WindowXML):

    pointsP1 = []
    pointsP2 = []
    pointsP3 = []
    pointsP4 = []

    hold = []
    dice = []

    soundOn = True

    game_round = 0
    actualTry = 0
    actualPlayer = 0

    player = 1
    computer = 1
    gameOn = False

    diceOn = False
    diceCnt = 0
    diceFinished = 0

    delayComputer = 0
    stop_thread = False

    #set values for game play speed
    time = 300
    delay = 5

    if (SPEED == '1'):
        time = 500
        delay = 10
    if (SPEED == '2'):
        time = 800
        delay = 15

# ----------------------------------------------------------------------------------------------------

    def onInit(self):

        self.p0x = self.getControl(6200)
        self.p0x.setLabel(self.GetPlayerName(1, False))
        self.p0x = self.getControl(6201)
        self.p0x.setLabel(self.GetPlayerName(2, False))
        self.p0x = self.getControl(6202)
        self.p0x.setLabel(self.GetPlayerName(3, False))
        self.p0x = self.getControl(6203)
        self.p0x.setLabel(self.GetPlayerName(4, False))

        # init vars
        result = yahtzee_logic.ReadRestgewinn()

        # init points
        for i in range(15):
            self.pointsP1.append(-1)
            self.pointsP2.append(-1)
            self.pointsP3.append(-1)
            self.pointsP4.append(-1)

        for i in range(5):
            self.hold.append(False)
            self.dice.append(6)

        # set points
        self.updatePoints()

        # get controls

        # init the grid

        # start the timer thread
        self.stop_thread = False
        threading.Thread(target=self.timer_thread).start()
        # start the game

        self.updateToggleButtons(0)

        # focus the dice button
        self.setFocusId(5008)

        if not result:
            self.close()

    def onAction(self, action):
        action_id = action.getId()
        focus_id = self.getFocusId()

        if action_id == ACTION_PREVIOUS_MENU:
            self.closeApp()
        if action_id == ACTION_NAV_BACK:
            self.closeApp()

    def closeApp(self):
        # do you really ...
        dialog = xbmcgui.Dialog()
        confirmed = dialog.yesno(addon.getLocalizedString(31025),
                                 addon.getLocalizedString(31045) + '\n' +
                                 addon.getLocalizedString(31046)
                                )
        if confirmed:
            self.stop_thread = True
            self.close()

    def onFocus(self, control_id):
        self.updateToggleButtons(control_id)

    def onClick(self, control_id):

        # set points from player
        if(self.actualPlayer <= self.player):
            if(control_id >= 5299) and (control_id < 5320):
                btn = control_id - 5300 + 1

                if(self.gameOn and not self.diceOn and (self.actualTry > 0)):
                    points = self.GetValuePlayer(self.actualPlayer)
                    if(points[btn-1] == -1):

                        value = yahtzee_points.GetCalc(btn, self.dice)

                        if(value == 0):
                            dialog = xbmcgui.Dialog()
                            confirmed = dialog.yesno(addon.getLocalizedString(31042),
                                                     addon.getLocalizedString(31043) + '\n' +
                                                     addon.getLocalizedString(31044) + '\n' +
                                                     addon.getLocalizedString(31012 + btn)
                                                     )

                            if confirmed:
                                self.SetValuePlayer(self.actualPlayer, btn-1, 0)
                                self.updatePoints()
                                self.NextPlayer()
                        else:
                            self.SetValuePlayer(self.actualPlayer, btn-1, value)
                            self.updatePoints()
                            self.NextPlayer()

        # new game
        if(control_id == 5002):
            if(self.gameOn):

                 # do you really ?
                 dialog = xbmcgui.Dialog()
                 confirmed = dialog.yesno(addon.getLocalizedString(31034),
                                          addon.getLocalizedString(31035) + '\n' +
                                          addon.getLocalizedString(31036)
                                          )
                 if confirmed:
                     self.NewGame()
            else:
                self.NewGame()

        # set how many player
        if(control_id == 5003):
            if(not self.gameOn):
                if(self.player < 4):
                    self.player = self.player + 1
                else:
                    self.player = 1
                    #self.player = 0  # for test computer vs computer
                if(self.player + self.computer) > 4:
                   self.computer = 4 - self.player
                self.updateToggleButtons(0)

        # set how many computer
        if(control_id == 5004):
            if(not self.gameOn):
                if self.computer < (4 - self.player):
                    # not implemeneted yet
                    self.computer = self.computer + 1
                    pass
                else:
                    self.computer = 0
                self.updateToggleButtons(0)

        # sound on/off
        if(control_id == 5005):
            self.soundOn = not self.soundOn
            self.updateToggleButtons(control_id)

        # dice player
        if(control_id == 5008):
            if(not self.gameOn):
                if((self.player + self.computer) > 0):
                    # if not in game then start the game
                    self.NewGame()

                    self.gameOn = True
                    self.actualPlayer = 1
                    self.actualTry = 1

                    if(self.soundOn):
                        xbmc.playSFX(MEDIA_PATH + '\\dice.wav')

                    self.diceOn = True
                    self.diceFinished = False

                    self.updateToggleButtons(control_id)

                    #if(NOTIFY):
                    #    xbmcgui.Dialog().notification(ADDON_NAME,
                    #                                  self.GetPlayerName(self.actualPlayer, False) + '\n1. ' + addon.getLocalizedString(3007),
                    #                                  time= self.time)
            else:
                if not self.diceOn:
                    if(self.actualPlayer <= self.player):
                        # do we have still one open
                        if(self.actualTry < 3):
                            self.actualTry = self.actualTry + 1
                            self.diceOn = True
                            self.diceFinished = False

                            if(self.soundOn):
                                xbmc.playSFX(MEDIA_PATH + '\\dice.wav')
                            self.updateToggleButtons(control_id);

                            #if(NOTIFY):
                            #    xbmcgui.Dialog().notification(ADDON_NAME,
                            #                              self.GetPlayerName(self.actualPlayer, False) + '\n' +str(self.actualTry) + '. ' + addon.getLocalizedString(3007),
                            #                              time= self.time)
                        else:
                            # last try reached, now set a field
                            dialog = xbmcgui.Dialog()
                            confirmed = dialog.ok(addon.getLocalizedString(31025),
                                                  addon.getLocalizedString(31029)
                                             )

        # give me a tip
        if(control_id == 5009):
            if(self.actualPlayer <= self.player):
                if(self.gameOn and not self.diceOn and (self.actualTry > 0)):

                    testTry = self.actualTry
                    value = self.GetYahzeeMove(testTry)

                    # we can already sign a value
                    if(value > 9999):
                        testTry = 3
                        value = self.GetYahzeeMove(testTry)

                    txt = '...'

                    if(testTry == 1):
                        if(value != 0):
                            txt = addon.getLocalizedString(31012) + ' : ' + str(value)
                        else:
                            txt = addon.getLocalizedString(31009)

                    if(testTry == 2):
                        if(value != 0):
                            txt = addon.getLocalizedString(31012) + ' : ' + str(value)
                        else:
                            txt = addon.getLocalizedString(31009)

                    if(testTry == 3):

                        x = value
                        if(x > 5):
                            x = x + 1

                        points = yahtzee_points.GetCalc(x + 1 , self.dice)
                        if(points > 0):
                            txt = addon.getLocalizedString(31040) + ' : ' + addon.getLocalizedString(31013 + x)
                        else:
                            txt = addon.getLocalizedString(31042) + ' : ' + addon.getLocalizedString(31013 + x)

                    dialog = xbmcgui.Dialog()
                    confirmed = dialog.ok(addon.getLocalizedString(31010),
                                          txt)

        # what's this?
        if(control_id == 5010):
            dialog = xbmcgui.Dialog()
            confirmed = dialog.ok(addon.getLocalizedString(31025),
                                  addon.getLocalizedString(31050)
                                  )

        # toggle hold button for the player
        if(self.actualPlayer <= self.player):
            if(self.actualTry > 0) and self.gameOn and not self.diceOn and self.diceFinished:
                if(control_id == 5200):
                    self.hold[0] = not self.hold[0]
                    self.updateToggleButtons(control_id)
                if(control_id == 5201):
                    self.hold[1] = not self.hold[1]
                    self.updateToggleButtons(control_id)
                if(control_id == 5202):
                    self.hold[2] = not self.hold[2]
                    self.updateToggleButtons(control_id)
                if(control_id == 5203):
                    self.hold[3] = not self.hold[3]
                    self.updateToggleButtons(control_id)
                if(control_id == 5204):
                    self.hold[4] = not self.hold[4]
                    self.updateToggleButtons(control_id)

    def timer_thread(self):
        while not xbmc.Monitor().abortRequested() and not self.stop_thread:
            if(self.diceOn):
                self.delayComputer = 0
                self.diceCnt = self.diceCnt +1
                if(self.diceCnt < 10):
                    for w in range(5):
                        if (self.hold[w] == False):
                            try:
                                x = randint(1, 6)
                                self.dice[w] = x

                                self.wx = self.getControl(5100 + w)
                                self.wx.setImage('w%s.png' % x)
                            except:
                                pass
                else:
                    self.diceOn = False
                    self.diceFinished = True
            else:
                self.diceCnt = 0

            self.delayComputer = self.delayComputer + 1
            if(self.delayComputer > self.delay):
                self.delayComputer = 0

                if(self.gameOn):
                    # computer dice
                    if(self.actualPlayer > self.player):
                        if(not self.diceOn):
                            if(self.actualTry == 0):

                                self.actualTry = self.actualTry + 1
                                self.updateTry()

                                # computer first dice
                                #if(NOTIFY):
                                #    xbmcgui.Dialog().notification(ADDON_NAME,
                                #                                  self.GetPlayerName(self.actualPlayer, True) + '\n1. ' + addon.getLocalizedString(3007),
                                #                                  time= self.time)

                                self.diceOn = True
                                self.diceFinished = False
                                self.diceCnt = 0

                                if(self.soundOn):
                                    xbmc.playSFX(MEDIA_PATH + '\\dice.wav')

                            elif((self.actualTry > 0) and (self.actualTry < 3)):

                                testTry = self.actualTry
                                value = self.GetYahzeeMove(testTry)

                                if(value < 9999):

                                    # reset hold
                                    self.hold[0] = False;
                                    self.hold[1] = False;
                                    self.hold[2] = False;
                                    self.hold[3] = False;
                                    self.hold[4] = False;

                                    # decode value
                                    a = int(value / 10000)
                                    value = value - (a * 10000)
                                    b = int(value / 1000)
                                    value = value - (b * 1000)
                                    c = int(value / 100)
                                    value = value - (c * 100)
                                    d = int(value  / 10)
                                    value = value - (d * 10)
                                    e = int(value)

                                    #check first digit
                                    if(a > 0):
                                        for x in range(0,5):
                                            if(self.hold[x] == False):
                                                if(self.dice[x] == a):
                                                    self.hold[x] = True
                                                    break
                                    #check second digit
                                    if(b > 0):
                                        for x in range(0,5):
                                            if(self.hold[x] == False):
                                                if(self.dice[x] == b):
                                                    self.hold[x] = True
                                                    break
                                    #check third digit
                                    if(c > 0):
                                        for x in range(0,5):
                                            if(self.hold[x] == False):
                                                if(self.dice[x] == c):
                                                    self.hold[x] = True
                                                    break
                                    #check fourth digit
                                    if(d > 0):
                                        for x in range(0,5):
                                            if(self.hold[x] == False):
                                                if(self.dice[x] == d):
                                                    self.hold[x] = True
                                                    break
                                    #check fivth digit
                                    if(e > 0):
                                        for x in range(0,5):
                                            if(self.hold[x] == False):
                                                if(self.dice[x] == e):
                                                    self.hold[x] = True
                                                    break

                                    self.updateToggleButtons(5200)
                                    self.updateToggleButtons(5201)
                                    self.updateToggleButtons(5202)
                                    self.updateToggleButtons(5203)
                                    self.updateToggleButtons(5204)

                                    # focus the dice button
                                    self.setFocusId(5008)

                                    self.actualTry = self.actualTry + 1
                                    self.updateTry()

                                    # player x (actual) dice
                                    #if(NOTIFY):
                                    #    xbmcgui.Dialog().notification(ADDON_NAME,
                                    #                                  self.GetPlayerName(self.actualPlayer, True) + '\n' +  str(self.actualTry)  + '. ' + addon.getLocalizedString(3007),
                                    #                                  time= self.time)

                                    self.diceOn = True
                                    self.diceFinished = False
                                    self.diceCnt = 0

                                    if(self.soundOn):
                                        xbmc.playSFX(MEDIA_PATH + '\\dice.wav')

                                else:
                                    # we can already set a position on the table

                                    sel = self.GetYahzeeMove(3)
                                    btn = sel + 1

                                    # because we have one field space (6)
                                    if(btn > 6):
                                        btn = btn + 1

                                    # player x set field y
                                    if(NOTIFY):
                                        xbmcgui.Dialog().notification(ADDON_NAME,
                                                                      self.GetPlayerName(self.actualPlayer, True) + '\n' + addon.getLocalizedString(31012 + btn),
                                                                      time= self.time)

                                    # get value
                                    value = yahtzee_points.GetCalc(btn, self.dice)

                                    self.SetValuePlayer(self.actualPlayer, btn-1, value)
                                    self.updatePoints()

                                    # we will wait 3s here, so we can display next player
                                    period = 3.0
                                    time_before = time.time()

                                    while (time.time() - time_before) < period:
                                        time.sleep(0.001)  # precision here

                                    self.NextPlayer()

                            elif (self.actualTry == 3):
                                # last try now set a position on the table

                                sel = self.GetYahzeeMove(self.actualTry)
                                btn = sel + 1

                                # because we have one field space (6)
                                if(btn > 6):
                                    btn = btn + 1

                                # get value
                                value = yahtzee_points.GetCalc(btn, self.dice)

                                # notify what
                                if(NOTIFY):
                                    if(value > 0):
                                        # we have a value
                                        xbmcgui.Dialog().notification(ADDON_NAME,
                                                                  self.GetPlayerName(self.actualPlayer, True) + '\n' + addon.getLocalizedString(31012 + btn),
                                                                  time= self.time)
                                    else:
                                        # we discard a field
                                        xbmcgui.Dialog().notification(ADDON_NAME,
                                                                  self.GetPlayerName(self.actualPlayer, True) + '\n' +
                                                                  addon.getLocalizedString(31042) + ': ' + addon.getLocalizedString(31012 + btn),
                                                                  time= self.time)

                                # player x set field y
                                self.SetValuePlayer(self.actualPlayer, btn-1, value)
                                self.updatePoints()

                                # we will wait 3s here, so we can display next player
                                period = 3.0
                                time_before = time.time()

                                while (time.time() - time_before) < period:
                                    time.sleep(0.001)  # precision here

                                self.NextPlayer()

            xbmc.sleep(200)

    def GetPlayerName(self, playerNo, comp):

        if(comp):
            if(playerNo == 1):
                return addon.getSetting('ply1') + ' (comp)'
            elif(playerNo == 2):
                return addon.getSetting('ply2') + ' (comp)'
            elif(playerNo == 3):
                return addon.getSetting('ply3') + ' (comp)'
            elif(playerNo == 4):
                return addon.getSetting('ply4') + ' (comp)'
        else:
            if(playerNo == 1):
                return addon.getSetting('ply1')
            elif(playerNo == 2):
                return addon.getSetting('ply2')
            elif(playerNo == 3):
                return addon.getSetting('ply3')
            elif(playerNo == 4):
                return addon.getSetting('ply4')

        return ""

    def GetValuePlayer(self, playerNo):
        if(playerNo == 1):
            return self.pointsP1
        if(playerNo == 2):
            return self.pointsP2
        if(playerNo == 3):
            return self.pointsP3
        if(playerNo == 4):
            return self.pointsP4

    def SetValuePlayer(self, playerNo, field, value):

        points = self.GetValuePlayer(playerNo)
        points[field] = value

        top = 0
        for i in range(6):
            if(points[i] > 0):
                top = top + points[i]

        # bonus rule top area
        if(top > 62):
            top = top + 35

        # bonus rule additional Yahtzee
        if(points[12] == 50):                   # do we have already a Yahtzee ?
            for i in range(6):                  # check 1 to 6
                if(points[i] == ((i+1) * 5)):   # do we have an additional Yahtzee's
                    top = top + 50              # add x Yahtzee / 50 points

        bottom = 0
        for i in range(7,14):
            if(points[i] > 0):
                bottom = bottom + points[i]

        points[6] = top
        points[14] = top + bottom

    def NewGame(self):

          self.game_round = 1
          # we dont't start yet, so we can change player / computer
          self.gameOn = False
          self.diceOn = False
          self.diceFinished = False

          self.actualPlayer = 1
          self.actualTry = 0

          for i in range(15):
              self.pointsP1[i] = -1
              self.pointsP2[i] = -1
              self.pointsP3[i] = -1
              self.pointsP4[i] = -1

          # reset hold
          for i in range(5):
              self.hold[i] = False

          self.updateToggleButtons(0)
          self.updatePoints()

          # focus the dice button
          self.setFocusId(5008)

    def NextPlayer(self):
        self.actualTry = 0
        self.updateTry()

        self.actualPlayer = self.actualPlayer + 1

        #reset hold
        for i in range(5):
            self.hold[i] = False

        if (self.actualPlayer > (self.player + self.computer)):
            self.actualPlayer = 1
            self.game_round = self.game_round + 1
            if (self.game_round  == 14):

                self.gameOn = False # game over
                if(self.soundOn):
                    xbmc.playSFX(MEDIA_PATH + '\\applaus.wav')

                maxPoints = 0
                maxPlayer = 0
                mode = 'win'

                for n in range(1,5):
                    points = self.GetValuePlayer(n)
                    x = points[14]

                    if((x == maxPoints) and (x > 0)):
                        mode = 'draw'
                    if(x > maxPoints):
                        maxPoints = x
                        maxPlayer = n
                        mode = 'win'

                if(mode == 'win'):
                    dialog = xbmcgui.Dialog()
                    confirmed = dialog.ok(ADDON_NAME,
                                      addon.getLocalizedString(31051) + '\n' +
                                      self.GetPlayerName(maxPlayer,False) + ": " + str(maxPoints))
                else:
                    # draw
                    dialog = xbmcgui.Dialog()
                    confirmed = dialog.ok(ADDON_NAME,
                                      addon.getLocalizedString(31052) + '\n' +
                                      addon.getLocalizedString(31027) + ": " + str(maxPoints))


        self.updateToggleButtons(0);

        # focus the dice button
        self.setFocusId(5008)

        self.delayComputer = 0

        #if(self.actualPlayer <= self.player):
        if(self.gameOn):
            # first player x first dice
            if(NOTIFY):
                xbmcgui.Dialog().notification(ADDON_NAME,
                                              self.GetPlayerName(self.actualPlayer, False),
                                              time= self.time)

    def updateToggleButtons(self, control_id):

        # update player settings
        self.p0x = self.getControl(5003)
        self.p0x.setLabel(addon.getLocalizedString(31002) + str(self.player))

        self.p0x = self.getControl(5004)
        self.p0x.setLabel(addon.getLocalizedString(31003) + str(self.computer))

        # update actual player
        self.p0x = self.getControl(5006)
        if(self.gameOn):
            self.p0x.setLabel(addon.getLocalizedString(31006) + ' ' + str(self.actualPlayer))
        else:
            self.p0x.setLabel(addon.getLocalizedString(31005))

        # protect for startup
        self.p0x = self.getControl(5007)
        self.p0x.setLabel(addon.getLocalizedString(31007) + ' ' + str(self.actualTry) + ' ' +
                          addon.getLocalizedString(31008) + ' 3')

        if len(self.hold) < 4:
            return

        # set fcous / set for the hold button
        for i in range(5):
            self.p0x = self.getControl(5900 + i)

            if(self.hold[i] == False):
                self.p0x.setImage('t_button.png')
            else:
                self.p0x.setImage('t_button_sel.png')

            if(control_id == (5200 + i)):
                if(self.hold[i] == False):
                    self.p0x.setImage('t_button_active.png')
                else:
                    self.p0x.setImage('t_button_active_sel.png')

        # set fcous / set for the sound button
        self.p0x = self.getControl(6005)
        if(self.soundOn == False):
            self.p0x.setImage('t_button.png')
        else:
            self.p0x.setImage('t_button_sel.png')
        if(control_id == (5005)):
            if(self.soundOn == False):
                self.p0x.setImage('t_button_active.png')
            else:
                self.p0x.setImage('t_button_active_sel.png')

    def updatePoints(self):
        for i in range(15):
            self.p0x = self.getControl(5400 + i)
            if(self.pointsP1[i] >= 0):
                self.p0x.setLabel(str(self.pointsP1[i]))
            else:
                self.p0x.setLabel('..')

            self.p0x = self.getControl(5500 + i)
            if(self.pointsP2[i] >= 0):
                self.p0x.setLabel(str(self.pointsP2[i]))
            else:
                self.p0x.setLabel('..')

            self.p0x = self.getControl(5600 + i)
            if(self.pointsP3[i] >= 0):
                self.p0x.setLabel(str(self.pointsP3[i]))
            else:
                self.p0x.setLabel('..')

            self.p0x = self.getControl(5700 + i)
            if(self.pointsP4[i] >= 0):
                self.p0x.setLabel(str(self.pointsP4[i]))
            else:
                self.p0x.setLabel('..')

    def updateTry(self):
        self.p0x = self.getControl(5007)
        self.p0x.setLabel(addon.getLocalizedString(31007) + ' ' + str(self.actualTry) + ' ' +
                          addon.getLocalizedString(31008) + ' 3')

    def GetYahzeeMove(self, actTry):
        data = []
        for i in range(15):
            data.append(0)

        for i in range (6):
            data[i] = self.GetValuePlayer(self.actualPlayer)[i]
        for i in range (6,13):
            data[i] = self.GetValuePlayer(self.actualPlayer)[i + 1]

        data[13] = actTry
        data[14] = (self.dice[0] * 10000) + (self.dice[1] * 1000) + (self.dice[2] * 100) + (self.dice[3] * 10) + (self.dice[4] * 1)

        return yahtzee_logic.EinzelAbfrage(data)

    def log(self, msg):
        xbmc.log('[ADDON][%s] %s' % ('TEST', msg),
                 level=xbmc.LOGDEBUG)

# ----------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    game = Game(
        'script-%s-main.xml' % ADDON_NAME,
        ADDON_PATH,
        'default',
        '720p'
    )
    game.doModal()
    del game

sys.modules.clear()
