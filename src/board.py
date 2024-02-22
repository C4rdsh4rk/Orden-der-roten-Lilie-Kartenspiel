"""Module that provides the Board class for the state and interaction with the environment"""
import random
from itertools import chain
# local imports
from src.row import Row
from src.cards import Card, EffectCard, Starter


class Board:
    """Represents the game board environment (state) for a card game.

    The purpose of this class is to 
    1. Store the current state of the game
    2. Provide functions to interact with the Board,
    i.e. playing a card, etc.
    """
    def __init__(self, top_player_name: str, bottom_player_name):
        """Initializes the game board with optional network play."""
        # blueprint for clearing the board
        self.half_board = {
            Row.FRONT: [],
            Row.WISE: [],
            Row.SUPPORT: [],
            Row.EFFECTS: []
        }
        # Player attributes
        self.player_states = {
            "top_player":{
                "name": top_player_name,
                "half_board": self.half_board.copy(),
                "passed": False,
                "deck": [],
                "hand": [],
                "graveyard": [],
                "current_rows_won": 0,
                "rounds_won": 0
            },
            "bottom_player":{
                "name": bottom_player_name,
                "half_board": self.half_board.copy(),
                "passed": False,
                "deck": [],
                "hand": [],
                "graveyard": [],
                "current_rows_won": 0,
                "rounds_won": 0
            }
        }
        # start with round 1
        self.round_number = 1
        #self.done = False
        # indicates which players turn it is
        self.turn_player = ""
        # Setup for game
        self.clear_deck()  # Generate empty player decks
        self.clear_hands() # Generate empty player hands
        self.round_number = 1

    def reset(self) -> None:
        # Player attributes
        self.player_states = {
            "top_player":{
                "name": self.get_player_name(False),
                "half_board": self.half_board.copy(),
                "passed": False,
                "deck": [],
                "hand": [],
                "graveyard": [],
                "current_rows_won": 0,
                "rounds_won": 0
            },
            "bottom_player":{
                "name": self.get_player_name(True),
                "half_board": self.half_board.copy(),
                "passed": False,
                "deck": [],
                "hand": [],
                "graveyard": [],
                "current_rows_won": 0,
                "rounds_won": 0
            }
        }
        # start with round 1
        self.round_number = 1
        self.done = False
        # indicates which players turn it is
        self.turn_player = ""
        # Setup for game
        self.clear_deck()  # Generate empty player decks
        self.clear_hands() # Generate empty player hands

    def _get_player_identifier(self, bottom_player: bool) -> str:
        """
        Method to get the internal identifier of a player

        Args:
            bottom_player (bool): If bottom player, identifier of bottom player will be returned.

        Returns:
            str: player identifier
        """
        if bottom_player:
            return "bottom_player"
        return "top_player"

    def clear_deck(self) -> None:
        """Clears the game board"""
        self.player_states["top_player"]["deck"] = []
        self.player_states["bottom_player"]["deck"] = []

    def clear_hands(self) -> None:
        """Clears the hands"""
        self.player_states["top_player"]["hand"] = []
        self.player_states["bottom_player"]["hand"] = []

    def set_deck(self, bottom_player: bool, deck: list[Card]) -> None:
        """
        Method to set the deck of a player. If bottom player is true,
        the deck of the bottom player will be set, otherwise the deck
        of the top player will be set

        Args:
            deck (list[Card]): _description_
            bottom_player (bool): _description_
        """
        player_identifier = self._get_player_identifier(bottom_player)
        self.player_states[player_identifier]["deck"] = deck

    def get_deck(self, bottom_player: bool):
        """
        Method to get the deck of a player. If bottom player the deck of
        the bottom player will be returned, otherwise the deck of the
        top player will be returned

        Args:
            bottom_player (bool): Indicate which players deck to get. True for bottom players deck
        """
        player_identifier = self._get_player_identifier(bottom_player)
        return self.player_states[player_identifier]["deck"]

    def get_graveyard(self, bottom_player: bool):
        """
        Method to get the graveyard of a player. If bottom player the graveyard of
        the bottom player will be returned, otherwise the graveyard of the
        top player will be returned

        Args:
            bottom_player (bool): Indicate which players graveyard to get. True for bottom players deck
        """
        player_identifier = self._get_player_identifier(bottom_player)
        return self.player_states[player_identifier]["graveyard"]

    def set_graveyard(self, bottom_player: bool, graveyard: list[Card]) -> None:
        """
        Method to set the graveyard of a player. If bottom player the graveyard of
        the bottom player will be returned, otherwise the graveyard of the
        top player will be returned

        Args:
            bottom_player (bool): Indicate which players graveyard to get. True for bottom players deck
        """
        player_identifier = self._get_player_identifier(bottom_player)
        self.player_states[player_identifier]["graveyard"] = graveyard

    def get_rounds_won(self, bottom_player: bool) -> None:
        """
        Method to get the rounds won of a player. 

        Args:
            bottom_player (bool): Indicate which players score to get. True for bottom players deck
        """
        player_identifier = self._get_player_identifier(bottom_player)
        return self.player_states[player_identifier]["rounds_won"]

    def get_player_name(self, bottom_player: bool) -> str:
        """
        Method to get the name of a player

        Args:
            bottom_player (bool): Indicates if name of bottom or top player is returned

        Returns:
            str: name of the player
        """
        player_identifier = self._get_player_identifier(bottom_player)
        return self.player_states[player_identifier]["name"]

    def get_hand(self, bottom_player: bool) -> list[Card]:
        """
        Method to get the hand of a player

        Args:
            bottom_player (bool): Indicates if hand of bottom or top player is returned

        Returns:
            list[Card]: Hand of the player
        """
        player_identifier = self._get_player_identifier(bottom_player)
        return self.player_states[player_identifier]["hand"]

    def set_hand(self, bottom_player: bool, hand: list[Card]) -> None:
        """
        Method to get the hand of a player

        Args:
            bottom_player (bool): Indicates if hand of bottom or top player is returned

        Returns:
            list[Card]: Hand of the player
        """
        player_identifier = self._get_player_identifier(bottom_player)
        self.player_states[player_identifier]["hand"] = hand

    def get_half_board(self, bottom_player: bool) -> dict[Row, list]:
        """
        Method to get the board of a player.

        Args:
            bottom_player (bool): 

        Returns:
            dict[Row, list]: Row: [Cards] dict
        """
        player_identifier = self._get_player_identifier(bottom_player)
        return self.player_states[player_identifier]["half_board"]

    def get_valid_choices(self, bottom_player: bool) -> list[int]:
        """
        Returns the possible **cards indices** for the cards the player can play.

        Args:
            bottom_player (bool): If true bottom player choice will be returned,
            otherwise top players

        Returns:
            list[int]: _description_
        """
        valid_choices = list(range(len(self.get_hand(bottom_player))))
        return valid_choices

    def draw_cards_to_hand(self, bottom_player: bool, num_cards=2, shuffle=False) -> None:
        """Allows a player to draw a specified number of cards into their hand.
        Args:
            bottom_player: The player who will draw cards.
            num_cards (int, optional): The number of cards to draw. Defaults to 2.
            shuffle (boolean, optional)
        """
        actually_drawn = min(len(self.get_deck(bottom_player)), num_cards)
        if shuffle:
            random.shuffle(self.get_deck(bottom_player))
            #self.set_deck(bottom_player, )
        # Draw cards from the deck
        self.set_hand(bottom_player, self.get_hand(bottom_player) + self.get_deck(bottom_player)[:actually_drawn])
        # Remove drawn cards from the deck
        self.set_deck(bottom_player, self.get_deck(bottom_player)[actually_drawn:])
    
    def draw_cards_from_graveyard(self, bottom_player: bool, num_cards=1) -> None:
        """Allows a player to draw a specified number of cards into their hand from the graveyard.
        Args:
            bottom_player: The player who will draw cards.
            num_cards (int, optional): The number of cards to draw. Defaults to 2.
        """
        actually_drawn = min(len(self.get_graveyard(bottom_player)), num_cards)
        self.set_hand(bottom_player, self.get_hand(bottom_player) + self.get_graveyard(bottom_player)[:actually_drawn])
        # Remove drawn cards from the deck
        self.set_graveyard(bottom_player, self.get_graveyard(bottom_player)[actually_drawn:])
        
    def draw_card_from_board(self, bottom_player: bool, card_row_index: int, row: Row) -> None:
        """Allows a player to draw a specified card back to their hand from the board.
        Args:
            bottom_player: The player who will draw cards.
            row
            card_row_index
        """
        self.set_hand(bottom_player, self.get_hand(bottom_player).append(self.get_half_board(bottom_player)[row][card_row_index]))
        # Remove drawn cards from the board
        self.remove_card_from_board(bottom_player, card_row_index, row)

    def play_card(self, bottom_player, card_index, row) -> None:
        """
        Method to play a card. Updates player states accordingly.

        Args:
            player (str): identifier of the player
            card (int): index of the card that is played (index in hand)
            row (Row): row in which the card is played
        """
        if row==Row.ANY:
            row = random.choice([
                        Row.FRONT,
                        Row.WISE,
                        Row.SUPPORT])

        played_card = self.get_hand(bottom_player)[card_index]
        # special case if effect card
        if isinstance(played_card, EffectCard):
            played_card.execute_effect(self, bottom_player)
        if played_card.type != Row.EFFECTS:
            # **PLEASE LEAVE AS IS, is using += the function adds cards to both boards (dont know why 0_o)
            # add it to the players board
            row_cards = self.player_states[self._get_player_identifier(bottom_player)]["half_board"][row]
            self.player_states[self._get_player_identifier(bottom_player)]["half_board"][row] = row_cards + [played_card]
        # remove card from hand
        self.set_hand(bottom_player, self.get_hand(bottom_player)[:card_index] + self.get_hand(bottom_player)[card_index+1:])

        top_player_won_rows, bottom_player_won_rows = self.get_won_rows()
        self.player_states["top_player"]["current_rows_won"] = top_player_won_rows
        self.player_states["bottom_player"]["current_rows_won"] = bottom_player_won_rows

    def pass_round(self, bottom_player: bool) -> None:
        """
        Method to pass a round. Players passing state will be set to true.

        Args:
            bottom_player (bool): Set for bottom or top player
        """
        player_identifier = self._get_player_identifier(bottom_player)
        self.player_states[player_identifier]["passed"] = True

    def end_round(self):
        """
        Method to handle the end of a round. Updates the round won scores,
        moves cards from the board into the graveyard and updates the round number
        and resets the passing states of the players.
        Drawing cards for the next round has to be handled outside of this class.
        """
        for bottom_player in [True, False]:
            player = self._get_player_identifier(bottom_player)
            opponent = self._get_player_identifier(not bottom_player)
            # update round scores
            if self.player_states[player]["current_rows_won"] >= self.player_states[opponent]["current_rows_won"]:
                self.player_states[player]["rounds_won"] += 1
        
        for bottom_player in [True, False]:
            player = self._get_player_identifier(bottom_player)   
            # update graveyard
            self.player_states[player]["graveyard"] = list(chain(*self.player_states[player]["half_board"].values()))
            # reset board
            self.player_states[player]["half_board"] = self.half_board.copy()
            # reset rows won
            self.player_states[player]["current_rows_won"] = 0
            # reset passed state
            self.player_states[player]["passed"] = False
        # update round ticker
        self.round_number += 1

    def game_ended(self) -> bool:
        """
        Method to check if the game is finished

        Returns:
            bool: True is game is finished
        """
        top_player_won = self.player_states[self._get_player_identifier(False)]["rounds_won"] >= 2
        bottom_player_won = self.player_states[self._get_player_identifier(True)]["rounds_won"] >= 2
        return self.round_number >= 4 or top_player_won or bottom_player_won

    def get_row_score(self, bottom_player: bool, row: Row) -> int:
        """
        Method to get the score for one row of a player. The return will be a single int
        
        Args:
            bottom_player (bool): Indicates if scores for bottom (otherwise top) player should be
            returned
            row (Row): Row for which the score is requested

        Returns:
            int: score of the row
        """
        player_identifier = self._get_player_identifier(bottom_player)
        return sum(
            card.strength for card in self.player_states[player_identifier]["half_board"][row]
        )

    def get_row_scores(self, bottom_player: bool) -> dict[Row, int]:
        """
        Gets the score for each row based on the current cards in play.

        Args:
            bottom_player(bool): If true returns scores of bottom player, top players otherwise

        Returns:
            tuple[dict, dict]: dict that contains rows as keys and int scores as values,
            indicating the row score
        """
        field_rows = [row for row in self.half_board.keys() if row != Row.EFFECTS]
        row_scores = {row: self.get_row_score(bottom_player, row) for row in field_rows}
        return row_scores

    def get_won_rows(self) -> tuple[int, int]:
        """
        Method to get the number of won rows for each player.
        The first value in the return is the top player, the second is the
        score for the bottom player

        Returns:
            tuple[int, int]: Number of won rows for each player. (top_player, bottom_player)
        """
        top_score = 0
        bottom_score = 0

        scores_top = self.get_row_scores(False)
        scores_bottom = self.get_row_scores(True)
        for row in scores_top.keys():
            # only add scores that are non empty
            if scores_bottom[row] == scores_top[row] and scores_bottom[row]==0:
                continue
            top_score += int(scores_top[row] >= scores_bottom[row])
            bottom_score += int(scores_top[row] <= scores_bottom[row])

        return top_score, bottom_score
    
    def get_winner(self) -> list[bool]:
        """
        Determines and the winner of the game based on the final scores.

        Returns:
            List[bool]: list of winning players (top, bottom) where True indicates a win
        """
        winners = [False, False]
        rounds_top_player_won = self.player_states["top_player"]["rounds_won"]
        rounds_bottom_player_won = self.player_states["bottom_player"]["rounds_won"]

        winners[0] = (rounds_top_player_won >= rounds_bottom_player_won)
        winners[1] = (rounds_top_player_won <= rounds_bottom_player_won)
        return winners

    def get_round_winner(self) -> list[str]:
        """
        Determines and the winner of the game based on the scores after one round.

        Returns:
            List[str]: list of winning players names (could be one or two, if draw)
        """
        winner = []
        rows_top_player_won, rows_bottom_player_won = self.get_won_rows()

        if rows_top_player_won >= rows_bottom_player_won:
            winner += [self.get_player_name(False)]
        if rows_top_player_won <= rows_bottom_player_won:
            winner += [self.get_player_name(True)]
        return winner

    def has_passed(self, bottom_player: bool) -> bool:
        """
        Method to check if a player has passed.

        Args:
            bottom_player (bool): If True, checks the bottom player, top player otherwise

        Returns:
            bool: True if the given player has passed the round
        """
        player_identifier = self._get_player_identifier(bottom_player)
        return self.player_states[player_identifier]["passed"]

    def remove_card_from_board(self, bottom_player: bool, card_row_index: int, row: Row):
        # remove card from board
        player_identifier = self._get_player_identifier(bottom_player)
        self.player_states[player_identifier]["half_board"][row] = self.get_half_board(bottom_player)[row][: card_row_index] + self.get_half_board(bottom_player)[row][card_row_index+1:]

