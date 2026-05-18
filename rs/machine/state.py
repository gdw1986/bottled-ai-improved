import json
from typing import List

from rs.calculator.interfaces.memory_items import MemoryItem
from rs.game.card import card_id_to_name
from rs.game.deck import Deck
from rs.game.event import Event
from rs.machine.command import Command
from rs.machine.orb import Orb
from rs.machine.the_bots_memory_book import TheBotsMemoryBook
import sys


def _compact_identifier(value: str) -> str:
    return ''.join(ch for ch in str(value).lower() if ch.isalnum())


def _compact_identifier_variants(value: str) -> set[str]:
    compact = _compact_identifier(value)
    return {compact, compact.rstrip('0123456789')}


class GameState:
    def __init__(self, json_state: json, the_bots_memory_book: TheBotsMemoryBook):
        self.the_bots_memory_book: TheBotsMemoryBook = the_bots_memory_book
        self.json = json_state
        if "game_state" in json_state:
            if "combat_state" in json_state["game_state"]:
                self.hand: Deck = Deck(json_state["game_state"]["combat_state"]["hand"])
                self.draw_pile: Deck = Deck(json_state["game_state"]["combat_state"]["draw_pile"])
                self.discard_pile: Deck = Deck(json_state["game_state"]["combat_state"]["discard_pile"])
                self.exhaust_pile: Deck = Deck(json_state["game_state"]["combat_state"]["exhaust_pile"])

                current_turn = json_state["game_state"]["combat_state"]["turn"]
                if self.the_bots_memory_book.memory_general[MemoryItem.LAST_KNOWN_TURN] != current_turn:
                    self.the_bots_memory_book.set_new_turn_state()
                self.the_bots_memory_book.memory_general[MemoryItem.LAST_KNOWN_TURN] = current_turn

            else:
                self.the_bots_memory_book.set_new_battle_state()

            self.deck: Deck = Deck(json_state["game_state"]["deck"])
            self.memory_by_card = self.the_bots_memory_book.memory_by_card.copy()
            self.memory_general = self.the_bots_memory_book.memory_general.copy()

    def is_game_running(self) -> bool:
        return self.json["in_game"]

    def game_state(self):
        return self.json["game_state"]

    def combat_state(self):
        if 'combat_state' in self.game_state():
            return self.game_state()["combat_state"]
        else:
            return None

    def has_command(self, command: Command) -> bool:
        return command.value in self.json.get("available_commands")

    def get_player_combat(self):
        return self.game_state()["combat_state"]["player"]

    def get_player_health_percentage(self) -> float:
        return self.game_state()["current_hp"] / self.game_state()["max_hp"]

    def get_monsters(self):
        if "combat_state" not in self.game_state():
            return []
        return self.game_state()["combat_state"]["monsters"]

    def _build_choice_name_map(self) -> dict[str, str]:
        """Build a mapping from localized names in choice_list to English names.

        For card screens (GRID, CARD_REWARD, SHOP_SCREEN, HAND_SELECT): maps Chinese card names
        to lowercase English card names using screen_state.cards (id field is always English).

        For event screens: maps Chinese option labels to English labels using screen_state.options.

        For rest screens: maps Chinese rest option names to English using screen_state.rest_options.
        """
        name_map = {}
        screen_type = self.game_state().get("screen_type")
        screen_state = self.game_state().get("screen_state", {})

        # Card-related screens: use card id to build name map
        if screen_type in ("GRID", "CARD_REWARD", "SHOP_SCREEN", "HAND_SELECT"):
            raw_choice_list = self.game_state().get("choice_list", [])
            cards = screen_state.get("hand", []) if screen_type == "HAND_SELECT" else screen_state.get("cards", [])
            for pos, card in enumerate(cards):
                cn_name = card.get("name")
                en_id = card.get("id")
                if cn_name and en_id:
                    en_name = card_id_to_name(en_id)
                    if card.get("upgrades", 0) > 0:
                        en_name += "+"
                    name_map[cn_name] = en_name
                    if screen_type == "HAND_SELECT" and pos < len(raw_choice_list):
                        name_map[raw_choice_list[pos]] = en_name

        # Event screens: map Chinese labels to English via option position
        elif screen_type == "EVENT" and "options" in screen_state:
            raw_choice_list = self.game_state().get("choice_list", [])
            options = screen_state.get("options", [])
            for pos, opt in enumerate(options):
                cn_label = opt.get("label", "").strip().lower()
                if cn_label and pos < len(raw_choice_list):
                    # Use option position + choice_index to map the raw entry
                    idx = opt.get("choice_index")
                    if idx is not None and idx < len(raw_choice_list):
                        name_map[raw_choice_list[idx]] = cn_label

        # Rest screen: use rest_options for mapping
        elif screen_type == "REST" and "rest_options" in screen_state:
            raw_choice_list = self.game_state().get("choice_list", [])
            rest_options = [opt.lower() for opt in screen_state["rest_options"]]
            if len(raw_choice_list) == len(rest_options):
                for i, opt in enumerate(rest_options):
                    # rest_options are always English even in Chinese game
                    name_map[raw_choice_list[i]] = opt
            else:
                # Some states include unavailable rest options in rest_options.
                # In that case, positional mapping can turn recall into lift.
                for item in raw_choice_list:
                    lowered = item.lower()
                    if lowered in rest_options:
                        name_map[item] = lowered

        # SHOP_ROOM: "shop" in choice_list
        elif screen_type == "SHOP_ROOM":
            raw_choice_list = self.game_state().get("choice_list", [])
            for item in raw_choice_list:
                name_map[item] = item.lower()

        # CHEST, COMBAT_REWARD, BOSS_REWARD, MAP: lowercase the raw list
        elif screen_type in ("CHEST", "COMBAT_REWARD", "MAP"):
            raw_choice_list = self.game_state().get("choice_list", [])
            for item in raw_choice_list:
                name_map[item] = item.lower()

        # BOSS_REWARD: translate Chinese relic names to English IDs
        elif screen_type == "BOSS_REWARD":
            raw_choice_list = self.game_state().get("choice_list", [])
            relics = screen_state.get("relics", [])
            # Build lookup: relic name/id (any language) → id (lowercase)
            relic_lookup = {}
            for relic in relics:
                rid = relic.get("id", "").lower()
                if rid:
                    relic_lookup[relic.get("name", "")] = rid
                    relic_lookup[rid] = rid  # also match by id itself
            for item in raw_choice_list:
                key = item.strip()
                name_map[item] = relic_lookup.get(key, item.lower())

        return name_map

    def get_choice_list(self):
        raw = self.game_state()["choice_list"]
        name_map = self._build_choice_name_map()
        if name_map:
            return [name_map.get(item, item.lower()) for item in raw]
        return raw

    def get_choice_list_upgrade_stripped_from_choice(self):
        choice_list_modified = self.get_choice_list()
        for idx, choice in enumerate(choice_list_modified):
            choice_list_modified[idx] = choice.replace("+", "")
        return choice_list_modified

    def get_relics(self):
        return self.game_state()["relics"]

    def has_relic(self, relic_name: str) -> bool:
        target = _compact_identifier(relic_name)
        for relic in self.get_relics():
            relic_keys = (
                _compact_identifier_variants(relic.get('name', ''))
                | _compact_identifier_variants(relic.get('id', ''))
            )
            if target in relic_keys:
                return True
        return False

    def get_relic_counter(self, relic_name: str) -> int:
        target = _compact_identifier(relic_name)
        for relic in self.get_relics():
            relic_keys = (
                _compact_identifier_variants(relic.get('name', ''))
                | _compact_identifier_variants(relic.get('id', ''))
            )
            if target in relic_keys:
                return relic['counter']
        return False

    def get_potions(self):
        return self.game_state()["potions"]

    def get_held_potion_names(self):
        potion_names = []
        for pot in self.game_state()["potions"]:
            potion_names.append(pot["name"])
        potion_names = [potion_name.lower() for potion_name in potion_names]
        return potion_names

    def get_reward_potion_names(self):
        potion_names = []
        for reward in self.game_state()["screen_state"]["rewards"]:
            if reward["reward_type"] == "POTION":
                potion_names.append(reward["potion"]["name"])
        potion_names = [potion_name.lower() for potion_name in potion_names]
        return potion_names

    def are_potions_full(self) -> bool:
        for pot in self.get_potions():
            if pot['id'] == "Potion Slot":
                return False
        return True

    def screen_type(self):
        return self.game_state()["screen_type"]

    def screen_state(self):
        return self.game_state()["screen_state"]

    def screen_state_max_cards(self):
        state = self.screen_state()
        return 0 if not state else state["max_cards"]

    def screen_state_must_pick_card(self):
        state = self.screen_state()
        return 1 if not state else state["can_pick_zero"]

    def screen_state_exhaust_cards(self):
        return 0 if not self.current_action() == "ExhaustAction" else self.screen_state_max_cards()

    def screen_state_discard_cards(self):
        return 0 if not self.current_action() == "DiscardAction" else self.screen_state_max_cards()

    def current_action(self):
        if self.game_state()["screen_type"] == "HAND_SELECT" or \
                (self.combat_state() is not None and self.game_state()["screen_type"] == "GRID"):
            return self.game_state()["current_action"]

    def get_cards_discarded_this_turn(self):
        state = self.combat_state()
        return 0 if not state else state["cards_discarded_this_turn"]

    def floor(self) -> int:
        return self.game_state()["floor"]

    def act(self) -> int:
        return self.game_state()["act"]

    def player_entangled(self):
        return bool(next((p for p in self.get_player_combat()["powers"] if p["id"] == "Entangled"), None))

    def get_deck_card_list_by_id(self) -> dict[str, int]:
        cards = {}
        for card in self.deck.cards:
            card_id = card.id.lower()
            if card_id in cards:
                cards[card_id] += 1
            else:
                cards[card_id] = 1
        return cards

    def get_deck_card_list_by_name_with_upgrade_stripped(self) -> dict[str, int]:
        cards = {}
        for card in self.deck.cards:
            # Use card id (always English) instead of name (may be localized).
            name = card_id_to_name(card.id)
            if name in cards:
                cards[name] += 1
            else:
                cards[name] = 1
        return cards

    def get_map(self) -> List[dict]:
        return self.game_state()["map"]

    def has_monster(self, name: str) -> bool:
        target_keys = _compact_identifier_variants(name)
        for monster in self.get_monsters():
            monster_keys = (
                _compact_identifier_variants(monster.get('name', ''))
                | _compact_identifier_variants(monster.get('id', ''))
            )
            if target_keys & monster_keys:
                return True
        return False

    def get_player_block(self) -> int:
        return self.get_player_combat()['block']

    def get_player_orbs(self) -> list[(Orb, int)]:
        orbs = self.get_player_combat()['orbs']
        if not orbs:
            return []
        return [(Orb(o['id']), o['evoke_amount']) for o in orbs if 'id' in o and o['id'] != 'Empty' and 'evoke_amount' in o]

    def get_player_orb_slots(self) -> int:
        orbs = self.get_player_combat()['orbs']
        if not orbs:
            return 0
        return len(orbs)

    def _build_cn_to_en_card_name_map(self) -> dict[str, str]:
        """Build a mapping from Chinese card names to lowercase English display names
        using the current deck data.

        In Chinese game mode, the option text contains Chinese display names (e.g. "宁静+")
        while config lists use English display names (e.g. "tranquility"). This map bridges
        that gap by mapping Chinese name -> English display name derived from card.id.

        Role suffixes (_R, _P, _B, _G) are stripped from IDs so that "Strike_R" and "Strike_P"
        both map to "strike", matching the config key format.
        """
        name_map = {}
        for card in self.game_state().get("deck", []):
            cn_name = card.get("name", "")
            en_id = card.get("id", "")
            if cn_name and en_id:
                name_map[cn_name] = card_id_to_name(en_id)
        return name_map

    def get_falling_event_options(self) -> list:
        options = []

        def extract_card_from_text(text):
            # Support both English ("Lose") and Chinese ("失去") game text
            for keyword in ("Lose", "失去"):
                if keyword in text:
                    return text.split(keyword, 1)[1].strip()
            return None

        def is_chinese(text):
            """Check if text contains any non-ASCII characters (Chinese chars)."""
            return any(ord(c) > 127 for c in text)

        cn_to_en = self._build_cn_to_en_card_name_map()

        for option in self.screen_state()["options"]:
            if not option["disabled"]:
                text = option["text"]
                extracted = extract_card_from_text(text)
                if extracted is not None:
                    if is_chinese(extracted):
                        # Chinese game: translate Chinese name to English
                        en_name = cn_to_en.get(extracted, extracted.lower())
                        options.append(en_name)
                    else:
                        # English game: use the display name directly (matches config keys)
                        options.append(extracted.lower())
                else:
                    # Fallback: use the full text lowercased (better than crashing)
                    options.append(text.lower())
        for idx, choice in enumerate(options):
            options[idx] = choice.replace("+", "")
        return options

    def get_event(self) -> Event:
        # Prefer event_id (English, matches Event enum values) over event_name
        # (Chinese display name, breaks match in non-English game versions).
        screen = self.game_state()['screen_state']
        event_id = screen.get('event_id', screen.get('event_name', ''))
        possible_events = set(item.value for item in Event)

        if event_id not in possible_events:
            return event_id  # log_missing_event in caller handles the case
        return Event(event_id)
