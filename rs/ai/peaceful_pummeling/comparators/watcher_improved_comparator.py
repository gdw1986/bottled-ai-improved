from typing import List

from rs.calculator.battle_state import BattleState
from rs.calculator.enums.card_id import CardId
from rs.calculator.enums.power_id import PowerId
from rs.calculator.interfaces.memory_items import MemoryItem, StanceType
from rs.common.comparators.common_general_comparator import (
    CommonGeneralComparator,
    add_to_comparison_list,
    move_in_comparison_list,
    Comparison,
)
from rs.common.comparators.core.comparisons import (
    battle_not_lost, battle_is_won, most_optimal_winning_battle,
    most_dead_monsters, most_enemy_vulnerable, most_enemy_weak,
    most_tranquility, most_crescendo, most_block_saved_for_next_turn,
    stance_is_calm, stance_is_not_wrath, no_blasphemy,
    least_incoming_damage, least_incoming_damage_over_1,
    most_free_early_draw, most_free_draw, most_lasting_intangible,
    most_good_player_powers, most_less_good_player_powers,
    least_bad_player_powers, most_powered_up_ritual_dagger,
    kept_expensive_decreasing_cost_retain_cards,
    lowest_health_monster, lowest_total_monster_health,
    lowest_barricaded_block, lowest_enemy_plated_armor,
    most_orb_slots, most_channeled_orbs, most_draw_pay_early, most_draw_pay,
    most_bad_cards_exhausted, most_powered_up_genetic_algorithm,
    most_cards_left_in_hand, most_ethereal_cards_saved_for_later,
    most_powered_up_claws, least_powered_down_steam_barrier,
    preserve_revive_options, killed_with_lesson_learned,
    avoid_inconvenient_time_warp,
)
from .improved_comparisons import (
    prefers_block_over_setup,
    prefers_setup_over_damage,
    prefers_divine_setup,
    prefers_calm_for_wrath_exit,
    prefers_more_block_for_next_turn,
    penalizes_low_hp_setup,
)


# ----------------------------------------------------------------------
# Watcher 专用的评估函数（扩展 ComparatorAssessment 的能力）
# ----------------------------------------------------------------------

def _player_block(state: BattleState) -> int:
    return state.player.block


def _raw_incoming_damage(state: BattleState) -> int:
    total = 0
    for m in state.monsters:
        if not m.hits or m.damage == -1:
            continue
        strength = m.powers.get(PowerId.STRENGTH, 0)
        weak_mod = 0.75 if m.powers.get(PowerId.WEAKENED) else 1.0
        total += max(int((m.damage + strength) * weak_mod), 0)
    return total


def _player_current_hp(state: BattleState) -> int:
    return state.player.current_hp


def _divine_setup_value(state: BattleState) -> int:
    mantra = state.memory_general.get(MemoryItem.MANTRA_INTERNAL, 0)
    mantra_card_ids = {'inner_peace', 'deceive_reality', 'carve_reality',
                       'prayer', 'wish', 'devotion'}
    add_count = sum(
        1 for c in state.hand
        if any(key in c.id.value for key in mantra_card_ids)
    )
    return mantra + add_count * 3


def _calm_setup_value(state: BattleState) -> int:
    wrath_exits = {
        CardId.EMPTY_BODY, CardId.EMPTY_FIST, CardId.EMPTY_MIND,
        CardId.FEAR_NO_EVIL, CardId.INNER_PEACE,
        CardId.TRANQUILITY, CardId.VIGILANCE,
    }
    return sum(1 for c in state.hand if c.id in wrath_exits)


def _incoming_damage_over_15(state: BattleState) -> bool:
    return _raw_incoming_damage(state) > 15


# ----------------------------------------------------------------------
# 改进的比较函数（调用扩展评估方法）
# ----------------------------------------------------------------------

def prefers_block_over_setup_improved(best, challenger) -> bool | None:
    best_raw = best.state.player.block + _raw_incoming_damage(best.state)
    chal_raw = challenger.state.player.block + _raw_incoming_damage(challenger.state)
    if chal_raw > 15 and best_raw > 15:
        return challenger.state.player.block > best.state.player.block
    return None


