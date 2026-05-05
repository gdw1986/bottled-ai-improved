from dataclasses import dataclass

from rs.ai.requested_strike.ironclad_comparator import IroncladComparator
from rs.calculator.executor import get_best_battle_action, get_best_battle_action_with_retry
from rs.common.handlers.common_battle_handler import CommonBattleHandler, BattleHandlerConfig
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState
from rs.machine.command import Command

# Number of retry attempts for the first turn of combat.
# Each retry explores BFS paths in a different order via shuffle_seed.
BATTLE_RETRY_COUNT = 3


@dataclass
class IroncladBattleHandlerConfig(BattleHandlerConfig):
    """Ironclad-specific battle handler config using IroncladComparator."""
    general_comparator = IroncladComparator


class IroncladBattleHandler(CommonBattleHandler):
    """Ironclad battle handler with first-turn retry optimization.

    On turn 1 of combat, runs BFS path-finding multiple times with shuffled
    play exploration orders to find superior card sequencing. Subsequent turns
    use standard single-pass path-finding (already on the best trajectory).
    """

    def handle(self, state: GameState) -> HandlerAction:
        is_turn_1 = state.combat_state() and state.combat_state().get('turn') == 1

        if is_turn_1 and BATTLE_RETRY_COUNT > 1:
            actions = get_best_battle_action_with_retry(
                state, self.select_comparator(state),
                self.max_path_count, retries=BATTLE_RETRY_COUNT
            )
        else:
            actions = get_best_battle_action(
                state, self.select_comparator(state), self.max_path_count
            )

        if actions:
            return actions
        if state.has_command(Command.END):
            return HandlerAction(commands=["end"], memory_book=None)
        return HandlerAction(commands=[], memory_book=None)


def get_ironclad_battle_handler(max_path_count: int = 11_000) -> Handler:
    """Factory for Ironclad-optimized battle handler.

    Uses IroncladBattleHandler which adds:
    - Ironclad-specific power ratings (Rage)
    - Survival-priority logic (block under threat, power setup when safe)
    - Priority target selection (kill dangerous enemies first)
    - First-turn retry with shuffled BFS order for optimal card sequencing
    """
    config = IroncladBattleHandlerConfig()
    config.general_comparator = IroncladComparator
    return IroncladBattleHandler(config=config, max_path_count=max_path_count)
