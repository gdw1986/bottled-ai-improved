"""
Dynamic card reward picker: load conditional winrate data, score candidates.

Phase 2 of the Plan B pipeline. Phase 1 extracted decision points from 35,691
runs; this module loads the output and provides a runtime picker.

Scoring: for each candidate card, look up conditions matching the current
deck context (act, size bucket, feature presence). Score = weighted avg
of conditional winrate deltas, weighted by log(sample_count). If no
conditions match or total samples < threshold, returns None → caller
falls back to static list.

Data file expected at: rs/ai/requested_strike/data/conditional_winrates.json
Synergy data at: rs/ai/requested_strike/data/synergies.json
"""
import json, os, math
from typing import Optional

# Loaded once at import time
_DATA = None
_SYNERGIES = None
_DATA_BY_NAME = None
_SYNERGY_BY_PAIR = None

def _load():
    global _DATA, _SYNERGIES, _DATA_BY_NAME, _SYNERGY_BY_PAIR
    if _DATA is not None:
        return
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    with open(os.path.join(data_dir, 'conditional_winrates.json'), encoding='utf-8') as f:
        _DATA = json.load(f)
    with open(os.path.join(data_dir, 'synergies.json'), encoding='utf-8') as f:
        _SYNERGIES = json.load(f)
    _DATA_BY_NAME = {_normalize_card_name(k): v for k, v in _DATA.items()}
    _SYNERGY_BY_PAIR = {}
    for key, value in _SYNERGIES.items():
        if '→' not in key:
            continue
        left, right = key.split('→', 1)
        _SYNERGY_BY_PAIR[(_normalize_card_name(left), _normalize_card_name(right))] = value


def _normalize_card_name(name: str) -> str:
    return name.lower().replace('_', ' ').replace('-', ' ').strip()


# Feature extraction (mirrors Phase 1 categories)
ATTACK = {_normalize_card_name(c) for c in {'Strike_R','Bash','Anger','Body Slam','Clash','Cleave','Clothesline',
    'Dropkick','Dual Wield','Fiend Fire','Headbutt','Heavy Blade',
    'Hemokinesis','Immolate','Infernal Blade','Iron Wave','Perfected Strike',
    'Pommel Strike','Pummel','Rampage','Reaper','Reckless Charge',
    'Searing Blow','Sever Soul','Sword Boomerang','Thunderclap','Twin Strike',
    'Uppercut','Whirlwind','Wild Strike','Blood for Blood','Carnage',
    'Feed','Havoc','Bludgeon','RecklessCharge'}}
BLOCK = {_normalize_card_name(c) for c in {'Defend_R','Armaments','Ghostly Armor','Impervious','Iron Wave',
    'Power Through','Second Wind','Shrug It Off','True Grit','Flame Barrier',
    'Sentinel','Entrench','Barricade','Body Slam'}}
DRAW = {_normalize_card_name(c) for c in {'Battle Trance','Burning Pact','Offering','Pommel Strike','Warcry',
    'Dark Embrace','Evolve','Shrug It Off'}}
SCALE = {_normalize_card_name(c) for c in {'Spot Weakness','Inflame','Demon Form','Limit Break','Barricade',
    'Corruption','Feel No Pain','Rupture','Brutality','Combust',
    'Juggernaut','Metallicize','Rage','Dark Embrace','J.A.X.','Entrench','Body Slam'}}
AOE = {_normalize_card_name(c) for c in {'Cleave','Whirlwind','Immolate','Thunderclap'}}
WEAK = {_normalize_card_name(c) for c in {'Clothesline','Shockwave','Uppercut','Disarm'}}
VULN = {_normalize_card_name(c) for c in {'Bash','Shockwave','Uppercut','Thunderclap'}}
ENERGY = {_normalize_card_name(c) for c in {'Offering','Seeing Red','Bloodletting','Berserk'}}

STRENGTH_SOURCES = {_normalize_card_name(c) for c in {'Inflame', 'Spot Weakness', 'Demon Form', 'Flex', 'J.A.X.'}}
STRENGTH_MULTIPLIERS = {_normalize_card_name(c) for c in {'Limit Break'}}
STRENGTH_PAYOFFS = {_normalize_card_name(c) for c in {
    'Heavy Blade', 'Sword Boomerang', 'Pummel', 'Whirlwind', 'Reaper',
    'Twin Strike', 'Perfected Strike', 'Dropkick',
}}
PREMIUM_STRENGTH_PAYOFFS = {_normalize_card_name(c) for c in {
    'Heavy Blade', 'Sword Boomerang', 'Pummel', 'Whirlwind', 'Reaper',
}}


def deck_features(deck_card_names: list[str]) -> dict:
    """Extract feature vector from list of card names (strings)."""
    deck_card_names = [_normalize_card_name(c) for c in deck_card_names]
    s = set(deck_card_names)
    cnt = lambda cats: sum(1 for c in deck_card_names if c in cats)
    has = lambda cats: 1 if s & cats else 0
    return {
        'size': len(deck_card_names),
        'has_draw': has(DRAW),    'has_scaling': has(SCALE),
        'has_aoe': has(AOE),      'has_weak': has(WEAK),
        'has_vuln': has(VULN),    'has_energy': has(ENERGY),
        'has_strength_source': has(STRENGTH_SOURCES),
        'has_strength_multiplier': has(STRENGTH_MULTIPLIERS),
        'has_strength_payoff': has(STRENGTH_PAYOFFS),
        'attack_cnt': cnt(ATTACK), 'block_cnt': cnt(BLOCK),
        'draw_cnt': cnt(DRAW),    'aoe_cnt': cnt(AOE),
    }


