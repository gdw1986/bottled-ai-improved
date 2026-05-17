import unittest

from ai.requested_strike.rs_test_handler_fixture import RsTestHandlerFixture
from rs.ai.requested_strike.handlers.battle_handler import IroncladBattleHandler
from rs.ai.requested_strike.handlers.potions_handler import (
    LiquidMemoriesGridHandler,
    LiquidMemoriesHandler,
    PotionsEmergencyHandler,
    PotionsHealHandler,
    PotionsScalingHandler,
    SmokeBombEscapeHandler,
)
from rs.machine.state import GameState
from rs.machine.the_bots_memory_book import TheBotsMemoryBook


class PotionsHandlerTestCase(RsTestHandlerFixture):
    def test_elite_potions_handler(self):
        self.handler = PotionsEmergencyHandler
        self.execute_handler_tests('/other/potions_elite.json', ['wait 30', 'potion use 0 0', 'wait 30'])

    def test_potions_dead_minions(self):
        self.handler = PotionsEmergencyHandler
        self.execute_handler_tests('/other/potions_dead_minions.json', ['wait 30', 'potion use 1 4', 'wait 30'])

    def test_potions_reptomancer(self):
        self.handler = PotionsEmergencyHandler
        self.execute_handler_tests('/other/potions_reptomancer.json', ['wait 30', 'potion use 1 3', 'wait 30'])

    def test_boss_potions_handler(self):
        self.handler = IroncladBattleHandler
        self.execute_handler_tests('/other/potions_boss.json', ['play 4 0'])

    def test_do_not_use_potion(self):
        self.handler = IroncladBattleHandler
        self.execute_handler_tests('/other/potions_boss_disliked_potion.json', ['play 4 0'])

    def test_scaling_potion_matches_spaced_energy_id(self):
        state = self._potion_state("Energy Potion", hp=60, room_type="MonsterRoomBoss")
        handler = PotionsScalingHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["wait 30", "potion use 0", "wait 30"], handler.handle(state).commands)

    def test_scaling_potion_matches_steroid_alias(self):
        state = self._potion_state("SteroidPotion", hp=60, room_type="MonsterRoomElite")
        handler = PotionsScalingHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["wait 30", "potion use 0", "wait 30"], handler.handle(state).commands)

    def test_healing_potion_matches_spaced_regen_id(self):
        state = self._potion_state("Regen Potion", hp=50, room_type="MonsterRoom")
        handler = PotionsHealHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["wait 30", "potion use 0", "wait 30"], handler.handle(state).commands)

    def test_emergency_does_not_use_fairy_alias(self):
        state = self._potion_state("FairyPotion", hp=10, room_type="MonsterRoom")

        self.assertFalse(PotionsEmergencyHandler().can_handle(state))

    def test_smoke_bomb_escapes_dangerous_elite(self):
        state = self._potion_state(
            "SmokeBomb",
            hp=30,
            room_type="MonsterRoomElite",
            requires_target=True,
        )
        handler = SmokeBombEscapeHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["wait 30", "potion use 0 0", "wait 30"], handler.handle(state).commands)

    def test_smoke_bomb_does_not_escape_safe_hallway(self):
        state = self._potion_state("SmokeBomb", hp=70, room_type="MonsterRoom")

        self.assertFalse(SmokeBombEscapeHandler().can_handle(state))

    def test_liquid_memories_uses_for_discard_lethal(self):
        state = self._potion_state(
            "LiquidMemories",
            hp=30,
            room_type="MonsterRoomBoss",
            monsters=[self._monster(current_hp=9, move_damage=0)],
            discard_pile=[self._card("Strike_R", "ATTACK", upgrades=1)],
            hand=[],
        )
        handler = LiquidMemoriesHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["wait 30", "potion use 0", "wait 30"], handler.handle(state).commands)

    def test_liquid_memories_does_not_spend_when_hand_already_has_lethal(self):
        state = self._potion_state(
            "LiquidMemories",
            hp=30,
            room_type="MonsterRoomBoss",
            monsters=[self._monster(current_hp=6, move_damage=0)],
            discard_pile=[self._card("Strike_R", "ATTACK", upgrades=1)],
            hand=[self._card("Strike_R", "ATTACK", upgrades=1)],
        )

        self.assertFalse(LiquidMemoriesHandler().can_handle(state))

    def test_liquid_memories_uses_when_hand_lethal_has_no_energy(self):
        state = self._potion_state(
            "LiquidMemories",
            hp=30,
            room_type="MonsterRoomBoss",
            monsters=[self._monster(current_hp=6, move_damage=0)],
            discard_pile=[self._card("Strike_R", "ATTACK", upgrades=1)],
            hand=[self._card("Strike_R", "ATTACK", upgrades=1)],
            energy=0,
        )

        self.assertTrue(LiquidMemoriesHandler().can_handle(state))

    def test_liquid_memories_uses_for_incoming_lethal_block(self):
        state = self._potion_state(
            "LiquidMemories",
            hp=10,
            room_type="MonsterRoomBoss",
            monsters=[self._monster(current_hp=80, move_damage=20)],
            discard_pile=[self._card("Shrug It Off", "SKILL")],
            hand=[],
        )

        self.assertTrue(LiquidMemoriesHandler().can_handle(state))

    def test_liquid_memories_grid_picks_discard_lethal(self):
        cards = [
            self._card("Defend_R", "SKILL"),
            self._card("Strike_R", "ATTACK", upgrades=1),
        ]
        state = self._potion_state(
            "LiquidMemories",
            hp=30,
            room_type="MonsterRoomBoss",
            monsters=[self._monster(current_hp=9, move_damage=0)],
            screen_type="GRID",
            screen_state={"cards": cards, "num_cards": 1, "for_purge": False},
            choice_list=[card["name"] for card in cards],
            current_action="LiquidMemoryAction",
            available_commands=["choose", "potion", "wait", "state"],
        )
        handler = LiquidMemoriesGridHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["wait 30", "choose 1", "wait 30"], handler.handle(state).commands)

    def test_liquid_memories_grid_picks_rescue_block(self):
        cards = [
            self._card("Strike_R", "ATTACK"),
            self._card("Shrug It Off", "SKILL"),
        ]
        state = self._potion_state(
            "LiquidMemories",
            hp=10,
            room_type="MonsterRoomBoss",
            monsters=[self._monster(current_hp=80, move_damage=30)],
            screen_type="GRID",
            screen_state={"cards": cards, "num_cards": 1, "for_purge": False},
            choice_list=[card["name"] for card in cards],
            current_action="LiquidMemoryAction",
            available_commands=["choose", "potion", "wait", "state"],
        )
        handler = LiquidMemoriesGridHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["wait 30", "choose 1", "wait 30"], handler.handle(state).commands)

    def test_liquid_memories_grid_does_not_handle_headbutt_grid(self):
        cards = [
            self._card("Strike_R", "ATTACK"),
            self._card("Shrug It Off", "SKILL"),
        ]
        state = self._potion_state(
            "Potion Slot",
            hp=30,
            room_type="MonsterRoom",
            screen_type="GRID",
            screen_state={"cards": cards, "num_cards": 1, "for_purge": False},
            choice_list=[card["name"] for card in cards],
            current_action="DiscardPileToTopOfDeckAction",
            available_commands=["choose", "wait", "state"],
        )

        self.assertFalse(LiquidMemoriesGridHandler().can_handle(state))

    @staticmethod
    def _potion_state(
            potion_id: str,
            hp: int,
            room_type: str,
            requires_target: bool = False,
            monsters: list[dict] = None,
            discard_pile: list[dict] = None,
            hand: list[dict] = None,
            screen_type: str = "NONE",
            screen_state: dict = None,
            choice_list: list[str] = None,
            current_action: str = None,
            available_commands: list[str] = None,
            energy: int = 3,
    ) -> GameState:
        if available_commands is None:
            available_commands = ["play", "end", "potion", "wait", "state"]
        if monsters is None:
            monsters = [PotionsHandlerTestCase._monster()]
        if discard_pile is None:
            discard_pile = []
        if hand is None:
            hand = []
        if screen_state is None:
            screen_state = {}
        if choice_list is None:
            choice_list = []

        game_state = {
            "screen_type": screen_type,
            "screen_state": screen_state,
            "choice_list": choice_list,
            "seed": 1,
            "combat_state": {
                "draw_pile": [],
                "discard_pile": discard_pile,
                "exhaust_pile": [],
                "cards_discarded_this_turn": 0,
                "times_damaged": 0,
                "monsters": monsters,
                "turn": 1,
                "limbo": [],
                "hand": hand,
                "player": {
                    "orbs": [],
                    "current_hp": hp,
                    "block": 0,
                    "max_hp": 80,
                    "powers": [],
                    "energy": energy,
                },
            },
            "deck": hand + discard_pile,
            "relics": [{"name": "Burning Blood", "id": "Burning Blood", "counter": -1}],
            "max_hp": 80,
            "act_boss": "The Guardian",
            "gold": 0,
            "action_phase": "WAITING_ON_USER",
            "act": 1,
            "screen_name": screen_type,
            "room_phase": "COMBAT",
            "is_screen_up": screen_type != "NONE",
            "potions": [{
                "requires_target": requires_target,
                "can_use": True,
                "can_discard": True,
                "name": potion_id,
                "id": potion_id,
            }],
            "current_hp": hp,
            "floor": 1,
            "ascension_level": 0,
            "class": "IRONCLAD",
            "map": [],
            "room_type": room_type,
        }
        if current_action is not None:
            game_state["current_action"] = current_action

        return GameState(
            {
                "available_commands": available_commands,
                "ready_for_command": True,
                "in_game": True,
                "game_state": game_state,
            },
            TheBotsMemoryBook.new_default(),
        )

    @staticmethod
    def _monster(current_hp: int = 50, move_damage: int = 6) -> dict:
        return {
            "is_gone": False,
            "move_hits": 1,
            "move_base_damage": move_damage,
            "move_adjusted_damage": move_damage,
            "max_hp": max(50, current_hp),
            "name": "Cultist",
            "current_hp": current_hp,
            "block": 0,
            "id": "Cultist",
            "powers": [],
        }

    @staticmethod
    def _card(card_id: str, card_type: str, upgrades: int = 0) -> dict:
        return {
            "exhausts": False,
            "is_playable": True,
            "cost": 1,
            "name": card_id_to_test_name(card_id, upgrades),
            "id": card_id,
            "type": card_type,
            "ethereal": False,
            "uuid": card_id + str(upgrades),
            "upgrades": upgrades,
            "rarity": "BASIC",
            "has_target": card_type == "ATTACK",
        }


def card_id_to_test_name(card_id: str, upgrades: int) -> str:
    name = card_id.replace("_R", "").replace("_", " ")
    return name + ("+" if upgrades else "")


if __name__ == '__main__':
    unittest.main()
