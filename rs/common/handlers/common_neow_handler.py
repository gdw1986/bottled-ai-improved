from typing import List

from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.game.screen_type import ScreenType
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState

# We don't cover choice 2, which is an option constructed out of a buff AND a debuff. 3 is always relic swap.
default_desired_choices = [
    'obtain a random common relic',
    'upgrade a card',
    'obtain 100 gold',
    'choose a card to obtain',
    'enemies in your next three combats have 1 hp',
    'remove a card from your deck',
    'obtain 3 random potions',
    'max hp +8',
    'transform a card',
    'lose your starting relic obtain a random boss relic',
    'obtain a random rare card',
    'choose a colorless card to obtain',
]

# In Chinese game environment, CommunicationMod sends GBK-encoded choice_list text
# which gets corrupted when Python reads as UTF-8. Match by option position instead of text.
_NEOW_POSITION_MAP = {
    # First Neow (before floor 1): 4 options in fixed positions
    'obtain a random rare card': {0},
    'obtain 3 random potions': {1},
    'receive a curse. obtain a random rare card': {2},
    'lose your starting relic obtain a random boss relic': {3},
    # Later Neow options: can be at any position
    'choose a card to obtain': {0, 1, 2, 3},
    'upgrade a card': {0, 1, 2, 3},
    'obtain 100 gold': {0, 1, 2, 3},
    'transform a card': {0, 1, 2, 3},
    'remove a card from your deck': {0, 1, 2, 3},
    'max hp +8': {0, 1, 2, 3},
    'max hp +7': {0, 1, 2, 3},
    'max hp +14': {0, 1, 2, 3},
    'obtain a random common relic': {0, 1, 2, 3},
    'enemies in your next three combats have 1 hp': {0, 1, 2, 3},
    'choose a colorless card to obtain': {0, 1, 2, 3},
}


class CommonNeowHandler(Handler):

    def __init__(self, desired_choices: List[str] = None):
        self.desired_choices: List[str] = default_desired_choices if desired_choices is None else desired_choices

    def can_handle(self, state: GameState) -> bool:
        return state.screen_type() == ScreenType.EVENT.value \
               and state.has_command(Command.CHOOSE) \
               and state.game_state()['screen_state']['event_id'] == "Neow Event"

    def handle(self, state: GameState) -> HandlerAction:
        if "leave" in state.get_choice_list():
            if presentation_mode:
                return HandlerAction(commands=[p_delay_s, "choose 0"])
            return HandlerAction(commands=["choose 0"])

        options = state.game_state()["screen_state"].get("options", [])

        # Try desired_choices in priority order, matching by option position
        for desired in self.desired_choices:
            positions = _NEOW_POSITION_MAP.get(desired, set())
            for pos in positions:
                if pos >= len(options):
                    continue
                opt = options[pos]
                if opt.get("disabled", False):
                    continue
                idx = opt["choice_index"]
                if presentation_mode:
                    return HandlerAction(commands=[p_delay, "choose " + str(idx), "wait 30"])
                return HandlerAction(commands=["choose " + str(idx), "wait 30"])

        # Fallback: pick first non-disabled option
        for opt in options:
            if not opt.get("disabled", False):
                idx = opt["choice_index"]
                if presentation_mode:
                    return HandlerAction(commands=[p_delay, "choose " + str(idx), "wait 30"])
                return HandlerAction(commands=["choose " + str(idx), "wait 30"])

        return HandlerAction(commands=["wait 30"])