def strength_synergy_bonus(candidate: str, deck_card_names: list[str], act: int) -> float:
    """Small deterministic nudge toward coherent strength packages."""
    candidate = _normalize_card_name(candidate)
    deck = {_normalize_card_name(c) for c in deck_card_names}
    has_source = bool(deck & STRENGTH_SOURCES)
    has_multiplier = bool(deck & STRENGTH_MULTIPLIERS)
    has_payoff = bool(deck & STRENGTH_PAYOFFS)

    bonus = 0.0
    if candidate in STRENGTH_SOURCES:
        bonus += 0.05
        if has_payoff:
            bonus += 0.05
        if act <= 1:
            bonus += 0.02
    elif candidate in STRENGTH_MULTIPLIERS:
        bonus += 0.09 if has_source else -0.04
        if has_payoff:
            bonus += 0.02
    elif candidate in PREMIUM_STRENGTH_PAYOFFS:
        if has_source or has_multiplier:
            bonus += 0.08
        elif act <= 1:
            bonus += 0.02

    return max(min(bonus, 0.12), -0.04)


def _lookup_card_data(candidate: str):
    _load()
    assert _DATA_BY_NAME is not None
    candidate_key = _normalize_card_name(candidate)
    return (
        _DATA_BY_NAME.get(candidate_key)
        or _DATA_BY_NAME.get(f'{candidate_key}+1')
    )


def pick_best_card(candidates: list[str], deck_card_names: list[str],
                   act: int, min_samples: int = 20) -> Optional[str]:
    """Pick the best card from candidates using conditional winrate data.

    Args:
        candidates: list of base card names from the reward screen
        deck_card_names: list of card names currently in the deck
        act: current act (1, 2, or 3)
        min_samples: minimum total samples for a card to be considered

    Returns:
        Best card name (base form) or None if data insufficient for all
    """
    _load()
    assert _DATA is not None and _SYNERGY_BY_PAIR is not None
    feats = deck_features(deck_card_names)

    # Determine size bucket
    sz = feats['size']
    if sz < 12:
        size_bucket = 'size_small'
    elif sz < 18:
        size_bucket = 'size_med'
    elif sz < 25:
        size_bucket = 'size_large'
    else:
        size_bucket = 'size_xl'

    act_key = f'act_{act}'

    best_card = None
    best_score = -999.0

    for candidate in candidates:
        # Look up candidate in data — names from the game are lowercase, data keys are not.
        card_data = _lookup_card_data(candidate)

        if card_data is None:
            continue
        if card_data['total_n'] < min_samples:
            continue

        base_wr = card_data['base_wr']
        conditions = card_data.get('conditions', {})

        # Compute score: weighted avg of matching condition deltas
        total_weight = 0.0
        weighted_delta = 0.0
        matched = 0

        # Priority conditions (act and size are always relevant)
        for cond_key in [act_key, size_bucket]:
            if cond_key in conditions:
                c = conditions[cond_key]
                delta = c.get('delta', 0)
                n = c.get('n', 1)
                w = math.log(max(n, 2))
                weighted_delta += delta * w
                total_weight += w
                matched += 1

        # Feature conditions
        for feat in ['has_draw', 'has_scaling', 'has_aoe', 'has_weak', 'has_energy']:
            label = f'{feat}_with' if feats[feat] else f'{feat}_without'
            if label in conditions:
                c = conditions[label]
                delta = c.get('delta', 0)
                n = c.get('n', 1)
                w = math.log(max(n, 2))
                weighted_delta += delta * w
                total_weight += w
                matched += 1

        if matched == 0 or total_weight == 0:
            continue

        score = base_wr + (weighted_delta / total_weight)

        # --- Synergy bonus ---
        # For each card already in deck, check synergy pairs "deck_card→candidate"
        # Synergy delta weighted by log(n), capped at +0.15 to prevent runaway.
        synergy_bonus = 0.0
        candidate_key = _normalize_card_name(candidate)
        for deck_card in deck_card_names:
            deck_key = _normalize_card_name(deck_card)
            for key in ((deck_key, candidate_key), (candidate_key, deck_key),
                        (f'{deck_key}+1', candidate_key), (candidate_key, f'{deck_key}+1')):
                if key in _SYNERGY_BY_PAIR:
                    s = _SYNERGY_BY_PAIR[key]
                    if s['n'] >= 10:
                        synergy_bonus += s['delta'] * math.log(s['n']) / math.log(100)
        synergy_bonus = min(synergy_bonus, 0.15)
        score += synergy_bonus
        score += strength_synergy_bonus(candidate, deck_card_names, act)

        if score > best_score:
            best_score = score
            best_card = candidate

    return best_card
