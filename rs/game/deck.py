from typing import List

from rs.calculator.enums.card_id import CardId
from rs.game.card import Card, CardType, card_id_to_name, compact_card_name


class Deck:
    def __init__(self, json):
        self.cards: List[Card] = list(map(lambda card: Card(card), json))

    def contains_type(self, type: CardType) -> bool:
        for card in self.cards:
            if card.type == type:
                return True
        return False

    def contains_curses_of_any_kind(self) -> bool:
        for card in self.cards:
            if card.type == CardType.CURSE:
                return True
        return False

    def contains_curses_we_can_remove(self) -> bool:
        for card in self.cards:
            if card.type == CardType.CURSE and not \
                    card.id.lower() == "curseofthebell" and not \
                    card.id.lower() == "necronomicurse" and not \
                    card.id.lower() == "ascender\u0027sbane":
                return True
        return False

    def contains_cards(self, names: List[str]) -> bool:
        names = [compact_card_name(element) for element in names]
        for card in self.cards:
            # Use card id (always English) instead of name (may be localized).
            if compact_card_name(card_id_to_name(card.id)) in names:
                return True
        return False

    def contains_card_amount(self, card_name) -> int:
        # note that upgrades include "+" at the end of the name!
        amount = 0
        cmp = card_name.lower()
        want_upgraded = cmp.endswith('+')
        cmp_base = compact_card_name(cmp.rstrip('+'))
        for c in self.cards:
            # Use card id (always English) instead of name (may be localized).
            base_id = compact_card_name(card_id_to_name(c.id))
            is_upgraded = c.upgrades > 0
            if base_id == cmp_base and is_upgraded == want_upgraded:
                amount += 1
        return amount

    def get_card_index(self, id: str) -> int:
        for i in range(len(self.cards)):
            if self.cards[i].id == id:
                return i
        return -1
