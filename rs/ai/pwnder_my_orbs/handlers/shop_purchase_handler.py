"""PWNDER_MY_ORBS (Defect) 商店购买处理器 - 基于 choice_list 索引映射"""
from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.ai.pwnder_my_orbs.config import CARD_REMOVAL_PRIORITY_LIST
from rs.game.screen_type import ScreenType
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.handlers.shop_index_mapper import build_choice_index_map
from rs.machine.state import GameState


class ShopPurchaseHandler(Handler):

    def __init__(self):
        self.relics_to_buy = [
            'Orange Pellets',
            'Data Disk',
            'Runic Capacitor',
            'Clockwork Souvenir',
            'Bag of Preparation',
            'Eternal Feather',
            'Meal Ticket',
            'Anchor',
            'Horn Cleat',
            'Frozen Egg',
            'Bronze Scales',
            'Preserved Insect',
            'Bag of Marbles',
            'Toxic Egg',
            'Orichalcum',
            'Torii',
            'Vajra',
        ]

        self.cards_to_buy = [
            "Self Repair",
            "Biased Cognition",
            "Capacitor",
            "Defragment",
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

        raw_choice_list = state.game_state().get('choice_list', [])
        card_indices, relic_indices, potion_indices, purge_index = \
            build_choice_index_map(raw_choice_list, shop_cards, shop_relics, shop_potions)

        def choose_purge():
            if purge_index >= 0:
                return f"choose {purge_index}"
            return None

        def choose_card(i: int):
            if i in card_indices:
                return f"choose {card_indices[i]}"
            return None

        def choose_relic(i: int):
            if i in relic_indices:
                return f"choose {relic_indices[i]}"
            return None

        def choose_potion(i: int):
            if i in potion_indices:
                return f"choose {potion_indices[i]}"
            return None

        # 1. Purge curses
        if can_purge and state.deck.contains_curses_we_can_remove():
            action = choose_purge()
            if action:
                return action

        # 2. Membership Card
        for i, relic in enumerate(shop_relics):
            if relic.get('id', '') == 'Membership Card' and gold >= relic.get('price', 999):
                action = choose_relic(i)
                if action:
                    return action

        # 3. Cards we want
        deck_ids = state.get_deck_card_list_by_id()
        for wanted in self.cards_to_buy:
            for i, card in enumerate(shop_cards):
                if card.get('id', '') == wanted and gold >= card.get('price', 999):
                    if wanted.lower() not in deck_ids:
                        action = choose_card(i)
                        if action:
                            return action

        # 4. Relics we want
        for i, relic in enumerate(shop_relics):
            rid = relic.get('id', '')
            price = relic.get('price', 999)
            if gold >= price and rid in self.relics_to_buy:
                action = choose_relic(i)
                if action:
                    return action

        # 5. Purge basics
        if can_purge and state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST):
            action = choose_purge()
            if action:
                return action

        # 6. Buy any potion if we have a free slot
        if not state.are_potions_full():
            for i, potion in enumerate(shop_potions):
                if gold >= potion.get('price', 999):
                    action = choose_potion(i)
                    if action:
                        return action

        return ''
