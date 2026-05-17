from enum import Enum


class Command(Enum):
    CANCEL = "cancel"
    CHOOSE = "choose"
    CONFIRM = "confirm"
    END = "end"
    KEY = "key"
    LEAVE = "leave"
    PLAY = "play"
    POTION = "potion"
    PROCEED = "proceed"
    RETURN = "return"
    SKIP = "skip"
    WAIT = "wait"
