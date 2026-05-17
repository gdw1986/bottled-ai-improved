from ai.requested_strike.rs_test_handler_fixture import RsTestHandlerFixture
from rs.ai.requested_strike.handlers.boss_relic_handler import BossRelicHandler
from rs.machine.state import GameState
from rs.machine.the_bots_memory_book import TheBotsMemoryBook


class BossRelicHandlerTestCase(RsTestHandlerFixture):
    handler = BossRelicHandler

    def test_skip_bad_energy_relics_when_applicable(self):
        self.execute_handler_tests('relics/boss_reward_nothing_to_take.json', ['skip', 'proceed'])

    def test_skip_runic_dome_when_it_is_the_only_offer(self):
        state = self._boss_reward_state(["Runic Dome"], ["Runic Dome"])
        handler = BossRelicHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["skip", "proceed"], handler.handle(state).commands)

    def test_take_other_relic_over_runic_dome(self):
        state = self._boss_reward_state(["Runic Dome", "Black Star"], ["Runic Dome", "Black Star"])
        handler = BossRelicHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["choose 1"], handler.handle(state).commands)

    @staticmethod
    def _boss_reward_state(choice_list: list[str], relic_ids: list[str]) -> GameState:
        return GameState(
            {
                "available_commands": ["choose", "skip", "proceed", "wait", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "choice_list": choice_list,
                    "screen_type": "BOSS_REWARD",
                    "screen_state": {
                        "relics": [
                            {"name": relic_id, "id": relic_id, "counter": -1}
                            for relic_id in relic_ids
                        ],
                    },
                    "seed": 1,
                    "deck": [],
                    "relics": [{"name": "Burning Blood", "id": "Burning Blood", "counter": -1}],
                    "max_hp": 80,
                    "act_boss": "Hexaghost",
                    "gold": 0,
                    "action_phase": "WAITING_ON_USER",
                    "act": 1,
                    "screen_name": "BOSS_REWARD",
                    "room_phase": "COMPLETE",
                    "is_screen_up": True,
                    "potions": [],
                    "current_hp": 80,
                    "floor": 16,
                    "ascension_level": 0,
                    "class": "IRONCLAD",
                    "map": [],
                    "room_type": "TreasureRoomBoss",
                },
            },
            TheBotsMemoryBook.new_default(),
        )

