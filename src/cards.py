from abc import ABC, abstractmethod
import random
from enum import Enum
from src.row import Row


class CardName(Enum):
    KNIGHT = 0
    CLERIC = 1
    HEALER = 2
    HERO = 3
    DRAW1 = 4
    DRAW2 = 5


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


class DrawCard(EffectCard):
    def __init__(self, name, num_cards):
        super().__init__(name, num_cards, None)
        self.num_card = num_cards

    def execute_effect(self, env) -> None:
        current_player = env.get_current_player()
        safe_n_cards = min(len(env.get_deck(current_player)), self.num_card)
        env.draw_cards_to_hand(env.turn_player, num_cards=safe_n_cards)


class Booster:
    def __init__(self):
        self.available_strength = [1,2,3,4,5]
        self.available_cards_weights = [0.3, 0.3, 0.3, 0.05, 0.05] # Probabilities
        self.strength_weights = [0.35, 0.25, 0.2, 0.15, 0.05] # Probabilities
        self.available_effects = [
            DrawCard("DRAW1", 1),
            DrawCard("DRAW2", 2)
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