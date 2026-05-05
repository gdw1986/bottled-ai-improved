from typing import List, Optional
import random

from rs.calculator.battle_state import PLAY_DISCARD, Play, PLAY_EXHAUST, BattleState
from rs.calculator.game_state_converter import create_battle_state, battlestate_deepcopy
from rs.calculator.interfaces.comparator_interface import ComparatorInterface
from rs.calculator.play_path import PlayPath, get_paths_bfs
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState
from rs.machine.the_bots_memory_book import TheBotsMemoryBook


def get_best_battle_path(game_state: GameState, comparator: ComparatorInterface,
                         max_path_count: int, shuffle_seed: int | None = None) -> PlayPath:
    original_state = create_battle_state(game_state)
    paths = get_paths_bfs(original_state, max_path_count, shuffle_seed=shuffle_seed)
    best_path = None
    for path in paths.values():
        path.state.end_turn()
        if best_path is None:
            best_path = path
        else:
            if comparator.does_challenger_defeat_the_best(best_path.state, path.state, original_state):
                best_path = path

    return best_path


def get_best_battle_action_with_retry(
        game_state: GameState,
        comparator: ComparatorInterface,
        max_path_count: int = 11_000,
        retries: int = 3
) -> Optional[HandlerAction]:
    """Run battle path-finding N times with different BFS exploration orders.
    
    Each retry uses a different shuffle_seed for get_paths_bfs, which varies
    the order in which card plays are explored. This helps find better card
    ordering when multiple paths have similar scores.

    The best result (lowest HP loss) is returned.
    """
    best_path = None
    best_hp = -1

    for attempt in range(retries):
        seed = hash(str(game_state) + str(attempt)) % (2 ** 31)
        path = get_best_battle_path(game_state, comparator, max_path_count, shuffle_seed=seed)

        if path is None:
            continue

        # Evaluate by final HP (higher is better)
        final_hp = path.state.player.current_hp
        if best_path is None or final_hp > best_hp:
            best_hp = final_hp
            best_path = path

    if best_path and best_path.plays:
        return _build_action_from_path(best_path, game_state)
    return None


def get_best_battle_action(game_state: GameState, comparator: ComparatorInterface, max_path_count: int = 11_000) -> \
        Optional[HandlerAction]:
    path = get_best_battle_path(game_state, comparator, max_path_count)

    if path and path.plays:
        return _build_action_from_path(path, game_state)
    return None


def _build_action_from_path(path: PlayPath, game_state: GameState) -> HandlerAction:
    """Build a HandlerAction from the first play in a path."""
    next_move = path.plays[0]

    # create a temp state for finding the state of the custom state after the chosen action
    state = create_battle_state(game_state)
    state.transform_from_play(next_move, is_first_play=False)
    memory_book = TheBotsMemoryBook(
        memory_by_card=state.memory_by_card.copy(),
        memory_general=state.memory_general.copy()
    )

    if next_move[1] == -1:
        return HandlerAction(commands=[f"play {next_move[0] + 1}"], memory_book=memory_book)
    if next_move[1] == PLAY_DISCARD:
        return HandlerAction(commands=get_discard_commands(path.plays), memory_book=memory_book)
    if next_move[1] == PLAY_EXHAUST:
        return HandlerAction(commands=get_exhaust_commands(path.plays), memory_book=memory_book)
    return HandlerAction(commands=[f"play {next_move[0] + 1} {next_move[1]}"], memory_book=memory_book)


def get_discard_commands(plays: List[Play]) -> List[str]:
    raw_indexes = []
    for (card_idx, play_type) in plays:
        if play_type == PLAY_DISCARD:
            raw_indexes.append(card_idx)
        else:
            break
    raw_indexes.reverse()
    adjusted_indexes = []
    for (i, idx) in enumerate(raw_indexes):
        for j in range(i + 1, len(raw_indexes)):
            if raw_indexes[j] <= idx:
                idx += 1
        adjusted_indexes.append(idx)
    adjusted_indexes.reverse()

    return [f"choose {idx}" for idx in adjusted_indexes] + ["confirm", "wait 30"]


def get_exhaust_commands(plays: List[Play]) -> List[str]:
    raw_indexes = []
    for (card_idx, play_type) in plays:
        if play_type == PLAY_EXHAUST:
            raw_indexes.append(card_idx)
        else:
            break
    raw_indexes.reverse()
    adjusted_indexes = []
    for (i, idx) in enumerate(raw_indexes):
        for j in range(i + 1, len(raw_indexes)):
            if raw_indexes[j] <= idx:
                idx += 1
        adjusted_indexes.append(idx)
    adjusted_indexes.reverse()

    return [f"choose {idx}" for idx in adjusted_indexes] + ["confirm", "wait 30"]
