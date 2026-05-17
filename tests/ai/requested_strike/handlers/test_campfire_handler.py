from unittest import TestCase
from unittest.mock import MagicMock

from rs.ai.requested_strike.handlers.campfire_handler import IroncladCampfireHandler


class IroncladCampfireHandlerTestCase(TestCase):

    def test_uses_named_rest_choice_after_fusion_hammer(self):
        state = MagicMock()
        state.get_choice_list.return_value = ["rest", "recall"]
        state.game_state.return_value = {"act": 2}
        state.has_relic.return_value = False
        state.floor.return_value = 23
        state.get_player_health_percentage.return_value = 34 / 80
        state.deck.contains_cards.return_value = False
        state.deck.contains_curses_we_can_remove.return_value = False

        action = IroncladCampfireHandler().handle(state)

        self.assertEqual(["choose rest"], action.commands)
