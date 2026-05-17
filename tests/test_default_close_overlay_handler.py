import unittest
from unittest.mock import MagicMock

from rs.machine.command import Command
from rs.machine.handlers.default_close_overlay import DefaultCloseOverlayHandler


class DefaultCloseOverlayHandlerTestCase(unittest.TestCase):

    def test_closes_master_deck_view_with_key_cancel(self):
        state = MagicMock()
        state.has_command.side_effect = lambda command: command == Command.KEY
        state.game_state.return_value = {
            "is_screen_up": True,
            "screen_name": "MASTER_DECK_VIEW",
        }
        state.screen_type.return_value = "NONE"

        handler = DefaultCloseOverlayHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["key cancel", "wait 30"], handler.handle(state).commands)

    def test_closes_settings_overlay_with_key_cancel(self):
        state = MagicMock()
        state.has_command.side_effect = lambda command: command == Command.KEY
        state.game_state.return_value = {
            "is_screen_up": True,
            "screen_name": "SETTINGS",
        }
        state.screen_type.return_value = "NONE"

        handler = DefaultCloseOverlayHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["key cancel", "wait 30"], handler.handle(state).commands)

    def test_does_not_handle_when_overlay_is_not_up(self):
        state = MagicMock()
        state.has_command.side_effect = lambda command: command == Command.KEY
        state.game_state.return_value = {
            "is_screen_up": False,
            "screen_name": "MASTER_DECK_VIEW",
        }
        state.screen_type.return_value = "NONE"

        self.assertFalse(DefaultCloseOverlayHandler().can_handle(state))

    def test_does_not_handle_choice_screens(self):
        state = MagicMock()
        state.has_command.side_effect = lambda command: command == Command.KEY
        state.game_state.return_value = {
            "is_screen_up": True,
            "screen_name": "MASTER_DECK_VIEW",
        }
        state.screen_type.return_value = "BOSS_REWARD"

        self.assertFalse(DefaultCloseOverlayHandler().can_handle(state))


if __name__ == "__main__":
    unittest.main()
