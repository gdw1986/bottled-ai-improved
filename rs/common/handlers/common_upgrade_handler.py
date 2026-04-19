from typing import List

from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class CommonUpgradeHandler(Handler):

    def __init__(self, priorities: List[str]):
        self.upgrade_priorities: List[str] = priorities

    def can_handle(self, state: GameState) -> bool:
        return state.has_command(Command.CHOOSE) \
               and state.game_state()["screen_type"] == "GRID" \
               and state.game_state()["screen_state"]["for_upgrade"]

    def transform_priorities_based_on_game_state(self, priorities: List[str], state: GameState):
        # can be implemented by children
        pass

    def handle(self, state: GameState) -> HandlerAction:
        choice_list = state.game_state()["choice_list"]

        # we have to copy this, otherwise it will modify the list until the bot is rerun
        transformed_priorities = self.upgrade_priorities.copy()
        self.transform_priorities_based_on_game_state(transformed_priorities, state)

        # Use get_choice_list() for matching (auto-translated to English), but use raw list for index
        translated_list = state.get_choice_list()
        for priority in transformed_priorities:
            if priority in translated_list:
                idx = translated_list.index(priority)
                if presentation_mode:
                    return HandlerAction(commands=[p_delay, "choose " + str(idx), p_delay_s])
                return HandlerAction(commands=["choose " + str(idx)])
        if presentation_mode:
            return HandlerAction(commands=[p_delay, "choose 0", p_delay_s])
        return HandlerAction(commands=["choose 0"])