# Example usage
if __name__ == '__main__':
    # small testing
    board = Board(top_player_name="Hungriger", bottom_player_name="Hugo")
    bottom_player = False
    assert "Hungriger" == board.get_player_name(bottom_player)

    board.reset()
    board.clear_deck()
    board.clear_hands()

    board.set_deck(bottom_player, Starter().open(20))
    x = len(board.get_deck(bottom_player))
    assert len(board.get_deck(bottom_player)) == 20

    board.draw_cards_to_hand(bottom_player, 5, True)

    assert len(board.get_deck(bottom_player)) == 15
    assert len(board.get_valid_choices(bottom_player)) == 5
    board.play_card(False, 0, Row.FRONT)
    assert len(board.player_states["top_player"]["half_board"][Row.FRONT]) == 1
    assert len(board.player_states["bottom_player"]["half_board"][Row.FRONT]) == 0
    #board.player_states["top_player"]["half_board"]
    board.reset()
    board.set_deck(bottom_player, [Card("KNIGHT", 10, Row.FRONT)])

    board.draw_cards_to_hand(bottom_player, 2)
    board.play_card(bottom_player, 0 , Row.FRONT)

    if not board.has_passed(bottom_player):
        board.pass_round(bottom_player)
    assert board.has_passed(bottom_player) is True

    assert board.get_row_score(bottom_player, Row.FRONT) == board.get_row_scores(bottom_player)[Row.FRONT]
    assert board.get_row_scores(bottom_player)[Row.FRONT] == 10

    assert board.get_won_rows()
    assert board.get_won_rows()

    p_t, p_b = board.get_won_rows()
    assert p_t == 1
    assert p_b == 0

    board.end_round()
    assert len(board.get_graveyard(bottom_player)) == 1
    assert len(board.get_hand(bottom_player)) == 0

    board.player_states["top_player"]["rounds_won"] = 2
    board.player_states["bottom_player"]["rounds_won"] = 1
    if board.game_ended():
        winner = board.get_winner()
        assert len(winner) == 2 and winner[0] == True and winner[1] == False
