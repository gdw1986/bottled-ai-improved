from typing import List

from rs.game.card import card_id_to_name, compact_card_name
from rs.game.screen_type import ScreenType
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


def normalize_potion_id(potion_id: str) -> str:
    return ''.join(ch for ch in str(potion_id).lower() if ch.isalnum())


# Never use these potions automatically
dont_play_potions = [
    'FairyPotion',
    'FairyInABottle',   # auto-revive — save for death
    'Fairy In A Bottle',
    'Smoke Bomb',
    'SmokeBomb',        # escape fight — only use when truly stuck
    'Elixir Potion',
    'ElixirPotion',     # removes debuffs — situational
    'Liquid Memories',
    'LiquidMemories',   # choose card from discard — situational
    'Snecko Oil',
    'SneckoOil'         # randomizes costs — can backfire
]

# Early-use scaling potions for elite/boss fights
scaling_potions = [
    'Strength Potion',
    'StrengthPotion',
    'SteroidPotion',
    'Dexterity Potion',
    'DexterityPotion',
    'SpeedPotion',
    'Speed Potion',
    'Flex Potion',
    'FlexPotion',
    'Energy Potion',
    'EnergyPotion',
    'Cultist Potion',
    'CultistPotion',
    'Liquid Bronze',
    'LiquidBronze',
    'Essence of Steel',
    'EssenceOfSteel',
    'Heart of Iron',
    'HeartOfIron',
    'Blessing of the Forge',
    'BlessingOfTheForge',
    'Duplication Potion',
    'DuplicationPotion',
    'Power Potion',
    'PowerPotion',
    'Attack Potion',
    'AttackPotion',
    'Skill Potion',
    'SkillPotion',
    'Colorless Potion',
    'ColorlessPotion',
    'Swift Potion',
    'SwiftPotion',
    'Fear Potion',
    'FearPotion',
    'Weak Potion',
    'WeakPotion',
    'Fire Potion',
    'FirePotion',
    'Explosive Potion',
    'ExplosivePotion',
    'Block Potion',
    'BlockPotion',
    'Distilled Chaos',
    'DistilledChaos',
    'Entropic Brew',
    'EntropicBrew',
]

# Healing potions — use before we're critically low
healing_potions = [
    'Blood Potion',
    'BloodPotion',      # heals 20% max HP
    'Regen Potion',
    'RegenPotion',       # heals over time
    'Fruit Juice',
    'FruitJuice',        # +5 max HP (effectively heal 5)
]

dont_play_potion_ids = {normalize_potion_id(potion_id) for potion_id in dont_play_potions}
scaling_potion_ids = {normalize_potion_id(potion_id) for potion_id in scaling_potions}
healing_potion_ids = {normalize_potion_id(potion_id) for potion_id in healing_potions}
smoke_bomb_potion_ids = {normalize_potion_id(potion_id) for potion_id in ('Smoke Bomb', 'SmokeBomb')}
liquid_memories_potion_ids = {normalize_potion_id(potion_id) for potion_id in ('Liquid Memories', 'LiquidMemories')}
snecko_oil_potion_ids = {normalize_potion_id(potion_id) for potion_id in ('Snecko Oil', 'SneckoOil')}

attack_damage = {
    'anger': 6,
    'bash': 8,
    'bludgeon': 32,
    'bloodforblood': 18,
    'carnage': 20,
    'clash': 14,
    'cleave': 8,
    'clothesline': 12,
    'dropkick': 5,
    'feed': 10,
    'fiendfire': 20,
    'headbutt': 9,
    'heavyblade': 14,
    'hemokinesis': 15,
    'immolate': 21,
    'ironwave': 5,
    'perfectedstrike': 16,
    'pommelstrike': 9,
    'pummel': 8,
    'rampage': 8,
    'reaper': 4,
    'recklesscharge': 7,
    'searingblow': 12,
    'seversoul': 16,
    'strike': 6,
    'swordboomerang': 9,
    'thunderclap': 4,
    'twinstrike': 10,
    'uppercut': 13,
    'whirlwind': 5,
}

