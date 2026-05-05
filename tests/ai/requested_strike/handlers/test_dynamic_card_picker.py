import unittest

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


if __name__ == '__main__':
    unittest.main()
