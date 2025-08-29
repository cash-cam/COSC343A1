__author__ = "Lech Szymanski"
__organization__ = "COSC343/AIML402, University of Otago"
__email__ = "lech.szymanski@otago.ac.nz"

import os,sys
import numpy as np
import importlib.util
import time
from settings import game_settings
import copy

def time_to_str(time_in_seconds):
   timeStr = ''
   if time_in_seconds > 3600:
      hours = int(np.floor(time_in_seconds / 3600))
      timeStr += "%d h, " % hours
      time_in_seconds %= 3600

   if time_in_seconds > 60:
      minutes = int(np.floor(time_in_seconds / 60))
      timeStr += "%d min, " % minutes
      time_in_seconds %= 60

   if time_in_seconds < 1:
      timeStr += "%.3f s" % time_in_seconds
   else:
      timeStr += "%d s" % time_in_seconds

   return timeStr

def table_resolve(table, card, xth_card_takes):

   table = copy.deepcopy(table)
   select_row = None
   card_diff = np.inf
   points = 0
   for r, row in enumerate(table):
      if row[-1][0] < card[0] and card[0] - row[-1][0] < card_diff:
         card_diff = card[0] - row[-1][0]
         select_row = r 

   # Find the rows in the table that can take the card
   if select_row is not None:
      r = select_row
      if len(table[r]) < xth_card_takes:
         table[r].append(card)
         return table, points, r
   else:
      # No rows available, find the row with the least points
      r = np.argmin([sum(c[1] for c in row) for row in table])

   for c in table[r]:
      points -= c[1]
   table[r] = [card]
   
   return table, points, r


# Class player is a wrapper for a player agent
class Player:
   def __init__(self, game, playerFile, jointname=False):
      if playerFile == 'human_agent.py':
         game.showTable = False
         game.autoPlayLastCard = False

      self.playerFile = playerFile
      self.game = game

      # Player file must be in same folder as raj.py
      game_folder = os.path.dirname(os.path.realpath(__file__))
      playerFile = os.path.join(game_folder,playerFile)

      if not os.path.exists(playerFile):
         raise RuntimeError("Error! Agent file '%s' not found" % self.playerFile)

      if len(self.playerFile) > 3 and self.playerFile[-3:].lower() == '.py':
         playerModule = self.playerFile[:-3]
      else:
         raise RuntimeError("Error! Agent file %s needs a '.py' extension" % self.playerFile)


      try:

         spec = importlib.util.spec_from_file_location(playerModule, playerFile)
         self.exec = importlib.util.module_from_spec(spec)
         sys.modules["module.name"] = self.exec
         spec.loader.exec_module(self.exec)
      except Exception as e:
         raise RuntimeError(str(e))

      deck = list(game.deck)

      try:
         self.agent = self.exec.XNimmtAgent(deck=list(deck), num_rows=game.num_rows, max_cards_in_hand=game.max_cards_in_hand, xth_card_takes=game.xth_card_takes)
      except Exception as e:
         raise RuntimeError(str(e))

      if hasattr(self.exec, 'agentName') and self.exec.agentName[0] != '<':
         self.name = self.exec.agentName
      else:
         if self.game.in_tournament and self.playerFile != 'random_agent.py':
            self.name = self.playerFile.split('/')[-2]# playerFile.split('.')[1]
         else:
            self.name = self.playerFile

      if jointname and self.game.in_tournament:
         self.pname = self.playerFile.split('/')[-2]


