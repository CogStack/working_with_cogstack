from typing import List, Tuple, Dict, Set, Callable, Optional, Union, Iterator, Iterable

from pydantic import BaseModel
from enum import Enum, auto
from copy import deepcopy

import pandas as pd
import json


class ResultsTally(BaseModel):
    pt2ch: Optional[Dict[str, Set[str]]]
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

    def count(self, raw: Dict):
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

    def _get_for_cui_recusive(self, cui: str, include_children: int = 0
                              ) -> Tuple[List[str], List[int], List[float], Set[str]]:
        all_names = [self.cui2name(cui), ]
        all_counts = [self.per_cui_count.get(cui, 0), ]
        all_accuracies = [self.per_cui_acc.get(cui, 0), ]
        all_forms = self.per_cui_forms.get(cui, set())
        if include_children == 0 or not self.pt2ch:
            return all_names, all_counts, all_accuracies, all_forms
        for child in self.pt2ch.get(cui, []):
            child_names, child_counts, child_accs, child_forms = self._get_for_cui_recusive(child, include_children-1)
            all_names.extend(child_names)
            all_counts.extend(child_counts)
            all_accuracies.extend(child_accs)
            all_forms.update(child_forms)
        return all_names, all_counts, all_accuracies, all_forms


    def get_for_cui(self, cui: str, include_children: int = 0) -> dict:
        if cui not in self.per_cui_count:
            return {"name": "N/A", "count": "N/A", "acc": "N/A", "forms": "N/A"}
        all_names, all_counts, all_accuracies, all_forms = self._get_for_cui_recusive(cui, include_children)
        names = f"{all_names[0]}"
        nr_of_names = len(all_names)
        if 4 > nr_of_names > 1:
            names += f" ({', '.join(all_names[1:])})"
        elif nr_of_names > 1:
            names += f" (and {len(all_names) - 1} children)"
        counts = sum(all_counts)
        accuracies = sum(all_accuracies)
        return {"name": names,
                "count": counts,
                "acc": accuracies,
                "forms": len(all_forms)}


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
    # NOTE: in the following cases we consider the annotated CUI
    #       so if the first annotates C101 and that does not exist
    #       in the second, then SAME_SPAN_CONCEPT_NOT_IN_2ND.
    #       However, when determininig this, we will do this after
    #       determining parents/grandparents to that these will be
    #       given priority (i.e if the 1st annotates a child that
    #       does not exist in the 2nd, but the parent does exist
    #       and is specified, then the parent relationship will
    #       be determined instead of the missing concept one)
    SAME_SPAN_CONCEPT_NOT_IN_1ST = auto()
    SAME_SPAN_CONCEPT_NOT_IN_2ND = auto()
    SAME_SPAN_DIFF_CONCEPT = auto()
    IDENTICAL = auto()
    SAME_PARENT = auto()
    SAME_GRANDPARENT = auto()

    def in_first(self) -> bool:
        return self != AnnotationComparisonType.SECOND_HAS

    def in_second(self) -> bool:
        return self != AnnotationComparisonType.FIRST_HAS

    @classmethod
    def _determine_parent(cls, cui1: str, cui2: str,
                          pt2ch: Dict) -> Optional['AnnotationComparisonType']:
        for ch in pt2ch.get(cui1, []):
            if ch == cui2:
                return cls.SAME_PARENT
        return None

    @classmethod
    def _determine_grandparent(cls, cui1: str, cui2: str,
                               pt2ch1: Optional[Dict], pt2ch2: Optional[Dict]
                               ) -> Optional['AnnotationComparisonType']:
        if pt2ch1:
            for ch in pt2ch1.get(cui1, []):
                parent = cls._determine_parent(ch, cui2, pt2ch1)
                if parent == cls.SAME_PARENT:
                    return cls.SAME_GRANDPARENT
        if pt2ch2:
            for ch in pt2ch2.get(cui2, []):
                parent = cls._determine_parent(ch, cui1, pt2ch2)
                if parent == cls.SAME_PARENT:
                    return cls.SAME_GRANDPARENT
        return None

    @classmethod
    def _determine_same_span(cls, cui1: str, cui2: str,
                           pt2ch1: Optional[Dict], pt2ch2: Optional[Dict]
                           ) -> 'AnnotationComparisonType':
        if pt2ch1:
            # check for children of cui1 in pt2ch1
            parent = cls._determine_parent(cui1, cui2, pt2ch1)
            if parent:
                return parent
        if pt2ch2:
            # check for children of cui2 in pt2ch2
            parent = cls._determine_parent(cui2, cui1, pt2ch2)
            if parent:
                return parent
        grandparents = cls._determine_grandparent(cui1, cui2, pt2ch1, pt2ch2)
        if grandparents:
            return grandparents
        return cls.SAME_SPAN_DIFF_CONCEPT

    @classmethod
    def _determine_missing_concept(cls, cui1: str, cui2: str,
                                   model1_cuis: Set[str],
                                   model2_cuis: Set[str]
                                   ) -> 'AnnotationComparisonType':
        if cui1 not in model2_cuis:
            return cls.SAME_SPAN_CONCEPT_NOT_IN_2ND
        elif cui2 not in model1_cuis:
            return cls.SAME_SPAN_CONCEPT_NOT_IN_1ST
        return cls.SAME_SPAN_DIFF_CONCEPT

    @classmethod
    def determine(cls, d1: Optional[dict], d2: Optional[dict],
                  pt2ch1: Optional[dict], pt2ch2: Optional[dict],
                  model1_cuis: Set[str], model2_cuis: Set[str],
                  ) -> 'AnnotationComparisonType':
        """Determine the annotated comparison between two annotations.

        Annotated entities are assumed to have the following keys:
            ['pretty_name', 'cui', 'type_ids', 'types', 'source_value', 'detected_name',
            'acc', 'context_similarity', 'start', 'end', 'icd10', 'ontologies',
            'snomed', 'id', 'meta_anns']

        Args:
            d1 (Optional[dict]): The entity dict for 1st, or None.
            d2 (Optional[dict]): The entity dict for 2nd, or None.
            pt2ch1 (Optional[dict]): The parent to child mapping for the 1st.
            pt2ch2 (Optional[dict]): The parent to child mapping for the 2nd.
            model1_cuis (Set[str]): All CUIs in 1st model.
            model2_cuis (Set[str]): All CUIs in 2nd model.

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
            same_span = cls._determine_same_span(cui1, cui2, pt2ch1, pt2ch2)
            if same_span != cls.SAME_SPAN_DIFF_CONCEPT:
                return same_span
            # determine concepts missing in one of the models
            return cls._determine_missing_concept(cui1, cui2, model1_cuis, model2_cuis)
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
    def iterate_over(cls, raw1: dict, raw2: dict,
                     pt2ch1: Optional[dict], pt2ch2: Optional[dict],
                     model1_cuis: Set[str], model2_cuis: Set[str],
                     ) -> Iterator['AnnotationPair']:
        # keep originals
        _raw1 = raw1
        _raw2 = raw2
        raw1 = deepcopy(raw1)
        raw2 = deepcopy(raw2)
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
            comp = AnnotationComparisonType.determine(v1, v2, pt2ch1, pt2ch2,
                                                      model1_cuis, model2_cuis)
            rem_1st = comp.in_first()
            rem_2nd = comp.in_second()
            if rem_1st:
                del raw1[k1]
            else:
                # now overlap with 1st
                v1 = None
            if rem_2nd:
                del raw2[k2]
            else:
                # no overlap with 2nd
                v2 = None
            if not rem_1st and not rem_2nd:
                # can't move forward, would be stuck in infinte loop
                raise ValueError("Unknown comparison that leaves us"
                                 "in an infinite loop. Happened while"
                                 f"comparing '{k1}' ({v1})"
                                 f"to '{k2}' ({v2})")
            # using parts from the original dict instead of
            # the copied one for better memory management
            # (since the original raw is also being kept in PerDocAnnotationDifferences)
            if k1 is not None and v1 is not None:
                v1 = _raw1[k1]
            if k2 is not None and v2 is not None:
                v2 = _raw2[k2]
            yield cls(one=v1, two=v2, comparison_type=comp)


class PerDocAnnotationDifferences(BaseModel):
    nr_of_comparisons: Dict[AnnotationComparisonType, int] = {}
    all_annotation_pairs: List[AnnotationPair] = []
    raw_text: str
    raw1: Dict
    raw2: Dict

    @classmethod
    def get(cls, raw_text: str, d1: dict, d2: dict,
            pt2ch1: Optional[dict], pt2ch2: Optional[dict],
            model1_cuis: Set[str], model2_cuis: Set[str],
            keep_raw: bool = True,
            ) -> 'PerDocAnnotationDifferences':
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
        for pair in AnnotationPair.iterate_over(raw1, raw2, pt2ch1, pt2ch2,
                                                model1_cuis, model2_cuis):
            comp = pair.comparison_type
            if comp not in comparisons:
                comparisons[comp] = 0
            comparisons[comp] += 1
            all_annotation_pairs.append(pair)
        if not keep_raw:
            raw_text = ''
        return cls(nr_of_comparisons=comparisons, all_annotation_pairs=all_annotation_pairs,
                   raw1=raw1, raw2=raw2, raw_text=raw_text)


class PerAnnotationDifferences(BaseModel):
    model1_cuis: Set[str]
    model2_cuis: Set[str]
    pt2ch1: Optional[Dict]
    pt2ch2: Optional[Dict]
    per_doc_results: Dict[str, PerDocAnnotationDifferences] = {}
    totals: Optional[Dict[AnnotationComparisonType, int]] = None
    keep_raw: bool = True

    def look_at_doc(self, d1: dict, d2: dict, doc_id: str, raw_text: str):
        self.per_doc_results[doc_id] = PerDocAnnotationDifferences.get(raw_text, d1, d2,
                                                                       self.pt2ch1, self.pt2ch2,
                                                                       self.model1_cuis,
                                                                       self.model2_cuis,
                                                                       self.keep_raw)

    def finalise(self):
        totals: Dict[AnnotationComparisonType, int] = {}
        for value in self.per_doc_results.values():
            for k, v in value.nr_of_comparisons.items():
                if k not in totals:
                    totals[k] = 0
                totals[k] += v
        self.totals = totals

    def iter_ann_pairs(self,
                       docs: Optional[Iterable[str]] = None,
                       omit_identical: bool = True) -> Iterator[Tuple[str, AnnotationPair]]:
        """ITerate over annotation pairs, potentially only for a specific subset of documents.

        If no document IDs are specified, all documents are used.
        Otherwise, only the documents specified are used.

        If the list of documents contains document IDs that have not been looked at
        they will be ignored.

        Args:
            docs (Optional[Iterable[str]], optional): The document IDs to use. Defaults to None.
            omit_identical (bool, optional): Whether to omit identical annotations. Defaults to True.

        Yields:
            Iterator[Tuple[str, AnnotationPair]]: An iteration of document name and annotation pair.
        """
        targets = [(doc, self.per_doc_results[doc]) for doc in self.per_doc_results
                    if docs is None or doc in docs]
        for doc, pdad in targets:
            for pair in pdad.all_annotation_pairs:
                if omit_identical and pair.comparison_type == AnnotationComparisonType.IDENTICAL:
                    continue
                yield doc, pair

    def iter_document_annotations(self, docs: Optional[Iterable[str]] = None,
                                  omit_identical: bool = True
                                  ) -> Iterator[Tuple[str, str, Optional[Dict], Optional[Dict]]]:
        """Iterate over document annotations (including raw text).

        Args:
            docs (Optional[Iterable[str]], optional): The documents to iterate over (or all). Defaults to None.
            omit_identical (bool, optional): Whether to omit identical annotations. Defaults to True.

        Yields:
            Iterator[Tuple[str, str, Dict, Dict]]:
                The document ID, the raw text, the annotations for model 1, the annotaitons for model 2
        """
        targets = [(doc, self.per_doc_results[doc]) for doc in self.per_doc_results
                    if docs is None or doc in docs]
        for doc, pdad in targets:
            for pair in pdad.all_annotation_pairs:
                if omit_identical and pair.comparison_type == AnnotationComparisonType.IDENTICAL:
                    continue
                yield doc, pdad.raw_text, pair.one, pair.two

    def _get_text(self, raw_text: str, span_char_limit: Optional[int],
                  ann1: Optional[dict], ann2: Optional[dict],
                 ) -> str:
        if span_char_limit is None:
            text = raw_text
        else:
            if ann1:
                start1, end1 = ann1['start'], ann1['end']
            else:
                start1, end1 = -1, -1
            if ann2:
                start2, end2 = ann2['start'], ann2['end']
                if not ann1:
                    start1, end1 = start2, end2
            else:
                start2, end2 = start1, end1
            min_char_nr = max(min(start1, start2) - span_char_limit, 0)
            max_char_nr = min(max(end1, end2) + span_char_limit, len(raw_text) + 1)
            text = raw_text[min_char_nr: max_char_nr]
            # update start and end chars so that they match the new text
            if ann1:
                ann1['start'], ann1['end'] = start1 - min_char_nr, end1 - min_char_nr
                ann1['start-raw'], ann1['end-raw'] = start1, end1
            if ann2:
                ann2['start'], ann2['end'] = start2 - min_char_nr, end2 - min_char_nr
                ann2['start-raw'], ann2['end-raw'] = start2, end2
        return text

    def _to_raw(self, docs: Set[str],
                span_char_limit: Optional[int] = 200
                ) -> List[Tuple[str, str, str, str]]:
        data: List[Tuple[str, str, str, str]] = []
        for doc_id, raw_text, ann1, ann2 in self.iter_document_annotations(docs, omit_identical=False):
            text = self._get_text(raw_text, span_char_limit=span_char_limit, ann1=ann1, ann2=ann2)
            # convert annotation dicts to json
            data.append((doc_id, text, json.dumps(ann1), json.dumps(ann2)))
        return data

    def to_csv(self, csv_file: str,
               docs: Optional[Iterable[str]] = None,
               span_char_limit: Optional[int] = 200) -> None:
        """Generates a CSV file based on the results.

        Each annotation pair creates a line in the CSV.

        The CSV file has the following columns:
        doc_id: the ID of the document for this annotation
        text: the text (`span_char_limit` both ways, or the entire text if None)
        ann1: the annotation for model 1
        ann2: the annotation for model 2

        NOTE: One of the annotations in each line may be None (NaN).
              This happens when one of the model did not annotate that span.

        Args:
            csv_file (str): The csv file to write to.
            docs (Optional[Iterable[str]], optional): The documents to include (or all). Defaults to None.
            span_char_limit (Optional[int], optional): The char span limit either side (or all if None). Defaults to 200.
        """
        if docs is None:
            docs = set(self.per_doc_results)
        else:
            docs = set(docs)
        data = self._to_raw(docs, span_char_limit=span_char_limit)
        df = pd.DataFrame(data, columns=["doc_id", "text", "ann1", "ann2"])
        df.to_csv(csv_file, index=False)
