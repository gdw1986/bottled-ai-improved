from rs.ai.peaceful_pummeling.card_picker import apply_dynamic_picks
from rs.ai.peaceful_pummeling.config import DESIRED_CARDS_FOR_DECK, DESIRED_CARDS_FROM_POTIONS
from rs.common.handlers.card_reward.common_card_reward_handler import CommonCardRewardHandler
from rs.machine.state import GameState


class CardRewardHandler(CommonCardRewardHandler):

    def __init__(self):
        super().__init__(
            cards_desired_for_deck=DESIRED_CARDS_FOR_DECK,
            cards_desired_from_potions=DESIRED_CARDS_FROM_POTIONS)

    def transform_desired_cards_map_from_state(self, cards: dict[str, int], state: GameState):
        # --- Legacy removals (kept for backwards compatibility) ---
        remove_if_snecko = [
            'consecrate',
            'halt',
            'just lucky',
            'scrawl',
        ]

        if state.has_relic("Snecko Eye"):
            for c in remove_if_snecko:
                cards.pop(c, None)

        remove_if_pyramid = [
            'battle hymn',
        ]

        if state.has_relic("Runic Pyramid"):
            for c in remove_if_pyramid:
                cards.pop(c, None)

        # --- Dynamic card picking: adjusts priorities based on deck state ---
        apply_dynamic_picks(cards, state)
