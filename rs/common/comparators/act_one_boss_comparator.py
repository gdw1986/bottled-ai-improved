from typing import Optional

from rs.common.comparators.common_general_comparator import CommonGeneralComparator, default_comparisons
from rs.common.comparators.core.assessment import ComparatorAssessment as CA
from rs.common.comparators.core.comparisons import least_incoming_damage_over_1


comparisons = default_comparisons.copy()
incoming_damage_index = comparisons.index(least_incoming_damage_over_1)


def least_incoming_damage_over_12(best: CA, challenger: CA) -> Optional[bool]:
    return None if max(12, best.incoming_damage()) == max(12, challenger.incoming_damage()) \
        else challenger.incoming_damage() < best.incoming_damage()


comparisons[incoming_damage_index] = least_incoming_damage_over_12


class ActOneBossComparator(CommonGeneralComparator):
    def __init__(self):
        super().__init__(comparisons)