def prefers_setup_over_damage_improved(best, challenger) -> bool | None:
    best_surv = best.player_current_hp() > _raw_incoming_damage(best.state)
    chal_surv = challenger.player_current_hp() > _raw_incoming_damage(challenger.state)
    if best_surv and chal_surv:
        best_setup = _divine_setup_value(best.state) + _calm_setup_value(best.state)
        chal_setup = _divine_setup_value(challenger.state) + _calm_setup_value(challenger.state)
        if best_setup != chal_setup:
            return chal_setup > best_setup
    return None


def prefers_divine_setup_improved(best, challenger) -> bool | None:
    if best.battle_won() or challenger.battle_won():
        return None
    best_val = _divine_setup_value(best.state)
    chal_val = _divine_setup_value(challenger.state)
    return None if best_val == chal_val else chal_val > best_val


def prefers_calm_for_wrath_exit_improved(best, challenger) -> bool | None:
    best_val = _calm_setup_value(best.state)
    chal_val = _calm_setup_value(challenger.state)
    return None if best_val == chal_val else chal_val > best_val


def prefers_more_block_for_next_turn_improved(best, challenger) -> bool | None:
    best_total = best.block_for_next_turn() + best.state.player.block
    chal_total = challenger.block_for_next_turn() + challenger.state.player.block
    return None if best_total == chal_total else chal_total > best_total


def penalizes_low_hp_setup_improved(best, challenger) -> bool | None:
    best_hp_pct = best.player_current_hp() / best.player_max_hp()
    chal_hp_pct = challenger.player_current_hp() / challenger.player_max_hp()
    if best_hp_pct < 0.3 or chal_hp_pct < 0.3:
        if best.incoming_damage() != challenger.incoming_damage():
            return challenger.incoming_damage() < best.incoming_damage()
    return None


# ----------------------------------------------------------------------
# Comparator 构造
# ----------------------------------------------------------------------

improved_comparisons: List[Comparison] = [
    # 1. 存活优先
    battle_not_lost,
    battle_is_won,

    # 2. 最优胜利（保留原有胜利条件判断）
    most_optimal_winning_battle,

    # 3. 【新增】敌人意图感知
    prefers_block_over_setup_improved,      # 高威胁时优先格挡
    prefers_setup_over_damage_improved,     # 安全时优先 setup
    penalizes_low_hp_setup_improved,         # 低血量时优先保命

    # 4. 姿态相关（保留原有，补充新比较）
    prefers_divine_setup_improved,          # 【新增】优先进入 Divinity
    prefers_calm_for_wrath_exit_improved,   # 【新增】有 exit 卡时优先 Calm
    stance_is_calm,
    stance_is_not_wrath,
    no_blasphemy,
    most_crescendo,
    most_tranquility,

    # 5. 怪物击杀
    most_dead_monsters,
    most_enemy_vulnerable,
    most_enemy_weak,

    # 6. 【新增】格挡保护（比原有权重更高）
    prefers_more_block_for_next_turn_improved,
    most_block_saved_for_next_turn,
    least_incoming_damage_over_1,
    least_incoming_damage,

    # 7. 资源管理
    most_free_early_draw,
    most_free_draw,
    most_lasting_intangible,
    most_good_player_powers,
    most_less_good_player_powers,
    least_bad_player_powers,
    most_powered_up_ritual_dagger,
    kept_expensive_decreasing_cost_retain_cards,

    # 8. 怪物属性
    lowest_health_monster,
    lowest_total_monster_health,
    lowest_barricaded_block,
    lowest_enemy_plated_armor,

    # 9. Defect 相关（保留兼容）
    most_orb_slots,
    most_channeled_orbs,
    most_draw_pay_early,
    most_draw_pay,
    most_bad_cards_exhausted,
    most_powered_up_genetic_algorithm,
    most_cards_left_in_hand,
    most_ethereal_cards_saved_for_later,
    most_powered_up_claws,
    least_powered_down_steam_barrier,
    most_energy,
    preserve_revive_options,
    killed_with_lesson_learned,
    avoid_inconvenient_time_warp,
]


class WatcherImprovedComparator(CommonGeneralComparator):
    """
    Watcher（Peaceful Pummeling）改进版Comparator。

    主要改进：
    - 敌人意图感知：高威胁时优先格挡，低威胁时优先 setup
    - Divinity 姿态评估：优先选择接近进入神性的路径
    - Calm 姿态评估：有 wrath exit 卡时优先选择 Calm
    - 低血量保护：HP < 30% 时优先保命而非 setup
    - 格挡优先级提升：在对比链中提前考虑下一回合格挡
    """

    def __init__(self):
        super().__init__(improved_comparisons)
