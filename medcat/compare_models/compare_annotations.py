from typing import List, Tuple, Dict, Set, Callable, Optional, Union, Iterator

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

    def _count(self, entity: Dict):
        cui = entity['cui']
        type_ids = entity['type_ids']
        form = entity['detected_name']
        acc = entity['acc']
        if cui not in self.per_cui_count:
            self.per_cui_count[cui] = 0
            self.per_cui_acc[cui] = 0
            self.per_cui_forms[cui] = set()
        # update total count
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

    def _remove_cui(self, cui: str) -> None:
        # TODO - this could potentially use all fields that start with `per_cui`
        cnt = self.per_cui_count[cui]
        self.total_count -= cnt
        del self.per_cui_count[cui]
        del self.per_cui_acc[cui]
        del self.per_cui_forms[cui]

    def filter_cuis(self, cuis: Union[Set[str], List[str]]) -> None:
        """Filter the results to only include the CUIs specified.

        Args:
            cuis (Union[Set[str], List[str]]): The CUIs to include.
        """
        for cui in list(self.per_cui_count):
            if cui not in cuis:
                self._remove_cui(cui)

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
        # if len1 == len2:
        # same length, but not identical span
        if cui1 == cui2:
            return cls.PARTIAL_OVERLAP_SAME_CONCEPT
        return cls.PARTIAL_OVERLAP_DIFF_CONCEPT


class AnnotationPair(BaseModel):
    one: Optional[Dict]
    two: Optional[Dict]
    comparison_type: AnnotationComparisonType

    @classmethod
    def iterate_over(cls, raw1: dict, raw2: dict) -> Iterator['AnnotationPair']:
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
            yield cls(one=v1, two=v2, comparison_type=comp)


class PerDocAnnotationDifferences(BaseModel):
    nr_of_comparisons: Dict[AnnotationComparisonType, int] = {}
    all_annotation_pairs: List[AnnotationPair] = []

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
        comparisons: Dict[AnnotationComparisonType, int] = {}
        all_annotation_pairs: List[AnnotationPair] = []
        for pair in AnnotationPair.iterate_over(raw1, raw2):
            comp = pair.comparison_type
            if comp not in comparisons:
                comparisons[comp] = 0
            comparisons[comp] += 1
            all_annotation_pairs.append(pair)
        return cls(nr_of_comparisons=comparisons, all_annotation_pairs=all_annotation_pairs)


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

    def iter_ann_pairs(self, docs: Optional[List[str]] = None) -> Iterator[Tuple[str, AnnotationPair]]:
        targets = [(doc, self.per_doc_results[doc]) for doc in self.per_doc_results
                    if docs is None or doc in docs]
        for doc, pdad in targets:
            for pair in pdad.all_annotation_pairs:
                yield doc, pair
