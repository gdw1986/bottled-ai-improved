import unittest
from unittest.mock import patch

from rs.ai.requested_strike.handlers.card_reward_handler import DynamicCardRewardHandler
from rs.ai.requested_strike.handlers.dynamic_card_picker import (
    _lookup_card_data,
    deck_features,
    strength_synergy_bonus,
)


class DynamicCardPickerTestCase(unittest.TestCase):

    def test_lowercase_card_names_match_data_file(self):
        self.assertIsNotNone(_lookup_card_data('inflame'))
        self.assertIsNotNone(_lookup_card_data('spot weakness'))
        self.assertIsNotNone(_lookup_card_data('heavy blade'))

    def test_strength_features_work_with_lowercase_deck_names(self):
        features = deck_features(['inflame', 'flex', 'heavy blade'])

        self.assertEqual(1, features['has_strength_source'])
        self.assertEqual(1, features['has_strength_payoff'])
        self.assertEqual(1, features['attack_cnt'])  # Flex is a skill, not an attack.

    def test_strength_payoff_gets_bonus_when_strength_source_exists(self):
        self.assertGreater(
            strength_synergy_bonus('heavy blade', ['inflame'], act=2),
            strength_synergy_bonus('heavy blade', [], act=2)
        )

    def test_limit_break_waits_for_strength_source(self):
        self.assertGreater(
            strength_synergy_bonus('limit break', ['spot weakness'], act=2),
            strength_synergy_bonus('limit break', [], act=2)
        )

    def test_dynamic_reward_uses_current_act_and_respects_copy_caps(self):
        class FakeState:
            def get_choice_list_upgrade_stripped_from_choice(self):
                return ['shockwave', 'perfected strike']

            def get_deck_card_list_by_name_with_upgrade_stripped(self):
                return {'perfected strike': 3}

            def game_state(self):
                return {'room_phase': 'COMPLETE'}

            def act(self):
                return 2

        handler = DynamicCardRewardHandler({'shockwave': 1, 'perfected strike': 3})

        with patch('rs.ai.requested_strike.handlers.card_reward_handler.pick_best_card') as picker:
            picker.return_value = 'shockwave'
            action = handler.handle(FakeState())

        picker.assert_called_once_with(['shockwave'], ['perfected strike'] * 3, 2, min_samples=20)
        self.assertEqual(['choose 0', 'wait 30'], action.commands)

    def test_act1_survival_fallback_handles_cards_outside_main_pool(self):
        class FakeState:
            def get_choice_list_upgrade_stripped_from_choice(self):
                return ['uppercut', 'ghostly armor']

            def get_deck_card_list_by_name_with_upgrade_stripped(self):
                return {}

            def game_state(self):
                return {'room_phase': 'COMPLETE'}

            def act(self):
                return 1

        handler = DynamicCardRewardHandler({'shrug it off': 1})

        with patch('rs.ai.requested_strike.handlers.card_reward_handler.pick_best_card') as picker:
            action = handler.handle(FakeState())

        picker.assert_not_called()
        self.assertEqual(['choose 0', 'wait 30'], action.commands)


if __name__ == '__main__':
    unittest.main()
