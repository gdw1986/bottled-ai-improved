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


def _compact_label(label: str) -> str:
    return ''.join(ch for ch in str(label).lower() if ch.isalnum())


def _normalize_label(label: str) -> str:
    """Normalize an option label for fuzzy matching.

    English labels are matched exactly after lowercasing. Localized labels are
    handled by _infer_neow_choice, which knows the Chinese Neow option text.
    """
    return label.strip().lower()


def _is_downside_neow_label(label: str) -> bool:
    normalized = _normalize_label(label)
    compact = _compact_label(label)
    return any(token in normalized for token in ("lose", "obtain a curse")) \
        or any(token in compact for token in ("失去", "诅咒", "受伤", "牺牲"))


def _infer_neow_choice(label: str, choice_index: int) -> str | None:
    normalized = _normalize_label(label)
    compact = _compact_label(label)

    # The last Neow choice is structurally stable across locales.
    if choice_index == 3:
        return 'lose your starting relic obtain a random boss relic'

    if 'choose a card to obtain' in normalized \
            or ('选择' in compact and '获得' in compact and '牌' in compact
                and '无色' not in compact and '稀有' not in compact):
        return 'choose a card to obtain'
    if 'upgrade a card' in normalized or '升级' in compact:
        return 'upgrade a card'
    if 'random common relic' in normalized \
            or ('随机' in compact and '普通' in compact and '遗物' in compact):
        return 'obtain a random common relic'
    if '100' in compact and ('gold' in normalized or '金币' in compact):
        return 'obtain 100 gold'
    if ('3' in compact or '三' in compact) and ('potion' in normalized or '药水' in compact):
        return 'obtain 3 random potions'
    if ('max hp +8' in normalized or '+8' in label) and ('hp' in normalized or '生命' in compact):
        return 'max hp +8'
    if ('remove a card' in normalized or '移除' in compact or '删除' in compact) and not _is_downside_neow_label(label):
        return 'remove a card from your deck'
    if ('transform a card' in normalized or '转化' in compact or '变化' in compact) and not _is_downside_neow_label(label):
        return 'transform a card'
    if ('random rare card' in normalized or '随机稀有' in compact) and 'colorless' not in normalized and '无色' not in compact:
        return 'obtain a random rare card'
    if ('colorless card' in normalized or '无色' in compact) and not _is_downside_neow_label(label):
        return 'choose a colorless card to obtain'
    if ('next three combats' in normalized or ('敌' in compact and ('1' in compact or '一' in compact))):
        return 'enemies in your next three combats have 1 hp'

    return None


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
                labels = {_normalize_label(label)}
                text = opt.get("text", "")
                if text:
                    labels.add(_normalize_label(text.strip("[] ")))
                inferred = _infer_neow_choice(" ".join(labels), idx)
                if inferred:
                    labels.add(inferred)
                available.append((labels, idx))

        # Try desired_choices in priority order, matching by normalized label text
        for desired in self.desired_choices:
            desired_norm = desired.strip().lower()
            for labels, idx in available:
                if desired_norm in labels:
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
