from typing import List

from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class CommonGridSelectHandler(Handler):
    """
    Handles GRID screens that require selecting multiple cards.
    This covers events like Augmenter that use for_transform=False but still need multi-select.
    """

    def __init__(self, preferences: List[str]):
        self.preferences: List[str] = preferences

    def can_handle(self, state: GameState) -> bool:
        if not state.has_command(Command.CHOOSE):
            return False
        if state.game_state().get("screen_type") != "GRID":
            return False
        screen_state = state.game_state().get("screen_state", {})
        if screen_state.get("for_purge"):
            return False
        # Handle any GRID with num_cards > 0 (multi-select)
        num_cards = screen_state.get("num_cards", 0)
        return num_cards > 0

    def handle(self, state: GameState) -> HandlerAction:
        choices = state.get_choice_list()
        screen_state = state.game_state().get("screen_state", {})

        num_cards = screen_state.get("num_cards", 1)
        already_selected = len(screen_state.get("selected_cards", []))
        cards_to_select = num_cards - already_selected

        def append_confirm_if_available(commands: List[str]):
            if state.has_command(Command.CONFIRM):
                commands.append("confirm")
                commands.append("wait 30")

        if cards_to_select <= 0:
            commands = ["wait 30"]
            append_confirm_if_available(commands)
            return HandlerAction(commands=commands)

        # Build ordered list of choices based on preferences
        ordered_choices = []
        for pref in self.preferences:
            for i, card in enumerate(choices):
                if pref.lower() in card.lower() and i not in ordered_choices:
                    ordered_choices.append(i)

        # Add remaining cards not in preferences
        for i in range(len(choices)):
            if i not in ordered_choices:
                ordered_choices.append(i)

        # Select the required number of cards
        commands = ["wait 30"]
        for c in ordered_choices[:cards_to_select]:
            commands.append("choose " + str(c))
            commands.append("wait 30")

        append_confirm_if_available(commands)
        return HandlerAction(commands=commands)
