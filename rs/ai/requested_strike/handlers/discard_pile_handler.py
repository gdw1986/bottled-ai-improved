from rs.game.card import card_id_to_name, compact_card_name
from rs.game.screen_type import ScreenType
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


headbutt_topdeck_priority = [
    'perfectedstrike',
    'offering',
    'bash',
    'twinstrike',
    'pommelstrike',
    'whirlwind',
    'immolate',
    'cleave',
    'shrugitoff',
    'powerthrough',
    'disarm',
    'shockwave',
    'battletrance',
    'armaments',
    'strike',
    'defend',
]

headbutt_damage = {
    'bash': 8,
    'cleave': 8,
    'immolate': 21,
    'perfectedstrike': 16,
    'pommelstrike': 9,
    'strike': 6,
    'swordboomerang': 9,
    'twinstrike': 10,
    'whirlwind': 5,
}

headbutt_upgrade_bonus = {
    'bash': 2,
    'cleave': 3,
    'immolate': 7,
    'perfectedstrike': 2,
    'pommelstrike': 1,
    'strike': 3,
    'swordboomerang': 3,
    'twinstrike': 4,
    'whirlwind': 3,
}


class DiscardPileToTopDeckHandler(Handler):
    """Choose the best card for Headbutt-style discard-pile-to-top effects."""

    def can_handle(self, state: GameState) -> bool:
        if not state.has_command(Command.CHOOSE):
            return False
        if not state.combat_state():
            return False
        if state.screen_type() != ScreenType.GRID.value:
            return False
        if state.game_state().get('current_action') != 'DiscardPileToTopOfDeckAction':
            return False
        return bool(state.screen_state().get('cards'))

    def handle(self, state: GameState) -> HandlerAction:
        cards = state.screen_state().get('cards', [])
        return HandlerAction(commands=["wait 30", "choose " + str(self._best_card_index(state, cards)), "wait 30"])

    def _best_card_index(self, state: GameState, cards: list[dict]) -> int:
        lethal_cards = [
            (self._estimated_card_damage(state, card), index)
            for index, card in enumerate(cards)
            if self._card_can_kill_any_monster(state, card)
        ]
        if lethal_cards:
            return max(lethal_cards)[1]

        priority_by_card = {card: priority for priority, card in enumerate(headbutt_topdeck_priority)}
        ranked = []
        for index, card in enumerate(cards):
            key = self._card_key(card)
            priority = priority_by_card.get(key, len(headbutt_topdeck_priority))
            score = self._estimated_card_damage(state, card)
            ranked.append((-priority, score, -index))
        return -max(ranked)[2] if ranked else 0

    def _card_can_kill_any_monster(self, state: GameState, card: dict) -> bool:
        for monster in state.get_monsters():
            if monster.get('is_gone'):
                continue
            effective_hp = monster.get('current_hp', 0) + monster.get('block', 0)
            if self._estimated_card_damage(state, card, monster) >= effective_hp:
                return True
        return False

    def _estimated_card_damage(self, state: GameState, card: dict, monster: dict = None) -> int:
        key = self._card_key(card)
        damage = headbutt_damage.get(key, 0)
        if damage <= 0:
            return 0
        damage += headbutt_upgrade_bonus.get(key, 0) * self._card_upgrades(card)
        damage += self._player_power_amount(state, 'Strength')
        if monster and self._monster_power_amount(monster, 'Vulnerable') > 0:
            damage *= 1.5
        return int(damage)

    @staticmethod
    def _card_key(card: dict) -> str:
        card_id = card.get('id', '')
        card_name = card_id_to_name(card_id) if card_id else card.get('name', '')
        compact = compact_card_name(card_name or card.get('name', ''))
        return ''.join(ch for ch in compact if ch.isalnum())

    @staticmethod
    def _card_upgrades(card: dict) -> int:
        return card.get('upgrades', 1 if '+' in card.get('name', '') else 0)

    @staticmethod
    def _player_power_amount(state: GameState, power_id: str) -> int:
        for power in state.get_player_combat().get('powers', []):
            if power.get('id') == power_id:
                return power.get('amount', 0)
        return 0

    @staticmethod
    def _monster_power_amount(monster: dict, power_id: str) -> int:
        for power in monster.get('powers', []):
            if power.get('id') == power_id:
                return power.get('amount', 0)
        return 0
