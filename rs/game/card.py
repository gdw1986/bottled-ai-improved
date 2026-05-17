from enum import Enum
import re


_BASE_CARD_IDS = {
    "strike_r": "strike",
    "strike_g": "strike",
    "strike_b": "strike",
    "strike_p": "strike",
    "strike": "strike",
    "defend_r": "defend",
    "defend_g": "defend",
    "defend_b": "defend",
    "defend_p": "defend",
    "defend": "defend",
}

_SPECIAL_CARD_ID_NAMES = {
    "handofgreed": "handofgreed",
    "talktothehand": "talk to the hand",
    "waveofthehand": "wave of the hand",
}


def card_id_to_name(card_id: str) -> str:
    """Convert Communication Mod card ids to strategy/config card names."""
    if not card_id:
        return ""

    lower_id = card_id.lower()
    if lower_id in _BASE_CARD_IDS:
        return _BASE_CARD_IDS[lower_id]
    if lower_id in _SPECIAL_CARD_ID_NAMES:
        return _SPECIAL_CARD_ID_NAMES[lower_id]

    stripped_id = re.sub(r"_[rRgGbBpP]$", "", card_id)
    stripped_id = stripped_id.replace("_", " ")
    stripped_id = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", stripped_id)
    return stripped_id.lower()


def compact_card_name(card_name: str) -> str:
    """Normalize card names for loose comparisons across ids/display names."""
    return re.sub(r"[\s_\-+]+", "", card_name.lower())


class Card:
    def __init__(self, json_map):
        self.exhausts: bool = json_map["exhausts"]
        self.is_playable: bool = False if "is_playable" not in json_map else json_map["is_playable"]
        self.cost: int = json_map["cost"]
        self.name: str = json_map["name"]
        self.id: str = json_map["id"]
        self.type: CardType = CardType(json_map["type"])
        self.ethereal: bool = json_map["ethereal"]
        self.uuid: str = json_map["uuid"]
        self.upgrades: int = json_map["upgrades"]
        self.rarity: CardRarity = CardRarity(json_map["rarity"])
        self.has_target: bool = json_map["has_target"]


class CardType(Enum):
    SKILL = "SKILL"
    ATTACK = "ATTACK"
    POWER = "POWER"
    STATUS = "STATUS"
    CURSE = "CURSE"
    FAKE = "FAKE"
    OTHER = "OTHER"


class CardRarity(Enum):
    BASIC = "BASIC"
    COMMON = "COMMON"
    UNCOMMON = "UNCOMMON"
    RARE = "RARE"
    SPECIAL = "SPECIAL"
    CURSE = "CURSE"
