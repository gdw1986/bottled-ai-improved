from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.ai.claw_is_law.config import CARD_REMOVAL_PRIORITY_LIST
from rs.game.screen_type import ScreenType
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class ShopPurchaseHandler(Handler):

    def __init__(self):
        self.relics_to_buy = [
            'Kunai',
            'Shuriken',
            'Ornamental Fan',
            'Preserved Insect',
            'Bag of Marbles',
            'Pen Nib',
            'Orichalcum',
            'Torii',
            'Vajra',
            'Eternal Feather',
            'Meal Ticket',
            'Anchor',
            'Horn Cleat',
        ]

        self.cards_to_buy = [
            "All For One",
            "Gash",
        ]

    def can_handle(self, state: GameState) -> bool:
        return state.screen_type() == ScreenType.SHOP_SCREEN.value

    def handle(self, state: GameState) -> HandlerAction:
        choice = self.find_choice(state)
        if choice:
            idx = state.get_choice_list().index(choice)
            if presentation_mode:
                return HandlerAction(commands=[p_delay, "choose " + str(idx), p_delay_s, "wait 30"])
            return HandlerAction(commands=["choose " + str(idx), "wait 30"])
        if presentation_mode:
            return HandlerAction(commands=["wait " + p_delay, "return", "proceed"])
        return HandlerAction(commands=["return", "proceed"])

    def find_choice(self, state: GameState) -> str:
        gold = state.game_state()['gold']
        screen_state = state.game_state()['screen_state']
        can_purge = screen_state.get('purge_available', False) and gold >= screen_state.get('purge_cost', 999)
        choice_list = state.get_choice_list()

        # 0. Kunai/Shuriken (match by id, always English)
        for relic in screen_state.get('relics', []):
            if relic.get('id') == 'Kunai' and gold >= relic.get('price', 999):
                return "kunai"

        for relic in screen_state.get('relics', []):
            if relic.get('id') == 'Shuriken' and gold >= relic.get('price', 999):
                return "shuriken"

        # 1. Purge curses
        if can_purge and state.deck.contains_curses_we_can_remove():
            return "purge"

        # 2. Membership Card
        for relic in screen_state.get('relics', []):
            if relic.get('id') == 'Membership Card' and gold >= relic.get('price', 999):
                return "membership card"

        # 3. Cards based on list (match by id)
        deck_card_list = state.get_deck_card_list_by_id()
        for p in self.cards_to_buy:
            for card in screen_state.get('cards', []):
                if card.get('id') == p and gold >= card.get('price', 999):
                    if p.lower() not in deck_card_list:
                        # Return the localized name from choice_list (already translated by get_choice_list)
                        card_name = card.get('name', '').lower()
                        if card_name in choice_list:
                            return card_name
                        # Fallback: find by matching id in screen_state.cards
                        for idx, choice in enumerate(choice_list):
                            if choice == card_name:
                                return choice

        # 4. Relics based on list (match by id)
        for p in self.relics_to_buy:
            for relic in screen_state.get('relics', []):
                if relic.get('id') == p and gold >= relic.get('price', 999):
                    relic_name = relic.get('name', '').lower()
                    if relic_name in choice_list:
                        return relic_name

        # 5. Purge basics
        if can_purge and state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST):
            return "purge"

        # Nothing we want / can afford, leave.
        return ''