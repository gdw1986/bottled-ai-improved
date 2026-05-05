"""PEACEFUL_PUMMELING (Watcher) 商店购买处理器 - 基于 choice_list 索引映射"""
from rs.ai.peaceful_pummeling.config import CARD_REMOVAL_PRIORITY_LIST
from rs.game.screen_type import ScreenType
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.handlers.shop_index_mapper import build_choice_index_map
from rs.machine.state import GameState


class ShopPurchaseHandler(Handler):
    """
    PEACEFUL_PUMMELING 专用商店处理器。

    使用 choice_list name-matching 定位，不依赖数组长度计算索引。
    """

    DESIRED_CARDS: set[str] = {
        "Blasphemy", "Meditate", "Scrawl", "EmptyBody", "Nirvana",
        "DeceiveReality", "Pray", "MasterReality", "ForeignInfluence",
        "TalkToTheHand", "WreathOfFlame", "Smite", "WheelKick",
        "FlyingSleeves", "Consecrate", "CutThroughFate", "PressurePoints",
        "JustLucky", "Halt", "FearNoEvil", "Evaluate", "SandsOfTime",
        "WaveOfTheHand", "Eruption", "InnatePower", "Prostrate",
        "SpiritShield", "Tranquility", "Vault", "Rushdown", "Wallop",
        "Collect", "Alpha", "Beta", "Omega", "BattleHymn", "Reaper",
        "Cleave", "IronWave", "PommelStrike", "ShrugItOff",
        "Impervious", "Immolate", "Corruption", "Bloodletting",
        "Carnage", "Dropkick", "Hemokinesis", "Pummel", "Rage",
        "TwinStrike", "Anger", "Bash", "Clash", "Flex", "Havoc",
        "Sentinel", "Shockwave", "SpotWeakness", "Thunderclap",
        "Uppercut", "WildStrike",
    }

    DESIRED_RELICS: set[str] = {
        "Kunai", "Shuriken", "OrnamentalFan", "PreservedInsect",
        "BagOfMarbles", "PenNib", "Orichalcum", "Torii", "Vajra",
        "EternalFeather", "MealTicket", "Anchor", "HornCleat",
        "Duality", "SneckoSkull", "GoldPlatedCables", "Nunchaku",
        "CharonAshes", "Threadbare", "TheSpecimen", "Calipers",
    }

    DESIRED_POTIONS: set[str] = {
        "FirePotion", "SpeedPotion", "StrengthPotion", "DexterityPotion",
        "GhostInAJar", "FairyPotion", "FruitJuice", "RegenPotion",
        "SteroidPotion", "SwiftPotions", "WeakPotion", "BlockPotion",
    }

    def can_handle(self, state: GameState) -> bool:
        return state.screen_type() == ScreenType.SHOP_SCREEN.value

    def handle(self, state: GameState) -> HandlerAction:
        action = self._find_choice(state)
        if action:
            return HandlerAction(commands=[action, "wait 30"])
        return HandlerAction(commands=["return", "proceed"])

    def _find_choice(self, state: GameState) -> str:
        """Returns 'choose N' or '' to leave. Uses name-matching for correct indices."""
        gs = state.game_state()
        sc = gs["screen_state"]
        gold = gs["gold"]
        can_purge = sc.get("purge_available", False) and gold >= sc.get("purge_cost", 999)
        shop_cards = sc.get("cards", [])
        shop_relics = sc.get("relics", [])
        shop_potions = sc.get("potions", [])

        raw_choice_list = state.game_state().get("choice_list", [])
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

        # 1. Purge if we have removable cards
        if can_purge and (
            state.deck.contains_curses_we_can_remove()
            or state.deck.contains_cards(CARD_REMOVAL_PRIORITY_LIST)
        ):
            action = choose_purge()
            if action:
                return action

        # 2. Best cards first
        for i, card in enumerate(shop_cards):
            cid = card.get("id", "")
            price = card.get("price", 999)
            if gold >= price and cid in self.DESIRED_CARDS:
                action = choose_card(i)
                if action:
                    return action

        # 3. Best relics
        for i, relic in enumerate(shop_relics):
            rid = relic.get("id", "")
            price = relic.get("price", 999)
            if gold >= price and rid in self.DESIRED_RELICS:
                action = choose_relic(i)
                if action:
                    return action

        # 4. Potions if we have a slot
        if not state.are_potions_full():
            for i, potion in enumerate(shop_potions):
                pid = potion.get("id", "")
                price = potion.get("price", 999)
                if gold >= price and pid in self.DESIRED_POTIONS:
                    action = choose_potion(i)
                    if action:
                        return action

        return ""
