import unittest

from ai.requested_strike.rs_test_handler_fixture import RsTestHandlerFixture
from rs.ai.requested_strike.handlers.potions_handler import PotionsEliteHandler, PotionsBossHandler
from rs.common.handlers.common_battle_handler import CommonBattleHandler
from test_helpers.resources import load_resource_state


class PotionsHandlerTestCase(RsTestHandlerFixture):
    def test_elite_potions_handler(self):
        self.handler = PotionsEliteHandler
        self.execute_handler_tests('/other/potions_elite.json', ['wait 30', 'potion use 0 0', 'wait 30'])

    def test_potions_dead_minions(self):
        self.handler = PotionsEliteHandler
        self.execute_handler_tests('/other/potions_dead_minions.json', ['wait 30', 'potion use 1 4', 'wait 30'])

    def test_potions_reptomancer(self):
        self.handler = PotionsEliteHandler
        self.execute_handler_tests('/other/potions_reptomancer.json', ['wait 30', 'potion use 1 3', 'wait 30'])

    def test_boss_potions_handler(self):
        self.handler = PotionsBossHandler
        self.execute_handler_tests('/other/potions_boss.json', ['wait 30', 'potion use 0 0', 'wait 30'])

    def test_do_not_use_potion(self):
        self.handler = CommonBattleHandler
        self.execute_handler_tests('/other/potions_boss_disliked_potion.json', ['play 4 0'])

    def test_lagavulin_uses_setup_potion_before_waking(self):
        state = load_resource_state(
            '/battles/specific_comparator_cases/waiting_lagavulin/waiting_lagavulin_turn_1_without_powers.json')
        state.game_state()['potions'][0] = {
            "requires_target": False,
            "can_use": True,
            "can_discard": True,
            "name": "Strength Potion",
            "id": "Strength Potion",
        }

        handler = PotionsEliteHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(['wait 30', 'potion use 0', 'wait 30'], handler.handle(state).commands)

    def test_gremlin_nob_uses_offensive_potion_before_low_hp(self):
        state = load_resource_state('/battles/specific_comparator_cases/gremlin_nob/gremlin_nob_defend_early.json')

        handler = PotionsEliteHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(['wait 30', 'potion use 0 0', 'wait 30'], handler.handle(state).commands)

    def test_three_sentries_prioritizes_explosive_potion(self):
        state = load_resource_state('/battles/specific_comparator_cases/three_sentries/sentry_yolo_state_with_three.json')
        state.game_state()['potions'][0] = {
            "requires_target": False,
            "can_use": True,
            "can_discard": True,
            "name": "Block Potion",
            "id": "BlockPotion",
        }
        state.game_state()['potions'][1] = {
            "requires_target": False,
            "can_use": True,
            "can_discard": True,
            "name": "Explosive Potion",
            "id": "ExplosivePotion",
        }

        handler = PotionsEliteHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(['wait 30', 'potion use 1', 'wait 30'], handler.handle(state).commands)


if __name__ == '__main__':
    unittest.main()
