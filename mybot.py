#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
# File:   pyfred.py              
#
# This file is a part of Shoddy Battle.
# Copyright (C) 2011  Catherine Fitzpatrick and Benjamin Gwin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, visit the Free Software Foundation, Inc.
# online at http://gnu.org.
#
##############################################################################

import random
import time
import os.path

from bot import *
import parsers
from pokemon import Pokemon

import clips

clips.Clear()
clips.Reset()
#SHOULD ESYS BE GLOBAL?
esys = clips.Environment()
esys.Clear()

#HOST = 'smogon.com'
HOST = 'lab.pokemonexperte.de'
PORT = 8446
USERNAME = 'Acurion'
PASSWORD = 'ValyxeBotShipU2012'
TEAM_DIR = "Teams/"
TEAMS = ["Team3.sbt"]
# An awesome, super human robot capable of beating any challenger
class PyFred(MessageHandler):
    
    def __init__(self):
        self.battles = dict()
        self.challenges = dict()
        random.seed()
    
    def handle_welcome_message(self, version, name, message):
        #print name
        #print message
        pass
    
    def handle_metagame_list(self, metagames):
        self.metagames = metagames
        
    def handle_registry_response(self, type, details):
        if type == 7:
            print "Successfully authenticated"
            self.join_channel("main")
        else:
            print "Authentication failed, code ", type
            if details: print details
            
    def handle_incoming_challenge(self, user, generation, n, team_length):
        #too lazy to handle n > 1 or non 6 challenges
        if n > 1 or team_length != 6:
            self.reject_challenge(user)
        else:
            file = TEAM_DIR + TEAMS[random.randint(0, len(TEAMS) - 1)]
            file = os.path.normpath(file)
            team = parsers.parse_team_file(file)
            self.challenges[user] = file
            self.accept_challenge(user, team)
    
    def handle_battle_begin(self, fid, user, party):
        print "Started battle against ", user
        b = Battle(fid, self, party, user, self.challenges[user])
        self.battles[fid] = b
        del self.challenges[user]
    
    def handle_battle_use_move(self, fid, party, slot, name, id):
        self.battles[fid].handle_use_move(party, id)
        
    def handle_battle_send_out(self, fid, party, slot, index, name, id, gender, level):
        self.battles[fid].handle_send_out(party, index, id, gender, level)
        
    def handle_battle_health_change(self, fid, party, slot, delta, total, denominator):
        self.battles[fid].handle_health_change(party, delta, total, denominator)
        
    def handle_battle_fainted(self, fid, party, slot, name):
        self.battles[fid].handle_fainted(party)
        
    def handle_battle_print(self, fid, cat, id, args):
        self.battles[fid].print_message(cat, id, args)
        
    def handle_request_action(self, fid, slot, pos, replace, switches, can_switch, forced, moves):
        self.battles[fid].request_action(slot, pos, replace, switches, can_switch, forced, moves)
        
    def handle_battle_begin_turn(self, fid, turn):
        self.battles[fid].start_turn(turn)

        
    def handle_battle_victory(self, fid, party):
        battle = self.battles[fid]
        winner = (battle.party == party)
        battle.handle_victory(winner)
        del self.battles[fid]

    def handle_battle_set_move(self, fid, index, slot, id, pp, max):
        battle = self.battles[fid]
        battle.set_move(index, slot, id, pp, max)
       
