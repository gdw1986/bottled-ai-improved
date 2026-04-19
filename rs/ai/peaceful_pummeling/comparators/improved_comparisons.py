from typing import Optional

from rs.calculator.enums.power_id import PowerId
from rs.calculator.interfaces.monster_interface import MonsterInterface
from rs.common.comparators.core.assessment import ComparatorAssessment as CA


# ----------------------------------------------------------------------
# 1. 敌人意图感知
# ----------------------------------------------------------------------

def incoming_attack_damage(monster: MonsterInterface) -> int:
    """计算敌人本回合的实际攻击伤害（含 strength 加成）。"""
    if not monster.hits or monster.damage == -1:
        return 0
    base = monster.damage
    strength = monster.powers.get(PowerId.STRENGTH, 0)
    weak_mod = 0.75 if monster.powers.get(PowerId.WEAKENED) else 1.0
    return max(int((base + strength) * weak_mod), 0)


def calc_net_damage_to_player(state) -> int:
    """玩家本回合结束时会受到的总伤害（攻击伤害 - 格挡）。"""
    total_incoming = 0
    for m in state.monsters:
        dmg = incoming_attack_damage(m)
        if dmg > 0:
            total_incoming += dmg
    player_block = state.player.block
    return max(total_incoming - player_block, 0)


def calc_raw_incoming_damage(state) -> int:
    """不考虑格挡的原始总伤害。"""
    return sum(incoming_attack_damage(m) for m in state.monsters)


def estimate_turns_to_kill_monsters(state) -> int:
    """粗估还要几回合才能清光怪物（假设每回合造成 20 点有效伤害）。"""
    total_hp = sum(
        m.current_hp
        for m in state.monsters
        if m.current_hp > 0 and not m.is_gone
    )
    return max(1, total_hp // 20)


def prefers_block_over_setup(best: CA, challenger: CA) -> Optional[bool]:
    """
    当下一回合会受到 >15 伤害时，优先选能格挡最多的路径。
    这个比较放在 most_optimal_winning_battle 之后，
    当双方都赢不了 / 都差不多时，倾向防守。
    """
    best_block = best.player_block()
    chal_block = challenger.player_block()
    best_raw = best_block + best.raw_incoming_damage()
    chal_raw = chal_block + challenger.raw_incoming_damage()

    # raw_incoming_damage > 15 说明有实质威胁
    if chal_raw > 15 and best_raw > 15:
        return chal_block > best_block
    return None  # 继续下一个比较


def prefers_setup_over_damage(best: CA, challenger: CA) -> Optional[bool]:
    """
    当本回合结束没有致命威胁时（剩余 HP > incoming_damage），
    优先选有更好姿态/能量 setup 的路径。
    """
    best_survivable = best.player_current_hp() > best.raw_incoming_damage()
    chal_survivable = challenger.player_current_hp() > challenger.raw_incoming_damage()

    if best_survivable and chal_survivable:
        # 双方都能活，倾向于更有 setup 价值的
        best_setup = best.stance_setup_value()
        chal_setup = challenger.stance_setup_value()
        if best_setup != chal_setup:
            return chal_setup > best_setup
    return None


# ----------------------------------------------------------------------
# 2. 姿态价值评估（Watcher 专用）
# ----------------------------------------------------------------------

def divine_setup_value(state) -> int:
    """
    评估进入神性姿态（Divinity）的准备程度。
    分值 = Mantra 已有层数 + 手牌中可用 Mantra 产出卡数量 * 3
    """
    from rs.calculator.interfaces.memory_items import MemoryItem, StanceType

    mantra = state.memory_general.get(MemoryItem.MANTRA_INTERNAL, 0)
    cards_that_add_mantra = [
        'inner_peace',
        'deceive_reality',
        'carve_reality',
        'prayer',
        'wish',          # 药水/奖励可得
        'devotion',      # power 持续产 Mantra
    ]
    add_count = sum(
        1 for c in state.hand
        if any(key in c.id.value for key in cards_that_add_mantra)
    )
    return mantra + add_count * 3


def calm_setup_value(state) -> int:
    """
    评估 Calm 姿态的价值。
    如果手牌中有 wrath_exit 卡（能安全退出 Wrath 的牌），Calm 更有价值。
    """
    from rs.calculator.enums.card_id import CardId

    wrath_exits = [
        CardId.EMPTY_BODY,
        CardId.EMPTY_FIST,
        CardId.EMPTY_MIND,
        CardId.FEAR_NO_EVIL,
        CardId.INNER_PEACE,
        CardId.TRANQUILITY,
        CardId.VIGILANCE,
    ]
    exit_count = sum(1 for c in state.hand if c.id in wrath_exits)
    return exit_count


def prefers_divine_setup(best: CA, challenger: CA) -> Optional[bool]:
    """
    双方都存活且有 setup 价值时，优先选更接近 Divinity 的路径。
    """
    if best.battle_won() or challenger.battle_won():
        return None
    best_val = best.divine_setup_value()
    chal_val = challenger.divine_setup_value()
    return None if best_val == chal_val else chal_val > best_val


def prefers_calm_for_wrath_exit(best: CA, challenger: CA) -> Optional[bool]:
    """
    如果有 wrath exit 卡在手里，Calm 姿态更安全（比留在 Wrath 好）。
    """
    best_val = best.calm_setup_value()
    chal_val = challenger.calm_setup_value()
    return None if best_val == chal_val else chal_val > best_val


# ----------------------------------------------------------------------
# 3. 跨回合生存评估
# ----------------------------------------------------------------------

def prefers_more_block_for_next_turn(best: CA, challenger: CA) -> Optional[bool]:
    """
    优先选下一回合剩余格挡更多的路径。
    这是对原有 most_block_saved_for_next_turn 的补充，
    额外考虑本回合结束后还未消耗的格挡。
    """
    best_total = best.block_for_next_turn() + best.player_block()
    chal_total = challenger.block_for_next_turn() + challenger.player_block()
    return None if best_total == chal_total else chal_total > best_total


def penalizes_low_hp_setup(best: CA, challenger: CA) -> Optional[bool]:
    """
    当 HP 较低时（<30%），setup 的价值降低，优先保命。
    """
    best_hp_pct = best.player_current_hp() / best.player_max_hp()
    chal_hp_pct = challenger.player_current_hp() / challenger.player_max_hp()

    if best_hp_pct < 0.3 or chal_hp_pct < 0.3:
        # 低血量时更看重存活，倾向于受伤害更少的
        best_dmg = best.incoming_damage()
        chal_dmg = challenger.incoming_damage()
        return None if best_dmg == chal_dmg else chal_dmg < best_dmg
    return None


# ----------------------------------------------------------------------
# 4. 实用优先级排序辅助
# ----------------------------------------------------------------------

def best_watcher_next_turn_energy(best: CA, challenger: CA) -> Optional[bool]:
    """
    Watcher 特色：剩余能量越多，下回合越灵活。
    """
    best_e = best.state.player.energy
    chal_e = challenger.state.player.energy
    return None if best_e == chal_e else chal_e > best_e


def prefers_wrath_for_kill(best: CA, challenger: CA) -> Optional[bool]:
    """
    在 Wrath 姿态下有攻击牌且能击杀/大削怪物时，Wrath 优先。
    只在双方都没赢的情况下比较。
    """
    if best.battle_won() or challenger.battle_won():
        return None
    best_wrath = best.state.memory_general.get('STANCE', 0)
    chal_wrath = challenger.state.memory_general.get('STANCE', 0)
    # Wrath 在这里是数字枚举值，简单判断
    return None
