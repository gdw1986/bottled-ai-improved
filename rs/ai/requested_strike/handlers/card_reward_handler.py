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


ACT1_SURVIVAL_FALLBACK_CARDS = [
    ('uppercut', 1),
    ('clothesline', 1),
    ('carnage', 1),
    ('ghostly armor', 1),
    ('iron wave', 1),
    ('metallicize', 1),
    ('feel no pain', 1),
]


class DynamicCardRewardHandler(CommonCardRewardHandler):

    def __init__(self, cards_desired_for_deck: dict[str, int],
                 cards_desired_from_potions: dict[str, int] = None,
                 min_samples: int = 20):
        super().__init__(cards_desired_for_deck, cards_desired_from_potions)
        self._min_samples = min_samples

    def handle(self, state: GameState) -> HandlerAction:
        choice_list = state.get_choice_list_upgrade_stripped_from_choice()
        deck_card_list = state.get_deck_card_list_by_name_with_upgrade_stripped()

        # Skip dynamic for bowl / potion screens.
        if 'bowl' in choice_list or state.game_state()["room_phase"] == "COMBAT":
            return super().handle(state)

        # Build full list of card names (with duplicates) for feature extraction
        deck_names = []
        for name, count in deck_card_list.items():
            deck_names.extend([name] * count)

        act = state.act()

        candidates = []
        for candidate in choice_list:
            max_copies = self.cards_desired_for_deck.get(candidate)
            if max_copies is None:
                continue
            if deck_card_list.get(candidate, 0) >= max_copies:
                continue
            candidates.append(candidate)

        if not candidates:
            return super().handle(state)

        best = pick_best_card(candidates, deck_names, act, min_samples=self._min_samples)

        if best is not None and best in choice_list:
            idx = choice_list.index(best)
            cmd = f"choose {idx}"
            if presentation_mode:
                return HandlerAction(commands=[p_delay, cmd, "wait 30"])
            return HandlerAction(commands=[cmd, "wait 30"])

        fallback = self._pick_act1_survival_fallback(choice_list, deck_card_list, state)
        if fallback is not None:
            cmd = f"choose {choice_list.index(fallback)}"
            if presentation_mode:
                return HandlerAction(commands=[p_delay, cmd, "wait 30"])
            return HandlerAction(commands=[cmd, "wait 30"])

        # Data insufficient → fall back to static list
        return super().handle(state)

    def _pick_act1_survival_fallback(
            self,
            choice_list: list[str],
            deck_card_list: dict[str, int],
            state: GameState,
    ) -> str | None:
        if state.act() != 1:
            return None
        if state.floor() > 6:
            return None

        for card, max_copies in ACT1_SURVIVAL_FALLBACK_CARDS:
            if card in choice_list and deck_card_list.get(card, 0) < max_copies:
                return card
        return None
