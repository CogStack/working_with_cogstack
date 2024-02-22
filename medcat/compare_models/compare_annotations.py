from typing import List, Tuple, Dict, Set, Callable, Optional

from pydantic import BaseModel
from enum import Enum, auto


class ResultsTally(BaseModel):
    cat_data: dict
    cui2name: Callable[[str], str]
    total_count = 0
    per_cui_count: Dict[str, int] = {}
    per_cui_acc: Dict[str, float] = {}
    per_cui_forms: Dict[str, Set[str]] = {}
    per_type_counts: Dict[str, int] = {}

    # def __init__(self, cat_data: dict, cui2name: Callable[[str], str]) -> None:
        # self.cat_data = cat_data
        # self._cui2name = cui2name
        # self._total_count = 0
        # self._per_cui_count: Dict[str, int] = {}
        # self._per_cui_acc: Dict[str, float] = {}
        # self._per_cui_forms: Dict[str, Set[str]] = {}
        # self._per_type_counts: Dict[str, int] = {}

    def _count(self, entity: Dict):
        # ['pretty_name', 'cui', 'type_ids', 'types', 'source_value', 'detected_name',
        #   'acc', 'context_similarity', 'start', 'end', 'icd10', 'ontologies',
        #   'snomed', 'id', 'meta_anns']
        # print(key, '->', value.keys())
        cui = entity['cui']
        type_ids = entity['type_ids']
        form = entity['detected_name']
        acc = entity['acc']
        # sim = entity['context_similarity']
        # print(cui, type_ids, form, acc)
        # if sim != acc:
        #     print("SIM AND ACC DIFFER", sim, 'vs', acc)
        #     print("ALL:")
        #     print(entity)
        if cui not in self.per_cui_count:
            self.per_cui_count[cui] = 0
            self.per_cui_acc[cui] = 0
            self.per_cui_forms[cui] = set()
        # update total count
        # print("SELF\n", self, '\nKEYS', self.dict().keys())
        self.total_count += 1
        # update accuracy
        prev_cui_cnt = self.per_cui_count[cui]
        self.per_cui_acc[cui] = (self.per_cui_acc[cui] * prev_cui_cnt + acc) / (prev_cui_cnt + 1)
        # update count
        self.per_cui_count[cui] = prev_cui_cnt + 1
        # update forms
        self.per_cui_forms[cui].add(form)
        for type_id in type_ids:
            if type_id not in self.per_type_counts:
                self.per_type_counts[type_id] = 0
            self.per_type_counts[type_id] += 1

    def count(self, entities: Dict):
        raw = entities['entities']
        # print("RAW", raw.keys())
        for _, value in raw.items():
            self._count(value)

    def summary(self) -> Dict:
        summary = {
            "total": self.total_count,
            "per-cui": {cui: {"name": self.cui2name(cui),
                              "count": self.per_cui_count[cui],
                              "acc": self.per_cui_acc[cui],
                              "forms": len(self.per_cui_forms[cui])} for cui in self.per_cui_count}
        }
        return summary

    def get_for_cui(self, cui: str) -> dict:
        if cui not in self.per_cui_count:
            return {"name": "N/A", "count": "N/A", "acc": "N/A", "forms": "N/A"}
        return {"name": self.cui2name(cui),
                "count": self.per_cui_count[cui],
                "acc": self.per_cui_acc[cui],
                "forms": len(self.per_cui_forms[cui])}


# def _check_overlap(d1: dict, d2: dict) -> Tuple[bool, bool]:
#     """Check if two annotated entities are overlapping (or identical).

#     Annotated entities are assumed to have the following keys:
#         ['pretty_name', 'cui', 'type_ids', 'types', 'source_value', 'detected_name',
#         'acc', 'context_similarity', 'start', 'end', 'icd10', 'ontologies',
#         'snomed', 'id', 'meta_anns']
#     Though this method shoudl only be interested in 'start' and 'end'.

#     Args:
#         d1 (dict): The 1st annotated entity. 
#         d2 (dict): The 2nd annotated entity.

#     Returns:
#         Tuple[bool, bool]: Whether there's overlapping, whether the first is before.
#     """
#     # NOTE: Using strictly less than since it would
#     #       not make a lot of sense for the next entity
#     #       to start with the character that the previous
#     #       ended with ('end' should be the end character)
#     start1, end1 = d1['start'], d1['end']
#     start2, end2 = d2['start'], d2['end']
#     return _check_overlap_internal(start1, end1, start2, end2)


def _check_overlap_internal(start1: int, end1: int, start2: int, end2: int) -> bool:
    if end1 < start2:
        # 1st ends before 2nd starts
        return False
    elif end2 < start1:
        # 2nd ends before 1st starts
        return False
    return True