class XNimmtGame:

   def __init__(self,num_players, num_rows, num_cards_in_deck, max_cards_in_hand, xth_card_takes, verbose=0,tournament=False):

      if num_players < 2:
         raise RuntimeError("Error! Number of players must be at least 2")

      if num_cards_in_deck < max_cards_in_hand * num_players + num_rows:
         raise RuntimeError(f"Error! Number of cards in deck must be at least {max_cards_in_hand * num_players + num_rows} for a {num_players}-player game with {max_cards_in_hand} cards in hand and {num_rows} rows on the table.")

      self.num_players = num_players
      self.num_cards_in_deck = num_cards_in_deck
      self.num_rows = num_rows
      self.max_cards_in_hand = max_cards_in_hand
      self.xth_card_takes = xth_card_takes
      self.showTable = True
      self.autoPlayLastCard = True
      

      



      card_numbers = np.arange(0,self.num_cards_in_deck+1)
      card_points = np.ones((self.num_cards_in_deck+1),dtype='int')
      card_points[::3] = 2
      card_points[::5] = 3
      card_points[::7] = 5
      card_points[self.num_cards_in_deck//2] = 7
      card_numbers = card_numbers[1:].tolist() # remove 0 card
      card_points = card_points[1:].tolist()

      self.deck = list(zip(card_numbers, card_points))

      self.in_tournament = tournament

      self.verbose = verbose
      if tournament:
         self.throwError = self.errorAndReturn
      else:
         self.throwError = self.errorAndExit

      if self.verbose:
         print("XNimmt! game settings:")

         print(f' Deck: {self.deck}')
         print(f' Cards in hand: {self.max_cards_in_hand}')
         print(f' Xth card takes: {self.xth_card_takes}'   )
         print(f' Num players: {self.num_players}')

   def errorAndExit(self,errorStr):
      raise RuntimeError(errorStr)

   def errorAndReturn(self,errorStr):
      self.errorStr = errorStr
      return None



   def play(self,players,deck):

      scores = np.zeros((self.num_players))

      hands = []
      for p in range(self.num_players):
         if len(deck) < self.max_cards_in_hand:
            self.throwError("Error! Not enough cards in deck to deal to players")

         hand = deck[:self.max_cards_in_hand]
         deck = deck[self.max_cards_in_hand:]
         hand.sort(key=lambda x: x[0])  # Sort by card number
         hands.append(hand)
      table = []

      for i in range(self.num_rows):
         table.append([])
         table[-1].append(deck[0])
         deck = deck[1:]
      table.sort(key=lambda x: x[0][0])  # Sort by card value

      if self.verbose and self.showTable:
         print("\n  Table:")
         for r, row in enumerate(table):
            print(f"  {r+1}: {row}")
      while len(hands[0]) > 0:

         if self.verbose > 1:
            if len(hands[0]) > 1:
              print(f"\n  - {len(hands[0])} cards left in hand -")
            else:
               print("\n  - 1 card left in hand -")

         selected_cards = []      
         for p, player in enumerate(players):
            percepts = (list(hands[p]), copy.deepcopy(table))
 
            try:
               if len(hands[p]) > 1 or not self.autoPlayLastCard:
                  action = player.agent.AgentFunction(percepts)
               else:
                  action = hands[p][0][0]
            except Exception as e:
               self.throwError(str(e))

            try:
               card_numbers_hand = list(list(zip(*hands[p]))[0])
               if action not in card_numbers_hand:
                  self.throwError("Error! AgentFunction from '%s.py' returned a card that's not in player's hand" % (player.playerFile))


               i = card_numbers_hand.index(action)
               card = hands[p][i]
               selected_cards.append((p, card))
               hands[p].remove(card)


            except Exception as e:
               self.throwError(str(e))


         if self.verbose:
            for p, card in selected_cards:
               print("  Player %d (%s) selected card %s." % (p+1, players[p].name, card))

         selected_cards.sort(key=lambda x: x[1][0])

         for p, card in selected_cards:
            table, points, r = table_resolve(table, card, self.xth_card_takes)

            if self.verbose > 1:
               if points == 0:
                  print(f"  - Resolve: Player {p+1} ({players[p].name}) {card} to row {r+1}.")
               else:
                  print(f"  - Resolve: Player {p+1} ({players[p].name}) takes row {r+1} with {points}.")

            scores[p] += points
           
            if self.verbose > 1 or (self.verbose==1 and p==self.num_players-1) and self.showTable:
               print("  Table:")
               for r, row in enumerate(table):
                  print(f"  {r+1}: {row}")

      if self.verbose:
         print("")
      return scores


   def run(self,agentFiles,num_games=1000,seed=None):

      if self.verbose:
         print("Game play:")
         print("  Num rounds:       %d" % num_games)

      if seed is None:
         seed = int(time.time())

      rnd = np.random.RandomState(seed)

      players = []
      for i, agentFile in enumerate(agentFiles):
         try:
            player = Player(game=self, playerFile=agentFile)
            players.append(player)
         except Exception as e:
            self.throwError(str(e))
            
      win_counts = np.zeros((self.num_players), dtype='int')
      draw_count = 0


      all_decks = np.zeros((num_games, len(self.deck))).astype('int')
      for n in range(num_games):
         all_decks[n] = rnd.choice(np.arange(len(self.deck)),size=len(self.deck),replace=False)

      score = np.zeros((self.num_players))
      game_count = 0
      tot_time = 0
      for n in range(num_games):
         deck = all_decks[n].tolist()
         deck = [self.deck[i] for i in deck]
         if self.verbose:
            print("\nRound %d/%d" % (game_count+1,num_games))

         start = time.time()
         game_score = self.play(players,deck=deck)
         end = time.time()
         score += game_score
         best = np.max(game_score)
         winners = [i for i, s in enumerate(game_score) if abs(s - best) < 1e-9]
         if len(winners) == 1:
            win_counts[winners[0]] += 1
         else:
            draw_count += 1
         game_count += 1
         score_str = "  Score in game %d: " % game_count
         for i in range(self.num_players):
            score_str += "\n    Player %d (%s): %.2f" % (i+1, players[i].name, game_score[i])
         print(score_str)
 
         score_str = "\nAverage score after game %d: " % game_count
         for i in range(self.num_players):
            score_str += "\n  Player %d (%s): %.2f" % (i+1, players[i].name, score[i]/game_count)
         print(score_str)
         tot_time += end - start

         if game_count < num_games:
            avg_time = tot_time / game_count
            print("Average running time per game %s." % (time_to_str(avg_time)))
            print("Time remaining %s." % (time_to_str(avg_time * (num_games-game_count))))
            print("Expected total running time %s." % (time_to_str(avg_time * num_games)))
         else:
            print("Total running time %s." % (time_to_str(tot_time)))
      print("\n === Win rate over %d games ===" % game_count)
      for i in range(self.num_players):
         wr = win_counts[i] / max(1, game_count)
         print(f"  Player {i+1} ({players[i].name}): {win_counts[i]} wins  ({wr:.1%})")
      if draw_count:
         print(f"  Draws: {draw_count} ({draw_count / max(1, game_count):.1%})")
         




if __name__ == "__main__":

   game = XNimmtGame(num_players=len(game_settings['players']),
                    num_rows=game_settings['numRows'],
                    num_cards_in_deck=game_settings['numCardsInDeck'],
                    max_cards_in_hand=game_settings['maxCardsInHand'],
                    xth_card_takes=game_settings['XthCardTakes'],
                    verbose=game_settings['verboseLevel'])
   
   game.run(agentFiles=game_settings['players'],
            num_games=game_settings['totalNumberOfGames'],
            seed=game_settings['seed'])



