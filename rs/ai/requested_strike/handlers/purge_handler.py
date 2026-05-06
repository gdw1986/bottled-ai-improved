"""
Custom purge handler for requested_strike.
Key fix: instead of matching card names against choice_list (fragile with Chinese encoding),
we rank cards by iterating state.deck.cards directly and map to choice_list indices.

Removal order:
  1. Curses — always first
  2. Starters (Strike, Defend) — replace with better cards
  3. Low-winrate cards (from CARD_REMOVAL_PRIORITY_LIST)
  4. Everything else — desirable cards (Feel No Pain, etc.) come LAST
"""

from typing import List

from presentation_config import presentation_mode, p_delay
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class PurgeHandler(Handler):

    def __init__(self):
        # Cards we WANT to remove (ordered: remove these first)
        self.removal_preferences: List[str] = [
            # Curses
            'regret', 'doubt', 'injury', 'pain', 'decay', 'shame',
            'writhe', 'normality', 'parasite', 'clumsy',
            'curseofthebell', 'necronomicurse', 'ascendersbane',
            # Starters
            'strike_r', 'defend_r', 'strike', 'defend',
            'strike_r+1', 'defend_r+1', 'strike+1', 'defend+1',
            # Bad cards — low winrate ceiling
            'rampage', 'wild strike', 'hemokinesis', 'combust',
            'carnage', 'anger', 'fire breathing', 'searing blow',
            # Upgraded variants
            'rampage+1', 'wild strike+1', 'hemokinesis+1', 'combust+1',
            'carnage+1', 'anger+1', 'fire breathing+1', 'searing blow+1',
        ]

        # Cards we NEVER want to remove unless forced (high-value keepers)
        self.keeper_cards: List[str] = [
            'offering', 'impervious', 'battle trance', 'limit break',
            'feel no pain', 'corruption', 'dark embrace', 'barricade',
            'demon form', 'reaper', 'exhume', 'shockwave', 'disarm',
            'apotheosis', 'shrug it off', 'burning pact', 'brutality',
            'double tap', 'armaments', 'sentinel', 'warcry',
            'power through', 'spot weakness', 'inflame',
            'ghostly armor', 'second wind', 'juggernaut', 'entrench',
            'metallicize', 'fiend fire', 'evolve', 'true grit',
            'master of strategy', 'dark shackles', 'flash of steel',
            'panache', 'panacea', 'finesse', 'mayhem', 'bandage up',
            'trip', 'blind',
        ]

    def can_handle(self, state: GameState) -> bool:
        return (state.has_command(Command.CHOOSE)
                and state.game_state()["screen_type"] == "GRID"
                and state.game_state()["screen_state"]["for_purge"]
                and len(state.get_choice_list()) > 0)

    def handle(self, state: GameState) -> HandlerAction:
        commands = []
        amount = 1
        screen_state = state.game_state().get('screen_state', {})
        if 'num_cards' in screen_state:
            amount = screen_state['num_cards']

        choices = self._get_choices(state)
        for card_index in choices[:amount]:
            if presentation_mode:
                commands.append(p_delay)
            commands.append(f"choose {card_index}")
            commands.append("wait 30")
        return HandlerAction(commands=commands)

    def _get_choices(self, state: GameState) -> List[int]:
        """Build removal order by inspecting state.deck.cards directly.
        
        This avoids the name-matching-through-translation issue that
        caused desirable cards like Feel No Pain to be selected early.
        
        Bug fix: each deck card must map to a UNIQUE choice_list index.
        Previously, 3 Strike_R cards all mapped to index 0, causing
        choices[:2] = [0, 0] → choose 0 selects then deselects → infinite loop.
        """
        choice_list = state.get_choice_list()
        deck_cards = state.deck.cards

        # Phase 1: rank every card in deck by removal priority
        # Lower score = remove first
        ranked: List[tuple[int, int]] = []  # (score, choice_list_index)
        used_indices: set[int] = set()       # track which indices are already assigned

        for card in deck_cards:
            card_id = card.id.lower()
            # Find this card in choice_list, skipping already-used indices
            card_index = self._find_in_choice_list(card_id, choice_list, exclude=used_indices)
            if card_index is None:
                continue

            used_indices.add(card_index)

            # Score: 0 = remove first, 100 = keep, 50 = neutral
            score = self._score_card(card_id, card)
            ranked.append((score, card_index))

        # Sort by score ascending (remove first = lowest score)
        ranked.sort(key=lambda x: x[0])

        result = [idx for _, idx in ranked]

        # Append any choice_list items not found in deck (shouldn't happen, but safe)
        for i in range(len(choice_list)):
            if i not in result:
                result.append(i)

        return result

    def _score_card(self, card_id: str, card) -> int:
        """Score a card for removal: 0 = remove first, 100 = never remove."""
        card_key = self._normalize_name(card_id)
        base_id = self._base_card_key(card_id)

        # Curses → always remove first
        if card.type.value in ('CURSE', 'Curse', 'curse'):
            return 0

        # Exact match in removal preferences → remove early
        for i, pref in enumerate(self.removal_preferences):
            pref_key = self._normalize_name(pref)
            pref_base_key = self._base_card_key(pref)
            if base_id == pref_base_key or base_id == pref_key or card_key == pref_key:
                return 10 + i  # curses=0..9, starters=10.., bad cards=18..

        # Keeper cards → never remove (unless no other choice)
        for pref in self.keeper_cards:
            pref_key = self._normalize_name(pref)
            pref_base_key = self._base_card_key(pref)
            if base_id == pref_base_key or base_id == pref_key or card_key == pref_key:
                return 90

        # Neutral cards → middle of the pack
        return 50

    @classmethod
    def _find_in_choice_list(cls, card_id: str, choice_list: List[str],
                             exclude: set[int] | None = None) -> int | None:
        """Find a card in choice_list by its id. Handles translated names.
        
        Args:
            card_id: English card ID (e.g. 'strike_r')
            choice_list: list of card names (English after get_choice_list() mapping)
            exclude: set of indices to skip (already assigned to another deck card)
        
        When multiple deck cards share the same name (e.g. 3x Strike_R),
        without exclude they'd all map to the same choice_list index,
        causing choose N to toggle select/deselect instead of picking distinct cards.
        """
        if exclude is None:
            exclude = set()
        card_key = cls._normalize_name(card_id)
        base_id = cls._base_card_key(card_id)

        # Try exact match first
        for i, name in enumerate(choice_list):
            if i in exclude:
                continue
            name_key = cls._normalize_name(name)
            if name_key == base_id or name_key == card_key:
                return i

        # Try partial match (card_id as substring of choice_list name)
        for i, name in enumerate(choice_list):
            if i in exclude:
                continue
            if base_id in cls._normalize_name(name):
                return i

        return None

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.lower().replace(' ', '').replace('_', '').replace('-', '').replace("'", "")

    @classmethod
    def _base_card_key(cls, name: str) -> str:
        base = name.lower()
        for suffix in ('_r', '_g', '_b', '_p'):
            if base.endswith(suffix):
                base = base[: -len(suffix)]
                break
        return cls._normalize_name(base)
