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
        # Data-driven from 35,691 Ironclad runs — sorted by frequency in winning runs
        self.relics = [
            'ClockworkSouvenir',      # 308 wins — artifact is premium
            'Vajra',                   # 263 wins — +1 strength universally good
            'Brimstone',               # 258 wins — high-risk high-reward scaling
            "Lee's Waffle",            # 255 wins — full heal
            'Sling',                   # 240 wins — fight shop relic
            'Lantern',                 # 234 wins — T1 energy
            'Bag of Preparation',      # 234 wins — draw 2 always good
            'Happy Flower',            # 226 wins — passive energy
            'Anchor',                  # 222 wins — block setup turns
            'PreservedInsect',         # 202 wins — elite hunting
            'Oddly Smooth Stone',      # 200 wins — dexterity
            'Bag of Marbles',          # 200 wins — vulnerable on T1
            'Red Skull',               # 200 wins — strength at low HP
            'Orrery',                  # 194 wins — 5 card picks
            'Medical Kit',             # 192 wins — status immunity
            'Pen Nib',                 # 179 wins — double damage
            'HandDrill',               # 185 wins — strip artifact charges
            'Bronze Scales',           # 183 wins — thorns
            'War Paint',               # 169 wins — 2 random upgrades
            'Strike Dummy',            # strikes+3
            'Paper Phrog',             # vulnerable bonus
            'Meat on the Bone',        # sustain
            'Eternal Feather',         # heal per floor
            'Regal Pillow',            # rest bonus
            'Meal Ticket',             # shop healing
            'Strawberry',              # +7 max HP
            'Toy Ornithopter',         # potion healing
            'Pantograph',              # boss heal
            'Pear',                    # +10 max HP
            'Orichalcum',              # block if no block
            'Horn Cleat',              # T2 block
            'Self Forming Clay',       # block stacking
            'Thread and Needle',       # plated armor
            'Centennial Puzzle',       # draw on damage
            'Singing Bowl',            # +2 max HP per skip
            'DollysMirror',            # duplicate a card
            'Blood Vial',              # heal 2 per combat
            'Molten Egg 2',            # attacks upgraded
            'Toxic Egg 2',             # skills upgraded
            'Frozen Egg 2',            # powers upgraded
            'Gambling Chip',           # discard + redraw T1
            'Ginger',                  # weakened immunity
            'Turnip',                  # frail immunity
            # New additions (A15+ win-rate data, formerly missing)
            'Omamori',                 # 63 wins — blocks 2 curses
            'MawBank',                 # 59 wins — +12 gold per floor
            'Ancient Tea Set',         # 55 wins — +2 energy after campfire
            'Potion Belt',             # 55 wins — +2 potion slots
            'Question Card',           # 55 wins — card reward 4-choose-1
            'Whetstone',               # 52 wins — upgrade 2 random attacks
            'Red Mask',                # 51 wins — extra gold from events
            'Juzu Bracelet',           # 50 wins — fewer normal combats
            'Nunchaku',                # 50 wins — energy after 10 attacks
            'Art of War',              # 49 wins — +1 energy if no attack played
            'Dead Branch',             # 46 wins — random card on exhaust
            'Chemical X',              # 18 buys — Whirlwind damage multiplier
        ]

        # Cards worth buying in shop (match by id)
        self.cards = [
            "Offering",
            "Battle Trance",
            "Shockwave",
            "Impervious",
            "Reaper",
            "Corruption",
            "Feel No Pain",
            "Dark Embrace",
            "Limit Break",
            "Demon Form",
            "Barricade",
            "Apotheosis",
            "Shrug It Off",
            "Inflame",
            "Spot Weakness",
            "Disarm",
            "Flame Barrier",
            "Metallicize",
            "Feed",
            # New additions (A15+ win-rate data, formerly missing)
            "Armaments",    # upgrades hand when upgraded — #5 most picked
            "Whirlwind",    # AoE + strength multiplier
            "Flex",         # 0-cost strength burst
            "True Grit",    # exhaust control + block
            "Evolve",       # status draw (Power Through synergy)
            "Pommel Strike", # draw + damage
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

        def choose_potion(i: int):
            if i in potion_indices:
                return f"choose {potion_indices[i]}"
            return None  # Potion not in choice_list (unaffordable)

        log_to_run(f"[SHOP] gold={gold}, choices={raw_choice_list}, "
                   f"card_idx={card_indices}, relic_idx={relic_indices}, potion_idx={potion_indices}")

        # 1. Membership Card — #3 most purchased in winning runs (545 wins)
        #    Must buy FIRST before spending any gold — reduces all future prices by 50%
        for i, relic in enumerate(shop_relics):
            if relic['id'] == 'Membership Card' and gold >= relic['price']:
                action = choose_relic(i)
                if action:
                    log_to_run(f"[SHOP] Buying Membership Card for {relic['price']}")
                    return action

        # Safety: if we got here and have low gold, just leave
        if gold < 100:
            return ''

        # 2. Purge curses
        if can_purge and state.deck.contains_curses_we_can_remove():
            action = choose_purge()
            if action:
                return action

        # 3. Perfected Strike — core archetype card
        for i, card in enumerate(shop_cards):
            if card['id'] == 'Perfected Strike' and gold >= card['price']:
                action = choose_card(i)
                if action:
                    return action

        # 4. Purge in general (avoid duplicates by checking deck has cards to remove)
        if can_purge and state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST):
            action = choose_purge()
            if action:
                return action

        # 5. Relics based on priority list (match by id - always English)
        for wanted in self.relics:
            for i, relic in enumerate(shop_relics):
                if relic['id'] == wanted and gold >= relic['price']:
                    action = choose_relic(i)
                    if action:
                        return action

        # 6. Cards based on list (match by id - always English)
        deck_card_ids = state.get_deck_card_list_by_id()
        for wanted in self.cards:
            wanted_lower = wanted.lower()
            for i, card in enumerate(shop_cards):
                if card['id'].lower() == wanted_lower and gold >= card['price']:
                    if wanted_lower not in deck_card_ids:
                        action = choose_card(i)
                        if action:
                            return action

        # 7. Potions we want — only if we have empty slots (check FIRST)
        if not state.are_potions_full():
            for i, potion in enumerate(shop_potions):
                if potion.get('price', 999) <= gold:
                    action = choose_potion(i)
                    if action:
                        log_to_run(f"[SHOP] Buying potion {potion['id']} for {potion['price']}")
                        return action

        # 8. If gold is low or nothing good found, just leave
        return ''
