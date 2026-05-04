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
            'Self-Forming Clay',       # block stacking
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

        # 1. Membership Card — #3 most purchased in winning runs (545 wins)
        #    Must buy FIRST before spending any gold — reduces all future prices by 50%
        for i, relic in enumerate(shop_relics):
            if relic['id'] == 'Membership Card' and gold >= relic['price']:
                return choose_relic(i)

        # 2. Purge curses
        if can_purge and state.deck.contains_curses_we_can_remove():
            return choose_purge()

        # 3. Perfected Strike — core archetype card
        for i, card in enumerate(shop_cards):
            if card['id'] == 'Perfected Strike' and gold >= card['price']:
                return choose_card(i)

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
