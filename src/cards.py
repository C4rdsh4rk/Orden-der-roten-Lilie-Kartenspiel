from abc import ABC, abstractmethod
import random
from enum import Enum
from src.row import Row
from src.utils import get_index

class CardName(Enum):
    KNIGHT = 0
    CLERIC = 1
    HEALER = 2
    HERO = 3
    DRAW1 = 4
    DRAW2 = 5
    BURN = 6
    SUMMON = 7
    REVIVE = 8

class Card:  
    def __init__(self, name: CardName, strength: int, row_restriction=Row | None):
        self.name = name
        self.type = row_restriction
        self.strength = strength
    
    def get_card_vector(self):
        return self.strength, self.type.value, CardName[self.name].value

    def __str__(self):
        return f"{self.name} (Str: {self.strength}, Row: {self.type})"

class EffectCard(Card, ABC):
    def __init__(self, name: CardName, strength: int, row_restriction=Row | None):
        super().__init__(name, strength, row_restriction)

    @abstractmethod
    def execute_effect(self, env) -> None:
        """
        Method to resolve the effect of an effect card

        Args:
            env (Board): receives the board to do any kind of effect on it

        Raises:
            NotImplementedError: Abstract method
        """
        raise NotImplementedError
    
    #def get_card_vector(self):
        #return 1, 4, self.name

class DrawCard(EffectCard):
    def __init__(self, name, num_cards):
        super().__init__(name, num_cards, Row.EFFECTS)
        self.num_card = num_cards

    def execute_effect(self, env, bottom_player) -> None:
        safe_n_cards = min(len(env.get_deck(bottom_player)), self.num_card)
        env.draw_cards_to_hand(bottom_player, num_cards=safe_n_cards)

class Burn(EffectCard):
    def __init__(self, name):
        super().__init__(name, 1, Row.EFFECTS)
        self.name = name
    
    def execute_effect(self, env, bottom_player) -> None:
        half_board = env.get_half_board(not bottom_player)
        targets = [
            (str(card), row, i) for row in half_board.keys() for i, card in enumerate(half_board[row])
        ]
        target_index = get_index("Which card do you want to burn?", [card_info[0] for card_info in targets], "Burn Effect")
        _, row, card_row_index = targets[target_index]
        env.remove_card_from_board(not bottom_player, card_row_index, row)

class Summon(EffectCard):
    def __init__(self, name):
        super().__init__(name, 1, Row.WISE)
        self.name = name
    
    def execute_effect(self, env, bottom_player) -> None:
        if len(env.get_deck(bottom_player)) < 1:
            return
        
        env.draw_cards_to_hand(bottom_player, num_cards=1)
        card_index = len(env.get_hand(bottom_player)) - 1
        card_row = env.get_hand(bottom_player)[-1].type
        env.play_card(bottom_player, card_index, card_row)

class Revive(EffectCard):
    def __init__(self, name):
        super().__init__(name, 1, Row.WISE)
        self.name = name
    
    def execute_effect(self, env, bottom_player) -> None:
        graveyard = env.get_graveyard(bottom_player)
        if len(graveyard) < 1:
            return
        env.draw_cards_from_graveyard(bottom_player, num_cards=1)
        card_index = len(env.get_hand(bottom_player)) - 1
        card_row = env.get_hand(bottom_player)[-1].type
        env.play_card(bottom_player, card_index, card_row)

class Booster:
    def __init__(self):
        self.available_strength = [1,2,3,4,5]
        self.available_cards_weights = [0.3, 0.3, 0.3, 0.05, 0.05] # Probabilities
        self.strength_weights = [0.35, 0.25, 0.2, 0.15, 0.05] # Probabilities
        self.available_effects = [
            #DrawCard("DRAW2", 2),
            #Burn("BURN")
        ]
        self.available_cards = [
                            Card("KNIGHT", random.choices(self.available_strength, self.strength_weights)[0], Row.FRONT),
                            Card("CLERIC", random.choices(self.available_strength, self.strength_weights)[0], Row.WISE),
                            Card("HEALER", random.choices(self.available_strength, self.strength_weights)[0], Row.SUPPORT),
                            Card("HERO", random.choices(self.available_strength, self.strength_weights)[0], Row.ANY), # Can be played in any row
                            random.choice(self.available_effects)
                            ]

    def open(self,size):
        return random.choices(self.available_cards, self.available_cards_weights, k=size)
    
class Starter:
    def __init__(self):
        self.available_effects = [
            #Burn("BURN"),
            Revive("REVIVE"),
            Summon("SUMMON")
        ]
        self.defined_deck = []

        strenghts = [1,2,2,3,4]
        #strenghts = [2, 3, 4]
        self.defined_deck.append(Revive("REVIVE"))
        self.defined_deck.append(Summon("SUMMON"))
        for strength  in strenghts:
            self.defined_deck.append(Card("KNIGHT", strength, Row.FRONT))
            self.defined_deck.append(Card("CLERIC", strength, Row.WISE))
            self.defined_deck.append(Card("HEALER", strength, Row.SUPPORT))
        self.defined_deck.append(random.choice(self.available_effects))
        self.defined_deck.append(random.choice(self.available_effects))
        self.defined_deck.append(Card("HERO", 5, Row.ANY))


    def open(self):
        return self.defined_deck