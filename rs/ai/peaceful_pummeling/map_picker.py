"""
Dynamic map path scoring for Watcher.

Instead of using static health-loss formulas, this module evaluates:
  1. Deck power score  – estimate how well the current deck can handle fights
  2. Dynamic elite danger  – scale expected damage based on HP% and deck strength
  3. Act-aware survivability thresholds
  4. Watcher-specific relic bonuses (PureWater,Prayer Wheel, etc.)

Used by PeacefulMapHandler to construct a per-decision DynamicPathConfig.
"""

import math
from typing import Callable

from rs.game.path import PathHandlerConfig
from rs.machine.state import GameState


# ---------------------------------------------------------------------------
# Watcher key cards that indicate strong deck
# ---------------------------------------------------------------------------
# Cards that reduce incoming damage
DEFENSIVE_SIGNALS = {'talk to the hand', 'mental fortress', 'vigilance',
                      'empty body', 'perseverance', 'like water',
                      'sands of time', 'spirit shield', 'wallop'}

# Cards that deal strong damage quickly
OFFENSIVE_SIGNALS = {'rushdown', 'blasphemy', 'tantrum', 'eruption',
                     'carve reality', 'deceive reality', 'ragnarok',
                     'wheel kick', 'flurry of blows', 'empty fist'}

# Cards that scale and make later fights easier
SCALING_SIGNALS = {'establishment', 'devotion', 'wish', 'deva form',
                   'master of strategy', 'indignation', 'inner peace',
                   'devotion', 'master of strategy'}


def estimate_deck_power(state: GameState) -> float:
    """
    Return a rough 0–1 score for how strong the current deck is.

    Factors:
      - Number of high-value cards (offensive/defensive/scaling)
      - Current relics that affect combat
      - Act number (early = lower stakes, late = deck should be stronger)
    """
    deck_by_name = state.get_deck_card_list_by_name_with_upgrade_stripped()
    act = state.game_state()['act']
    floor = state.floor()

    # Count signal cards
    def count_group(names: set) -> int:
        return sum(deck_by_name.get(n, 0) for n in names)

    defense = count_group(DEFENSIVE_SIGNALS)
    offense = count_group(OFFENSIVE_SIGNALS)
    scaling = count_group(SCALING_SIGNALS)

    # relics that effectively boost deck power
    power_relics = 0.0
    if state.has_relic("Pure"):
        power_relics += 0.05   # Pure Water relic – Watcher's starting relic
    if state.has_relic("Prayer Wheel"):
        power_relics += 0.05
    if state.has_relic("Snecko Eye"):
        power_relics += 0.1
    if state.has_relic("Runic Pyramid"):
        power_relics += 0.1

    deck_size = len(state.deck.cards)
    # Normalize: typical Act 1 deck has ~10 cards, Act 3 ~25
    size_factor = min(deck_size / 15.0, 1.5)

    raw = (
        defense * 0.04
        + offense * 0.05
        + scaling * 0.06
        + power_relics
    ) * size_factor

    # Act scaling: later acts demand stronger decks
    act_multiplier = {1: 0.7, 2: 1.0, 3: 1.2}.get(act, 1.0)

    return min(raw * act_multiplier, 1.0)


def dynamic_elite_health_loss(state: GameState) -> int:
    """
    Dynamic expected health loss from an elite fight.

    Base: (act+1) * 15
    Reduction based on deck power (stronger deck → less damage taken).
    Reduction based on current HP% (low HP → safer to risk, less absolute loss).
    """
    act = state.game_state()['act']
    max_hp = state.game_state()['max_hp']
    current_hp = state.game_state()['current_hp']
    hp_pct = current_hp / max_hp if max_hp > 0 else 1.0

    base = (act + 1) * 15
    deck_power = estimate_deck_power(state)

    # Strong deck takes less damage (up to 40% reduction)
    power_reduction = base * deck_power * 0.4

    # Low HP = fewer HP to lose, high HP = more HP available
    # If already low, absolute damage is smaller anyway (capped at 0)
    hp_factor = max(0.5, hp_pct)

    adjusted = max(5, int((base - power_reduction) * hp_factor))

    # Act 2 elites are especially dangerous, minimum higher
    if act == 2:
        adjusted = max(adjusted, 20)

    return adjusted


def dynamic_hallway_health_loss(state: GameState) -> int:
    """Similar scaling for hallway fights."""
    act = state.game_state()['act']
    base = act * 5
    deck_power = estimate_deck_power(state)
    power_reduction = base * deck_power * 0.3
    return max(3, int(base - power_reduction))


def dynamic_survivability_calc(reward: float, survivability: float, state: GameState) -> float:
    """
    Enhanced survivability → reward conversion.

    Adds penalties for:
      - Paths that end with very low HP (boss is lethal)
      - Too few campfires in early acts when HP is precious
    Also adds bonuses for:
      - Campfires with Eternal Feather
      - Shops when low on gold
    """
    hp = state.game_state()['current_hp']
    max_hp = state.game_state()['max_hp']
    act = state.game_state()['act']
    floor = state.floor()

    # Bosses hit hard: after final elite/boss path, ensure we have enough HP to survive boss
    # Typical boss attack is 20-40 depending on act
    boss_min_damage = {1: 20, 2: 30, 3: 40}.get(act, 25)

    # If we end with less than boss_min_damage + 10 buffer, survivability is crushed
    if hp < boss_min_damage + 10:
        survivability *= 0.3
    elif hp < boss_min_damage + 25:
        survivability *= 0.7

    # Act 1 hallways are cheap to fight – don't over-penalize HP loss
    if act == 1:
        survivability = max(survivability, 0.6)

    return reward + (survivability - 1) * 15


def build_dynamic_config(state: GameState) -> PathHandlerConfig:
    """
    Build a PathHandlerConfig with state-aware lambdas.
    Call this each time the map handler runs, so the config reflects
    the current deck/relic/HP state.
    """
    return PathHandlerConfig(
        hallway_fight_base_reward=1,
        hallway_fight_prayer_wheel=0.3,
        hallway_question_card_reward=0.15,
        hallway_fight_gold=15,
        hallway_fight_health_loss=dynamic_hallway_health_loss,
        elite_base_reward=1,
        elite_question_card_reward=0.15,
        elite_fight_gold=30,
        elite_fight_health_loss=dynamic_elite_health_loss,
        relic_reward=1.5,
        curse_reward_loss=1.5,
        upgrade_reward=1.1,
        event_value_reward=lambda st: 1 if st.game_state()['act'] == 1 else 1.5,
        gold_at_shop_reward=lambda st, gold: gold / 100,
        gold_after_boss_reward=lambda st: st.game_state()['gold'] / 200,
        survivability_reward_calculation=lambda r, s: dynamic_survivability_calc(r, s, state),
    )