attack_hits = {
    'pummel': 4,
    'swordboomerang': 3,
    'twinstrike': 2,
}

upgrade_extra_hits = {
    'pummel': 1,
    'swordboomerang': 1,
}

attack_upgrade_bonus = {
    'bash': 2,
    'bludgeon': 10,
    'carnage': 8,
    'cleave': 3,
    'feed': 2,
    'headbutt': 3,
    'heavyblade': 3,
    'immolate': 7,
    'ironwave': 2,
    'pommelstrike': 1,
    'reaper': 1,
    'searingblow': 4,
    'strike': 3,
    'thunderclap': 3,
    'twinstrike': 4,
    'uppercut': 2,
    'whirlwind': 3,
}

block_values = {
    'armaments': 5,
    'defend': 5,
    'flamebarrier': 12,
    'ghostlyarmor': 10,
    'impervious': 30,
    'ironwave': 5,
    'powerthrough': 15,
    'secondwind': 10,
    'shrugitoff': 8,
    'truegrit': 7,
}

block_upgrade_bonus = {
    'armaments': 3,
    'defend': 3,
    'flamebarrier': 4,
    'ghostlyarmor': 3,
    'impervious': 10,
    'ironwave': 2,
    'powerthrough': 5,
    'shrugitoff': 3,
    'truegrit': 2,
}

rescue_card_values = {
    'disarm': 10,
    'intimidate': 8,
    'shockwave': 12,
}

liquid_memories_priority = [
    'offering',
    'impervious',
    'shockwave',
    'disarm',
    'powerthrough',
    'shrugitoff',
    'flamebarrier',
    'secondwind',
    'bash',
    'perfectedstrike',
    'twinstrike',
    'pommelstrike',
    'strike',
    'defend',
]

ignored_liquid_memories_grid_actions = {
    'DiscardAction',
    'ExhaustAction',
    'GamblingChipAction',
    'ScryAction',
}

liquid_memories_grid_actions = {
    'BetterDiscardPileToHandAction',
    'LiquidMemoryAction',
}


