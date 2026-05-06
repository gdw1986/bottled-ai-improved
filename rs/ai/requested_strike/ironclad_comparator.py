"""
Ironclad-specific battle comparator extending CommonGeneralComparator.

Changes from the generic comparator:
1. Added Ironclad-specific powers to powers_we_like (Rage, Brutality, Combust, Rupture)
2. Removed Berserk from powers_we_like (applies Vulnerable — net negative)
3. Added survival-priority comparisons: block under threat, setup when safe
4. Prioritize killing dangerous enemies first (Gremlin Leader minions, Slavers' Red Slaver)
"""
from typing import List, Optional

from rs.calculator.battle_state import BattleState
from rs.calculator.enums.card_id import CardId
from rs.calculator.enums.power_id import PowerId
from rs.calculator.powers import DEBUFFS
from rs.game.card import CardType
from rs.common.comparators.common_general_comparator import (
    CommonGeneralComparator,
    Comparison,
    powers_we_like as base_powers_we_like,
    powers_we_like_less as base_powers_we_like_less,
    powers_we_dislike,
    default_comparisons,
)
from rs.common.comparators.core.assessment import ComparatorAssessmentConfig
from rs.common.comparators.core.comparisons import (
    battle_not_lost, battle_is_won, most_optimal_winning_battle,
    most_dead_monsters, most_enemy_vulnerable, most_enemy_weak,
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
    avoid_inconvenient_time_warp, stance_is_calm, stance_is_not_wrath,
    no_blasphemy,
    least_nob_adjusted_scaling_damage,
    most_enemy_strength_reduction,
    most_tranquility,
    most_block_saved_for_next_turn,
    lowest_health_edge_monster,
    most_energy,
    CA,
)

# ---------------------------------------------------------------------------
# Ironclad-specific power lists
# ---------------------------------------------------------------------------

# Powers we like: base list + Ironclad additions - Berserk (applies Vulnerable)
ironclad_powers_we_like: List[PowerId] = [
    p for p in base_powers_we_like
    if p != PowerId.BERSERK  # Vulnerable is too dangerous
] + [
    PowerId.RAGE,         # Attack grants Block — key block source
]


# ---------------------------------------------------------------------------
# Improved comparison functions (mirrors peaceful_pummeling approach)
# ---------------------------------------------------------------------------

def raw_incoming_damage(state: BattleState) -> int:
    """Compute raw incoming damage (before block)."""
    total = 0
    for m in state.monsters:
        if not m.hits or m.damage == -1:
            continue
        strength = m.powers.get(PowerId.STRENGTH, 0)
        weak_mod = 0.75 if m.powers.get(PowerId.WEAKENED) else 1.0
        total += max(int((m.damage + strength) * weak_mod), 0)
    return total


def prefers_block_under_threat(best: CA, challenger: CA) -> Optional[bool]:
    """When incoming damage exceeds block significantly, prioritize more block."""
    best_threat = raw_incoming_damage(best.state) - best.state.player.block
    chal_threat = raw_incoming_damage(challenger.state) - challenger.state.player.block
    # Only trigger if both are facing significant threat (>10 net incoming)
    if best_threat > 10 and chal_threat > 10:
        if best.state.player.block != challenger.state.player.block:
            return challenger.state.player.block > best.state.player.block
    return None


def prefers_setup_when_safe(best: CA, challenger: CA) -> Optional[bool]:
    """When safe (will survive), prefer playing powers/scaling."""
    best_survives = best.state.player.current_hp > raw_incoming_damage(best.state) - best.state.player.block
    chal_survives = challenger.state.player.current_hp > raw_incoming_damage(challenger.state) - challenger.state.player.block
    if best_survives and chal_survives:
        best_powers = best.player_powers_good() + best.player_powers_great()
        chal_powers = challenger.player_powers_good() + challenger.player_powers_great()
        if best_powers != chal_powers:
            return chal_powers > best_powers
    return None


def penalizes_low_hp_setup_ironclad(best: CA, challenger: CA) -> Optional[bool]:
    """At low HP, prioritize survival over scaling."""
    best_hp_pct = best.state.player.current_hp / best.player_max_hp()
    chal_hp_pct = challenger.state.player.current_hp / challenger.player_max_hp()
    if best_hp_pct < 0.3 or chal_hp_pct < 0.3:
        if best.incoming_damage() != challenger.incoming_damage():
            return challenger.incoming_damage() < best.incoming_damage()
    return None


def prefers_killing_dangerous_enemy_first(best: CA, challenger: CA) -> Optional[bool]:
    """Against known dangerous enemies, kill priority targets first.

    Priority targets: Red Slaver (Entangle+Vulnerable), Gremlin minions (prevent buff).
    """
    if best.battle_won() or challenger.battle_won():
        return None
    if len(best.state.monsters) < 3:
        return None  # only meaningful for 3+ monster fights
    best_dead = best.dead_monsters()
    chal_dead = challenger.dead_monsters()
    if best_dead == chal_dead:
        return None
    # If challenger killed the edge monster (Red Slaver, Sentry, etc.), prefer it
    best_edge_killed = best.dead_edge_monsters() > 0
    chal_edge_killed = challenger.dead_edge_monsters() > 0
    if best_edge_killed != chal_edge_killed:
        return chal_edge_killed
    return None


def prefers_strength_tiebreaker(best: CA, challenger: CA) -> Optional[bool]:
    """When outcomes are otherwise identical, prefer higher strength.
    
    Ironclad's strength scaling means having +3 strength vs +0 turns
    every attack into a significantly better play next turn. This acts
    as a soft nudge in the comparison chain.
    """
    best_str = best.state.player.powers.get(PowerId.STRENGTH, 0)
    chal_str = challenger.state.player.powers.get(PowerId.STRENGTH, 0)
    if best_str != chal_str:
        return chal_str > best_str
    return None


