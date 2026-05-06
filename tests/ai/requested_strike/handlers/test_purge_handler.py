from copy import deepcopy
import unittest

from rs.ai.requested_strike.handlers.purge_handler import PurgeHandler
from rs.ai.requested_strike.requested_strike import REQUESTED_STRIKE
from rs.machine.state import GameState
from rs.machine.the_bots_memory_book import TheBotsMemoryBook
from test_helpers.resources import load_resource_state


class RequestedStrikePurgeHandlerTestCase(unittest.TestCase):

    def test_purge_handler_runs_before_generic_grid_select(self):
        state = self._build_purge_state()

        for handler in REQUESTED_STRIKE.handlers:
            if handler.can_handle(state):
                self.assertIsInstance(handler, PurgeHandler)
                return

        self.fail("No requested_strike handler accepted the purge state")

    def test_purge_keeps_feel_no_pain_when_a_removal_card_is_available(self):
        state = self._build_purge_state()

        self.assertEqual(['choose 1', 'wait 30'], PurgeHandler().handle(state).commands)

    def test_empty_cage_multi_select_no_duplicate_indices(self):
        """Bug fix: when num_cards=2 (e.g. Empty Cage), duplicate card names in
        choice_list must map to DISTINCT indices. Previously, 3 Strike_R cards
        all mapped to index 0, causing choose 0 to select-then-deselect in a loop.
        """
        state = self._build_multi_purge_state()

        action = PurgeHandler().handle(state)
        # Should select 2 different Strike cards, not the same one twice
        choose_commands = [c for c in action.commands if c.startswith('choose')]
        self.assertEqual(2, len(choose_commands))
        # The two indices must be DIFFERENT
        idx0 = int(choose_commands[0].split()[1])
        idx1 = int(choose_commands[1].split()[1])
        self.assertNotEqual(idx0, idx1,
                            f"choose {idx0} twice would toggle select/deselect -> infinite loop")

    @staticmethod
    def _build_purge_state() -> GameState:
        raw = deepcopy(load_resource_state('/other/purge_regular.json').json)
        cards = [
            {
                "exhausts": False,
                "cost": 1,
                "name": "Feel No Pain",
                "id": "Feel No Pain",
                "type": "POWER",
                "ethereal": False,
                "uuid": "feel-no-pain",
                "upgrades": 0,
                "rarity": "UNCOMMON",
                "has_target": False,
            },
            {
                "exhausts": False,
                "cost": 1,
                "name": "Strike",
                "id": "Strike_R",
                "type": "ATTACK",
                "ethereal": False,
                "uuid": "strike-r",
                "upgrades": 0,
                "rarity": "BASIC",
                "has_target": True,
            },
            {
                "exhausts": False,
                "cost": 2,
                "name": "Bash",
                "id": "Bash",
                "type": "ATTACK",
                "ethereal": False,
                "uuid": "bash",
                "upgrades": 0,
                "rarity": "BASIC",
                "has_target": True,
            },
        ]
        raw["game_state"]["choice_list"] = [card["name"] for card in cards]
        raw["game_state"]["screen_state"]["cards"] = cards
        raw["game_state"]["screen_state"]["for_purge"] = True
        raw["game_state"]["screen_state"]["num_cards"] = 1
        raw["game_state"]["deck"] = cards
        return GameState(raw, TheBotsMemoryBook.new_default())

    @staticmethod
    def _build_multi_purge_state() -> GameState:
        """Simulate Empty Cage (num_cards=2) with 3 Strikes in deck."""
        raw = deepcopy(load_resource_state('/other/purge_regular.json').json)
        cards = [
            {
                "exhausts": False, "cost": 1, "name": "Strike", "id": "Strike_R",
                "type": "ATTACK", "ethereal": False, "uuid": "strike-r-1",
                "upgrades": 0, "rarity": "BASIC", "has_target": True,
            },
            {
                "exhausts": False, "cost": 1, "name": "Strike", "id": "Strike_R",
                "type": "ATTACK", "ethereal": False, "uuid": "strike-r-2",
                "upgrades": 0, "rarity": "BASIC", "has_target": True,
            },
            {
                "exhausts": False, "cost": 1, "name": "Strike", "id": "Strike_R",
                "type": "ATTACK", "ethereal": False, "uuid": "strike-r-3",
                "upgrades": 0, "rarity": "BASIC", "has_target": True,
            },
            {
                "exhausts": False, "cost": 1, "name": "Defend", "id": "Defend_R",
                "type": "SKILL", "ethereal": False, "uuid": "defend-r-1",
                "upgrades": 0, "rarity": "BASIC", "has_target": False,
            },
            {
                "exhausts": False, "cost": 2, "name": "Bash", "id": "Bash",
                "type": "ATTACK", "ethereal": False, "uuid": "bash",
                "upgrades": 0, "rarity": "BASIC", "has_target": True,
            },
        ]
        raw["game_state"]["choice_list"] = [card["name"] for card in cards]
        raw["game_state"]["screen_state"]["cards"] = cards
        raw["game_state"]["screen_state"]["for_purge"] = True
        raw["game_state"]["screen_state"]["num_cards"] = 2  # Empty Cage: remove 2
        raw["game_state"]["deck"] = cards
        return GameState(raw, TheBotsMemoryBook.new_default())


if __name__ == '__main__':
    unittest.main()
