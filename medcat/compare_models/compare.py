from typing import List, Tuple, Dict, Set, Callable, Optional
from medcat.cat import CAT

import pandas as pd
import tqdm

from compare_cdb import compare as compare_cdbs, CDBCompareResults
from compare_annotations import ResultsTally, PerAnnotationDifferences
from output import parse_and_show



def load_documents(file_name: str) -> List[Tuple[str, str]]:
    with open(file_name) as f:
        df = pd.read_csv(f, names=["id", "text"])
    if df.iloc[0].id == "id" and df.iloc[0].text == "text":
        # removes the header
        # but also messes up the index a little
        df = df.iloc[1:, :]
    return list(df.itertuples(index=False))


def do_counting(cat: CAT, documents: List[Tuple[str, str]]) -> ResultsTally:
    def cui2name(cui):
        if cui in cat.cdb.cui2preferred_name:
            return cat.cdb.cui2preferred_name[cui]
        all_names = cat.cdb.cui2names[cui]
        # longest anme
        return sorted(all_names, key=lambda name: len(name), reverse=True)[0]
    res = ResultsTally(cat_data=cat.cdb.make_stats(), cui2name=cui2name)
    for _, doc in tqdm.tqdm(documents):
        entities = cat.get_entities(doc)
        res.count(entities)
    return res


def _get_pt2ch(cat: CAT) -> Optional[Dict]:
    if 'pt2ch' in cat.cdb.addl_info:
        return cat.cbd.addl_inf['pt2ch']
    return None


def get_per_annotation_diffs(cat1: CAT, cat2: CAT, documents: List[Tuple[str, str]],
                             show_progress: bool = True) -> PerAnnotationDifferences:
    pt2ch1: Optional[Dict] = _get_pt2ch(cat1)
    pt2ch2: Optional[Dict] = _get_pt2ch(cat2)
    pad = PerAnnotationDifferences(pt2ch1=pt2ch1, pt2ch2=pt2ch2)
    for doc_id, doc in tqdm.tqdm(documents, disable=not show_progress):
        pad.look_at_doc(cat1.get_entities(doc), cat2.get_entities(doc), doc_id)
    pad.finalise()
    return pad


def get_diffs_for(model_pack_path_1: str,
                  model_pack_path_2: str,
                  documents_file: str,
                  cui_filter: Optional[Set[str]] = None,
                  show_progress: bool = True
                  ) -> Tuple[CDBCompareResults, ResultsTally, ResultsTally, PerAnnotationDifferences]:
    documents = load_documents(documents_file)
    if show_progress:
        print("Loading [1]", model_pack_path_1)
    cat1 = CAT.load_model_pack(model_pack_path_1)
    if show_progress:
        print("Loading [2]", model_pack_path_2)
    cat2 = CAT.load_model_pack(model_pack_path_2)
    if cui_filter:
        if show_progress:
            print("Applying filter to CATs:", len(cui_filter), 'CUIs')
        cat1.config.linking.filters.cuis = cui_filter
        cat2.config.linking.filters.cuis = cui_filter
    if show_progress:
        print("Counting [1]")
    res1 = do_counting(cat1, documents)
    if show_progress:
        print("Counting [2]")
    res2 = do_counting(cat2, documents)
    if show_progress:
        print("CDB compare")
    cdb_diff = compare_cdbs(cat1.cdb, cat2.cdb)
    if show_progress:
        print("Per annotations diff finding")
    ann_diffs = get_per_annotation_diffs(cat1, cat2, documents)
    return cdb_diff, res1, res2, ann_diffs
    


def main(mpn1: str, mpn2: str, documents_file: str):
    cdb_diff, res1, res2, ann_diffs = get_diffs_for(mpn1, mpn2, documents_file, show_progress=False)
    print("Results:")
    parse_and_show(cdb_diff, res1, res2, ann_diffs)


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])