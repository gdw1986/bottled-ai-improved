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
"""
import json, os, math
from typing import Optional

# Loaded once at import time
_DATA = None

def _load():
    global _DATA
    if _DATA is not None:
        return
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'conditional_winrates.json')
    with open(path, encoding='utf-8') as f:
        _DATA = json.load(f)


# Feature extraction (mirrors Phase 1 categories)
ATTACK = {'Strike_R','Bash','Anger','Body Slam','Clash','Cleave','Clothesline',
    'Dropkick','Dual Wield','Fiend Fire','Flex','Headbutt','Heavy Blade',
    'Hemokinesis','Immolate','Infernal Blade','Iron Wave','Perfected Strike',
    'Pommel Strike','Pummel','Rampage','Reaper','Reckless Charge',
    'Searing Blow','Sever Soul','Sword Boomerang','Thunderclap','Twin Strike',
    'Uppercut','Whirlwind','Wild Strike','Blood for Blood','Carnage',
    'Feed','Havoc','Bludgeon','RecklessCharge'}
BLOCK = {'Defend_R','Armaments','Ghostly Armor','Impervious','Iron Wave',
    'Power Through','Second Wind','Shrug It Off','True Grit','Flame Barrier',
    'Sentinel','Entrench'}
DRAW = {'Battle Trance','Burning Pact','Offering','Pommel Strike','Warcry',
    'Dark Embrace','Evolve','Shrug It Off'}
SCALE = {'Spot Weakness','Inflame','Demon Form','Limit Break','Barricade',
    'Corruption','Feel No Pain','Rupture','Brutality','Combust',
    'Juggernaut','Metallicize','Rage','Dark Embrace'}
AOE = {'Cleave','Whirlwind','Immolate','Thunderclap'}
WEAK = {'Clothesline','Shockwave','Uppercut','Disarm'}
VULN = {'Bash','Shockwave','Uppercut','Thunderclap'}
ENERGY = {'Offering','Seeing Red','Bloodletting','Berserk'}


def deck_features(deck_card_names: list[str]) -> dict:
    """Extract feature vector from list of card names (strings)."""
    n = max(len(deck_card_names), 1)
    s = set(deck_card_names)
    cnt = lambda cats: sum(1 for c in deck_card_names if c in cats)
    has = lambda cats: 1 if s & cats else 0
    return {
        'size': len(deck_card_names),
        'has_draw': has(DRAW),    'has_scaling': has(SCALE),
        'has_aoe': has(AOE),      'has_weak': has(WEAK),
        'has_vuln': has(VULN),    'has_energy': has(ENERGY),
        'attack_cnt': cnt(ATTACK), 'block_cnt': cnt(BLOCK),
        'draw_cnt': cnt(DRAW),    'aoe_cnt': cnt(AOE),
    }


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
        # Look up candidate in data — try exact match first, then +1 variant
        card_data = None
        lookup_key = candidate
        if lookup_key in _DATA:
            card_data = _DATA[lookup_key]
        elif f'{candidate}+1' in _DATA:
            lookup_key = f'{candidate}+1'
            card_data = _DATA[lookup_key]

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

        if score > best_score:
            best_score = score
            best_card = candidate

    return best_card
