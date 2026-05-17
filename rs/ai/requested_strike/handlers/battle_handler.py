from dataclasses import dataclass

from rs.calculator.enums.card_id import CardId
from rs.ai.requested_strike.ironclad_comparator import IroncladComparator, IroncladGremlinNobComparator
from rs.calculator.executor import get_best_battle_action, get_best_battle_action_with_retry
from rs.calculator.game_state_converter import create_battle_state
from rs.calculator.interfaces.comparator_interface import ComparatorInterface
from rs.common.handlers.common_battle_handler import CommonBattleHandler, BattleHandlerConfig
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState
from rs.machine.command import Command
from rs.machine.the_bots_memory_book import TheBotsMemoryBook

# Number of retry attempts for the first turn of combat.
# Each retry explores BFS paths in a different order via shuffle_seed.
BATTLE_RETRY_COUNT = 3


@dataclass
class IroncladBattleHandlerConfig(BattleHandlerConfig):
    """Ironclad-specific battle handler config using IroncladComparator."""
    general_comparator: ComparatorInterface = IroncladComparator
    gremlin_nob_comparator: ComparatorInterface = IroncladGremlinNobComparator


class IroncladBattleHandler(CommonBattleHandler):
    """Ironclad battle handler with first-turn retry optimization.

    On turn 1 of combat, runs BFS path-finding multiple times with shuffled
    play exploration orders to find superior card sequencing. Subsequent turns
    use standard single-pass path-finding (already on the best trajectory).
    """

    def __init__(self, config: BattleHandlerConfig = None, max_path_count: int = 11_000):
        super().__init__(
            config=IroncladBattleHandlerConfig() if config is None else config,
            max_path_count=max_path_count
        )

    def handle(self, state: GameState) -> HandlerAction:
        high_priority_action = self._play_apotheosis_if_available(state)
        if high_priority_action:
            return high_priority_action

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

    def _play_apotheosis_if_available(self, state: GameState) -> HandlerAction | None:
        """Apotheosis upgrades the whole deck, so consume it before search ordering."""
        if not state.has_command(Command.PLAY):
            return None

        for card_index, card in enumerate(state.hand.cards):
            if card.id.lower() == CardId.APOTHEOSIS.value and card.is_playable:
                battle_state = create_battle_state(state)
                battle_state.transform_from_play((card_index, -1), is_first_play=False)
                memory_book = TheBotsMemoryBook(
                    memory_by_card=battle_state.memory_by_card.copy(),
                    memory_general=battle_state.memory_general.copy()
                )
                return HandlerAction(commands=[f"play {card_index + 1}"], memory_book=memory_book)
        return None


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
    config.gremlin_nob_comparator = IroncladGremlinNobComparator
    return IroncladBattleHandler(config=config, max_path_count=max_path_count)