class PotionsBaseHandler(Handler):
    """Base class for all potion handlers."""

    def can_handle(self, state: GameState) -> bool:
        pass

    def handle(self, state: GameState) -> HandlerAction:
        pot = self.get_potions_to_play(state)[0]
        wait_command = "wait 30"
        if pot['requires_target']:
            target = 0
            for m_index, monster in enumerate(state.get_monsters()):
                if monster['name'] == 'Reptomancer':
                    target = m_index
                    break
                if not monster['is_gone']:
                    target = m_index
            return HandlerAction(
                commands=[wait_command, "potion use " + str(pot['idx']) + " " + str(target), wait_command])
        return HandlerAction(commands=[wait_command, "potion use " + str(pot['idx']), wait_command])

    def get_potions_to_play(self, state: GameState) -> List[dict]:
        to_play = []
        for idx, pot in enumerate(state.get_potions()):
            if pot['can_use'] and normalize_potion_id(pot['id']) not in dont_play_potion_ids:
                pot['idx'] = idx
                to_play.append(pot)
        return to_play

    def _get_potions_by_id(self, state: GameState, potion_ids: set[str]) -> List[dict]:
        to_play = []
        for idx, pot in enumerate(state.get_potions()):
            normalized_ids = {
                normalize_potion_id(pot.get('id', '')),
                normalize_potion_id(pot.get('name', '')),
            }
            if pot.get('can_use') and normalized_ids & potion_ids:
                pot['idx'] = idx
                to_play.append(pot)
        return to_play

    def _get_potion_by_category(self, state: GameState, category: set[str]) -> List[dict]:
        """Get usable potions matching a specific category."""
        return [p for p in self.get_potions_to_play(state) if normalize_potion_id(p['id']) in category]

    def _hp_percent(self, state: GameState) -> float:
        return state.get_player_health_percentage() * 100

    def _living_monsters(self, state: GameState) -> List[dict]:
        return [monster for monster in state.get_monsters() if not monster.get('is_gone')]

    def _estimated_incoming_damage(self, state: GameState) -> int:
        incoming = 0
        for monster in self._living_monsters(state):
            damage = monster.get('move_adjusted_damage')
            if damage is None:
                damage = monster.get('move_base_damage')
            if damage is None or damage < 0:
                continue
            incoming += damage * max(1, monster.get('move_hits') or 1)
        return incoming

    def _incoming_damage_after_block(self, state: GameState) -> int:
        return max(0, self._estimated_incoming_damage(state) - state.get_player_combat().get('block', 0))

    def _player_power_amount(self, state: GameState, power_id: str) -> int:
        for power in state.get_player_combat().get('powers', []):
            if power.get('id') == power_id:
                return power.get('amount', 0)
        return 0

    def _monster_power_amount(self, monster: dict, power_id: str) -> int:
        for power in monster.get('powers', []):
            if power.get('id') == power_id:
                return power.get('amount', 0)
        return 0

    @staticmethod
    def _card_key(card: dict) -> str:
        card_id = card.get('id', '')
        card_name = card_id_to_name(card_id) if card_id else card.get('name', '')
        compact = compact_card_name(card_name or card.get('name', ''))
        return ''.join(ch for ch in compact if ch.isalnum())

    @staticmethod
    def _card_upgrades(card: dict) -> int:
        return card.get('upgrades', 1 if '+' in card.get('name', '') else 0)

    def _strike_count(self, state: GameState) -> int:
        count = 0
        for card in state.game_state().get('deck', []):
            if self._card_key(card) == 'strike':
                count += 1
        return count

    def _estimated_card_damage(self, state: GameState, card: dict, monster: dict = None) -> int:
        key = self._card_key(card)
        upgrades = self._card_upgrades(card)

        if key == 'bodyslam':
            damage = state.get_player_combat().get('block', 0)
            hits = 1
        elif key == 'perfectedstrike':
            per_strike = 3 if upgrades else 2
            damage = (8 if upgrades else 6) + per_strike * self._strike_count(state)
            hits = 1
        elif key == 'whirlwind':
            damage = (attack_damage[key] + attack_upgrade_bonus.get(key, 0) * upgrades) \
                     * max(1, state.get_player_combat().get('energy', 0))
            hits = max(1, state.get_player_combat().get('energy', 0))
        else:
            damage = attack_damage.get(key)
            if damage is None:
                if card.get('type') != 'ATTACK':
                    return 0
                damage = 6
            damage += attack_upgrade_bonus.get(key, 3) * upgrades
            hits = attack_hits.get(key, 1) + (upgrade_extra_hits.get(key, 0) * upgrades)

        damage += self._player_power_amount(state, 'Strength') * hits
        if self._player_power_amount(state, 'Weakened') > 0:
            damage *= 0.75
        if monster and self._monster_power_amount(monster, 'Vulnerable') > 0:
            damage *= 1.5
        return int(damage)

    def _estimated_card_block(self, state: GameState, card: dict) -> int:
        key = self._card_key(card)
        if key == 'entrench':
            return state.get_player_combat().get('block', 0)

        block = block_values.get(key, 0)
        if block <= 0:
            return 0

        block += block_upgrade_bonus.get(key, 0) * self._card_upgrades(card)
        block += self._player_power_amount(state, 'Dexterity')
        if self._player_power_amount(state, 'Frail') > 0:
            block *= 0.75
        return int(block)

    def _estimated_card_rescue_value(self, state: GameState, card: dict) -> int:
        key = self._card_key(card)
        return max(
            self._estimated_card_block(state, card),
            rescue_card_values.get(key, 0),
        )

    def _card_can_kill_any_monster(self, state: GameState, card: dict) -> bool:
        for monster in self._living_monsters(state):
            effective_hp = monster.get('current_hp', 0) + monster.get('block', 0)
            if self._estimated_card_damage(state, card, monster) >= effective_hp:
                return True
        return False

    def _has_likely_lethal_card(self, state: GameState, cards: List[dict]) -> bool:
        return any(self._card_can_kill_any_monster(state, card) for card in cards)

    def _has_likely_playable_lethal_card(self, state: GameState, cards: List[dict]) -> bool:
        energy = state.get_player_combat().get('energy', 0)
        for card in cards:
            if not card.get('is_playable', True):
                continue
            cost = card.get('cost', 0)
            if cost == -1 and energy <= 0:
                continue
            if cost >= 0 and cost > energy:
                continue
            if self._card_can_kill_any_monster(state, card):
                return True
        return False

    def _best_liquid_memories_card_index(self, state: GameState, cards: List[dict]) -> int:
        lethal_cards = [
            (self._estimated_card_damage(state, card, monster), index)
            for index, card in enumerate(cards)
            for monster in self._living_monsters(state)
            if self._estimated_card_damage(state, card, monster)
            >= monster.get('current_hp', 0) + monster.get('block', 0)
        ]
        if lethal_cards:
            return max(lethal_cards)[1]

        incoming_after_block = self._incoming_damage_after_block(state)
        if incoming_after_block >= state.game_state().get('current_hp', 0):
            rescue_cards = [
                (self._estimated_card_rescue_value(state, card), index)
                for index, card in enumerate(cards)
                if self._estimated_card_rescue_value(state, card) > 0
            ]
            if rescue_cards:
                return max(rescue_cards)[1]

        priority_by_card = {card: priority for priority, card in enumerate(liquid_memories_priority)}
        ranked_cards = []
        for index, card in enumerate(cards):
            key = self._card_key(card)
            priority = priority_by_card.get(key, len(liquid_memories_priority))
            score = max(
                self._estimated_card_damage(state, card),
                self._estimated_card_rescue_value(state, card),
            )
            ranked_cards.append((-priority, score, -index))

        return -max(ranked_cards)[2] if ranked_cards else 0


