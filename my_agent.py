__author__ = "Cam Clark "
__authorID__ = "8298806 "
__organization__ = "COSC343/AIML402, University of Otago"
__email__ = "claca067@student.otago.ac.nz"

agentName = "CamAIAgent"

from xnimmt import table_resolve
import copy

class XNimmtAgent:
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
   expectimax(self, table, my_hand, unseen, card, depth, pruning)
      Returns evaluation of how good a card is to play
   evaluate(self, table, my_hand, unseen_numbers)
     Returns a n estimate in "points" how bad this position is for my agent (The greater the points the worse the position).
   """
    
    def __init__(self, deck, num_rows, max_cards_in_hand, xth_card_takes):
        """
        :param deck: list of tuples (card number, card value) in the deck
        :param num_rows: number of rows on the table
        :param max_cards_in_hand: number of cards in hand
        :param xth_card_takes: the row length that forces a take
        """
        self.deck = deck
        self.deck_map = {n: (n, value) for (n, value) in deck} # Create a lookup-table/hashmap
        self.num_rows = num_rows
        self.max_cards_in_hand = max_cards_in_hand
        self.all_numbers = set(self.deck_map.keys())
        self.xth_card_takes = xth_card_takes
        self.max_depth = 3  # Can be changed for the program to run at different speeds. Was faster at 2 (less accurate), too slow at 4 for large tables
        self.removed_from_table = set() # Used to help keep track of opponent cards
        self.prev_table = None 
        self.am_pruning = True # Toggle used for testing
        
      
    
    def AgentFunction(self, percepts):
        my_hand, table = percepts
        
        if len(my_hand) == self.max_cards_in_hand: # Reset if needed
            self.prev_table = None 
            self.removed_from_table.clear()

        # Cards not yet played by either player
        if self.prev_table is not None:
            prev_nums = {n for row in self.prev_table for (n, value) in row}
            curr_nums = {n for row in table for (n, value) in row}
            picked_up = prev_nums - curr_nums
            if picked_up: self.removed_from_table.update(picked_up)
        
        self.prev_table = [list(row) for row in table]
	                    
        # creating the unseen card list
        seen = {n for (n, value) in my_hand}
        seen.update(self.removed_from_table)
        for row in table:
            seen.update(n for (n, value) in row)
        
        unseen = list(self.all_numbers - seen) # possible opp cards


        best_score = float("inf") # Want a score as close to 0 as possible
        best_card = None # updated as go through my hand with it being changed if the score for that card is lower then 'best_score

        for card in my_hand:
            pruning = best_score if self.am_pruning else float("inf") # toggle for pruning
            score = self.expectimax(table, my_hand, unseen, card, self.max_depth, pruning = pruning) 
            if score < best_score or (score == best_score and card[0] < best_card[0]): # Picks the card with lowest penalty
                best_score = score # the above ^ or () condition is if the best_score is even then take the one with card number
                best_card = card

        return best_card[0] # just the num value to play

    def expectimax(self, table, my_hand, unseen, my_card, depth, pruning):
        """
        Simultaneous move expectimax:
        - Fix my_card for this round.
        - Average over all possible opponent cards from unseen.
        - Resolve the round and recurse.
        """
        if depth == 0: # Base Case
            return self.evaluate(table, my_hand, unseen)

        total_score = 0 # keep track of the branches score
        opp_choices = unseen
        

        for opp_num in opp_choices:
            opp_card = self.deck_map[opp_num] # opp_choices is just a list of unseen so with deck_map I can just make map O(1)

            # Resolve round in ascending card order (Remember that the lowest card is placed first)
            t = copy.deepcopy(table) #deep copy the table as we recurse updating this new deepcopy
            if my_card[0] < opp_card[0]: # the lower card is played first  
                t, my_pts, _ = table_resolve(t, my_card, self.xth_card_takes)
                t, _, _ = table_resolve(t, opp_card, self.xth_card_takes)
            else: # opp card lower they play first
                t, _, _ = table_resolve(t, opp_card, self.xth_card_takes)
                t, my_pts, _ = table_resolve(t, my_card, self.xth_card_takes)

            # Update hands and unseen cards for recursion (Remove the card we just played from our recurs params)
            my_next_hand = [c for c in my_hand if c[0] != my_card[0]] 
            next_unseen = [u for u in unseen if u not in (my_card[0], opp_card[0])]

            if depth - 1 == 0 or not my_next_hand : # If played last card or depth-limit then we evaluate with curr table
                score = -my_pts + self.evaluate(t, my_next_hand, next_unseen) 
            else:
                best_next_round_cost = float("inf")
                for next_card in my_next_hand:
                    next_round_cost = self.expectimax(t, my_next_hand, next_unseen, next_card, depth - 1, pruning=pruning)
                    # Keep cheapest continuation
                    if next_round_cost < best_next_round_cost:
                        best_next_round_cost = next_round_cost
                        if best_next_round_cost == 0.0: # Cannot beat '0.0' lets early exit no need to continue looping
                            break
                # Total cost for this opponent reply is my peantly this round + best continuation
                score = -my_pts + best_next_round_cost
            # add on to running sum over all opponent replies
            total_score += score
            
            # prune the lower bound on final average
            # each per-reply is => 0, so even if all reaminging were 0
            # the final avg can't be lower then (total-score /total_number_of_replies)
            prune = total_score /len(opp_choices)
            if prune >= pruning:
                # this card can't beat the best card we've already found at the root so prune
                return prune
        # considered all opponent replies return the average expected cost
        return total_score / len(opp_choices) 

    def evaluate(self, table, my_hand, unseen_numbers):
        
        """
        Heuristic evaluation of the position is done with the engine points and possible outcome for opponent hand
        returns a positive int or 0 estimate of how bad state is. 
        Higher the state the worse it is
        Combination of two point taking actions
        1. The smallest immediate penalty we would take for a card in my hand. Because I use a positive prune 
           The table_resolve is -table_resolve so that it returns a positive
        2. The probablity that a random "unseen" card is smaller than all row tops (can't be placed) * the points in 
           the least cost row. Which the engine chooses ona. forced take). this captures table "pressure independent of our hand.
           
           Then return LB + FT. the return is non negative so can be pruned by total_score / len(opp_choices) 
        """

        lower_bound = 0.0
        if my_hand: # If I  still have cards in my hand compute cheapest cost
            lower_bound = min(
                (-table_resolve(table, card, self.xth_card_takes)[1]) # -table-resolve because makes it positive number
                for card in my_hand
            )

        forced_expect = 0.0
        if table and unseen_numbers:
            tops = [row[-1][0] for row in table if row] #last num of list is '-1' so can get it easily
            if tops:
                min_top = min(tops)  # must be smaller than ALL tops to force a take
                forced_count = sum(1 for n in unseen_numbers if n < min_top)
                total_unseen = len(unseen_numbers)
                p_forced = forced_count / total_unseen if total_unseen > 0 else 0.0
                # on a forced take you take the lowest val row
                least_row_points = min(sum(c[1] for c in row) for row in table)
                forced_expect = p_forced * least_row_points
        
        return lower_bound + forced_expect    
            
      

    
