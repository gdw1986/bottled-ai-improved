from typing import List

from rs.game.screen_type import ScreenType
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class CommonShopEntranceHandler(Handler):

    def can_handle(self, state: GameState) -> bool:
        return state.has_command(Command.CHOOSE) \
               and state.screen_type() == ScreenType.SHOP_ROOM.value

    def handle(self, state: GameState) -> HandlerAction:
        # choice_list for SHOP_ROOM contains "shop" (or localized), use index 0
        return HandlerAction(commands=["choose 0", "wait 30"])
