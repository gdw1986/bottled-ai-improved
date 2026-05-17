import unittest
from types import SimpleNamespace
from unittest.mock import patch

from rs.calculator.executor import (
    get_discard_commands,
    get_exhaust_commands,
    get_best_battle_action_with_retry,
    _stable_shuffle_seed,
)
from rs.calculator.battle_state import PLAY_DISCARD, PLAY_EXHAUST
from test_helpers.resources import load_resource_state


class CalculatorExecutorTestCase(unittest.TestCase):

    def test_simple_discard_command_case(self):
        # given
        plays = [(0, PLAY_DISCARD), (0, PLAY_DISCARD), (0, PLAY_DISCARD)]
        # when
        result = get_discard_commands(plays)
        # then
        self.assertEqual(["choose 0", "choose 1", "choose 2", "confirm", "wait 30"], result)

    def test_complex_discard_command_case(self):
        # given
        plays = [(2, PLAY_DISCARD), (1, PLAY_DISCARD), (3, PLAY_DISCARD)]
        # when
        result = get_discard_commands(plays)
        # then
        self.assertEqual(["choose 2", "choose 1", "choose 5", "confirm", "wait 30"], result)

    def test_partial_discard_command_case(self):
        # given
        plays = [(2, PLAY_DISCARD), (1, -1), (3, PLAY_DISCARD)]
        # when
        result = get_discard_commands(plays)
        # then
        self.assertEqual(["choose 2", "confirm", "wait 30"], result)

    def test_simple_exhaust_command_case(self):
        # given
        plays = [(0, PLAY_EXHAUST), (0, PLAY_EXHAUST), (0, PLAY_EXHAUST)]
        # when
        result = get_exhaust_commands(plays)
        # then
        self.assertEqual(["choose 0", "choose 1", "choose 2", "confirm", "wait 30"], result)

    def test_complex_exhaust_command_case(self):
        # given
        plays = [(2, PLAY_EXHAUST), (1, PLAY_EXHAUST), (3, PLAY_EXHAUST)]
        # when
        result = get_exhaust_commands(plays)
        # then
        self.assertEqual(["choose 2", "choose 1", "choose 5", "confirm", "wait 30"], result)

    def test_partial_exhaust_command_case(self):
        # given
        plays = [(2, PLAY_EXHAUST), (1, -1), (3, PLAY_EXHAUST)]
        # when
        result = get_exhaust_commands(plays)
        # then
        self.assertEqual(["choose 2", "confirm", "wait 30"], result)

    def test_retry_shuffle_seed_is_stable_for_same_state(self):
        first_state = load_resource_state("other/potions_boss.json")
        second_state = load_resource_state("other/potions_boss.json")

        self.assertEqual(_stable_shuffle_seed(first_state, 0), _stable_shuffle_seed(second_state, 0))
        self.assertNotEqual(_stable_shuffle_seed(first_state, 0), _stable_shuffle_seed(first_state, 1))

    def test_retry_uses_comparator_not_final_hp_only(self):
        game_state = load_resource_state("other/potions_boss.json")
        weaker_path = SimpleNamespace(
            plays=[(0, 0)],
            state=SimpleNamespace(score=1, player=SimpleNamespace(current_hp=70)),
        )
        stronger_path = SimpleNamespace(
            plays=[(1, 0)],
            state=SimpleNamespace(score=2, player=SimpleNamespace(current_hp=70)),
        )

        class ScoreComparator:
            def does_challenger_defeat_the_best(self, best, challenger, _original):
                return challenger.score > best.score

        with patch(
                "rs.calculator.executor.get_best_battle_path",
                side_effect=[weaker_path, stronger_path]):
            action = get_best_battle_action_with_retry(
                game_state,
                ScoreComparator(),
                retries=2,
            )

        self.assertEqual(["play 2 0"], action.commands)
