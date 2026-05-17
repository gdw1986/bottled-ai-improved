"""Ironclad (Requested Strike) 商店购买处理器 - 基于 choice_list 索引映射

关键发现：CommunicationMod 的 choice_list 只包含当前金币买得起的商品！
- 买不起的卡牌（如高价值无色牌）不在 choice_list 中
- 买不起的遗物不在 choice_list 中
- 买不起的药水不在 choice_list 中

因此不能用 screen_state 数组长度来计算 choose N 的索引，
必须通过 name 字段将 screen_state 条目与 choice_list 条目匹配，
获取实际的 choice_list 索引。
"""
from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.ai.requested_strike.config import CARD_REMOVAL_PRIORITY_LIST
from rs.game.screen_type import ScreenType
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.handlers.shop_index_mapper import build_choice_index_map
from rs.machine.state import GameState
from rs.helper.logger import log_to_run


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
            "Shockwave",
        ]

    def can_handle(self, state: GameState) -> bool:
        return state.screen_type() == ScreenType.SHOP_SCREEN.value

    def handle(self, state: GameState) -> HandlerAction:
        action = self._find_choice(state)
        if action:
            if presentation_mode:
                return HandlerAction(commands=[p_delay, action, p_delay_s, "wait 30"])
            return HandlerAction(commands=[action, "wait 30"])
        # No valid action found - leave shop
        if presentation_mode:
            return HandlerAction(commands=["wait 30", "return", "proceed"])
        return HandlerAction(commands=["return", "proceed"])

    def _find_choice(self, state: GameState) -> str:
        """Returns 'choose N' string, or '' to leave shop.

        Uses choice_list name-matching via build_choice_index_map to find
        the correct index. This correctly handles:
        - Unaffordable items excluded from choice_list
        - Colorless rare cards excluded from choice_list
        - Relics that may or may not appear in choice_list
        - Chinese/English name differences
        """
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
            return None  # Card not in choice_list (unaffordable or colorless rare)

        def choose_relic(i: int):
            if i in relic_indices:
                return f"choose {relic_indices[i]}"
            return None  # Relic not in choice_list (unaffordable)

        log_to_run(f"[SHOP] gold={gold}, choices={raw_choice_list}, "
                   f"card_idx={card_indices}, relic_idx={relic_indices}, potion_idx={potion_indices}")

        def entry_matches(entry: dict, wanted: str) -> bool:
            wanted_norm = wanted.lower().replace('-', ' ').replace("'", "")
            values = [str(entry.get('id', '')), str(entry.get('name', ''))]
            for value in values:
                normalized = value.lower().replace('-', ' ').replace("'", "")
                if normalized == wanted_norm or normalized.replace(' ', '') == wanted_norm.replace(' ', ''):
                    return True
            return False

        # 1. Purge curses
        if can_purge and state.deck.contains_curses_we_can_remove():
            action = choose_purge()
            if action:
                return action

        # 2. Perfected Strike
        for i, card in enumerate(shop_cards):
            if entry_matches(card, 'Perfected Strike') and gold >= card['price']:
                action = choose_card(i)
                if action:
                    return action

        # 3. Membership Card
        for i, relic in enumerate(shop_relics):
            if entry_matches(relic, 'Membership Card') and gold >= relic['price']:
                action = choose_relic(i)
                if action:
                    return action

        # 4. Purge in general
        if can_purge and state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST):
            action = choose_purge()
            if action:
                return action

        # 5. Relics based on the original Requested Strike priority list.
        for wanted in self.relics:
            for i, relic in enumerate(shop_relics):
                if entry_matches(relic, wanted) and gold >= relic['price']:
                    action = choose_relic(i)
                    if action:
                        return action

        # 6. Cards based on the original Requested Strike priority list.
        deck_card_ids = state.get_deck_card_list_by_id()
        for wanted in self.cards:
            wanted_lower = wanted.lower()
            for i, card in enumerate(shop_cards):
                if entry_matches(card, wanted) and gold >= card['price']:
                    if wanted_lower not in deck_card_ids:
                        action = choose_card(i)
                        if action:
                            return action

        # Nothing we want / can afford, leave.
        return ''
