import unittest
from types import SimpleNamespace

from ai.requested_strike.rs_test_handler_fixture import RsTestHandlerFixture
from rs.calculator.interfaces.memory_items import MemoryItem
from rs.ai.requested_strike.ironclad_comparator import (
    ironclad_comparisons,
    least_nob_adjusted_scaling_damage,
    prefers_armaments_played,
    prefers_block_under_threat,
    prefers_strength_gain,
    most_enemy_strength_reduction,
    lowest_health_monster,
    lowest_total_monster_health,
    most_enemy_vulnerable,
    most_retained_block_saved_for_next_turn,
    prefers_less_nob_enrage,
    raw_incoming_damage,
)
from rs.calculator.enums.power_id import PowerId
from rs.calculator.enums.relic_id import RelicId
from rs.ai.requested_strike.handlers.battle_handler import IroncladBattleHandler
from rs.calculator.game_state_converter import create_battle_state
from rs.game.card import CardType
from rs.machine.state import GameState
from rs.machine.the_bots_memory_book import TheBotsMemoryBook


class RequestedStrikeBattleHandlerTestCase(RsTestHandlerFixture):
    handler = IroncladBattleHandler

    def test_apotheosis_is_played_before_other_cards(self):
        state = self._combat_state([
            self._card("Strike_R", "打击+", "ATTACK", cost=1, upgrades=1, has_target=True),
            self._card("Apotheosis", "神化", "SKILL", cost=2, exhausts=True),
        ], energy=2)

        actual = IroncladBattleHandler().handle(state)

        self.assertEqual(["play 2"], actual.commands)
        self.assertEqual(CardType.SKILL, actual.memory_book.memory_general[MemoryItem.TYPE_LAST_PLAYED])

    @staticmethod
    def _combat_state(hand: list[dict], energy: int = 3, monsters: list[dict] | None = None) -> GameState:
        return GameState(
            {
                "available_commands": ["play", "end", "potion", "wait", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_type": "NONE",
                    "screen_state": {},
                    "seed": 1,
                    "combat_state": {
                        "draw_pile": [],
                        "discard_pile": [],
                        "exhaust_pile": [],
                        "cards_discarded_this_turn": 0,
                        "times_damaged": 0,
                        "monsters": monsters or [{
                            "is_gone": False,
                            "move_hits": 0,
                            "move_base_damage": -1,
                            "max_hp": 6,
                            "name": "Cultist",
                            "current_hp": 6,
                            "block": 0,
                            "id": "Cultist",
                            "powers": [],
                        }],
                        "turn": 1,
                        "limbo": [],
                        "hand": hand,
                        "player": {
                            "orbs": [],
                            "current_hp": 70,
                            "block": 0,
                            "max_hp": 80,
                            "powers": [],
                            "energy": energy,
                        },
                    },
                    "deck": hand,
                    "relics": [{"name": "Burning Blood", "id": "Burning Blood", "counter": -1}],
                    "max_hp": 80,
                    "act_boss": "The Guardian",
                    "gold": 0,
                    "action_phase": "WAITING_ON_USER",
                    "act": 1,
                    "screen_name": "NONE",
                    "room_phase": "COMBAT",
                    "is_screen_up": False,
                    "potions": [],
                    "current_hp": 70,
                    "floor": 1,
                    "ascension_level": 0,
                    "class": "IRONCLAD",
                    "map": [],
                    "room_type": "MonsterRoom",
                },
            },
            TheBotsMemoryBook.new_default(),
        )

    @staticmethod
    def _card(card_id: str, name: str, card_type: str, cost: int = 1,
              upgrades: int = 0, exhausts: bool = False, has_target: bool = False) -> dict:
        return {
            "exhausts": exhausts,
            "is_playable": True,
            "cost": cost,
            "name": name,
            "id": card_id,
            "type": card_type,
            "ethereal": False,
            "uuid": card_id,
            "upgrades": upgrades,
            "rarity": "RARE",
            "has_target": has_target,
        }

    @staticmethod
    def _assessment(saved_block: int, powers: dict | None = None, relics: dict | None = None):
        return SimpleNamespace(
            state=SimpleNamespace(
                saved_block_for_next_turn=saved_block,
                player=SimpleNamespace(powers=powers or {}),
                relics=relics or {},
            ),
            block_for_next_turn=lambda: saved_block,
        )

    def test_raw_incoming_damage_counts_multi_hits(self):
        state = self._combat_state([], monsters=[{
            "is_gone": False,
            "move_hits": 5,
            "move_base_damage": 6,
            "max_hp": 164,
            "name": "Book of Stabbing",
            "current_hp": 164,
            "block": 0,
            "id": "BookOfStabbing",
            "powers": [{"amount": 3, "name": "Strength", "id": "Strength"}],
        }])

        battle_state = create_battle_state(state)

        self.assertEqual(45, raw_incoming_damage(battle_state))

    def test_gremlin_nob_defensive_skill_not_worth_it(self):
        self.execute_handler_tests(
            'battles/specific_comparator_cases/gremlin_nob/gremlin_nob_defend_early.json',
            ['end']
        )

    def test_gremlin_nob_defensive_skill_worth_it_when_nob_is_low(self):
        self.execute_handler_tests(
            'battles/specific_comparator_cases/gremlin_nob/gremlin_nob_defend_late.json',
            ['play 5']
        )

    def test_gremlin_nob_avoids_defend_when_enrage_still_matters(self):
        state = self._combat_state([
            self._card("Defend_R", "Defend", "SKILL", cost=1),
        ], energy=1, monsters=[{
            "is_gone": False,
            "move_hits": 1,
            "move_base_damage": 14,
            "max_hp": 86,
            "name": "Gremlin Nob",
            "current_hp": 20,
            "block": 0,
            "id": "GremlinNob",
            "powers": [{"amount": 2, "name": "Enrage", "id": "Anger"}],
        }])

        actual = IroncladBattleHandler().handle(state)

        self.assertEqual(["end"], actual.commands)

    def test_gremlin_nob_scaling_damage_is_checked_before_ironclad_preferences(self):
        direct_enrage_index = ironclad_comparisons.index(prefers_less_nob_enrage)
        nob_index = ironclad_comparisons.index(least_nob_adjusted_scaling_damage)

        self.assertLess(direct_enrage_index, nob_index)
        self.assertLess(nob_index, ironclad_comparisons.index(prefers_block_under_threat))
        self.assertLess(nob_index, ironclad_comparisons.index(prefers_strength_gain))

    def test_armaments_plus_is_checked_before_strength_preferences(self):
        armaments_index = ironclad_comparisons.index(prefers_armaments_played)

        self.assertLess(armaments_index, ironclad_comparisons.index(prefers_strength_gain))

    def test_enemy_strength_reduction_is_after_damage_metrics_but_before_vulnerable(self):
        """Verify most_enemy_strength_reduction is positioned after lowest_total_monster_health
        but before most_enemy_vulnerable. This ensures Disarm is valued after kill metrics
        but before generic status effects."""
        str_red_idx = ironclad_comparisons.index(most_enemy_strength_reduction)
        total_hp_idx = ironclad_comparisons.index(lowest_total_monster_health)
        vuln_idx = ironclad_comparisons.index(most_enemy_vulnerable)

        self.assertLess(total_hp_idx, str_red_idx,
                        "strength_reduction should come after total_monster_health")
        self.assertLess(str_red_idx, vuln_idx,
                        "strength_reduction should come before enemy_vulnerable")

    def test_ordinary_overblock_is_not_preferred_as_saved_block(self):
        best = self._assessment(saved_block=0)
        challenger = self._assessment(saved_block=10)

        self.assertIsNone(most_retained_block_saved_for_next_turn(best, challenger))

    def test_retained_block_is_still_preferred_with_block_retention(self):
        best = self._assessment(saved_block=3, powers={PowerId.BARRICADE: 1})
        challenger = self._assessment(saved_block=10, powers={PowerId.BARRICADE: 1})

        self.assertTrue(most_retained_block_saved_for_next_turn(best, challenger))

    def test_calipers_saved_block_is_still_preferred(self):
        best = self._assessment(saved_block=0, relics={RelicId.CALIPERS: 1})
        challenger = self._assessment(saved_block=5, relics={RelicId.CALIPERS: 1})

        self.assertTrue(most_retained_block_saved_for_next_turn(best, challenger))


if __name__ == '__main__':
    unittest.main()
