from ai.common.co_test_handler_fixture import CoTestHandlerFixture
from rs.common.handlers.common_neow_handler import CommonNeowHandler
from test_helpers.resources import load_resource_state


class TestNeowHandler(CoTestHandlerFixture):
    handler = CommonNeowHandler

    def test_handle_neow(self):
        self.execute_handler_tests('/event/event_neow.json', ['choose 1', 'wait 30'])

    def test_handle_neow_chinese_common_relic(self):
        state = load_resource_state('/event/event_neow.json')
        options = state.game_state()['screen_state']['options']
        options[0]['label'] = '\u83b7\u5f97\u4e00\u5f20\u968f\u673a\u7a00\u6709\u724c'
        options[0]['text'] = '[ \u83b7\u5f97\u4e00\u5f20\u968f\u673a\u7a00\u6709\u724c ]'
        options[1]['label'] = '\u968f\u673a\u83b7\u5f97\u4e00\u4e2a\u666e\u901a\u9057\u7269'
        options[1]['text'] = '[ \u968f\u673a\u83b7\u5f97\u4e00\u4e2a\u666e\u901a\u9057\u7269 ]'

        self.assertEqual(['choose 1', 'wait 30'], CommonNeowHandler().handle(state).commands)

    def test_handle_neow_chinese_common_relic_over_choose_card(self):
        state = load_resource_state('/event/event_neow.json')
        options = state.game_state()['screen_state']['options']
        options[0]['label'] = '\u9009\u62e9\u5e76\u83b7\u5f97\u4e00\u5f20\u724c'
        options[0]['text'] = '[ \u9009\u62e9\u5e76\u83b7\u5f97\u4e00\u5f20\u724c ]'
        options[1]['label'] = '\u968f\u673a\u83b7\u5f97\u4e00\u4e2a\u666e\u901a\u9057\u7269'
        options[1]['text'] = '[ \u968f\u673a\u83b7\u5f97\u4e00\u4e2a\u666e\u901a\u9057\u7269 ]'

        self.assertEqual(['choose 1', 'wait 30'], CommonNeowHandler().handle(state).commands)

    def test_handle_neow_chinese_choose_card_over_max_hp(self):
        state = load_resource_state('/event/event_neow.json')
        state.game_state()['choice_list'] = [
            '\u9009\u62e9\u5e76\u83b7\u5f97\u4e00\u5f20\u724c',
            '\u6700\u5927\u751f\u547d\u503c +8',
            '\u83b7\u5f97\u4e00\u5f20\u8bc5\u5492\u3002\u9009\u62e9\u5e76\u83b7\u5f97\u4e00\u5f20\u7a00\u6709\u65e0\u8272\u724c',
            '\u5931\u53bb\u4f60\u7684\u521d\u59cb\u9057\u7269\uff0c\u83b7\u5f97\u4e00\u4e2a\u968f\u673aBoss\u9057\u7269\u3002',
        ]
        options = state.game_state()['screen_state']['options']
        options[0]['label'] = '\u9009\u62e9\u5e76\u83b7\u5f97\u4e00\u5f20\u724c'
        options[0]['text'] = '[ \u9009\u62e9\u5e76\u83b7\u5f97\u4e00\u5f20\u724c ]'
        options[1]['label'] = '\u6700\u5927\u751f\u547d\u503c +8'
        options[1]['text'] = '[ \u6700\u5927\u751f\u547d\u503c +8 ]'
        options[2]['label'] = '\u83b7\u5f97\u4e00\u5f20\u8bc5\u5492\u3002\u9009\u62e9\u5e76\u83b7\u5f97\u4e00\u5f20\u7a00\u6709\u65e0\u8272\u724c'
        options[2]['text'] = '[ \u83b7\u5f97\u4e00\u5f20\u8bc5\u5492\u3002\u9009\u62e9\u5e76\u83b7\u5f97\u4e00\u5f20\u7a00\u6709\u65e0\u8272\u724c ]'
        options[3]['label'] = '\u5931\u53bb\u4f60\u7684\u521d\u59cb\u9057\u7269\uff0c\u83b7\u5f97\u4e00\u4e2a\u968f\u673aBoss\u9057\u7269\u3002'
        options[3]['text'] = '[ \u5931\u53bb\u4f60\u7684\u521d\u59cb\u9057\u7269\uff0c\u83b7\u5f97\u4e00\u4e2a\u968f\u673aBoss\u9057\u7269\u3002 ]'

        self.assertEqual(['choose 0', 'wait 30'], CommonNeowHandler().handle(state).commands)
