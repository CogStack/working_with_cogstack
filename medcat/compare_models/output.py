from typing import Any, Optional, Callable, Tuple, Dict

from enum import Enum

from compare_cdb import compare as CDBCompareResults
from compare_annotations import ResultsTally, PerAnnotationDifferences


def _get_other_key(key: str) -> str:
    """Get the corresponding paired key.

    This expects the last character of the string to be a number.
    It is designed to work for 1 and 2; and will the former into
    the latter and vice versa.

    Args:
        key (str): The input key.

    Returns:
        str: The output paired key.
    """

    # "1" -> False or "2" -> True
    helper = bool(int(key[-1:]) - 1)
    other_nr = "1" if helper else "2"
    return f"{key[:-1]}{other_nr}"

    
def _has_paired_key(d: dict, key: str) -> bool:
    """Checks whether the key has a paired key in the dict.

    Args:
        d (dict): The dict to look in.
        key (str): The key in question.

    Returns:
        bool: Whether or not the paired key exists in the dict.
    """
    if not isinstance(key, str):
        return False
    if not key.endswith("1") and not key.endswith("2"):
        return False
    other_key = _get_other_key(key)
    return other_key in d


def default_formatter(path: str, v1: str, v2: Optional[str] = None) -> str:
    return f"{path:40s}\t{str(v1):40s}\t{str(v2 or ''):40s}"


def show_dict_deep(d: dict, path: str = '',
                   output_formatter: Callable[[str, str, Optional[str]], str] = default_formatter):
    """Shows the values key-value pairs of a dict depthwise.

    It will show each specific value in the (potentially) nested dict.
    I.e for top level dict the path will be its key, but for
        dicts within there, the paths will be the keys to get there
        joined by decimals. E.g root.key1.key2.

    Args:
        d (dict): The input (potentially nested) dict.
        path (str, optional): The current path. Defaults to ''.
        output_formatter (Callable[[str, str, Optional[str]], str], optional): The output formatter.
            Defaults to default_formatter.
    """
    paired_keys = set(key for key in d if _has_paired_key(d, key))
    key_pairs = [(key1, _get_other_key(key1)) for key1 in paired_keys if key1 < _get_other_key(key1)]
    for key, value in d.items():
        if key in paired_keys:
            continue
        if path:
            total_path = f"{path}.{key}"
        elif isinstance(key, Enum):
            total_path = key.name
        else:
            total_path = key
        if isinstance(value, dict):
            show_dict_deep(value, path=total_path)
            continue
        print(output_formatter(total_path, value, None))
    # for paired keys
    for key1, key2 in key_pairs:
        common_key = key1[:-1]
        total_path = f"{path}.{common_key}" if path else key
        print(output_formatter(total_path, d[key1], d[key2]))


def compare_dicts(d1: dict, d2: dict,
                  output_formatter: Callable[[str, str, Optional[str]], str] = default_formatter,
                  ignore_callables: bool = True,
                  custom_printval_gens: Optional[Dict[str, Callable[[Any], str]]] = None):
    """Compares two dicts with identical schemas to oneanother.

    This will attempt to unravel dict values in the following way
    - The number of keys will be used
    - For the values
      - If the dict maps to integers, the total value is counted (e.g train counts)
      - If the dict maps to floats, the average value is measured (e.g accuracy)
      - If the dict maps to sets the mean number of elements is measued (e.g per-cui forms)

    Args:
        d1 (dict): The first dict.
        d2 (dict): The second dict.
        output_formatter (Callable[[str, str, Optional[str]], str], optional): The output formatter.
            Defaults to default_formatter.
        ignore_callables (bool): Whether to ignore callable values. Defaults to True.
        custom_printval_gens (Optional[Dict[str, Callable[[Any], str]]]):
            The keys are ones that have a custom print value generator.
            And the values are the corresponding custom print value generators.
            Defaults to None (or an empty dict).
    raises:
        AssertionError: If the keys of the two dicts differ; or if value types mismatch.
    """
    assert d1.keys() == d2.keys()
    for key in d1:
        v1 = d1[key]
        v2 = d2[key]
        if custom_printval_gens and key in custom_printval_gens:
            printval1 = custom_printval_gens[key](v1)
            printval2 = custom_printval_gens[key](v2)
        elif callable(v1):
            if ignore_callables:
                continue
            printval1 = str(v1)
            printval2 = str(v2)
        elif isinstance(v1, dict):
            assert isinstance(v2, dict)
            # just number of items
            nr_of_keys1 = len(v1)
            nr_of_keys2 = len(v2)
            k0 = list(v1)[0]
            v0 = v1[k0]
            if isinstance(v0, int):
                total1 = sum(v1.values())
                total2 = sum(v2.values())
                printval1 = f"{nr_of_keys1} keys (total {total1} in value)"
                printval2 = f"{nr_of_keys2} keys (total {total2} in value)"
            elif isinstance(v0, float):
                mean1 = sum(v1.values())/nr_of_keys1
                mean2 = sum(v2.values())/nr_of_keys2
                printval1 = f"{nr_of_keys1} keys (mean {mean1} in value)"
                printval2 = f"{nr_of_keys2} keys (mean {mean2} in value)"
            elif isinstance(v0, set):
                total1 = sum(len(v) for v in v1.items())
                total2 = sum(len(v) for v in v2.items())
                printval1 = f"{nr_of_keys1} keys (mean {total1/nr_of_keys1} values per key)"
                printval2 = f"{nr_of_keys2} keys (mean {total2/nr_of_keys2} values per key)"
            else:
                printval1 = str(len(v1))
                printval2 = str(len(v2))
        else:
            printval1 = str(v1)
            printval2 = str(v2)
        print(output_formatter(key, printval1, printval2))


def parse_and_show(cdb_diff: CDBCompareResults, tally1: ResultsTally, tally2: ResultsTally,
                   ann_diffs: PerAnnotationDifferences,
                   output_formatter: Callable[[str, str, Optional[str]], str] = default_formatter):
    print("CDB overall differences:")
    show_dict_deep(cdb_diff.dict(), output_formatter=output_formatter)
    print("Now tally differences")
    gens = {"cat_data": lambda v: str(v)}
    compare_dicts(tally1.dict(), tally2.dict(), output_formatter=output_formatter, custom_printval_gens=gens)
    print("Now per-annotation differences:")
    show_dict_deep(ann_diffs.totals, output_formatter=output_formatter)
