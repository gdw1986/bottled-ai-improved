from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.ai.shivs_and_giggles.config import CARD_REMOVAL_PRIORITY_LIST
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
            'Toxic Egg',
            'Orichalcum',
            'Torii',
            'Vajra',
            'Eternal Feather',
            'Meal Ticket',
            'Anchor',
            'Horn Cleat',
            'Bronze Scales',
        ]

        self.cards_to_buy = [
            "Accuracy",
            "Blade Dance",
        ]

    def can_handle(self, state: GameState) -> bool:
        return state.screen_type() == ScreenType.SHOP_SCREEN.value

    def handle(self, state: GameState) -> HandlerAction:
        action = self._find_action(state)
        if action:
            if presentation_mode:
                return HandlerAction(commands=[p_delay, action, p_delay_s, "wait 30"])
            return HandlerAction(commands=[action, "wait 30"])
        if presentation_mode:
            return HandlerAction(commands=["wait 30", "return", "proceed"])
        return HandlerAction(commands=["return", "proceed"])

    def _find_action(self, state: GameState) -> str:
        gold = state.game_state()['gold']
        sc = state.game_state()['screen_state']
        can_purge = sc.get('purge_available', False) and gold >= sc.get('purge_cost', 999)
        shop_cards = sc.get('cards', [])
        shop_relics = sc.get('relics', [])
        shop_potions = sc.get('potions', [])

        def choose_purge():
            return "choose 0"

        def choose_card(i: int):
            return f"choose {(1 if can_purge else 0) + i}"

        def choose_relic(i: int):
            return f"choose {(1 if can_purge else 0) + len(shop_cards) + i}"

        def choose_potion(i: int):
            return f"choose {(1 if can_purge else 0) + len(shop_cards) + len(shop_relics) + i}"

        # 1. Kunai/Shuriken prioritized (key Silent relics)
        for i, relic in enumerate(shop_relics):
            rid = relic.get('id', '')
            price = relic.get('price', 999)
            if gold >= price and rid in ('Kunai', 'Shuriken'):
                return choose_relic(i)

        # 2. Purge curses
        if can_purge and state.deck.contains_curses_we_can_remove():
            return choose_purge()

        # 3. Membership Card
        for i, relic in enumerate(shop_relics):
            if relic.get('id', '') == 'Membership Card' and gold >= relic.get('price', 999):
                return choose_relic(i)

        # 4. Cards we want
        deck_ids = state.get_deck_card_list_by_id()
        for wanted in self.cards_to_buy:
            for i, card in enumerate(shop_cards):
                if card.get('id', '') == wanted and gold >= card.get('price', 999):
                    if wanted.lower() not in deck_ids:
                        return choose_card(i)

        # 5. Other relics
        for i, relic in enumerate(shop_relics):
            rid = relic.get('id', '')
            price = relic.get('price', 999)
            if gold >= price and rid in self.relics_to_buy:
                return choose_relic(i)

        # 6. Purge basics
        if can_purge and state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST):
            return choose_purge()

        # 7. Potions if we have a slot
        if not state.are_potions_full():
            for i, potion in enumerate(shop_potions):
                if gold >= potion.get('price', 999):
                    return choose_potion(i)

        return ''
