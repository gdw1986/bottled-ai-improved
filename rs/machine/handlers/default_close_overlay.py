from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class DefaultCloseOverlayHandler(Handler):
    """Close non-choice overlay screens that otherwise fall into wait loops."""

    closeable_screen_names = {
        "MASTER_DECK_VIEW",
    }

    def can_handle(self, state: GameState) -> bool:
        return (
            state.has_command(Command.KEY)
            and state.game_state().get("is_screen_up")
            and state.screen_type() == "NONE"
            and state.game_state().get("screen_name") in self.closeable_screen_names
        )

    def handle(self, state: GameState) -> HandlerAction:
        return HandlerAction(commands=["key cancel", "wait 30"])
