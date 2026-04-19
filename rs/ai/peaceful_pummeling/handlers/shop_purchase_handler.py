from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.ai.peaceful_pummeling.config import CARD_REMOVAL_PRIORITY_LIST
from rs.game.screen_type import ScreenType
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class ShopPurchaseHandler(Handler):

    def __init__(self):
        self.relics = [
            'Pen Nib',
            'Bag of Marbles',
            'Shuriken',
            'Meat on the Bone',
            'Vajra',
            'Bag of Preparation',
            'Kunai',
            'Eternal Feather',
            'Regal Pillow',
            'Lee’s Waffle',
            'Meal Ticket',
            'Strawberry',
            'Pear',
            'Pantograph',
            'Anchor',
            'Horn Cleat',
            'Lantern',
            'Centennial Puzzle',
            'Damaru',
        ]

        self.cards = [
            # 'Blasphemy',  # We have a specific line for purchasing Blasphemy with higher priority than Relics
            'Adaptation',  # Rushdown
            'Mentalfortress',
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

        # 1. Purge curses
        if can_purge and state.deck.contains_curses_we_can_remove():
            return "purge"

        # 2. Membership Card (match by id, always English)
        for relic in screen_state.get('relics', []):
            if relic.get('id') == 'Membership' and gold >= relic.get('price', 999):
                return "membership"

        # 3. Blasphemy
        for card in screen_state.get('cards', []):
            if card.get('id') == 'Blasphemy' and gold >= card.get('price', 999):
                return card.get('name', '').lower()

        # 4. Relics based on list (match by id)
        for p in self.relics:
            for relic in screen_state.get('relics', []):
                if relic.get('id') == p and gold >= relic.get('price', 999):
                    return relic.get('name', '').lower()

        # 5. Cards based on list (match by id)
        deck_card_list = state.get_deck_card_list_by_id()
        for p in self.cards:
            for card in screen_state.get('cards', []):
                if card.get('id') == p and gold >= card.get('price', 999):
                    if p.lower() not in deck_card_list:
                        return card.get('name', '').lower()

        # 6. Purge in general
        if can_purge and state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST):
            return "purge"

        # Nothing we want / can afford, leave.
        return ''