class PotionsScalingHandler(PotionsBaseHandler):
    """Use scaling potions proactively on turn 1 of important fights."""

    def can_handle(self, state: GameState) -> bool:
        if not state.has_command(Command.POTION):
            return False
        if not state.combat_state():
            return False
        if state.screen_type() != ScreenType.NONE.value:
            return False

        hp = self._hp_percent(state)
        is_turn_1 = state.combat_state()['turn'] == 1
        room_type = state.game_state()['room_type']

        return (
            is_turn_1
            and hp > 40  # don't use scaling potions if we're about to die
            and (
                room_type == "MonsterRoomBoss"
                or (room_type == "MonsterRoomElite" and hp > 50)
            )
            and self._get_potion_by_category(state, scaling_potion_ids)
        )


class LiquidMemoriesHandler(PotionsBaseHandler):
    """Use Liquid Memories only when it can save the turn or close lethal."""

    def can_handle(self, state: GameState) -> bool:
        if not state.has_command(Command.POTION):
            return False
        if not state.combat_state():
            return False
        if state.screen_type() != ScreenType.NONE.value:
            return False
        if not self.get_potions_to_play(state):
            return False

        discard_pile = state.combat_state().get('discard_pile', [])
        if not discard_pile:
            return False

        hand = state.combat_state().get('hand', [])
        if self._has_likely_lethal_card(state, discard_pile) and not self._has_likely_playable_lethal_card(state, hand):
            return True

        incoming_after_block = self._incoming_damage_after_block(state)
        current_hp = state.game_state().get('current_hp', 0)
        has_rescue_card = any(self._estimated_card_rescue_value(state, card) > 0 for card in discard_pile)

        return (
            has_rescue_card
            and incoming_after_block > 0
            and (
                incoming_after_block >= current_hp
                or (self._hp_percent(state) <= 25 and incoming_after_block >= max(1, current_hp // 2))
            )
        )

    def get_potions_to_play(self, state: GameState) -> List[dict]:
        return self._get_potions_by_id(state, liquid_memories_potion_ids)


class SmokeBombEscapeHandler(PotionsBaseHandler):
    """Use Smoke Bomb to escape fights that are likely to end the run."""

    def can_handle(self, state: GameState) -> bool:
        if not state.has_command(Command.POTION):
            return False
        if not state.combat_state():
            return False
        if state.screen_type() != ScreenType.NONE.value:
            return False
        if not self.get_potions_to_play(state):
            return False

        room_type = state.game_state().get('room_type')
        if room_type == 'MonsterRoomBoss':
            return False

        hp = self._hp_percent(state)
        current_hp = state.game_state().get('current_hp', 0)
        incoming_after_block = self._incoming_damage_after_block(state)

        if incoming_after_block >= current_hp:
            return True

        if room_type == 'MonsterRoomElite':
            if hp <= 40:
                return True
            if state.act() >= 3 and hp <= 60:
                return True
            if state.has_relic('Runic Dome') and hp <= 70:
                return True

        return room_type == 'MonsterRoom' and hp <= 20 and incoming_after_block > 0

    def get_potions_to_play(self, state: GameState) -> List[dict]:
        return self._get_potions_by_id(state, smoke_bomb_potion_ids)


class SneckoOilEmergencyHandler(PotionsBaseHandler):
    """Use Snecko Oil only as a last-ditch boss/elite stabilizer."""

    def can_handle(self, state: GameState) -> bool:
        if not state.has_command(Command.POTION):
            return False
        if not state.combat_state():
            return False
        if state.screen_type() != ScreenType.NONE.value:
            return False
        if not self.get_potions_to_play(state):
            return False

        room_type = state.game_state().get('room_type')
        if room_type not in ('MonsterRoomBoss', 'MonsterRoomElite'):
            return False

        current_hp = state.game_state().get('current_hp', 0)
        return self._incoming_damage_after_block(state) >= current_hp or self._hp_percent(state) <= 25

    def get_potions_to_play(self, state: GameState) -> List[dict]:
        return self._get_potions_by_id(state, snecko_oil_potion_ids)


class LiquidMemoriesGridHandler(PotionsBaseHandler):
    """Pick the recovered card after Liquid Memories opens a combat GRID screen."""

    def can_handle(self, state: GameState) -> bool:
        if not state.has_command(Command.CHOOSE):
            return False
        if not state.combat_state():
            return False
        if state.screen_type() != ScreenType.GRID.value:
            return False

        screen_state = state.screen_state()
        if screen_state.get('for_purge') or screen_state.get('for_upgrade') or screen_state.get('for_transform'):
            return False
        current_action = state.game_state().get('current_action')
        if current_action in ignored_liquid_memories_grid_actions:
            return False
        if current_action not in liquid_memories_grid_actions:
            return False

        return bool(screen_state.get('cards'))

    def handle(self, state: GameState) -> HandlerAction:
        cards = state.screen_state().get('cards', [])
        card_index = self._best_liquid_memories_card_index(state, cards)
        return HandlerAction(commands=["wait 30", "choose " + str(card_index), "wait 30"])


class PotionsHealHandler(PotionsBaseHandler):
    """Use healing potions proactively — don't die with Blood Potion unused."""

    def can_handle(self, state: GameState) -> bool:
        hp = self._hp_percent(state)

        return (
            state.has_command(Command.POTION)
            and state.combat_state()
            and state.screen_type() == ScreenType.NONE.value
            and hp < 75  # Blood Potion restores 20% → use below 75%
            and self._get_potion_by_category(state, healing_potion_ids)
        )


class PotionsEmergencyHandler(PotionsBaseHandler):
    """Use any potion when HP is critically low — last resort."""

    def can_handle(self, state: GameState) -> bool:
        if not state.has_command(Command.POTION):
            return False
        if not state.combat_state():
            return False
        if state.screen_type() != ScreenType.NONE.value:
            return False

        hp = self._hp_percent(state)
        room_type = state.game_state()['room_type']

        # In elites, threshold is higher (they're more dangerous)
        threshold = 35 if room_type == "MonsterRoomElite" else 25

        return hp <= threshold and self.get_potions_to_play(state)


# Backward-compatible names for older tests and local scripts.
PotionsEliteHandler = PotionsScalingHandler
PotionsBossHandler = PotionsScalingHandler
