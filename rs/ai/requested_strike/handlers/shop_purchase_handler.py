from typing import List

from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.ai.requested_strike.config import CARD_REMOVAL_PRIORITY_LIST
from rs.game.card import CardType
from rs.game.screen_type import ScreenType
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class ShopPurchaseHandler(Handler):

    def __init__(self):
        self.relics = [
            'Bag of Marbles',
            'Pen Nib',
            'Strike Dummy',
            'Paper Phrog',
            'Preserved Insect',
            'Red Skull',
            'Meat on the Bone',
            'Eternal Feather',
            'Regal Pillow',
            "Lee's Waffle",
            'Meal Ticket',
            'Strawberry',
            'Toy Ornithopter',
            'Pantograph',
            'Pear',
            'Orichalcum',
            'Anchor',
            'Horn Cleat',
            'Self-Forming Clay',
            'Thread and Needle',
            'Lantern',
            'Happy Flower',
            'Bag of Preparation',
            'Centennial Puzzle',
        ]

        self.cards = [
            "Offering",
            "Battle Trance",
            "Shockwave"
        ]

    def can_handle(self, state: GameState) -> bool:
        return state.screen_type() == ScreenType.SHOP_SCREEN.value

    def handle(self, state: GameState) -> HandlerAction:
        action = self.find_choice(state)
        if action:
            # Safety: validate index is within bounds
            try:
                idx = int(action.split()[1])
                max_idx = len(state.get_choice_list()) - 1
                if idx > max_idx:
                    print(f"[SHOP] ERROR: choose {idx} exceeds max {max_idx}, choices: {state.get_choice_list()}")
                    return HandlerAction(commands=["return", "proceed"])
            except (ValueError, IndexError):
                pass
            if presentation_mode:
                return HandlerAction(commands=[p_delay, action, p_delay_s, "wait 30"])
            return HandlerAction(commands=[action, "wait 30"])
        if presentation_mode:
            return HandlerAction(commands=["wait 30", "return", "proceed"])
        return HandlerAction(commands=["return", "proceed"])

    def find_choice(self, state: GameState) -> str:
        """Returns 'choose N' string, or '' to leave shop. Uses index-based matching to avoid
        Chinese/English name translation issues."""
        gold = state.game_state()['gold']
        screen_state = state.game_state()['screen_state']

        can_purge = screen_state.get('purge_available', False) and gold >= screen_state.get('purge_cost', 999)
        shop_cards = screen_state.get('cards', [])
        shop_relics = screen_state.get('relics', [])
        shop_potions = screen_state.get('potions', [])

        # Index offsets in the choice_list (same order as CommunicationMod sends them)
        def choose_purge():
            return "choose 0"

        def choose_card(i: int):
            offset = 1 if can_purge else 0
            return f"choose {offset + i}"

        def choose_relic(i: int):
            offset = (1 if can_purge else 0) + len(shop_cards)
            return f"choose {offset + i}"

        def choose_potion(i: int):
            offset = (1 if can_purge else 0) + len(shop_cards) + len(shop_relics)
            return f"choose {offset + i}"

        # 1. Purge curses
        if can_purge and state.deck.contains_curses_we_can_remove():
            return choose_purge()

        # 2. Perfected Strike
        for i, card in enumerate(shop_cards):
            if card['id'] == 'Perfected Strike' and gold >= card['price']:
                return choose_card(i)

        # 3. Membership Card
        for i, relic in enumerate(shop_relics):
            if relic['id'] == 'Membership Card' and gold >= relic['price']:
                return choose_relic(i)

        # 4. Purge in general (avoid duplicates by checking deck has cards to remove)
        if can_purge and state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST):
            return choose_purge()

        # 5. Relics based on priority list (match by id - always English)
        for wanted in self.relics:
            for i, relic in enumerate(shop_relics):
                if relic['id'] == wanted and gold >= relic['price']:
                    return choose_relic(i)

        # 6. Cards based on list (match by id - always English)
        deck_card_ids = state.get_deck_card_list_by_id()
        for wanted in self.cards:
            wanted_lower = wanted.lower()
            for i, card in enumerate(shop_cards):
                if card['id'].lower() == wanted_lower and gold >= card['price']:
                    if wanted_lower not in deck_card_ids:
                        return choose_card(i)

        # 7. Potions we want
        for i, potion in enumerate(shop_potions):
            if potion.get('price', 999) <= gold:
                # buy any affordable potion if we have a slot
                if not state.are_potions_full():
                    return choose_potion(i)

        return ''
