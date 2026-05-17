import unittest
from unittest.mock import MagicMock

from rs.machine.command import Command
from rs.machine.handlers.default_return import DefaultReturnHandler


class DefaultReturnHandlerTestCase(unittest.TestCase):

    def test_handles_return_command(self):
        state = MagicMock()
        state.has_command.side_effect = lambda command: command == Command.RETURN

        handler = DefaultReturnHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["return"], handler.handle(state).commands)

    def test_does_not_handle_without_return_command(self):
        state = MagicMock()
        state.has_command.return_value = False

        handler = DefaultReturnHandler()

        self.assertFalse(handler.can_handle(state))


if __name__ == "__main__":
    unittest.main()
