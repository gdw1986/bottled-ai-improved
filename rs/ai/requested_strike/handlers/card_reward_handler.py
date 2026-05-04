"""
Dynamic card reward handler for Ironclad/requested_strike.

Wraps CommonCardRewardHandler, tries data-driven selection first,
falls back to static DESIRED_CARDS_FOR_DECK list when data is insufficient.
"""
from presentation_config import presentation_mode, p_delay
from rs.common.handlers.card_reward.common_card_reward_handler import CommonCardRewardHandler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState
from rs.ai.requested_strike.handlers.dynamic_card_picker import pick_best_card


class DynamicCardRewardHandler(CommonCardRewardHandler):

    def __init__(self, cards_desired_for_deck: dict[str, int],
                 cards_desired_from_potions: dict[str, int] = None,
                 min_samples: int = 20):
        super().__init__(cards_desired_for_deck, cards_desired_from_potions)
        self._min_samples = min_samples

    def handle(self, state: GameState) -> HandlerAction:
        choice_list = state.get_choice_list_upgrade_stripped_from_choice()
        deck_card_list = state.get_deck_card_list_by_name_with_upgrade_stripped()

        # Skip dynamic for bowl / potion screens
        if 'bowl' in choice_list:
            return super().handle(state)

        # Build full list of card names (with duplicates) for feature extraction
        deck_names = []
        for name, count in deck_card_list.items():
            deck_names.extend([name] * count)

        try:
            act = state.act()
        except Exception:
            act = 1

        candidates = [c for c in choice_list if c != 'bowl']

        best = pick_best_card(candidates, deck_names, act, min_samples=self._min_samples)

        if best is not None and best in choice_list:
            idx = choice_list.index(best)
            cmd = f"choose {idx}"
            if presentation_mode:
                return HandlerAction(commands=[p_delay, cmd, "wait 30"])
            return HandlerAction(commands=[cmd, "wait 30"])

        # Data insufficient → fall back to static list
        return super().handle(state)
