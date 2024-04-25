from typing import Any, Optional, Callable, Tuple, Dict

from enum import Enum
from copy import deepcopy
import numbers

from compare_cdb import compare as CDBCompareResults
from compare_annotations import ResultsTally, PerAnnotationDifferences

from IPython.display import display, Markdown


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


def markdown_formatter(path: str, v1: str, v2: Optional[str] = None) -> str:
    return f"{path:40s} | {str(v1):40s} | {str(v2 or ''):40s}"


def show_dict_deep(d: dict, path: str = '',
                   output_formatter: Callable[[str, str, Optional[str]], str] = default_formatter,
                   notebook_output: bool = False, do_show: bool = True) -> str:
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
        notebook_output (bool): Whether to use notebook-specific output. Defaults to False.
        do_show (bool): Whether to show the output. Defaults to True.
    """
    paired_keys = set(key for key in d if _has_paired_key(d, key))
    key_pairs = [(key1, _get_other_key(key1)) for key1 in paired_keys if key1 < _get_other_key(key1)]
    total_out = []
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
            cur_out = show_dict_deep(value, path=total_path, output_formatter=output_formatter,
                                     notebook_output=notebook_output, do_show=False)
            total_out.append(cur_out)
            continue
        text = output_formatter(total_path, value, None)
        total_out.append(text)
    # for paired keys
    for key1, key2 in key_pairs:
        common_key = key1[:-1]
        total_path = f"{path}.{common_key}" if path else key
        text = output_formatter(total_path, d[key1], d[key2])
        total_out.append(text)
    all_text = '\n'.join(total_out)
    if do_show:
        if notebook_output:
            # add column markers
            all_text = "| " + all_text.replace("\n", " |\n| ") + " |"
            header = '| Path | Value | [Optional] Comparison |\n| ----- | ----- | ----- |\n'
            display(Markdown(header + all_text))
        else:
            print(all_text)
    return all_text

def _empty_values_recursively(d: dict, cur_depth: int = 0, max_depth: int = 2) -> None:
    for k in set(d.keys()):
        v = d[k]
        if isinstance(v, dict) and cur_depth < max_depth:
            _empty_values_recursively(v, cur_depth=cur_depth + 1, max_depth=max_depth)
        else:
            if isinstance(v, str):
                d[k] = ''
            elif isinstance(v, numbers.Number):
                d[k] = 0
            if isinstance(v, dict):
                d[k] = {}
            else:
                # unknown
                d[k] = ''


def _get_nulled_copy(d: dict, depth: int = 0) -> dict:
    d2 = deepcopy(d)
    _empty_values_recursively(d2, cur_depth=0, max_depth=depth)
    return d2


def compare_dicts(d1: Optional[dict], d2: Optional[dict],
                  output_formatter: Callable[[str, str, Optional[str]], str] = default_formatter,
                  ignore_callables: bool = True,
                  custom_printval_gens: Optional[Dict[str, Callable[[Any], str]]] = None,
                  notebook_output: bool = False):
    """Compares two dicts with identical schemas to oneanother.

    This will attempt to unravel dict values in the following way
    - The number of keys will be used
    - For the values
      - If the dict maps to integers, the total value is counted (e.g train counts)
      - If the dict maps to floats, the average value is measured (e.g accuracy)
      - If the dict maps to sets the mean number of elements is measued (e.g per-cui forms)

    Args:
        d1 (Optional[dict]): The first dict.
        d2 (Optional[dict]): The second dict.
        output_formatter (Callable[[str, str, Optional[str]], str], optional): The output formatter.
            Defaults to default_formatter.
        ignore_callables (bool): Whether to ignore callable values. Defaults to True.
        custom_printval_gens (Optional[Dict[str, Callable[[Any], str]]]):
            The keys are ones that have a custom print value generator.
            And the values are the corresponding custom print value generators.
            Defaults to None (or an empty dict).
        notebook_output (bool): Whether to use notebook output. Defaults to False.
    raises:
        AssertionError: If the keys of the two dicts differ; or if value types mismatch.
    """
    if d1 is None and d2 is None:
        raise ValueError("At least one of the two dicts needs to be non-None")
    # latter condition is for mypy
    if d1 is None and d2 is not None:
        d1 = _get_nulled_copy(d2)
    # latter condition is for mypy
    if d2 is None and d1 is not None:
        d2 = _get_nulled_copy(d1)
    # for mypy - these are now both non-None
    d1: Dict = d1  # type: ignore
    d2: Dict = d2  # type: ignore
    assert d1.keys() == d2.keys()
    all_out = []
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
            value_keys = list(v1)
            if value_keys:
                k0 = value_keys[0]
                v0 = v1[k0]
            else:
                # empty dict
                v0 = v1
            if isinstance(v0, int):
                key = f"{key} (Dict[{type(key).__name__}, int])"
                total1 = sum(v1.values())
                total2 = sum(v2.values())
                printval1 = f"{nr_of_keys1} keys (total {total1} in value)"
                printval2 = f"{nr_of_keys2} keys (total {total2} in value)"
            elif isinstance(v0, float):
                key = f"{key} (Dict[{type(key).__name__}, float])"
                if nr_of_keys1:
                    mean1 = sum(v1.values())/nr_of_keys1
                else:
                    mean1 = 0.0
                if nr_of_keys2:
                    mean2 = sum(v2.values())/nr_of_keys2
                else:
                    mean2 = 0.0
                printval1 = f"{nr_of_keys1} keys (mean {mean1} in value)"
                printval2 = f"{nr_of_keys2} keys (mean {mean2} in value)"
            elif isinstance(v0, set):
                key = f"{key} (Dict[{type(key).__name__}, Set])"
                total1 = sum(len(v) for v in v1.items())
                total2 = sum(len(v) for v in v2.items())
                if nr_of_keys1:
                    mean1 = total1/nr_of_keys1
                else:
                    mean1 = 0.0
                if nr_of_keys2:
                    mean2 = total2/nr_of_keys2
                else:
                    mean2 = 0.0
                printval1 = f"{nr_of_keys1} keys (mean {mean1} values per key)"
                printval2 = f"{nr_of_keys2} keys (mean {mean2} values per key)"
            else:
                key = f"{key} (Dict[{type(key).__name__}, {type(v0).__name__}])"
                printval1 = str(len(v1))
                printval2 = str(len(v2))
        else:
            printval1 = str(v1)
            printval2 = str(v2)
        all_out.append(output_formatter(key, printval1, printval2))
    all_text = "\n".join(all_out)
    if notebook_output:
        # add column markers
        all_text = "| " + all_text.replace("\n", " |\n| ") + " |"
        header = '| Path | First | Second |\n| ----- | ----- | ----- |\n'
        display(Markdown(header + all_text))
    else:
        print(all_text)


def parse_and_show(cdb_diff: CDBCompareResults, tally1: ResultsTally, tally2: ResultsTally,
                   ann_diffs: PerAnnotationDifferences,
                   output_formatter: Callable[[str, str, Optional[str]], str] = default_formatter,
                   notebook_output: bool = False):
    if notebook_output:
        display(Markdown("# CDB overall differences"))
    else:
        print("CDB overall differences:")
    show_dict_deep(cdb_diff.dict(), output_formatter=output_formatter, notebook_output=notebook_output)
    if notebook_output:
        display(Markdown("# Now tally differences"))
    else:
        print("Now tally differences")
    gens = {"cat_data": lambda v: str(v)}
    compare_dicts(tally1.dict(), tally2.dict(), output_formatter=output_formatter, custom_printval_gens=gens,
                  notebook_output=notebook_output)
    if notebook_output:
        display(Markdown("# Now per-annotation differences:"))
    else:
        print("Now per-annotation differences:")
    show_dict_deep(ann_diffs.totals, output_formatter=output_formatter, notebook_output=notebook_output)
