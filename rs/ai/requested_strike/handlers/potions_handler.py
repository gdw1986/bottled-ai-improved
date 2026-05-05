from typing import List

from rs.game.screen_type import ScreenType
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState

# Never use these potions automatically
dont_play_potions = [
    'FairyInABottle',   # auto-revive — save for death
    'SmokeBomb',        # escape fight — only use when truly stuck
    'ElixirPotion',     # removes debuffs — situational
    'LiquidMemories',   # choose card from discard — situational
    'SneckoOil'         # randomizes costs — can backfire
]

# Early-use scaling potions for elite/boss fights
scaling_potions = [
    'StrengthPotion',
    'DexterityPotion',
    'FlexPotion',
    'EnergyPotion',
    'CultistPotion',
    'LiquidBronze',
]

# Healing potions — use before we're critically low
healing_potions = [
    'BloodPotion',      # heals 20% max HP
    'RegenPotion',       # heals over time
    'FruitJuice',        # +5 max HP (effectively heal 5)
]


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
            if pot['can_use'] and pot['id'] not in dont_play_potions:
                pot['idx'] = idx
                to_play.append(pot)
        return to_play

    def _get_potion_by_category(self, state: GameState, category: List[str]) -> List[dict]:
        """Get usable potions matching a specific category."""
        return [p for p in self.get_potions_to_play(state) if p['id'] in category]

    def _hp_percent(self, state: GameState) -> float:
        return state.get_player_health_percentage() * 100


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
            and self._get_potion_by_category(state, scaling_potions)
        )


class PotionsHealHandler(PotionsBaseHandler):
    """Use healing potions proactively — don't die with Blood Potion unused."""

    def can_handle(self, state: GameState) -> bool:
        hp = self._hp_percent(state)

        return (
            state.has_command(Command.POTION)
            and state.combat_state()
            and state.screen_type() == ScreenType.NONE.value
            and hp < 75  # Blood Potion restores 20% → use below 75%
            and self._get_potion_by_category(state, healing_potions)
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