class AnnotationComparisonType(Enum):
    """Options as I see them
    - 1st has annotation, 2nd doesn't
    - 2nd has annotation, 1st doesn't
    - Both have overlapping annotations
      - One larger span, but different concept
      - One larger span and same concept
      - Identical, but different concept
      - Identical and same concept
    """
    FIRST_HAS = auto()
    SECOND_HAS = auto()
    OVERLAPP_1ST_LARGER_DIFF_CONCEPT = auto()
    OVERLAPP_2ND_LARGER_DIFF_CONCEPT = auto()
    OVERLAPP_1ST_LARGER_SAME_CONCEPT = auto()
    OVERLAPP_2ND_LARGER_SAME_CONCEPT = auto()
    PARTIAL_OVERLAP_DIFF_CONCEPT = auto()
    PARTIAL_OVERLAP_SAME_CONCEPT = auto()
    SAME_SPAN_DIFF_CONCEPT = auto()
    IDENTICAL = auto()

    def in_first(self) -> bool:
        return self != self.SECOND_HAS

    def in_second(self) -> bool:
        return self != self.FIRST_HAS

    @classmethod
    def determine(cls, d1: Optional[dict], d2: Optional[dict]) -> 'AnnotationComparisonType':
        """Determine the annotated comparison between two annotations.

        Annotated entities are assumed to have the following keys:
            ['pretty_name', 'cui', 'type_ids', 'types', 'source_value', 'detected_name',
            'acc', 'context_similarity', 'start', 'end', 'icd10', 'ontologies',
            'snomed', 'id', 'meta_anns']

        Args:
            d1 (Optional[dict]): The entity dict for 1st, or None.
            d2 (Optional[dict]): The entity dict for 2nd, or None.

        Returns:
            AnnotationComparisonType: _description_
        """
        if d1 is None:
            return cls.SECOND_HAS
        if d2 is None:
            return cls.FIRST_HAS
        
        start1, end1 = d1['start'], d1['end']
        start2, end2 = d2['start'], d2['end']
        cui1, cui2 = d1['cui'], d2['cui']
        has_overlap = _check_overlap_internal(start1, end1, start2, end2)
        if not has_overlap:
            if start1 < start2:
                return cls.FIRST_HAS
            return cls.SECOND_HAS
        if start1 == start2 and end1 == end2:
            if cui1 == cui2:
                return cls.IDENTICAL
            return cls.SAME_SPAN_DIFF_CONCEPT
        # semi-overlapping
        len1 = end1 - start1
        len2 = end2 - start2
        if len1 > len2:
            # first larger
            if cui1 == cui2:
                return cls.OVERLAPP_1ST_LARGER_SAME_CONCEPT
            return cls.OVERLAPP_1ST_LARGER_DIFF_CONCEPT
        if len2 > len1:
            # second larget
            if cui1 == cui2:
                return cls.OVERLAPP_2ND_LARGER_SAME_CONCEPT
            return cls.OVERLAPP_2ND_LARGER_DIFF_CONCEPT
        # condition shouldn't be necessary
        if len1 == len2:
            # same length, but not identical span
            if cui1 == cui2:
                return cls.PARTIAL_OVERLAP_SAME_CONCEPT
            return cls.PARTIAL_OVERLAP_DIFF_CONCEPT


class PerDocAnnotationDifferences(BaseModel):
    nr_of_comparisons: Dict[AnnotationComparisonType, int] = {}

    @classmethod
    def get(cls, d1: dict, d2: dict) -> 'PerDocAnnotationDifferences':
        # creating copies so I can ditch the entries
        # that I've already dealt with
        raw1 = dict(d1['entities'])
        raw2 = dict(d2['entities'])
        # now we have {'key': VAL}
        # where VAL has keys:
        # ['pretty_name', 'cui', 'type_ids', 'types', 'source_value', 'detected_name',
        #   'acc', 'context_similarity', 'start', 'end', 'icd10', 'ontologies',
        #   'snomed', 'id', 'meta_anns']
        # print("RAW", raw.keys())
        # cursor = 0
        comparisons: Dict[AnnotationComparisonType, int] = {}
        while len(raw1) or len(raw2):
            # first key in either dict of entities
            if raw1:
                k1 = sorted(raw1.keys())[0]
                v1 = raw1[k1]
            else:
                k1 = None
                v1 = None
            if raw2:
                k2 = sorted(raw2.keys())[0]
                v2 = raw2[k2]
            else:
                k2 = None
                v2 = None
            #     k1 = sorted(raw1.keys())[0]
            #     k2 = sorted(raw2.keys())[0]
            # corresponding value in either dict of entities
            comp = AnnotationComparisonType.determine(v1, v2)
            rem_1st = comp.in_first()
            rem_2nd = comp.in_second()
            if rem_1st:
                del raw1[k1]
            if rem_2nd:
                del raw2[k2]
            if not rem_1st and not rem_2nd:
                # can't move forward, would be stuck in infinte loop
                raise ValueError("Unknown comparison that leaves us"
                                 "in an infinite loop. Happened while"
                                 f"comparing '{k1}' ({v1})"
                                 f"to '{k2}' ({v2})")
            if comp not in comparisons:
                comparisons[comp] = 0
            comparisons[comp] += 1
        return cls(nr_of_comparisons=comparisons)


class PerAnnotationDifferences(BaseModel):
    per_doc_results: Dict[str, PerDocAnnotationDifferences] = {}
    totals: Optional[Dict[AnnotationComparisonType, int]] = None

    def look_at_doc(self, d1: dict, d2: dict, doc_id: str):
        self.per_doc_results[doc_id] = PerDocAnnotationDifferences.get(d1, d2)
    
    def finalise(self):
        totals: Dict[AnnotationComparisonType, int] = {}
        for value in self.per_doc_results.values():
            for k, v in value.nr_of_comparisons.items():
                if k not in totals:
                    totals[k] = 0
                totals[k] += v
        self.totals = totals
