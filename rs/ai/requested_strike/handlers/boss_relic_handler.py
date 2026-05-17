from typing import List

from rs.common.handlers.common_boss_relic_handler import CommonBossRelicHandler
from rs.machine.state import GameState


class BossRelicHandler(CommonBossRelicHandler):

    def __init__(self):
        super().__init__(preferred_relic_list=[
            # Data-driven ordering from 35,691 Ironclad runs (A15+ win-rate)
            "snecko eye",               # 25.4% wr — massive for requested_strike
            "pandora\u0027s box",        # 19.3% wr — transforms starters into real cards
            "philosopher\u0027s stone",   # 17.9% wr
            "coffee dripper",            # 17.6% wr (removed if act 1 or has energy relic)
            "busted crown",              # 16.7% wr (removed if act 1 or has energy relic)
            "mark of pain",              # 16.3% wr (removed if already has energy relic)
            "velvet choker",             # 15.4% wr
            "fusion hammer",             # 14.9% wr
            "sozu",                      # 14.3% wr
            "cursed key",                # 13.3% wr
            "empty cage",                # 13.1% wr
            "slaver\u0027s collar",       # 12.7% wr
            "calling bell",              # 12.6% wr
            "runic pyramid",             # 12.4% wr
            "black star",                # 12.1% wr
            "ectoplasm",                 # 11.8% wr
            "tiny house",                # 10.8% wr
            "sacred bark",               # 10.0% wr
            "astrolabe",                 #  9.7% wr
            "runic cube",                #  8.6% wr
            "black blood",               #  8.3% wr
        ])

    def adjust_preferences_based_on_game_state(self, prefs: List[str], state: GameState, has_energy_relic: bool):
        act = state.game_state()['act']

        if 'runic dome' in prefs:
            prefs.remove('runic dome')

        if act == 1 or has_energy_relic:
            for relic in ('busted crown', 'coffee dripper'):
                if relic in prefs:
                    prefs.remove(relic)

        if has_energy_relic:
            if 'mark of pain' in prefs:
                prefs.remove('mark of pain')
