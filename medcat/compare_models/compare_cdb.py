from typing import Dict, Set, Tuple

from medcat.cdb import CDB

import tqdm
from itertools import chain

from pydantic import BaseModel


class DictCompareKeys(BaseModel):
    """This is based on the keys."""
    total1: int
    """The total number of keys in 1st dict"""
    total2: int
    """The total number of keys in 2nd dict"""
    joint: int
    """The total number of keys (intersection)"""
    not_in_1: int
    """The number of keys in 2nd but not in 1st dict"""
    not_in_2: int
    """The number of keys in 1st but not in 2nd dict"""

    @classmethod
    def get(cls, d1: dict, d2: dict) -> "DictCompareKeys":
        # helpers
        all1 = set(d1)
        all2 = set(d2)
        # total keys
        total1 = len(all1)
        total2 = len(all2)
        # non-common keys
        joint = len(all1 & all2)
        all_combined = len(all1 | all2)
        not_in_1 = all_combined - total1
        not_in_2 = all_combined - total2
        return cls(total1=total1, total2=total2, joint=joint,
                   not_in_1=not_in_1, not_in_2=not_in_2)


class DictCompareValues(BaseModel):
    """This is based on the notion of the values being sets.
    
    With respect to the difference between `not_in_1` and `unique_in_2`:
    - If we have {"1": {"a", "b"}} and {"2": {"a", "b"}}
    - The values are identical overall (`unique_in_1==unique_in_2==0`)
    - However, the values are under different keys
    - So `not_in_1==not_in_2==2` (since this is per key)
    """
    total1: int
    """The total number of values in 1st dict"""
    total2: int
    """The total number of values in 2nd dict"""
    not_in_1: int
    """The number of values in 2nd, but not in 1st (per key)"""
    not_in_2: int
    """The number of values in 1st, but not in 2nd (per key)"""
    joint: int
    """Total number of values in both 1st and 2nd dict (overall)"""
    unique_in_1: int
    """The number of unique values in 1nd (overall)"""
    unique_in_2: int
    """The number of unique values in 2nd (overall)"""

    @classmethod
    def get(cls, d1: dict, d2: dict, progress: bool = True) -> "DictCompareValues":
        # helpers
        all_keys = set(d1) | set(d2)
        vals_in_1 = set(chain.from_iterable(d1.values()))
        vals_in_2 = set(chain.from_iterable(d2.values()))
        # total names
        total1 = sum(len(v) for v in d1.values())
        total2 = sum(len(v) for v in d2.values())
        # names ...
        not_in_1 = 0
        not_in_2 = 0
        for key in tqdm.tqdm(all_keys, desc="keys", disable=not progress):
            n1 = d1.get(key, set())
            n2 = d2.get(key, set())
            all_vals4key = len(n1 | n2)
            not_in_1 += all_vals4key - len(n1)
            not_in_2 += all_vals4key - len(n2)
        # names in common
        joint = len(vals_in_1 & vals_in_2)
        # names unique to one of the two
        vals_in_one_but_not_both = vals_in_1 ^ vals_in_2
        unique_in_1 = len(vals_in_one_but_not_both & vals_in_1)
        unique_in_2 = len(vals_in_one_but_not_both & vals_in_2)
        return cls(total1=total1, total2=total2, not_in_1=not_in_1,
                   not_in_2=not_in_2, joint=joint,
                   unique_in_1=unique_in_1, unique_in_2=unique_in_2)


class DictComparisonResults(BaseModel):
    keys: DictCompareKeys
    values: DictCompareValues

    @classmethod
    def get(cls, d1: dict, d2: dict, progress: bool = True) -> "DictComparisonResults":
        return cls(keys=DictCompareKeys.get(d1, d2),
                   values=DictCompareValues.get(d1, d2, progress=progress))


class CDBCompareResults(BaseModel):
    names: DictComparisonResults
    snames: DictComparisonResults


def compare(cdb1: CDB,
            cdb2: CDB,
            show_progress: bool = True) -> CDBCompareResults:
    """_summary_

    Args:
        cdb1 (CDB): _description_
        cdb2 (CDB): _description_
        show_progress (bool, optional): _description_. Defaults to True.

    Returns:
        CDBCompareResults: _description_
    """
    reg = DictComparisonResults.get(cdb1.cui2names, cdb2.cui2names, progress=show_progress)
    snames = DictComparisonResults.get(cdb1.cui2snames, cdb2.cui2snames, progress=show_progress)
    return CDBCompareResults(names=reg, snames=snames)
