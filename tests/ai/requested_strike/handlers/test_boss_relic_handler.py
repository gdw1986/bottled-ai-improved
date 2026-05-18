from ai.requested_strike.rs_test_handler_fixture import RsTestHandlerFixture
from rs.ai.requested_strike.handlers.boss_relic_handler import BossRelicHandler
from test_helpers.resources import load_resource_state


class BossRelicHandlerTestCase(RsTestHandlerFixture):
    handler = BossRelicHandler

    def test_skip_bad_energy_relics_when_applicable(self):
        self.execute_handler_tests('relics/boss_reward_nothing_to_take.json', ['skip', 'proceed'])

    def test_prefers_philosophers_stone_over_sozu(self):
        self.execute_handler_tests('relics/boss_reward_first_is_best.json', ['choose 2'])

    def test_skips_runic_dome_when_it_is_the_only_offer(self):
        state = self._boss_reward_state(["runic dome"])

        actual = self.handler().handle(state)

        self.assertEqual(["skip", "proceed"], actual.commands)

    def test_avoids_sozu_after_taking_an_energy_relic(self):
        state = self._boss_reward_state(["sozu", "black star"])
        state.json["game_state"]["relics"].append({
            "name": "Cursed Key",
            "id": "Cursed Key",
            "counter": -1,
        })

        actual = self.handler().handle(state)

        self.assertEqual(["choose 1"], actual.commands)

    def _boss_reward_state(self, choices):
        state = load_resource_state('relics/boss_reward_first_is_best.json')
        state.json["game_state"]["choice_list"] = choices
        state.json["game_state"]["screen_state"]["relics"] = [
            {
                "name": choice.title(),
                "id": choice.title(),
                "counter": -1,
            }
            for choice in choices
        ]
        return state

