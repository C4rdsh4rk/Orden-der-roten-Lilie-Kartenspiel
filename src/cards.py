from abc import ABC
import random
from colorama import Fore
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
    def __init__(self, name, strength, row_restriction=None):
        self.name = name
        self.type = row_restriction
        self.strength = strength
    
    def get_card_vector(self):
        return self.strength, self.type.value, CardName[self.name].value

    def __str__(self):
        return f"{self.name} (Str: {self.strength}, Row: {self.type})"


class EffectCard(Card, ABC):
    def execute_effect(self, player, opponent) -> None:
        raise NotImplementedError


class DrawCard(EffectCard):
    def __init__(self, name, num_cards):
        super().__init__(name, num_cards, None, "white")
        self.num_card = num_cards

    def execute_effect(self, env) -> None:
        player.draw_hand(min(len(player.deck), self.num_card))


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
                            Card("KNIGHT", random.choices(self.available_strength,self.strength_weights)[0], Row.FRONT, color="red"),
                            Card("CLERIC", random.choices(self.available_strength,self.strength_weights)[0], Row.WISE, color="white"),
                            Card("HEALER", random.choices(self.available_strength,self.strength_weights)[0], Row.SUPPORT, color="green"),
                            Card("HERO", random.choices(self.available_strength,self.strength_weights)[0], Row.ANY, color="yellow"), # Can be played in any row
                            random.choice(self.available_effects)
                            ]
        
    def open(self,size):
        return random.choices(self.available_cards, self.available_cards_weights, k=size)