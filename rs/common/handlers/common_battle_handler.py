from dataclasses import dataclass, field

from rs.calculator.executor import get_best_battle_action
from rs.calculator.interfaces.comparator_interface import ComparatorInterface
from rs.common.comparators.big_fight_comparator import BigFightComparator
from rs.common.comparators.common_general_comparator import CommonGeneralComparator
from rs.common.comparators.gremlin_nob_comparator import GremlinNobComparator
from rs.common.comparators.lagavulin_comparator import LagavulinComparator
from rs.common.comparators.three_sentry_comparator import ThreeSentriesComparator
from rs.common.comparators.three_sentry_turn_1_comparator import ThreeSentriesTurn1Comparator
from rs.common.comparators.transient_comparator import TransientComparator
from rs.common.comparators.waiting_lagavulin_comparator import WaitingLagavulinComparator
from rs.game.card import CardType
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


@dataclass
class BattleHandlerConfig:
    big_fight_floors: list[int] = field(default_factory=lambda: [33, 50])
    big_fight_comparator: ComparatorInterface = BigFightComparator
    gremlin_nob_comparator: ComparatorInterface = GremlinNobComparator
    lagavulin_comparator: ComparatorInterface = LagavulinComparator
    three_sentries_comparator: ComparatorInterface = ThreeSentriesComparator
    three_sentries_turn_1_comparator: ComparatorInterface = ThreeSentriesTurn1Comparator
    transient_comparator: ComparatorInterface = TransientComparator
    waiting_lagavulin_comparator: ComparatorInterface = WaitingLagavulinComparator
    general_comparator: ComparatorInterface = CommonGeneralComparator


class CommonBattleHandler(Handler):

    def __init__(self, config: BattleHandlerConfig = BattleHandlerConfig(), max_path_count: int = 11_000):
        self.config: BattleHandlerConfig = config
        self.max_path_count: int = max_path_count

    def can_handle(self, state: GameState) -> bool:
        return state.has_command(Command.PLAY) \
               or state.current_action() == "DiscardAction" \
               or state.current_action() == "ExhaustAction"

    def select_comparator(self, state: GameState) -> ComparatorInterface:
        alive_monsters = len(list(filter(lambda m: not m["is_gone"], state.get_monsters())))

        big_fight = state.floor() in self.config.big_fight_floors

        gremlin_nob_is_present = state.has_monster("Gremlin Nob")

        three_sentries_are_alive_turn_1 = state.has_monster("Sentry") \
                                   and alive_monsters == 3 \
                                   and state.combat_state()['turn'] == 1

        three_sentries_are_alive = state.has_monster("Sentry") \
                                          and alive_monsters == 3

        lagavulin_is_present = state.has_monster("Lagavulin")

        lagavulin_is_sleeping = self.lagavulin_is_waiting(state) \
                                and state.combat_state()['turn'] <= 2

        lagavulin_is_worth_delaying = state.deck.contains_type(CardType.POWER) \
                                      or state.deck.contains_cards(["Terror", "Terror+"]) \
                                      or state.deck.contains_cards(["Talk To The Hand", "Talk To The Hand+"]) \
                                      or state.has_relic("Warped Tongs") \
                                      or state.has_relic("Ice Cream")

        transient_is_present = state.has_monster("Transient") and alive_monsters == 1

        if big_fight:
            return self.config.big_fight_comparator()
        elif gremlin_nob_is_present:
            return self.config.gremlin_nob_comparator()
        elif three_sentries_are_alive_turn_1:
            return self.config.three_sentries_turn_1_comparator()
        elif three_sentries_are_alive:
            return self.config.three_sentries_comparator()
        elif lagavulin_is_sleeping and lagavulin_is_worth_delaying:
            return self.config.waiting_lagavulin_comparator()
        elif lagavulin_is_present:
            return self.config.lagavulin_comparator()
        elif transient_is_present:
            return self.config.transient_comparator()
        return self.config.general_comparator()

    def lagavulin_is_waiting(self, state: GameState) -> bool:
        if state.game_state()['room_type'] == "EventRoom":
            return False

        for monster in state.get_monsters():
            if monster.get("is_gone", False):
                continue
            monster_keys = {monster.get("id"), monster.get("name")}
            if "Lagavulin" in monster_keys and monster.get("intent") in ("SLEEP", "DEBUG"):
                return True
        return False

    def should_wait_against_sleeping_lagavulin(self, state: GameState) -> bool:
        if not self.lagavulin_is_waiting(state) or state.combat_state()['turn'] > 2:
            return False

        has_setup_in_hand = state.hand.contains_type(CardType.POWER) \
                            or state.hand.contains_cards(["Terror", "Terror+"]) \
                            or state.hand.contains_cards(["Talk To The Hand", "Talk To The Hand+"])
        has_good_wake_card = state.hand.contains_cards(["Bash", "Bash+"])

        lagavulin_is_worth_delaying = state.deck.contains_type(CardType.POWER) \
                                      or state.deck.contains_cards(["Terror", "Terror+"]) \
                                      or state.deck.contains_cards(["Talk To The Hand", "Talk To The Hand+"]) \
                                      or state.has_relic("Warped Tongs") \
                                      or state.has_relic("Ice Cream")

        return not has_setup_in_hand and (lagavulin_is_worth_delaying or not has_good_wake_card)

    def handle(self, state: GameState) -> HandlerAction:
        if self.should_wait_against_sleeping_lagavulin(state) and state.has_command(Command.END):
            return HandlerAction(commands=["end"], memory_book=None)

        actions = get_best_battle_action(state, self.select_comparator(state), self.max_path_count)
        if actions:
            return actions
        if state.has_command(Command.END):
            return HandlerAction(commands=["end"], memory_book=None)
        return HandlerAction(commands=[], memory_book=None)
