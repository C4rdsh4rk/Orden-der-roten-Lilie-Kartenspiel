import time
from rich import style
from rich import print as rprint
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from src.row import Row
from rich.console import Group
from rich.columns import Columns
from rich.prompt import Prompt
from rich.console import Console

# needed for input
import getchlib

from src.cards import Booster, Card


def row_sort_order(row_card_tuple: tuple):
        row, _ = row_card_tuple

        if row == Row.SUPPORT:
            return 3
        elif row == Row.WISE:
            return 2
        elif row == Row.FRONT:
            return 1
        return 0


class CardTable:
    def __init__(self, player_side_size=19) -> None:
        self.current_message = ""
        self.row_colors = {
            Row.FRONT: {
                "color": "white",
                "bgcolor": "dark_red"
            },
            Row.WISE: {
                "color": "white",
                "bgcolor": "bright_black"
            },
            Row.SUPPORT: {
                "color": "white",
                "bgcolor": "dark_green"
            },
            Row.ANY: {
                "color": "yellow",
                "bgcolor": "black"
            },
            Row.EFFECTS: {
                "color": "yellow",
                "bgcolor": "black"
            }
        }
        # value for the board if there are no cards
        self.empty_value = "\n".join([" "*8]*5)
        # size of the side of one player (static)
        self.player_side_size = player_side_size

        self.layout = Layout()
        self.layout.split_column(
            Layout(name="board_view", size=self.player_side_size*2),
            Layout(Panel(Text("Test")), name="prompt_view", size=4)
        )
        self.layout["board_view"].split_row(
            Layout(name="player_info", size=22),
            Layout(name="board"),
            Layout(name="right", size=22)
        )
        self._setup_hand()
        self._setup_player_info()
        self._setup_board()
        self.live = Live(self.layout, refresh_per_second=4)

    def _setup_board(self):
        self.layout["board_view"]["board"].split_column(
            Layout(
                self._get_table(
                    [(Row.FRONT, []), (Row.SUPPORT, []), (Row.WISE, [])],
                    False
                ),
                name="top_player",
                size=self.player_side_size
            ),
            Layout(
                self._get_table(
                    [(Row.FRONT, []), (Row.SUPPORT, []), (Row.WISE, [])],
                    True
                ),
                name="bottom_player",
                size=self.player_side_size
            )
        )

    def _setup_player_info(self):
        self.layout["board_view"]["player_info"].split_column(
            Layout(
                name="top_player",
                size=self.player_side_size
            ),
            Layout(
                name="bottom_player",
                size=self.player_side_size
            )
        )
        self.set_player_info("", 0, 0, "No move", 0, 0, True)
        self.set_player_info("", 0, 0, "No move", 0, 0, False)

    def _setup_hand(self):
        self.layout["board_view"]["right"].split_column(
            Layout(
                name="top_player",
                size=4
            ),
            Layout(
                name="bottom_player",
                size=self.player_side_size*2-6-1),
        )
        self.update_card_hand([], True)
        self.update_card_hand([], False)
    
    def _get_table(self, row_cards: list[tuple], bottom: bool) -> Table:
        """Method to generate a rich table for a player (bottom or top).
        The cards must be passed as a list of tuples, where the first value contains the row and
        the second value is a list with the cards in this row. Bottom indicates if the
        player is the bottom player, i.e. if the table should have the red row
        on top

        Args:
            row_cards (dict): row: cards dictionary
            bottom (bool): if True the first row will be the meele row, reversed otherwise

        Returns:
            Table: table containing the given cards
        """
        player_table = Table(show_lines=True, show_header=False, expand=True)
        player_table.add_column("Row type indicator", justify="left", vertical="center")
        player_table.add_column("Effects", justify="left")
        player_table.add_column("Normal Cards", justify="center", ratio=1)
        # add rows
        row_cards.sort(key=row_sort_order, reverse=not bottom)
        for row, cards in row_cards:
            if row == Row.EFFECTS:
                continue
            color = self.row_colors[row]["color"]
            bgcolor = self.row_colors[row]["bgcolor"]
            row_score = sum(card.strength for card in cards)

            card_group = self.empty_value
            if cards:
                card_group = Columns(
                    [
                        Panel(
                            Text(
                                f"{card.name}\n{card.strength}",
                                justify="center",
                                style=style.Style(color=self.row_colors[card.type]["color"])),
                                width=10
                            )
                        for card in cards
                    ]
                )
            player_table.add_row(
                Text(f"\n   \n {row_score} \n   \n", style=style.Style(color=color, bgcolor=bgcolor, bold=True)),
                self.empty_value,
                card_group
            )
        return player_table

    def write_message(self, message) -> None:
        self.current_message = message
        self.layout["prompt_view"].update(
            Panel(Text(message, justify="center", style=style.Style(bold=True)))
        )
    
    def write_sub_message(self, sub_message) -> None:
        self.layout["prompt_view"].update(
            Panel(Text(f"{self.current_message}\n{sub_message}", justify="center", style=style.Style(bold=True)))
        )

    def ask_prompt(self, prompt: str, choices) -> str:
        self.write_message(prompt + ":")
        run_once = False  # we need this if we want the empty input. In that case we have to run the inner loop once
        key = ""
        add = ""
        while key not in choices or not run_once:
            run_once = True
            while True:
                # the ' character has to be replaced due to a bug in the getchlib library (which returns "'character'" on windows instead of "character")
                add = getchlib.getkey().replace("'", "") #Prompt.ask(prompt=prompt, choices=choices, console=self.layout["prompt_view"])
                if add == "\x7f" or add == "\\x08":  # this is the delete button
                    key = key[:-1]
                elif add == "\n" or add == "\\r":
                    break
                elif add == "\\x03":  # add keyboard interrupt for windoof
                    raise KeyboardInterrupt()
                else:
                    key += add
                self.write_message(f"{prompt}: {key}")
            if key not in choices:
                self.write_sub_message("The input was invalid!")
                key = ""
        return key

    
    def set_player_cards(self, row_cards: list[tuple], bottom: bool) -> None:
        if bottom:
            self.layout["board_view"]["board"]["bottom_player"].update(
                self._get_table(row_cards, True)
            )
        else:
            self.layout["board_view"]["board"]["top_player"].update(
                self._get_table(row_cards, False)
            )

    def update_card_hand(self, cards, bottom_player: bool):
            # update the card count on the opponents hand
            if not bottom_player:
                self.layout["board_view"]["right"]["top_player"].update(
                    Panel(
                        Text(f"Enemy Hand\n{len(cards)}", justify="center")
                    )
                )
                return
            # update the hand of the player
            hand_table = Table(title="Your Hand", width=22)
            hand_table.add_column("Card", justify="left", ratio=1)
            hand_table.add_column("Str")
            for i, card in enumerate(cards):
                padding = " " if i<9 else ""
                card_name = Text(f"[{i+1}]{padding}{card.name}")
                card_name.stylize(f"bold {self.row_colors[card.type]}")  # card.color

                card_strength = Text(f"{card.strength}")
                card_strength.stylize(f"bold {self.row_colors[card.type]}")# card.color

                hand_table.add_row(card_name, card_strength)
            self.layout["board_view"]["right"]["bottom_player"].update(
                hand_table
            )
    
    def set_player_info(
            self,
            player_name: str,
            stack_cards: int,
            graveyard_cards: int,
            last_move: str,
            rows_won: int,
            rounds_won: int,
            bottom_player: bool
        ) -> None:
        player = "top_player" if not bottom_player else "bottom_player"
        # change vertical padding depending on player
        additional_padding_after = "\n"*int(bottom_player)
        info = [
            Panel(Text(f"Stack\n {stack_cards}", justify="center")),
            Panel(Text(f"Graveyard\n{graveyard_cards}", justify="center")),
            Panel(Text(f"Last move:\n{last_move}", justify="center")),
            Text(f"\n{player_name}\nWon rows: {rows_won}\nRounds won: {rounds_won}{additional_padding_after}", justify="center")
        ]
        if bottom_player:
            info.reverse()
        self.layout["board_view"]["player_info"][player].update(
            Panel(
                Group(
                    *info
                )
            )
        )
    
    def start_render(self):
        self.live.start()
    
    def stop_render(self):
        self.live.stop()


if __name__ == '__main__':
    ct = CardTable()
    ct.start_render()