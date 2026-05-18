from rs.common.comparators.common_general_comparator import CommonGeneralComparator, default_comparisons
from rs.common.comparators.core.comparisons import least_incoming_damage_over_1


comparisons = default_comparisons.copy()
comparisons.remove(least_incoming_damage_over_1)


class LagavulinComparator(CommonGeneralComparator):
    def __init__(self):
        super().__init__(comparisons)
