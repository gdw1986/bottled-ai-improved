from typing import List

from rs.common.handlers.common_boss_relic_handler import CommonBossRelicHandler
from rs.machine.state import GameState


class BossRelicHandler(CommonBossRelicHandler):

    def __init__(self):
        super().__init__(preferred_relic_list=[
            "philosopher\u0027s stone",
            "cursed key",
            "fusion hammer",
            "velvet choker",
            "ectoplasm",
            "mark of pain",  # removed if already have another energy relic
            "sozu",  # removed if already have another energy relic
            "snecko eye",
            "busted crown",  # removed if already have another energy relic or it's act 1
            "coffee dripper",  # removed if already have another energy relic or it's act 1
            "slaver\u0027s collar",
            "runic cube",
            "runic pyramid",
            "black blood",
            "calling bell",
            "empty cage",
            "black star",
            "sacred bark",
        ])

    def adjust_preferences_based_on_game_state(self, prefs: List[str], state: GameState, has_energy_relic: bool):
        act = state.game_state()['act']

        def drop(relic: str):
            if relic in prefs:
                prefs.remove(relic)

        if act == 1 or has_energy_relic:
            drop('busted crown')
            drop('coffee dripper')

        if has_energy_relic:
            drop('mark of pain')
            drop('sozu')
