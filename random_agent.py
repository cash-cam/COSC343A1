__author__ = "Lech Szymanski"
__organization__ = "COSC343/AIML402, University of Otago"
__email__ = "lech.szymanski@otago.ac.nz"

import random

agentName = "random"

class XNimmtAgent():
   """
   A class that encapsulates the code dictating the
   behaviour of the agent playing the game of X Nimmt!.

   ...

   Attributes
   ----------
   deck : list of tuples with (card number, card value) in
           the card deck
   num_rows : number of rows on the table
   num_cards_in_hand : number of cards in hand
   xth_card_takes: the card that take the row

   Methods
   -------
   AgentFunction(percepts)
      Returns the card from hand to play with.
   """

   def __init__(self, deck, num_rows, max_cards_in_hand, xth_card_takes):
      """
      :param deck: list of tuples with (card number, card value) in the deck. 
      :param num_rows: number of rows on the table
      :param max_cards_in_hand: number of cards in hand
      :param xth_card_takes: the card that take the row
 
      """
      self.deck = deck
      self.num_rows = num_rows
      self.max_cards_in_hand = max_cards_in_hand
      self.xth_card_takes = xth_card_takes

   def AgentFunction(self, percepts):
      """Returns the card from hand to play with

      :param percepts: a tuple three items: (my_hand, table, cards_played), where
      
         - my_hand - is a list of cards in hand, each a tuple with (card number, card value),
      
         - table - is a list of 4 lists of cards on the table.
      
      :return: int - card number from my_hand to play.
      """

      # Extract different parts of percepts.
      my_hand = percepts[0]
      table = percepts[1]
      
      # Make a random choice of the card to bid with
      card = random.choice(my_hand)
      card_number, card_value = card

      action = card_number

      # Return the bid
      return action
