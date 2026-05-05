import unittest

from ai.requested_strike.rs_test_handler_fixture import RsTestHandlerFixture
from rs.ai.requested_strike.ironclad_comparator import (
    ironclad_comparisons,
    least_nob_adjusted_scaling_damage,
    prefers_armaments_played,
    prefers_block_under_threat,
    prefers_strength_gain,
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


if __name__ == '__main__':
    unittest.main()
