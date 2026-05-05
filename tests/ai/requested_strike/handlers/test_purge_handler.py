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


if __name__ == '__main__':
    unittest.main()
