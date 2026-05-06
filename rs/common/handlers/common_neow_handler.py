from typing import List

from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.game.screen_type import ScreenType
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState
from rs.helper.logger import log_to_run

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


def _normalize_label(label: str) -> str:
    """Normalize an option label for fuzzy matching.

    screen_state.options[].label is English even in Chinese game (e.g.
    "Obtain a random rare Card"), while desired_choices are lowercase
    English (e.g. "obtain a random rare card").  We lowercase and strip
    to enable robust matching without relying on position.

    This replaces the old _NEOW_POSITION_MAP approach which always
    matched by position {0,1,2,3} and never verified option text,
    causing every run to pick position 0 ("obtain a random rare card")
    regardless of the actual desired choice.
    """
    return label.strip().lower()


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

        # Build a list of (normalized_label, choice_index) for non-disabled options.
        # screen_state.options[].label is always English even in Chinese game,
        # so we can match by text content instead of relying on position mapping.
        available = []
        for opt in options:
            if opt.get("disabled", False):
                continue
            idx = opt.get("choice_index")
            label = opt.get("label", "")
            if idx is not None:
                available.append((_normalize_label(label), idx))

        # Try desired_choices in priority order, matching by normalized label text
        for desired in self.desired_choices:
            desired_norm = desired.strip().lower()
            for label_norm, idx in available:
                if desired_norm == label_norm:
                    log_to_run(f"[Neow] Matched desired '{desired}' -> choose {idx}")
                    if presentation_mode:
                        return HandlerAction(commands=[p_delay, "choose " + str(idx), "wait 30"])
                    return HandlerAction(commands=["choose " + str(idx), "wait 30"])

        # Fallback: pick first non-disabled option
        for opt in options:
            if not opt.get("disabled", False):
                idx = opt.get("choice_index")
                if idx is not None:
                    log_to_run(f"[Neow] Fallback -> choose {idx} (label: {opt.get('label', '?')})")
                    if presentation_mode:
                        return HandlerAction(commands=[p_delay, "choose " + str(idx), "wait 30"])
                    return HandlerAction(commands=["choose " + str(idx), "wait 30"])

        return HandlerAction(commands=["wait 30"])
