from ai.common.co_test_handler_fixture import CoTestHandlerFixture
from rs.common.handlers.common_mass_discard_handler import CommonMassDiscardHandler
from test_helpers.resources import load_resource_state


class TestMassDiscardHandler(CoTestHandlerFixture):
    handler = CommonMassDiscardHandler

    def test_handle_mass_discard_with_relic(self):
        self.execute_handler_tests('/other/discard_relic.json', ['choose 1'])

    def test_handle_mass_discard_with_relic_curse(self):
        self.execute_handler_tests('/other/discard_relic_curse.json', ['choose 1'])

    def test_handle_mass_discard_with_relic_done(self):
        self.execute_handler_tests('/other/discard_relic_done.json', ['confirm'])

    def test_handle_mass_discard_everything_discarded(self):
        self.execute_handler_tests('/other/discarded_everything.json', ['confirm'])

    def test_handle_localized_mass_discard_with_empty_cards_list(self):
        state = load_resource_state('/other/discard_relic.json')
        translations = {
            'Battle Trance': '战斗专注',
            'Strike': '打击',
            'Defend': '防御',
            'Perfected Strike+': '完美打击+',
        }

        game_state = state.game_state()
        for idx, card in enumerate(game_state['screen_state']['hand']):
            card['name'] = translations[card['name']]
            game_state['choice_list'][idx] = card['name'].lower()
        game_state['screen_state']['cards'] = []

        actual = CommonMassDiscardHandler().handle(state)

        self.assertEqual(['choose 1'], actual.commands)