def prefers_armaments_played(best: CA, challenger: CA) -> Optional[bool]:
    """When Armaments+ is in hand, prefer the path that actually played it.

    The simulator does NOT model Armaments's upgrade-all-cards-in-hand effect
    (card_effects.py has no implementation), so the simulated state shows
    identical outcomes whether Armaments+ was played or not.

    This function uses the `armaments_was_played` flag set in `resolve_card_play`
    to detect whether Armaments+ was consumed in each path's play sequence.
    (We can't check hand because end_turn() already cleared it by comparison time.)

    Positioned after survival/threat checks but before generic damage metrics.
    """
    # Only fires when Armaments+ is in original (real-game) hand
    has_armaments_plus = any(
        c.id == CardId.ARMAMENTS and c.upgrade >= 1
        for c in challenger.original.hand
    )
    if not has_armaments_plus:
        return None

    best_played = best.state.armaments_was_played
    chal_played = challenger.state.armaments_was_played

    if best_played != chal_played:
        return chal_played  # prefer path that played Armaments+
    return None  # both or neither played → other comparisons decide


def prefers_strength_gain(best: CA, challenger: CA) -> Optional[bool]:
    """When strength-granting cards AND attack cards are in the original hand,
    prefer paths that gain more strength this turn.

    Ironclad's strength scaling means playing Inflame/Spot Weakness before
    attacks can turn Strikes from 6→8+ damage. But the simulator evaluates
    each turn independently — a path playing 3 Strikes (18 dmg) out-scores
    Inflame + 2 Strikes (16 dmg +2 STR). The +2 STR value only manifests
    across future turns, which the single-turn evaluation misses.

    This function nudges paths toward playing strength cards early in the
    fight by comparing strength gained. Positioned AFTER survival/threat
    checks so we never sacrifice survival for strength.
    """
    # Cards that directly increase player STRENGTH
    strength_granting = {
        CardId.INFLAME,
        CardId.SPOT_WEAKNESS,
        CardId.FLEX,
        CardId.LIMIT_BREAK,
        CardId.DEMON_FORM,
    }

    original = challenger.original
    has_strength_card = any(
        c.id in strength_granting for c in original.hand
    )
    if not has_strength_card:
        return None

    has_attack = any(
        c.type == CardType.ATTACK for c in original.hand
    )
    if not has_attack:
        return None  # no attacks to benefit from +STR yet

    original_str = original.player.powers.get(PowerId.STRENGTH, 0)
    best_str_gain = best.state.player.powers.get(PowerId.STRENGTH, 0) - original_str
    chal_str_gain = challenger.state.player.powers.get(PowerId.STRENGTH, 0) - original_str

    if best_str_gain != chal_str_gain:
        return chal_str_gain > best_str_gain
    return None


# ---------------------------------------------------------------------------
# Ironclad comparison chain
# ---------------------------------------------------------------------------

ironclad_comparisons: List[Comparison] = [
    # 1. Survival first
    battle_not_lost,
    battle_is_won,
    preserve_revive_options,
    most_optimal_winning_battle,

    # 2. Gremlin Nob: account for future damage from skills increasing Enrage strength
    least_nob_adjusted_scaling_damage,

    # 3. Threat assessment
    prefers_block_under_threat,            # High threat → more block
    penalizes_low_hp_setup_ironclad,       # Low HP → minimize damage
    prefers_setup_when_safe,               # Safe → play powers

    # 4. Enemy management — dangerous targets first
    prefers_killing_dangerous_enemy_first,  # Kill Red Slaver / Gremlin minions

    # 4.2. Hand quality — Armaments+ upgrade value evaluated before strength/damage
    prefers_armaments_played,

    # 4.3 Ironclad-specific: prioritize playing strength cards when attacks are available
    prefers_strength_gain,

    # 4.4 Ironclad-specific: when outcomes are tied, prefer strength buildup
    prefers_strength_tiebreaker,

    # 5. Generic damage / kill metrics
    most_dead_monsters,
    lowest_health_monster,
    lowest_total_monster_health,

    # 5.5. Enemy strength reduction — value Disarm / Piercing Wail / etc.
    # Must come after kill/blood metrics but before status effects,
    # otherwise "strike for 6" always beats "disarm for -2 STR"
    most_enemy_strength_reduction,

    # 6. Status effects on enemies
    most_enemy_vulnerable,
    most_enemy_weak,

    # 7. Damage / protection
    most_block_saved_for_next_turn,
    least_incoming_damage_over_1,
    least_incoming_damage,

    # 8. Resource economy
    most_free_early_draw,
    most_free_draw,
    most_lasting_intangible,
    most_good_player_powers,
    most_less_good_player_powers,
    least_bad_player_powers,
    most_powered_up_ritual_dagger,
    kept_expensive_decreasing_cost_retain_cards,

    # 9. Enemy debuffs
    lowest_barricaded_block,
    lowest_enemy_plated_armor,

    # 10. Defect compat (keep for shared code paths)
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
    killed_with_lesson_learned,
    avoid_inconvenient_time_warp,

    # 11. Watcher compat (keep for shared code paths)
    no_blasphemy,
    stance_is_calm,
    stance_is_not_wrath,
    most_tranquility,
    most_energy,
]


class IroncladComparator(CommonGeneralComparator):
    """Ironclad-optimized comparator with survival logic and Ironclad-specific power ratings."""

    def __init__(self):
        assessment_config = ComparatorAssessmentConfig(
            powers_we_like=ironclad_powers_we_like,
            powers_we_like_less=base_powers_we_like_less,
            powers_we_dislike=powers_we_dislike,
        )
        super().__init__(comparisons=ironclad_comparisons, assessment_config=assessment_config)
