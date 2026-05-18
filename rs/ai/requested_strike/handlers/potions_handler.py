from typing import List

from rs.game.screen_type import ScreenType
from rs.machine.command import Command
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState

dont_play_potions = [
    'FairyInABottle',
    'SmokeBomb',
    'ElixirPotion',
    'LiquidMemories',
    'SneckoOil'
]


def _potion_key(potion: dict) -> str:
    return ''.join(ch for ch in potion.get('id', potion.get('name', '')).lower() if ch.isalnum())


def _has_potion(potions: List[dict], potion_ids: List[str]) -> bool:
    potion_keys = {_potion_key(p) for p in potions}
    return bool(potion_keys & set(potion_ids))


def _act_one_elite(state: GameState) -> bool:
    return state.game_state()['room_type'] == "MonsterRoomElite" and state.game_state()['act'] == 1


LAGAVULIN_SETUP_POTIONS = [
    'strengthpotion',
    'cultistpotion',
    'ancientpotion',
    'fearpotion',
    'flexpotion',
    'steroidpotion',
    'firepotion',
]

NOB_OPENING_POTIONS = [
    'strengthpotion',
    'fearpotion',
    'firepotion',
    'flexpotion',
    'steroidpotion',
    'cultistpotion',
    'weakpotion',
]

SENTRY_OPENING_POTIONS = [
    'explosivepotion',
    'strengthpotion',
    'fearpotion',
    'firepotion',
    'dexteritypotion',
    'blockpotion',
    'speedpotion',
]

GENERAL_ELITE_POTIONS = [
    'strengthpotion',
    'fearpotion',
    'firepotion',
    'explosivepotion',
    'cultistpotion',
    'ancientpotion',
    'flexpotion',
    'steroidpotion',
    'weakpotion',
    'dexteritypotion',
    'blockpotion',
    'speedpotion',
]


class PotionsBaseHandler(Handler):

    def can_handle(self, state: GameState) -> bool:
        # must be implemented by children
        pass

    def handle(self, state: GameState) -> HandlerAction:
        pot = self.get_potions_to_play(state)[0]
        wait_command = "wait 30"
        if pot['requires_target']:
            target = 0
            for m_index, monster in enumerate(state.get_monsters()):  # Find the back-est monster that isn't dead
                if monster['name'] == 'Reptomancer':  # Special case since he might not be in the back
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
        return sorted(to_play, key=lambda p: self.potion_priority(state, p))

    def potion_priority(self, state: GameState, potion: dict) -> int:
        key = _potion_key(potion)

        if _act_one_elite(state):
            if state.has_monster("Lagavulin") and key in LAGAVULIN_SETUP_POTIONS:
                return LAGAVULIN_SETUP_POTIONS.index(key)
            if state.has_monster("Gremlin Nob") and key in NOB_OPENING_POTIONS:
                return NOB_OPENING_POTIONS.index(key)
            if state.has_monster("Sentry") and key in SENTRY_OPENING_POTIONS:
                return SENTRY_OPENING_POTIONS.index(key)
            if key in GENERAL_ELITE_POTIONS:
                return GENERAL_ELITE_POTIONS.index(key) + 20

        return 100


class PotionsEliteHandler(PotionsBaseHandler):
    def __int__(self):
        super().__init__()

    def can_handle(self, state: GameState) -> bool:
        hp_per = state.get_player_health_percentage() * 100
        potions = self.get_potions_to_play(state)
        return state.has_command(Command.POTION) \
               and state.combat_state() \
               and state.screen_type() == ScreenType.NONE.value \
               and state.game_state()['room_type'] == "MonsterRoomElite" \
               and (((hp_per <= 50 and state.combat_state()['turn'] == 1) or hp_per <= 30)
                    or self.should_use_act_one_elite_potion(state, potions)) \
               and potions

    def should_use_act_one_elite_potion(self, state: GameState, potions: List[dict]) -> bool:
        if not _act_one_elite(state) or state.combat_state()['turn'] > 2:
            return False

        if state.has_monster("Lagavulin"):
            return _has_potion(potions, LAGAVULIN_SETUP_POTIONS)

        if state.has_monster("Gremlin Nob"):
            return _has_potion(potions, NOB_OPENING_POTIONS)

        if state.has_monster("Sentry"):
            return _has_potion(potions, SENTRY_OPENING_POTIONS)

        return _has_potion(potions, GENERAL_ELITE_POTIONS)


class PotionsEventFightHandler(PotionsBaseHandler):  # Treat most Event Fights like Elites
    def __int__(self):
        super().__init__()

    def can_handle(self, state: GameState) -> bool:
        hp_per = state.get_player_health_percentage() * 100
        return state.has_command(Command.POTION) \
               and state.combat_state() \
               and state.screen_type() == ScreenType.NONE.value \
               and state.game_state()['room_type'] == "EventRoom" \
               and not state.has_monster("Fungi Beast") \
               and ((hp_per <= 50 and state.combat_state()['turn'] == 1) or hp_per <= 30) \
               and self.get_potions_to_play(state)


class PotionsBossHandler(PotionsBaseHandler):
    def __int__(self):
        super().__init__()

    def can_handle(self, state: GameState) -> bool:
        return state.has_command(Command.POTION) \
               and state.combat_state() \
               and state.screen_type() == ScreenType.NONE.value \
               and state.game_state()['room_type'] == "MonsterRoomBoss" \
               and state.combat_state()['turn'] == 1 \
               and self.get_potions_to_play(state)
