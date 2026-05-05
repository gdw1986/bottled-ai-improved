from typing import List

from presentation_config import presentation_mode, p_delay, p_delay_s
from rs.common.handlers.common_upgrade_handler import CommonUpgradeHandler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState

# Winrate tiers for fallback selection when no priority card is available.
# Higher tier = pick first. Uses raw card IDs (lowercase) from conditional_winrates.
FALLBACK_UPGRADE_TIERS: List[str] = [
    # S-tier — always worth upgrading
    'offering', 'impervious', 'battle trance', 'limit break',
    # A-tier
    'armaments', 'exhume', 'sentinel', 'warcry', 'shockwave',
    'power through', 'feel no pain', 'apotheosis', 'shrug it off',
    'burning pact', 'brutality', 'double tap', 'corruption', 'disarm',
    # B-tier
    'barricade', 'demon form', 'sword boomerang', 'dark embrace',
    'reaper', 'dropkick', 'ghostly armor', 'heavy blade',
    'pommel strike', 'intimidate', 'second wind', 'juggernaut',
    'entrench', 'metallicize', 'spot weakness', 'body slam',
    'iron wave', 'dual wield', 'inflame', 'flame barrier',
    'fiend fire', 'evolve', 'true grit', 'uppercut', 'pummel',
    'twin strike', 'perfected strike', 'clash',
    # C-tier — act 1 commons
    'cleave', 'clothesline', 'thunderclap', 'anger', 'headbutt',
    'whirlwind', 'flex',
    # Colorless/Shop
    'master of strategy', 'dark shackles', 'flash of steel',
    'panache', 'panacea', 'finesse', 'mayhem', 'bandage up',
    'trip', 'blind', 'handofgreed',
    'swift strike', 'dramatic entrance',
    # Last resort — starters (only if nothing else available)
    'bash', 'neutralize', 'zap', 'dualcast',
    # NEVER upgrade these — they're in removal list
]


class UpgradeHandler(CommonUpgradeHandler):

    def __init__(self):
        super().__init__(priorities=[
            'apotheosis',
            'limit break',        # #1.5: exhaust → non-exhaust — enables infinite strength
            'spot weakness',
            'inflame',
            'demon form',
            'armaments',          # #2 priority: upgrades entire hand
            'whirlwind',
            'heavy blade',
            'pummel',
            'sword boomerang',
            'perfected strike',
            'bash',
            'shockwave',
            'uppercut',  # Not in pickup list at time of writing
            'battle trance',
            'offering',
            'blind',
            'seeing red',  # Not in pickup list at time of writing
            'dropkick',
            'flame barrier',
            'twin strike',
            'pommel strike',
            'handofgreed',
            'thunderclap',
            'shrug it off',
            'impervious',
            'ghostly armor',
            'master of strategy',
            'flash of steel',
            'trip',
            'dark shackles',
            'swift strike',
            'dramatic entrance',
            'finesse',
        ])

    def transform_priorities_based_on_game_state(self, priorities: List[str], state: GameState):
        remove_if_snecko = [
            'barricade',
            'blood for blood',
            'body slam',
            'corruption',
            'dark embrace',
            'entrench',
            'exhume',
            'havoc',
            'infernal blade',
            'seeing red',
        ]
        safe_remove_if_snecko = []

        if state.has_relic("Snecko Eye"):
            for c in remove_if_snecko:
                if c in priorities:
                    safe_remove_if_snecko.append(c)
            for d in safe_remove_if_snecko:
                priorities.remove(d)

    def handle(self, state: GameState) -> HandlerAction:
        # Copy priorities (parent might modify them)
        transformed_priorities = self.upgrade_priorities.copy()
        self.transform_priorities_based_on_game_state(transformed_priorities, state)

        translated_list = state.get_choice_list()

        # First pass: try priority list
        for priority in transformed_priorities:
            if priority in translated_list:
                idx = translated_list.index(priority)
                if presentation_mode:
                    return HandlerAction(commands=[p_delay, "choose " + str(idx), p_delay_s])
                return HandlerAction(commands=["choose " + str(idx)])

        # Second pass: try fallback tiers — pick the highest-tier card available
        # Skip cards in removal list (we'll be removing them soon anyway)
        removal_list = {'strike_r', 'defend_r', 'strike', 'defend',
                        'strike_r+1', 'defend_r+1', 'strike+1', 'defend+1',
                        'rampage', 'rampage+1', 'handofgreed', 'handofgreed+1',
                        'wild strike', 'wild strike+1', 'hemokinesis', 'hemokinesis+1',
                        'combust', 'combust+1', 'carnage', 'carnage+1',
                        'anger', 'anger+1', 'fire breathing', 'fire breathing+1',
                        'searing blow', 'searing blow+1'}

        # Build ordered list: find best available card in fallback tiers, excluding removal candidates
        for tier_card in FALLBACK_UPGRADE_TIERS:
            if tier_card in translated_list and tier_card not in removal_list:
                idx = translated_list.index(tier_card)
                if presentation_mode:
                    return HandlerAction(commands=[p_delay, "choose " + str(idx), p_delay_s])
                return HandlerAction(commands=["choose " + str(idx)])

        # Third pass: pick any card NOT in removal list
        for i, card_name in enumerate(translated_list):
            if card_name not in removal_list:
                if presentation_mode:
                    return HandlerAction(commands=[p_delay, "choose " + str(i), p_delay_s])
                return HandlerAction(commands=["choose " + str(i)])

        # Absolute last resort: pick the first item (shouldn't reach here normally)
        if presentation_mode:
            return HandlerAction(commands=[p_delay, "choose 0", p_delay_s])
        return HandlerAction(commands=["choose 0"])
