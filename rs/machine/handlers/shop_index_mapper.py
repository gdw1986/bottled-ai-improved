"""Shop choice_list index mapper for CommunicationMod.

CRITICAL FINDING: CommunicationMod's choice_list only includes items
the player can currently afford (gold >= price). Items that are too
expensive are excluded from the choice_list entirely.

This means:
- screen_state.cards may include colorless rare cards not in choice_list
- screen_state.relics may include relics not in choice_list (too expensive)
- screen_state.potions may include potions not in choice_list (too expensive)

Therefore, we CANNOT use screen_state array lengths to calculate
'choose N' indices. Instead, we must match each screen_state item
by name against the raw choice_list to find the correct index.
"""


def build_choice_index_map(raw_choice_list, shop_cards, shop_relics, shop_potions):
    """Map each screen_state item to its actual index in the raw choice_list.

    Args:
        raw_choice_list: The raw choice_list from game_state (localized, may be lowercased)
        shop_cards: screen_state.cards array
        shop_relics: screen_state.relics array
        shop_potions: screen_state.potions array

    Returns:
        card_indices: {card_array_index: choice_list_index}
        relic_indices: {relic_array_index: choice_list_index}
        potion_indices: {potion_array_index: choice_list_index}
        purge_index: int (-1 if not in list)
    """
    card_indices = {}
    relic_indices = {}
    potion_indices = {}
    purge_index = -1

    # Track which screen_state items have been matched to avoid duplicate name collisions
    cards_matched = set()
    relics_matched = set()
    potions_matched = set()

    for choice_idx, choice_name in enumerate(raw_choice_list):
        if choice_name.lower() == 'purge':
            purge_index = choice_idx
            continue

        matched = False

        # Try to match with cards
        # choice_list uses localized lowercased names; screen_state uses original casing.
        # Compare case-insensitively to handle both English and Chinese games.
        for i, card in enumerate(shop_cards):
            if i not in cards_matched:
                if card.get('name', '').lower() == choice_name.lower():
                    card_indices[i] = choice_idx
                    cards_matched.add(i)
                    matched = True
                    break
        if matched:
            continue

        # Try to match with relics
        for i, relic in enumerate(shop_relics):
            if i not in relics_matched:
                if relic.get('name', '').lower() == choice_name.lower():
                    relic_indices[i] = choice_idx
                    relics_matched.add(i)
                    matched = True
                    break
        if matched:
            continue

        # Try to match with potions
        for i, potion in enumerate(shop_potions):
            if i not in potions_matched:
                if potion.get('name', '').lower() == choice_name.lower():
                    potion_indices[i] = choice_idx
                    potions_matched.add(i)
                    break

    return card_indices, relic_indices, potion_indices, purge_index
