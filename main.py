import sys
import time
import traceback

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

from rs.ai.claw_is_law.claw_is_law import CLAW_IS_LAW
from rs.ai.peaceful_pummeling.peaceful_pummeling import PEACEFUL_PUMMELING
from rs.ai.pwnder_my_orbs.pwnder_my_orbs import PWNDER_MY_ORBS
from rs.ai.requested_strike.requested_strike import REQUESTED_STRIKE
from rs.ai.shivs_and_giggles.shivs_and_giggles import SHIVS_AND_GIGGLES
from rs.helper.seed import make_random_seed
from rs.api.client import Client
from rs.machine.game import Game
from rs.helper.logger import log, init_log, log_new_run_sequence

# If there are run seeds, it will run them. Otherwise, it will use the run amount.
run_seeds = [
'75MD25VMB8CR',
'K7AURB80PDYR',
'8Y8KRGADR2YE',
'EYQGFIKNNTVV',
'7VECZLGSCEYI',
'M1KF5CR20A01',
'721G0DHYN0R2',
'BXD9ACW35VH',
'VVL2LJ8NMWRY',
'CFNV2X810SM4',
'DP4G29AQZJM2',
'HKVP462VKFT2',
'L5BG57LF16GY',
'N2DQTYZRSAQ0',
'EMU9YMSYH9QH',
'T41XAG6BABU6',
'S4UC7W4TM9RY',
'ZFCDIN4NZ45W',
'GPJY9RLR30WN',
'ISU4N9DT3DC0',
'5LSEI5KL83FX',
'H728LUIKSBW',
'77DFMD2S328D',
'G70SASBSIFR7',
'A8JF9AF8Z79K',
'SBVUILNMTZA2',
'9WR3EVSDTC15',
'NGU4TGGFTULS',
'11K0AVUIXNA3S',
'16EU8E4P34ZQ5',
'MG10R9WA4NMA',
'SYBBKJ44I4JT',
'4UD2VDRZF2UW',
'107HXTYQEITV9',
'WSDF391VL4QR',
'1513M92JUMEE5',
'K2PXTVWNXHJ7',
'BKA8SBY2TP7M',
'PRGP77XWNZBG',
'W67B42M262V9',
'DZQZFR3UPYQ3',
'B9E824BICP8X',
'RY0E8CCJVD1J',
'6FVSUDBQDEPX',
'GQN0PEN4XUUL',
'7DEVQ0EG76UY',
'H3TLHPUMKLP1',
'KLL0XCPH7XD8',
'1Y0PNICHZMB5',
'Y28X68WL701F'
]
# run_seeds = [
# '7VECZLGSCEYI'
# ]
run_amount = 1
strategy = REQUESTED_STRIKE

if __name__ == "__main__":
    init_log()
    log("Starting up")
    log_new_run_sequence()
    try:
        client = Client()
        game = Game(client, strategy)
        if run_seeds:
            for seed in run_seeds:
                game.start(seed)
                game.run()
                time.sleep(1)
        else:
            for i in range(run_amount):
                game.start(make_random_seed())
                game.run()
                time.sleep(1)

    except Exception as e:
        log("Exception! " + str(e))
        log(traceback.format_exc())
