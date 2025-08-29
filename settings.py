__author__ = "Lech Szymanski"
__organization__ = "COSC343/AIML402, University of Otago"
__email__ = "lech.szymanski@otago.ac.nz"

# You can manipulate these settings to change how the game is played.

game_settings = {

   # agent files that play the game
   "players": ("my_agent.py", "random_agent.py"), 

   "numCardsInDeck": 17,         # total number of cards in the deck CHANGE BACK TO 17
   
   "maxCardsInHand": 5,         # number of cards each player has at the 
                                #start of the game

   "XthCardTakes": 4,          # the card that takes the row

   "numRows": 3,                # number of rows on the table

   "totalNumberOfGames": 100,   # total number of games played

   "verboseLevel": 2,           # level of verbosity of the game output
                                # 0 - no output, 1 - summary of the game, 
                                # 2 - detailed output   

   "seed": 1                  # seed for random choices of bids in the game, None for random seed

}


# If main is run, create an instance of the game and run it
if __name__ == "__main__":
   from xnimmt import XNimmtGame

   game = XNimmtGame(num_players=len(game_settings['players']),
                    num_rows=game_settings['numRows'],
                    num_cards_in_deck=game_settings['numCardsInDeck'],
                    max_cards_in_hand=game_settings['maxCardsInHand'],
                    xth_card_takes=game_settings['XthCardTakes'],
                    verbose=game_settings['verboseLevel'])
   
   game.run(agentFiles=game_settings['players'],
            num_games=game_settings['totalNumberOfGames'],
            seed=game_settings['seed'])