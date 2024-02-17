# third party imports
from itertools import chain
import random
import numpy as np
from gymnasium import Env, spaces
import logging
import time

# local imports
from src.player import Human,ArtificialRetardation
from src.board import Board, Row
from src.display import CardTable
from src.cards import Starter


class Game_Controller(Env):
    """A gym-like environment that simulates a card game between two players.
    
    The game is played on a board with 4 rows and a hand of 10 cards for each player. The objective is to score points by playing cards in a specific order, combining their elements. Actions are performed by playing cards from the hand, which are removed from the hand after being used. The game ends when all cards have been played or a certain number of rounds has been won.
    
    Attributes:
        action_space (gym.spaces.Discrete): The space of possible actions, represented as an integer index corresponding to a card in the player's hand.
        observation_space (gym.spaces.Box): The space of possible observations, representing the state of the game board and players' hands."""
    metadata = {'render.modes': ['human']}

    def __init__(self, training = False, players = None):
        """Initialize the environment with a random seed and initial state."""

        super().__init__()
        self.training = training
        self.display = CardTable()
        # Define action and observation space
        self.action_space = spaces.Discrete(40)  # Example: two possible actions - 0 or 1
        self.observation_space = spaces.Box(low=0, high=50, shape=(466,), dtype=np.uint8)
        # Initialize state
        self._state = None
        self.done = False
        reverse_player_order = self.get_coin_flip()

        uses_action = True
        is_bottom_player = True
        
        if training:
            if players:
                self.players = players
            else:
                self.players = [
                    (uses_action, is_bottom_player, ArtificialRetardation("Trained Monkey")),          # Trainee
                    #(uses_action, is_bottom_player, MCTS_Idiot("Trained Monkey", self.action_space)),           # Trainee
                    (not uses_action, not is_bottom_player, ArtificialRetardation("Clueless Robot"))    # Opponent
                ]
        else:
            self.display.start_render()
            self.players =  [
                (uses_action, not is_bottom_player, ArtificialRetardation("Clueless Robot")),
                (not uses_action, is_bottom_player, Human("IQ Test Subject", self.display.ask_prompt))
            ]

        if reverse_player_order:
            self.players.reverse()

        bottom_name = [player for player in self.players if player[1]][0][2].name
        top_name = [player for player in self.players if not player[1]][0][2].name

        self.board = Board(top_name, bottom_name)

        self.rewards = {
            True : 0,
            False : 0
            }
        
        self.steps=0
        self.rounds_in_advantage = 0
        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.DEBUG, filename='logs/'+str(time_stamp)+'.log', filemode='w', format='%(message)s')

    def load_opponent_model(self, opponent_model):
        opponent = [player for player in self.players if not player[0]][0][2]
        opponent.model = opponent_model

    def setup_hand_for_new_round(self) -> None:
        #self.board.set_deck(True, Booster().open(20))
        self.board.set_deck(True, Starter().open())
        self.board.draw_cards_to_hand(True, 10, True)
        #self.board.set_deck(False, Booster().open(20))
        self.board.set_deck(False, Starter().open())
        self.board.draw_cards_to_hand(False, 10, True)

    def step(self, action):
        """Update the environment based on the provided action and return the new observation, reward, etc.
    
        Args:
            action (int): The index of the card to play.
            
        Returns:
            tuple: A tuple containing the new observation, 
            the reward obtained by the player, 
            a boolean indicating if the episode has been truncated, 
            a boolean indicating whether the episode has ended, 
            and a dictionary with additional information."""
        self.steps+=1
        logging.debug("Step: %s", self.steps)
        logging.debug("Action: %s", action)
        info = {}

        for uses_action, is_bottom_player, player in self.players:
            player_is_human = isinstance(player, Human)
            # we have already passed
            if self.board.has_passed(is_bottom_player):
                continue

            card_index = player.make_choice(
                self.board.get_valid_choices(is_bottom_player),
                self,
                action=action if uses_action else None
            )
            # we are passing this turn
            if card_index == 0:
                self.board.pass_round(is_bottom_player)
                if not self.training and not player_is_human:
                    self.display.write_sub_message(f"Player {self.board.get_player_name(is_bottom_player)} passed!")
                    time.sleep(1.5)
                continue
            card_index = card_index - 1
            # otherwise play card
            played_card = self.board.get_hand(is_bottom_player)[card_index]
            played_row = played_card.type
            if played_row == Row.ANY:
                played_row = player.make_row_choice(played_card, [Row.FRONT, Row.WISE, Row.SUPPORT])
            self.board.play_card(is_bottom_player, card_index, played_row) # (bool, card_index -> int, row (Enum))
            # if AR played we want to delay the move by 0.5 seconds to make it look more natural
            if not self.training and not player_is_human:
                time.sleep(0.5)
            # render the move of player one
            if not self.training and player == self.players[0][2]:
                self.render()
 

        round_over = self.board.has_passed(True) and self.board.has_passed(False)
        round_winner = self.board.get_round_winner()
        # let winner start
        if round_over and self.board.get_player_name(self.players[0][1]) not in self.board.get_round_winner():
            self.players.reverse()
        elif round_over and self.get_coin_flip():
            self.players.reverse()

        # display round winner
        if round_over and not self.training:
            if len(round_winner) == 1:
                message = f"{round_winner[0]} won the round!"
                logging.debug("%s won the %s. round", round_winner[0], self.board.round_number)
            else:
                message = "Draw, no one won the round!"
                logging.debug("Round %s was a draw",self.board.round_number)
            self.display.ask_prompt(message + " Press [Enter] to continue", [""])
        
        # game logic to end the round
        if round_over:
            self.board.end_round()
            self.board.draw_cards_to_hand(True)
            self.board.draw_cards_to_hand(False)

        truncated = self.steps == 100

        self.done = self.board.game_ended()

        # display the game winner
        if not self.training and self.done:
            winner = self.board.get_winner()
            if winner[0] and not winner[1]:
                message = f"{self.board.get_player_name(False)} won the game!"
                logging.debug("%s WON", winner[0])
            elif winner[1] and not winner[0]:
                message = f"{self.board.get_player_name(True)} won the game!"
                logging.debug("%s WON", winner[0])
            else:
                message = "Draw, no one won the game"
                logging.debug("DRAW")
            self.display.write_message(message)

        observation = self.get_state(action)
        reward = self.get_reward()
        logging.debug("Round Number: %s",self.board.round_number)
        if truncated:
            logging.debug("TRUNCATED")
        return observation, reward, truncated , self.done, info

    def reset(self, seed=None, options=None):
        """Reset the environment to its initial state and returns the starting observation.
        
        Args:
            seed (int, optional): Seed for randomizing the board. Defaults to None.
        
        Returns:
            np.array: The starting observation.
        """
        # Reset the environment to its initial state
        super().reset(seed=seed)
        self.steps=0
        self.rounds_in_advantage = 0
        info = {}
        self.rewards = {
            True : 0,
            False : 0
            }
        self.board.reset()
        self.setup_hand_for_new_round()
        self._state = self.get_state(True)
        logging.debug("NEW GAME")
        return self._state, info

    def render(self, mode='human'):
        """Render the environment for visualization."""
        for bottom_player in [True, False]:
            self.display.update_card_hand(
                self.board.get_hand(bottom_player),
                bottom_player
            )
            self.display.set_player_cards(
                list(self.board.get_half_board(bottom_player).items()),
                bottom_player
            )
            self.display.set_player_info(
                self.board.get_player_name(bottom_player),
                len(self.board.get_deck(bottom_player)),
                len(self.board.get_graveyard(bottom_player)),
                "NOT IMPLEMENTED :(",
                self.board.get_won_rows()[int(bottom_player)],
                self.board.get_rounds_won(bottom_player),
                bottom_player
            )

    def get_state(self, is_bottom_player, action = 0): # AR will always be player flag False
        """Return the current state of the environment.
    
        Returns:
        np.array: The current state of the environment as a vector."""

        # Board 76 * 3 +
        # Hand 38 * 3 +
        # Graveyard 38 * 3 +
        # turn score 6 +
        # rounds won 2 +
        # current round 1
        # action feedback
        # = 466

        state = np.zeros((466,), dtype=np.uint8)
        
        top_board_cards = list(chain(*list(self.board.get_half_board(False).values())))
        bottom_board_cards = list(chain(*list(self.board.get_half_board(True).values())))

        top_board_card_vectors = np.array([
            card.get_card_vector() for card in top_board_cards
        ], dtype=np.uint8).flatten()

        bot_board_card_vectors = np.array([
            card.get_card_vector() for card in bottom_board_cards
        ], dtype=np.uint8).flatten()

        hand = np.array([
            card.get_card_vector() for card in self.board.get_hand(True)
        ], dtype=np.uint8).flatten()
        row_scores = np.array(
            [score for row, score in self.board.get_row_scores(True).items()]+
            [score for row, score in self.board.get_row_scores(False).items()]
        ).flatten()
        #graveyard = np.concatenate(self.board.get_graveyard(False).flatten())
        skip = 0
        state[skip:len(bot_board_card_vectors)] = bot_board_card_vectors
        skip += 114 # 38 * card vector of 3
        state[skip:skip+len(top_board_card_vectors)] = top_board_card_vectors
        skip += 114 # 38 * card vector of 3
        state[skip:skip+len(hand)] = hand
        skip += 114 # 38 * card vector of 3
        state[skip:skip+len(row_scores)] = row_scores
        state[-4] = action 
        state[-3] = self.board.round_number             # 462
        state[-2] = self.board.get_rounds_won(True)     # 463
        state[-1] = self.board.get_rounds_won(False)    # 464

        self._state = state
        return self._state

    def get_coin_flip(self):
        """Determine whether the first player starts by coin flip (True) or fixed order (False).
    
        Returns:
        bool: True if the coin flip determines the starting player, False otherwise."""
        return bool(random.getrandbits(1))

    def close(self):
        self.display.stop_render()
    #####################################################################################################
    def get_reward(self, is_bottom_player=True):
        """
        Enhanced reward function for a DQN agent, incorporating strategic depth and dynamic rewarding.
        """
        reward = 0.0

        game_ended = self.board.game_ended()
        winners = self.board.get_winner()
        round_winner = self.board.get_round_winner()
        player_won_rows, opponent_won_rows = self.board.get_won_rows() if is_bottom_player else reversed(self.board.get_won_rows())
        row_difference = player_won_rows - opponent_won_rows
        # Standardize rewards to encourage both immediate and strategic play
        base_win_reward = 1.0
        base_loss_penalty = -1.0

        # Calculate the difference in rounds won between the player and the opponent
        rounds_won_difference = self.board.get_rounds_won(is_bottom_player) - self.board.get_rounds_won(not is_bottom_player)

        # Reward/Penalty for round outcomes
        if rounds_won_difference > 0:
            reward += base_win_reward * rounds_won_difference
        elif rounds_won_difference < 0:
            reward += base_loss_penalty * rounds_won_difference

        # Major reward for winning the game, encouraging the agent to aim for a win
        if self.board.get_rounds_won(is_bottom_player) >= 2:
            reward += 5.0  # Substantial reward for winning the game

        # Adjust rewards based on strategic passing
        if self.board.has_passed(is_bottom_player):
            passed_penalty = -0.5  # Penalize less for strategic passing
            reward += passed_penalty

        # Incorporate a decay factor for future rewards to promote strategic thinking
        gamma = 0.9  # Decay factor for future rewards
        future_rewards_estimate = self.estimate_future_rewards(is_bottom_player) * gamma
        reward += future_rewards_estimate

        # Normalize reward to be within a specific range to maintain consistency
        #max_possible_reward = 10.0
        #reward = max(min(reward, max_possible_reward), -max_possible_reward)

        # Update the player's accumulated rewards
        self.rewards[is_bottom_player] += reward
        return reward

    def estimate_future_rewards(self, player):
        # Heuristic-based future reward estimation
        
        # Example heuristic: Balance between aggression and defense based on the current state
        aggression_factor = 3  # Reward more aggressive play slightly
        defense_factor = 5 # Reward defensive play to a lesser extent

        # Calculate the current advantage or disadvantage in terms of rounds won
        rounds_advantage = self.board.get_rounds_won(player) - self.board.get_rounds_won(not player)

        # Adjust the future reward estimation based on the player's current position
        if rounds_advantage > 0:
            # Player is leading: encourage maintaining or extending the lead (defensive strategy)
            future_reward_estimation = rounds_advantage * self.rounds_in_advantage
            self.rounds_in_advantage += 1
        elif rounds_advantage < 0:
            # Player is trailing: encourage catching up or overtaking (aggressive strategy)
            future_reward_estimation = rounds_advantage * 2
            self.rounds_in_advantage = 0
        else:
            # No clear advantage: neutral encouragement for both aggression and defense
            future_reward_estimation = 0.0

        # Example adjustment based on additional game state considerations
        # If the opponent has passed and the player has a winning hand, increase the future reward estimation
        #if self.board.has_passed(not player) and not self.board.has_passed(player):
        #    future_reward_estimation += rounds_advantage*self.rounds_in_advantage

        return future_reward_estimation