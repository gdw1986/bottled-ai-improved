from rs.ai.requested_strike.handlers.event_handler import EventHandler
from test_helpers.resources import load_resource_state


def test_requested_strike_liars_game_uses_ssssserpent_choice():
    state = load_resource_state('/event/event_unknown.json')
    game_state = state.game_state()
    game_state['choice_list'] = ['\u540c\u610f', '\u53cd\u5bf9']
    game_state['screen_state']['event_id'] = 'Liars Game'
    game_state['screen_state']['event_name'] = '\u86c7\uff5e'
    game_state['screen_state']['options'] = [
        {'choice_index': 0, 'disabled': False, 'text': '[\u540c\u610f]', 'label': '\u540c\u610f'},
        {'choice_index': 1, 'disabled': False, 'text': '[\u53cd\u5bf9]', 'label': '\u53cd\u5bf9'},
    ]

    assert EventHandler().handle(state).commands == ['choose 1', 'wait 30']
