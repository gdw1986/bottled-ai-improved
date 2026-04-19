"""商店购买处理器 - 中英文兼容版（简化策略）"""
from rs.ai.peaceful_pummeling.config import CARD_REMOVAL_PRIORITY_LIST
from rs.game.screen_type import ScreenType
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class ShopPurchaseHandler(Handler):
    """
    PEACEFUL_PUMMELING 专用商店处理器。

    简化策略：进入商店后按 screen_state 顺序（从 cards/relics/potions 数组）
    找到第一个买得起且在白名单里的物品。
    choice_list 的中文名与英文 id 无法直接匹配，改用数组顺序决定。
    """

    DESIRED_CARDS: set[str] = {
        # Watcher 核心
        "Blasphemy", "Meditate", "Scrawl", "EmptyBody", "Nirvana",
        "DeceiveReality", "Pray", "MasterReality", "ForeignInfluence",
        "TalkToTheHand", "WreathOfFlame", "Smite", "WheelKick",
        "FlyingSleeves", "Consecrate", "CutThroughFate", "PressurePoints",
        "JustLucky", "Halt", "FearNoEvil", "Evaluate", "SandsOfTime",
        "WaveOfTheHand", "Eruption", "InnatePower", "Prostrate",
        "SpiritShield", "Tranquility", "Vault", "Rushdown", "Wallop",
        "Collect", "Alpha", "Beta", "Omega", "BattleHymn", "Reaper",
        # 通用
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
        "SteroidPotion", "SwiftPotion", "WeakPotion", "BlockPotion",
    }

    def can_handle(self, state: GameState) -> bool:
        return state.screen_type() == ScreenType.SHOP_SCREEN.value

    def handle(self, state: GameState) -> HandlerAction:
        idx = self._find_choice_index(state)
        if idx < 0:
            return HandlerAction(commands=["return", "proceed"])
        return HandlerAction(commands=[f"choose {idx}", "wait 30"])

    def _find_choice_index(self, state: GameState) -> int:
        """
        基于 screen_state 数组顺序 + choice_list 结构推断要买的物品索引。
        不依赖中英文名匹配。
        """
        gs = state.game_state()
        sc = gs["screen_state"]
        gold = gs["gold"]
        choice_list = state.get_choice_list()
        can_purge = sc.get("purge_available", False)
        purge_cost = sc.get("purge_cost", 999)

        # choice_list 结构（shop 主界面）：[purge?, card_0..card_N, ?, ?, relics..., potions..., leave]
        # 子 tab 界面：只有对应类别的物品
        # 策略：找 choice_list 中第一个在白名单里的物品的索引

        # 建立 screen_state 中所有物品的 id 集合（英文）
        desired_ids: set[str] = set()
        for c in sc.get("cards", []):
            cid = c.get("id", "")
            if cid in self.DESIRED_CARDS and c.get("price", 999) <= gold:
                desired_ids.add(cid)
        for r in sc.get("relics", []):
            rid = r.get("id", "")
            if rid in self.DESIRED_RELICS and r.get("price", 999) <= gold:
                desired_ids.add(rid)
        for p in sc.get("potions", []):
            pid = p.get("id", "")
            if pid in self.DESIRED_POTIONS and p.get("price", 999) <= gold:
                desired_ids.add(pid)

        if not desired_ids:
            # 没有买得起的目标，检查是否 purge
            if can_purge and gold >= purge_cost and CARD_REMOVAL_PRIORITY_LIST:
                for ci, choice_text in enumerate(choice_list):
                    if "purge" in choice_text.lower():
                        return ci
            return -1

        # 在 choice_list 中找第一个目标物品的索引
        for ci, choice_text in enumerate(choice_list):
            ct = choice_text.lower()
            # 匹配任何包含目标 id 的项
            for did in desired_ids:
                if did.lower() in ct or ct in did.lower():
                    return ci

        # Fallback: 直接按 screen_state 数组顺序买第一个买得起的
        # 假设 choice_list 按 [purge, cards, relics, potions, leave] 排列
        # 找到第一个符合条件物品在对应数组中的下标
        base = 1 if (can_purge and "purge" in [c.lower() for c in choice_list]) else 0

        for ci, card in enumerate(sc.get("cards", [])):
            cid = card.get("id", "")
            price = card.get("price", 999)
            if gold >= price and cid in self.DESIRED_CARDS:
                # 尝试在 choice_list 中找对应位置
                for cj, ct in enumerate(choice_list):
                    if cid.lower() in ct.lower():
                        return cj
                # 没找到对应中文名，用偏移估算（假设 cards 紧跟 purge）
                if ci < len(choice_list) - base:
                    return base + ci

        for ri, relic in enumerate(sc.get("relics", [])):
            rid = relic.get("id", "")
            price = relic.get("price", 999)
            if gold >= price and rid in self.DESIRED_RELICS:
                for cj, ct in enumerate(choice_list):
                    if rid.lower() in ct.lower():
                        return cj
                n_cards = len(sc.get("cards", []))
                if base + n_cards + ri < len(choice_list):
                    return base + n_cards + ri

        for pi, potion in enumerate(sc.get("potions", [])):
            pid = potion.get("id", "")
            price = potion.get("price", 999)
            if gold >= price and pid in self.DESIRED_POTIONS:
                for cj, ct in enumerate(choice_list):
                    if pid.lower() in ct.lower():
                        return cj
                n_cards = len(sc.get("cards", []))
                n_relics = len(sc.get("relics", []))
                if base + n_cards + n_relics + pi < len(choice_list):
                    return base + n_cards + n_relics + pi

        return -1
