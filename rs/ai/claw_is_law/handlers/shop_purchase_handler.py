"""商店购买处理器 - 使用索引而非名称进行选择"""

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
        idx = self.find_choice_index(state)
        if idx >= 0:
            if presentation_mode:
                return HandlerAction(commands=[p_delay, "choose " + str(idx), p_delay_s, "wait 30"])
            return HandlerAction(commands=["choose " + str(idx), "wait 30"])
        if presentation_mode:
            return HandlerAction(commands=["wait " + p_delay, "return", "proceed"])
        return HandlerAction(commands=["return", "proceed"])

    def find_choice_index(self, state: GameState) -> int:
        """返回要选择的索引，-1 表示不购买"""
        gold = state.game_state()['gold']
        screen_state = state.game_state()['screen_state']
        choice_list = state.get_choice_list()
        
        # 验证数据完整性
        if not choice_list or 'cards' not in screen_state:
            return -1

        can_purge = screen_state.get('purge_available', False) and gold >= screen_state.get('purge_cost', 999)

        # 遍历 choice_list 找匹配项
        for idx, choice in enumerate(choice_list):
            choice_lower = choice.lower()
            
            # 0. 检查遗物（通过 screen_state.relics 匹配）
            relics = screen_state.get('relics', [])
            for relic in relics:
                relic_id = relic.get('id', '')
                relic_name = relic.get('name', '').lower()
                relic_price = relic.get('price', 999)
                
                if gold >= relic_price:
                    # Kunai/Shuriken
                    if relic_id == 'Kunai' and relic_name == choice_lower:
                        return idx
                    if relic_id == 'Shuriken' and relic_name == choice_lower:
                        return idx
                    # 其他遗物
                    if relic_id in self.relics_to_buy and relic_name == choice_lower:
                        return idx

            # 1. 检查卡牌（通过 screen_state.cards 匹配）
            cards = screen_state.get('cards', [])
            for card in cards:
                card_id = card.get('id', '')
                card_name = card.get('name', '').lower()
                card_price = card.get('price', 999)
                
                if gold >= card_price and card_name == choice_lower:
                    # 检查是否在购买列表中
                    if card_id in self.cards_to_buy:
                        # 检查牌组是否已有
                        deck_card_list = state.get_deck_card_list_by_id()
                        if card_id.lower() not in deck_card_list:
                            return idx

        # 2. 检查删除诅咒
        if can_purge and state.deck.contains_curses_we_can_remove():
            try:
                return choice_list.index('purge')
            except ValueError:
                pass

        # 3. 检查删除基础牌
        if can_purge and state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST):
            try:
                return choice_list.index('purge')
            except ValueError:
                pass

        return -1
