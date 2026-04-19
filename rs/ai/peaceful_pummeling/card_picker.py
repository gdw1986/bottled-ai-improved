"""
Dynamic card picking strategies for Watcher.

Analyzes the current deck composition and game state to dynamically
adjust card pick priorities — instead of using a static desired count table.

Usage: import and call `apply_dynamic_picks(cards: dict, state: GameState)`
from within `CardRewardHandler.transform_desired_cards_map_from_state()`.
"""

from rs.game.card import CardType
from rs.machine.state import GameState

# ---------------------------------------------------------------------------
# Card type classification for Watcher
# ---------------------------------------------------------------------------
# Maps lowercase card name → type.
# Only cards present in DESIRED_CARDS_FOR_DECK need entries here.
WATCHER_CARD_TYPES: dict[str, str] = {
    # Attack
    'eruption': 'attack',
    'tantrum': 'attack',
    'flurry of blows': 'attack',
    'crescendo': 'attack',
    'halt': 'attack',
    'crush joints': 'attack',
    'empty fist': 'attack',
    'reach heaven': 'attack',
    'carve reality': 'attack',
    'deceive reality': 'attack',
    'ragnarok': 'attack',
    'wheel kick': 'attack',
    'fear no evil': 'attack',
    'wallop': 'attack',
    'cut through fate': 'attack',
    # Skill
    'talk to the hand': 'skill',
    'battle hymn': 'skill',
    'mental fortress': 'skill',
    'vigilance': 'skill',
    'tranquility': 'skill',
    'perseverance': 'skill',
    'like water': 'skill',
    'empty body': 'skill',
    'inner peace': 'skill',
    'spirit shield': 'skill',
    'sands of time': 'skill',
    # Power
    'blasphemy': 'power',
    'rushdown': 'power',
    'ritual dagger': 'power',
    'establishment': 'power',   # pseudo-power, affects cost
    'devotion': 'power',
    'deva form': 'power',
    'master of strategy': 'power',
    'wish': 'power',
    'enlightenment': 'power',
    'indignation': 'power',
    # Special / 0-cost entry
    'apparition': 'attack',   # 1-cost ghost, treat as attack
}

