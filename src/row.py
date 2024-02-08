from enum import Enum


class Row(Enum):
    FRONT = 1#"FRONT"
    WISE = 2#"WISE"
    SUPPORT = 3#"SUPPORT"
    EFFECTS = 4#"EFFECTS"
    ANY = 5#"ANY"

def row_sort_order(row_card_tuple: tuple):
        """
        Determines the sorting order for cards in a row.

        Args:
            row_card_tuple (tuple): A tuple containing a row identifier and its associated card.

        Returns:
            int: A numeric value representing the sort order based on the row type.
        """
        row, _ = row_card_tuple

        if row == Row.SUPPORT:
            return 3
        elif row == Row.WISE:
            return 2
        elif row == Row.FRONT:
            return 1
        return 0
