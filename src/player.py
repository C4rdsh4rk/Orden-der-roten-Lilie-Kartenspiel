from abc import ABC
import random
from typing import Callable
import numpy as np
import torch
from src.row import Row
from src.utils import get_name
from src.cards import Card
from src.MCTS import PolicyNetwork, MCTS

any_row_choice = {
    1: Row.FRONT,
    2: Row.WISE,
    3: Row.SUPPORT
}
class Player(ABC):
    def __init__(self, name):
        self.name = name

    def make_pass_choice(self, hand) -> bool:
        """
        Function that determines if the player passes
        """
        raise NotImplementedError

    def make_card_choice(self, valid_actions: list, env, action=None) -> Card:
        """
        Interface function that must return exactly one card that is played by the player.
        The card must be in the valid_choices.
        
        Args:
            valid_choices (list[Card]): Possible cards to play
        
        Returns:
            Card: Card that is played"""
        raise NotImplementedError
    
    def make_row_choice(self, card: Card, display) -> Row:
        """
        Interface function that must return exactly one row where the given card should be played in.

        Args: 
            card (Card): Card that is played
        
            Returns:
                Row: the row in which the card should be played
        """
        raise NotImplementedError

class Human(Player):
    def __init__(self, name: str, get_user_input: Callable):
        name = get_name()
        super().__init__(name)
        self.get_user_input = get_user_input

    def make_choice(self, valid_actions, env, action=None):
        valid_actions = [str(x+1) for x in valid_actions] # User friendly numbers
        valid_actions += ["0"]
        if len(valid_actions)==1:
            monkey_input = 0
        else:
            monkey_input = int(self.get_user_input("Choose a card from your hand or pass (with 0)", valid_actions))
        return monkey_input

    def make_row_choice(self, card, row_choices: list[Row]) -> Row:
        monkey_input = self.get_user_input(
            "Chose any row for your card [1-3]",
            [str(row_number+1) for row_number, _ in enumerate(row_choices)]
        )
        return row_choices[int(monkey_input) - 1]

class ArtificialRetardation(Player):
    def __init__(self, name, model=None):
        super().__init__(name)
        self.model = model

    def make_choice(self, valid_actions, env, action=None):
        is_bottom_player = [player for player in env.players if player[2]==self][0][1]
        if self.model and not action:
            action, _states = self.model.predict(env.get_state(is_bottom_player), deterministic=True)
        elif not self.model:
            action = int(random.choice(valid_actions)) # Monke

        if action and action >= len(env.board.get_hand(is_bottom_player))+1: # Check for valid card index
            action = 0
        return action

    def make_row_choice(self, card, row_choices: list[Row]) -> Row:
        return random.choice(list(row_choices))

    def make_pass_choice(self, hand) -> bool:
        if len(hand)==0:
            self.passed = True
        else:
            self.passed = random.choices([False, True],[0.97,0.03],k=1)[0]
        return self.passed

class MCTS_Idiot(Player):
    def __init__(self, name, policy_net: PolicyNetwork):
        super().__init__(name)
        self.policy_net = policy_net
        self.search_depth = 5
        
    def make_choice(self, valid_actions, env, action=None):
        is_bottom_player = [player for player in env.players if player[2]==self][0][1]
        state = env.get_state(is_bottom_player)
        mcts = MCTS(state, self.policy_net, env)
        # Run simulations and update the tree until search depth is reached or game ends
        for _ in range(self.search_depth):
            mcts.simulate()
        action_probs = mcts.get_action_probabilities()
        choice = 41
        while choice not in valid_actions:
            choice = np.random.choice(env.action_space, p=action_probs)
        return choice