# ---------------------------------------------------------------------------
# Synergy: relics → cards that become more valuable with them
# ---------------------------------------------------------------------------
RELIC_CARD_SYNERGIES: dict[str, list[str]] = {
    'runic pyramid': ['battle hymn'],  # extra copies of Battle Hymn are worse
    'snecko eye': ['consecrate', 'halt', 'scrawl', 'just lucky', 'eruption'],
    'prayer wheel': ['battle hymn'],
    'the_abacus': ['talk to the hand'],
    'incense burner': ['talk to the hand', 'vigilance'],
    'incense burner+': ['talk to the hand', 'vigilance'],
    'cursed_key': ['battle hymn', 'prayer wheel'],  # don't want more costs
    'coffee dripper': ['talk to the hand', 'vigilance', 'mental fortress'],
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def apply_dynamic_picks(cards: dict[str, int], state: GameState) -> None:
    """
    Adjusts the ``cards`` dict (a copy of DESIRED_CARDS_FOR_DECK) in-place
    based on the current game state.

    Strategies applied (in order):
      1. HP-aware adjustment       – low HP → boost defense skills
      2. Floor-aware adjustment   – early floor → more attacks; late → powers
      3. Deck-composition balance – count existing card types, boost sparse ones
      4. Synergy adjustment        – relics that make certain cards better/worse
      5. Soft cap on duplicates    – already have 2+ copies → reduce priority
    """
    deck = state.deck
    floor = state.floor()
    hp_pct = state.get_player_health_percentage()
    relics = [r['name'].lower() for r in state.get_relics()]

    # --- 1. HP-aware ---------------------------------------------------
    _adjust_hp_based(cards, hp_pct)

    # --- 2. Floor-aware -----------------------------------------------
    _adjust_floor_based(cards, floor)

    # --- 3. Deck-composition balance ----------------------------------
    _adjust_by_deck_composition(cards, deck)

    # --- 4. Synergy adjustments ---------------------------------------
    _adjust_synergies(cards, relics)

    # --- 5. Soft cap on duplicates ------------------------------------
    _apply_duplicate_cap(cards, state)

    # --- 6. Boost cards that unlock key combos -----------------------
    _boost_combo_enablers(cards, deck, state)


# ---------------------------------------------------------------------------
# Individual strategy functions
# ---------------------------------------------------------------------------

def _adjust_hp_based(cards: dict[str, int], hp_pct: float) -> None:
    """Low HP: boost defense skills. High HP: boost attacks/powers."""
    if hp_pct > 0.75:
        # Full health — aggressive, reduce skill desire slightly
        for skill_card in ['talk to the hand', 'mental fortress', 'perseverance']:
            if skill_card in cards:
                cards[skill_card] = max(1, cards[skill_card] - 1)
    elif hp_pct < 0.40:
        # Critically low HP — heavily favour defense
        for skill_card in ['talk to the hand', 'mental fortress', 'vigilance',
                           'perseverance', 'empty body', 'sands of time']:
            if skill_card in cards:
                cards[skill_card] = min(cards[skill_card] * 2, 5)
        # Deprioritize risky powers
        for power_card in ['blasphemy', 'deva form']:
            if power_card in cards:
                cards[power_card] = max(1, cards[power_card] - 1)


def _adjust_floor_based(cards: dict[str, int], floor: int) -> None:
    """Early game → more attacks; late game → more powers / finisher cards."""
    if floor < 8:
        # Early act 1: need damage to survive hallway fights
        for attack_card in ['eruption', 'tantrum', 'flurry of blows', 'fear no evil',
                            'crescendo', 'halt']:
            if attack_card in cards:
                cards[attack_card] = min(cards[attack_card] + 1, 4)
    elif floor < 20:
        # Mid game: already have some attacks, need stance control + powers
        for power_card in ['rushdown', 'establishment', 'devotion']:
            if power_card in cards:
                cards[power_card] = min(cards[power_card] + 1, 3)
    else:
        # Late game / act 3+: need finishers and scaling powers
        for power_card in ['blasphemy', 'deva form', 'wish']:
            if power_card in cards:
                cards[power_card] = min(cards[power_card] + 1, 3)
        # Reduce basic stance cards we probably already have
        for stance_card in ['crescendo', 'tranquility']:
            if stance_card in cards:
                cards[stance_card] = max(1, cards[stance_card] - 1)


def _adjust_by_deck_composition(cards: dict[str, int], deck) -> None:
    """Count existing deck card types and boost sparse types."""
    attack_count = 0
    skill_count = 0
    power_count = 0

    for card in deck.cards:
        card_lower = card.name.replace('+', '').lower()
        card_type = WATCHER_CARD_TYPES.get(card_lower)
        if card_type == 'attack':
            attack_count += 1
        elif card_type == 'skill':
            skill_count += 1
        elif card_type == 'power':
            power_count += 1

    total = attack_count + skill_count + power_count
    if total == 0:
        return  # no cards yet, skip

    # Calculate imbalance: which type is underrepresented?
    avg = total / 3.0

    def boost_sparse_type(target_type: str, boost_amount: int) -> None:
        for name, ctype in WATCHER_CARD_TYPES.items():
            if ctype == target_type and name in cards:
                cards[name] = min(cards[name] + boost_amount, 5)

    def penalise_dense_type(target_type: str, reduce_amount: int) -> None:
        for name, ctype in WATCHER_CARD_TYPES.items():
            if ctype == target_type and name in cards:
                cards[name] = max(cards[name] - reduce_amount, 1)

    if attack_count < avg * 0.6:
        boost_sparse_type('attack', 1)
    elif attack_count > avg * 1.5:
        penalise_dense_type('attack', 1)

    if skill_count < avg * 0.5:
        boost_sparse_type('skill', 1)
    elif skill_count > avg * 1.6:
        penalise_dense_type('skill', 1)

    if power_count < avg * 0.4:
        boost_sparse_type('power', 1)


def _adjust_synergies(cards: dict[str, int], relics: list[str]) -> None:
    """Reduce cards that are made worse by certain relics."""
    for relic in relics:
        relic_lower = relic.lower()
        if relic_lower in RELIC_CARD_SYNERGIES:
            synergy_cards = RELIC_CARD_SYNERGIES[relic_lower]
            for sc in synergy_cards:
                if sc in cards:
                    # Penalise cards that don't synergise with this relic
                    cards[sc] = max(1, cards[sc] - 1)


def _apply_duplicate_cap(cards: dict[str, int], state: GameState) -> None:
    """If deck already has 2+ copies of a card, reduce its desired count."""
    deck_by_name = state.get_deck_card_list_by_name_with_upgrade_stripped()

    for card_name, deck_count in deck_by_name.items():
        if card_name in cards:
            if deck_count >= 2:
                # Already have 2+, don't actively seek more
                cards[card_name] = max(1, cards[card_name] - 1)
            elif deck_count >= 3:
                # Have 3+, reduce to 1 (probably don't need more)
                cards[card_name] = 1


def _boost_combo_enablers(cards: dict[str, int], deck, state: GameState) -> None:
    """Boost cards that enable powerful combos based on current deck state."""
    deck_by_name = state.get_deck_card_list_by_name_with_upgrade_stripped()

    # If we have Establishment, Rushdown becomes much more valuable
    if 'establishment' in deck_by_name and 'rushdown' in cards:
        cards['rushdown'] = min(cards['rushdown'] + 2, 4)

    # If we have Rushdown, Calm cards (Tranquility, Inner Peace) are better
    if 'rushdown' in deck_by_name:
        for calm_card in ['tranquility', 'inner peace']:
            if calm_card in cards:
                cards[calm_card] = min(cards[calm_card] + 1, 3)

    # Divinity setup: if we have Blasphemy, Watcher's 0-cost stance cards
    # become more valuable for entering Divinity
    if 'blasphemy' in deck_by_name:
        for zero_cost_stance in ['tranquility', 'crescendo']:
            if zero_cost_stance in cards:
                cards[zero_cost_stance] = min(cards[zero_cost_stance] + 1, 3)

    # If we have multiple Deva Form already, reduce desire
    deva_count = deck_by_name.get('deva form', 0)
    if deva_count >= 1 and 'deva form' in cards:
        cards['deva form'] = max(1, cards['deva form'] - 1)

    # Mental Fortress is especially valuable with Snecko Eye (random cost helps)
    if state.has_relic('Snecko Eye') and 'mental fortress' in cards:
        cards['mental fortress'] = min(cards['mental fortress'] + 1, 4)

    # Talk to the Hand is always good but cap at 4 copies
    tth_count = deck_by_name.get('talk to the hand', 0)
    if 'talk to the hand' in cards and tth_count >= 4:
        cards['talk to the hand'] = 1