##############################################################
class Battle:
    def __init__(self, fid, handler, party, opponent, team):
        self.fid = fid
        self.handler = handler
        self.party = party
        self.opponent = opponent
        self.teams = [[], []]
        self.teams[party] = parsers.parse_team_file(team)
        for i in range(6):
            self.teams[party - 1].append(Pokemon(moves=[]))
        self.active = [0, 0]
    
    # send a message to the users in this battle
    def send_message(self, msg):
        self.handler.send_message(self.fid, msg)
        
    def send_move(self, index, target):
        self.handler.send_move(self.fid, index, target)
        
    def send_switch(self, index):
        self.handler.send_switch(self.fid, index)
    
    def start_turn(self, turn):
        if turn == 1:
            self.send_message("Prepare to lose %s!" % self.opponent) 
        
    def print_message(self, cat, id, args):
        #print cat, id, args
        pass
    
    def handle_use_move(self, party, id):
        if party != self.party:
            p = self.teams[party][self.active[party]]
            move_list = self.handler.client.move_list
            move = None
            for name in move_list:
                if move_list[name]["id"] == id:
                    move = move_list[name]
                    break
            if not move in p.moves:
                p.moves.append(move)
    
    def handle_send_out(self, party, index, id, gender, level):
        self.active[party] = index
        p = self.teams[party][index]
        if p.pokemonspecies is None:
            species_list = self.handler.client.species_list
            if party is self.party:
                p.pokemonspecies = species_list[p.species]
            else:
                species = None
                for key in species_list:
                    if species_list[key]["id"] == id:  
                        species = species_list[key]
                        break
                p.pokemonspecies = species
    
    def handle_health_change(self, party, delta, total, denominator):
        self.teams[party][self.active[party]].health = (total, denominator)
        
    def handle_fainted(self, party):
        self.teams[party][self.active[party]].fainted = True
        
    def handle_victory(self, winner):
        if winner:
            self.send_message("Thanks for the match.")
            verb = "Won"
        else:
            self.send_message("Well played.")
            verb = "Lost"
        self.handler.leave_channel(self.fid)
        print verb, "a battle against", self.opponent
    
    def set_move(self, index, slot, id, pp, max):
        move_list = self.handler.client.move_list
        for name, move in move_list.items():
            if move["id"] == id:
                self.teams[self.party][index].moves[slot] = move
                break                
    
    def get_active(self, us):
        party = self.party if us else self.party - 1    
        return self.teams[party][self.active[party]]
 
 
    ############################################################################
    #    types and effectiveness                                               #
    #    by Allan Simmons                                                      #
    #    Last modified: 9/3/12                                                 #
    #                                                                          #
    #        These are a paired set of variables. type is an enumerated type   #
    #    for Pokemon types, and effectiveness is an array that stores type     #
    #    multipliers.                                                          #
    ############################################################################
    types = { "Normal" : 0, "Fire" : 1, "Water" : 2, "Electric" : 3, "Grass" : 4, "Ice" : 5, "Fighting" : 6, "Poison" : 7, 
    "Ground" : 8, "Flying" : 9, "Psychic" : 10, "Bug" : 11, "Rock" : 12, "Ghost" : 13, "Dragon" : 14, "Dark" : 15, 
    "Steel" : 16}

    effectiveness = [[ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5, 0, 1, 1, 0.5],
                     [ 1, 0.5, 0.5, 1, 2, 2, 1, 1, 1, 1, 1, 2, 0.5, 1, 0.5, 1, 2],
                     [ 1, 2, 0.5, 1, 0.5, 1, 1, 1, 2, 1, 1, 1, 2, 1, 0.5, 1, 1],
                     [ 1, 1, 2, 0.5, 0.5, 1, 1, 1, 0, 2, 1, 1, 1, 1, 0.5, 1, 1],
                     [ 1, 0.5, 2, 1, 0.5, 1, 1, 0.5, 2, 0.5, 1, 0.5, 2, 1, 0.5, 1, 0.5],
                     [ 1, 0.5, 0.5, 1, 2, 0.5, 1, 1, 2, 2, 1, 1, 1, 1, 2, 1, 0.5],
                     [ 2, 1, 1, 1, 1, 2, 1, 0.5, 1, 0.5, 0.5, 0.5, 2, 0, 1, 2, 2],
                     [ 1, 1, 1, 1, 2, 1, 1, 0.5, 0.5, 1, 1, 1, 0.5, 0.5, 1, 1, 0],
                     [ 1, 2, 1, 2, 0.5, 1, 1, 2, 1, 0, 1, 0.5, 2, 1, 1, 1, 2],
                     [ 1, 1, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 0.5],
                     [ 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 0.5, 1, 1, 1, 1, 0, 0.5],
                     [ 1, 0.5, 1, 1, 2, 1, 0.5, 0.5, 1, 0.5, 2, 1, 1, 0.5, 1, 2, 0.5],
                     [ 1, 2, 1, 1, 1, 2, 0.5, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 0.5],
                     [ 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 0.5],
                     [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 0.5],
                     [ 1, 1, 1, 1, 1, 1, 0.5, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 0.5],
                     [ 1, 0.5, 0.5, 0.5, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0.5]]

    ############################################################################
    #    find_best_move                                                        #
    #    by Allan Simmons                                                      #
    #    Last modified: 9/21/12                                                #
    #                                                                          #
    #        This function determines the best move of all the moves           #
    #    the current Pokemon has.                                              #
    ############################################################################
    def find_best_move(self, me, them_types, legal_moves):
        best_damage = 0
        best_id = 0
        
        #Calculate for each move
        for i, move in enumerate(me.moves):
            move = self.handler.client.move_list[move[0]]
            #Only consider available moves
            if legal_moves[i] != 0:
                damage = move["power"]
                #Technician multiplies the power by 1.5 if it is 60 or less
                if move["power"] <= 60 and (me.get_ability() == "Technician"):
                    damage *= 1.5
                #Power is multiplied by 1.5 for STAB (Same Type Attack Bonus)
                for type1 in me.pokemonspecies["types"]:
                    if move["type"] == type1:
                        damage *= 1.5
                #Power is multiplied by multiple based on type of the move and type(s) of the opponent
                for type2 in them_types:
                    damage *= self.effectiveness[self.types[move["type"]]][self.types[type2]]
                #For multi-hit moves, calculate based on average number of hits, 3
                if move["id"] == 14 or move["id"] == 24 or move["id"] == 38 or move["id"] == 50 or move["id"] == 96 or move["id"] == 150 or move["id"] == 152 or move["id"] == 198 or move["id"] == 280 or move["id"] == 321 or move["id"] == 380 or move["id"] == 435:
                    damage *= 3
                #These are multi-hit moves that hit exactly twice
                if move["id"] == 39 or move["id"] == 92 or move["id"] == 437:
                    damage *= 2
                    
                if damage > best_damage:
                    best_damage = damage
                    best_id = move["id"]         
        return best_id       

    ############################################################################
    #    find_best_switch                                                      #
    #    by Allan Simmons                                                      #
    #    Last modified: 9/13/12                                                #
    #                                                                          #
    #        This function finds the index of the best ally to switch to       #
    #    based off of the ally's type(s) and the type(s) of the opponent.      #
    ############################################################################
    def find_best_switch(self, switches, them_types):
        best_mult = 100
        switch_pos = -1
        for i in range(len(switches)):
            #Only consider available switches
            if switches[i] != 0:
                p = self.teams[self.party][i]
                p.pokemonspecies = self.handler.client.species_list[p.species]
                mult = 1
                #Create a numerical representation of how good/bad the switch would be against the opponent
                #Finds best Pokemon defensively (based on defenses against current opponent)
                for type1 in p.pokemonspecies["types"]:
                    for type2 in them_types:
                        mult *= self.effectiveness[self.types[type2]][self.types[type1]]
                if mult < best_mult:
                    best_mult = mult
                    switch_pos = i
                    
        return switch_pos
    
    ############################################################################
    #    access_result                                                         #
    #    by Allan Simmons                                                      #
    #    Last modified: 9/3/12                                                 #
    #                                                                          #
    #        This function will retrieve the last fact from the fact list and  #
    #    split it into an array of strings. This final fact is the result of   #
    #    running the rules with the facts and represents the bot's chosen      #
    #    action                                                                #
    ############################################################################
    def access_result(self):
        f = esys.InitialFact()
        while f.Next() is not None:
            f = f.Next()
            words = f.PPForm().rsplit()
        return words 
    
    ############################################################################
    #    perform_result                                                        #
    #    by Allan Simmons                                                      #
    #    Last modified: 9/14/12                                                #
    #                                                                          #
    #        This function will perform the result as determined by the        #
    #    expert system. The first word of the result determines whether        #
    #    a move is used or a switch is made.                                   #
    ############################################################################
    def perform_result(self, result, me, switches):
        #IF KEYWORD IS MOVE OR SWITCH   
        if result[1] == "(Use":
            attack = int(result[2])
            move_pos = 0
            #FIND ATTACK IN LIST OF ATTACKS
            for i, move in enumerate(me.moves):
                move = self.handler.client.move_list[move[0]]
                if attack == move["id"]:
                    move_pos = i
            print "Used move ", attack
            self.send_move(move_pos, 1 - self.party)
            
        elif result [1] == "(Switch-to":
            pokemon = result[2]
            switch_pos = 0
            #FIND SWITCH IN LIST OF ALLIES
            for i in range(len(switches)):
                if switches[i] != 0:
                    p = self.teams[self.party][i]
                    p.pokemonspecies = self.handler.client.species_list[p.species]
                    if pokemon == p.species:
                        switch_pos = i
            print "Switched to ", switch_pos
            self.send_switch(switch_pos)
    
    ############################################################################
    #    request_action                                                        #
    #    by Allan Simmons                                                      #
    #    Last modified: 9/21/12                                                #
    #                                                                          #
    #        This function loads the rules into the expert system.             #
    ############################################################################
    def load_rules(self):
        esys.BuildRule("Replace", "(Need to replace Pokemon)", "(assert (Need to switch))", "")
        esys.BuildRule("Switch-to-best", "(Need to switch) (Best-switch-is ?pokemon)", "(assert (Switch-to ?pokemon Pokemon))", "")
        esys.BuildRule("Switch", "(not (Need to replace Pokemon)) (Want to switch)", "(assert (Need to switch))", "")
        esys.BuildRule("Heal", "(not (Need to switch)) (Need to heal) (Heal-move-is ?move)", "(assert (Use ?move move))", "")
        esys.BuildRule("Use-other", "(not (Need to switch)) (not (Need to heal)) (Can use Other)", "(assert (Use Other move))", "")
        esys.BuildRule("Hazards", "(declare (salience 4)) (not (Hazards used)) (not (Other used)) (Use Other move) (Hazard-move-is ?move)", "(assert (Use ?move move) (Other used))", "")
        esys.BuildRule("Weather", "(declare (salience 3)) (not (Weather used)) (not (Other used)) (Use Other move) (Weather-move-is ?move)", "(assert (Use ?move move) (Other used))", "")
        esys.BuildRule("Substitute", "(declare (salience 2)) (not (Substitute used)) (not (Other used)) (Use Other move) (Substitute-move-is ?move)", "(assert (Use ?move move) (Other used))", "")
        esys.BuildRule("Stat-boost", "(declare (salience 1)) (not (Stat-boost used)) (not (Other used)) (Use Other move) (Stat-boost-move-is ?move)", "(assert (Use ?move move) (Other used))", "")
        esys.BuildRule("Fight", "(not (Need to switch)) (not (Need to heal)) (Best-move-is ?move)", "(assert (Use ?move move))", "")
    
    ############################################################################
    #    request_action                                                        #
    #    by Allan Simmons                                                      #
    #    Last modified: 9/21/12                                                #
    #                                                                          #
    #        This function gathers information about the current Pokemon,      #
    #    the other team members, and the opposing Pokemon. This information    #
    #    is then stored as facts for PyClips to use along with rules set       #
    #    by the author. When run, PyClips will use both the facts and the      #
    #    rules to determine a course of action for the bot to take.            #
    ############################################################################
    def request_action(self, slot, pos, replace, switches, can_switch, forced, legal_moves):
        #Reset the facts and rules for the PyClips environment, then load in the rules
        esys.Reset()
        self.load_rules()
        
        #These represent the two active Pokemon
        me = self.get_active(True)
        them = self.get_active(False)
        
        #If the move is forced, there is no choice
        if forced:
            self.send_move(1, 1)
        else:
            #Start by getting the facts and adding them to the fact base            
            #If the current Pokemon is fainted, need to replace
            print replace
            if replace:
                replace_fact = "(Need to replace Pokemon)"
                esys.Assert(replace_fact)
            
            #Active 'Mon's health
            #    Note: Health is not updated until damage is taken
            HP = self.teams[self.party][slot].health[0]
            HP_fact = "(Health is {0})".format(HP)
            esys.Assert(HP_fact)            
            
            ##################################################
            #FIGURE OUT IF NEED TO HEAL OR SWITCH
            #FIGURE OUT IF POKEMON IS THREATHENED BY OPPONENT
            ##################################################
            
            
            #Move facts, only if there are legal moves
            if len(legal_moves) > 0:
                #Best move
                best_move_id = self.find_best_move(me, them.pokemonspecies["types"], legal_moves)
                best_move_fact = "(Best-move-is {0})".format(best_move_id)
                esys.Assert(best_move_fact)
                
                #Active 'Mon's "Other" class moves
                for i, move in enumerate(me.moves):
                    if legal_moves[i] !=0:
                        move = self.handler.client.move_list[move[0]]
                        if move["class"] == "Other":
                            #Hazard
                            if move["id"] == 381 or move["id"] == 430 or move["id"] == 386:
                                move_fact = "(Hazard-move-is {0})".format(move["id"])
                            #Weather
                            elif move["id"] == 307 or move["id"] == 398 or move["id"] == 169 or move["id"] == 337:
                                move_fact = "(Weather-move-is {0})".format(move["id"])
                            #Substitute
                            elif move["id"] == 396:
                                move_fact = "(Substitute-move-is {0})".format(move["id"])
                            #Stat-boost
                            elif move["id"] == 2 or move["id"] == 3 or move["id"] == 9 or move["id"] == 25 or move["id"] == 51 or move["id"] == 67 or move["id"] == 81 or move["id"] == 82 or move["id"] == 143 or move["id"] == 171 or move["id"] == 186 or move["id"] == 202 or move["id"] == 234 or move["id"] == 262 or move["id"] == 323 or move["id"] == 351 or move["id"] == 409 or move["id"] == 411 or move["id"] == 413 or move["id"] == 458:
                                move_fact = "(Stat-boost-move-is {0})".format(move["id"])
                                
                            move_fact = "(Move is {0})".format(move["id"])
                            esys.Assert(move_fact)
            
            #Best switch
            best_switch_pos = self.find_best_switch(switches, them.pokemonspecies["types"])
            if best_switch_pos != -1:
                best_switch_pokemon = self.teams[self.party][best_switch_pos].species
                best_switch_fact = "(Best-switch-is {0})".format(best_switch_pokemon)
                esys.Assert(best_switch_fact)
            else:
                best_switch_fact = "(No-best-switches)"
                esys.Assert(best_switch_fact)
            
            #Once all of the facts have been collected, proceed with the running of the expert system.
            esys.PrintAgenda()
            esys.Run()
            esys.PrintRules()
            esys.PrintFacts()

            #After the expert system has run, find the solution it has come up with and execute it.
            self.perform_result(self.access_result(), me, switches)

def start_pyfred(host=HOST, port=PORT, username=USERNAME, password=PASSWORD):
    try:
        client = BotClient(HOST, PORT)
    except socket.error:
        print "Failed to connect to host {0} on port {1}".format(host, port)
        exit(1)
    t1 = time.time()
    client.init_species("species.xml")
    t2 = time.time()
    client.init_moves("moves.xml")
    t3 = time.time()
    
    #print "Loaded species in", (t2-t1)*1000, "milliseconds"
    #print "Loaded moves in", (t3-t2)*1000, "milliseconds"
    client.set_handler(PyFred())
    client.authenticate(username, password)
    client.run()

if __name__ == "__main__":
    start_pyfred()


