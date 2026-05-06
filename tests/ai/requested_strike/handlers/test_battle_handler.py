import unittest

from ai.requested_strike.rs_test_handler_fixture import RsTestHandlerFixture
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
)
from rs.ai.requested_strike.handlers.battle_handler import IroncladBattleHandler


class RequestedStrikeBattleHandlerTestCase(RsTestHandlerFixture):
    handler = IroncladBattleHandler

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

    def test_gremlin_nob_scaling_damage_is_checked_before_ironclad_preferences(self):
        nob_index = ironclad_comparisons.index(least_nob_adjusted_scaling_damage)

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


if __name__ == '__main__':
    unittest.main()
