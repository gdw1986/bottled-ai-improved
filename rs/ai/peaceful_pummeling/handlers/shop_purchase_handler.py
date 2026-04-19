"""商店购买处理器 - 使用索引而非名称进行选择"""

from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.ai.peaceful_pummeling.config import CARD_REMOVAL_PRIORITY_LIST
from rs.game.screen_type import ScreenType
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class ShopPurchaseHandler(Handler):

    def __init__(self):
        self.relics = [
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

        self.cards = [
            "Blasphemy",
            "Meditate",
            "Scrawl",
            "Empty Mind",
            "Nirvana",
            "Deceive Reality",
            "Pray",
            "Master Reality",
            "Foreign Influence",
            "Talk to the Hand",
            "Wreath of Flame",
            "Smite",
            "Wheel Kick",
            "Flying Sleeves",
            "Consecrate",
            "Cut Through Fate",
            "Pressure Points",
            "Just Lucky",
            "Halt",
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
        
        if not choice_list or 'cards' not in screen_state:
            return -1

        can_purge = screen_state.get('purge_available', False) and gold >= screen_state.get('purge_cost', 999)

        # 遍历 choice_list 找匹配项
        for idx, choice in enumerate(choice_list):
            choice_lower = choice.lower()
            
            # 检查遗物
            for relic in screen_state.get('relics', []):
                relic_id = relic.get('id', '')
                relic_name = relic.get('name', '').lower()
                relic_price = relic.get('price', 999)
                
                if gold >= relic_price:
                    if relic_id == 'Membership' and relic_name == choice_lower:
                        return idx
                    if relic_id in self.relics and relic_name == choice_lower:
                        return idx

            # 检查卡牌
            for card in screen_state.get('cards', []):
                card_id = card.get('id', '')
                card_name = card.get('name', '').lower()
                card_price = card.get('price', 999)
                
                if gold >= card_price and card_name == choice_lower:
                    if card_id in self.cards:
                        deck_card_list = state.get_deck_card_list_by_id()
                        if card_id.lower() not in deck_card_list:
                            return idx

            # Blasphemy 单独处理
            if 'blasphemy' in choice_lower:
                for card in screen_state.get('cards', []):
                    if card.get('id') == 'Blasphemy' and gold >= card.get('price', 999):
                        deck_card_list = state.get_deck_card_list_by_id()
                        if 'blasphemy' not in deck_card_list:
                            return idx

        # 删除诅咒/基础牌
        if can_purge:
            if state.deck.contains_curses_we_can_remove() or state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST):
                try:
                    return choice_list.index('purge')
                except ValueError:
                    pass

        return -1
