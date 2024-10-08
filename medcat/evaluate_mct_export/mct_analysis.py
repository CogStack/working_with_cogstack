import plotly
import plotly.graph_objects as go
from medcat.cat import CAT
from datetime import date

import json
import torch
import math
from torch import nn
import numpy as np
import pandas as pd
from collections import Counter
from typing import List, Dict, Iterator, Tuple, Optional, Union
from medcat.tokenizers.meta_cat_tokenizers import TokenizerWrapperBase

from medcat.utils.meta_cat.ml_utils import create_batch_piped_data

from medcat.meta_cat import MetaCAT
from medcat.config_meta_cat import ConfigMetaCAT
from medcat.utils.meta_cat.data_utils import prepare_from_json, encode_category_values
import warnings


DATETIME_FORMAT = r"%Y-%m-%d:%H:%M:%S"


class MedcatTrainer_export(object):
    """
    Class to analyse MedCATtrainer exports
    """

    def __init__(self, mct_export_paths: List[str], model_pack_path: Optional[str] = None):
        """
        :param mct_export_paths: List of paths to MedCATtrainer exports
        :param model_pack_path: Path to medcat modelpack
        """
        self.cat: Optional[CAT] = None
        if model_pack_path:
            self.cat = CAT.load_model_pack(model_pack_path)
        self.mct_export_paths = mct_export_paths
        self.mct_export = self._load_mct_exports(self.mct_export_paths)
        self.project_names: List[str] = []
        self.document_names: List[str] = []
        self.annotations = self._annotations()
        self.model_pack_path = model_pack_path
        if model_pack_path is not None:
            if model_pack_path[-4:] == '.zip':
                self.model_pack_path = model_pack_path[:-4]

    def _iter_docs(self, add_proj_names: bool = True) -> Iterator[Tuple[str, dict]]:
        for proj in self.mct_export['projects']:
            if add_proj_names:
                self.project_names.append(proj['name'])
            for doc in proj['documents']:
                yield proj['name'], doc

    def _iter_anns(self, add_doc_names: bool = True,
                   add_proj_names: bool = True) -> Iterator[Tuple[str, str, dict]]:
        for proj_name, doc in self._iter_docs(add_proj_names):
            if add_doc_names:
                self.document_names.append(doc['name'])
            for ann in doc['annotations']:
                yield proj_name, doc['name'], ann

    def _annotations(self) -> List[dict]:
        ann_lst = []
        # reset project and document names
        # in case of a second time calling _annotations()
        # i.e if/when renaming meta annotations
        self.project_names.clear()
        self.document_names.clear()
        for proj_name, doc_name, ann in self._iter_anns():
            meta_anns_dict = dict()
            for meta_ann in ann['meta_anns'].items():
                meta_anns_dict.update({meta_ann[0]: meta_ann[1]['value']})
            _anns = ann.copy()
            _anns.pop('meta_anns')
            output = dict()
            output['project'] = proj_name
            output['document_name'] = doc_name
            output.update(_anns)
            output.update(meta_anns_dict)
            ann_lst.append(output)
        return ann_lst

    def _load_mct_exports(self, list_of_paths_to_mct_exports: List[str]) -> dict:
        """
        Loads a list of multiple MCT exports
        :param list_of_paths_to_mct_exports: list of mct exports
        :return: single json format object
        """
        mct_projects = []
        for mct_project in list_of_paths_to_mct_exports:
            with open(mct_project, 'r') as jsonfile:
                mct_projects.extend(json.load(jsonfile)['projects'])
        mct_proj_exports = {'projects': mct_projects}
        return mct_proj_exports

    def annotation_df(self) -> pd.DataFrame:
        """
        DataFrame of all annotations created
        :return: DataFrame
        """
        annotation_df = pd.DataFrame(self.annotations)
        if self.cat:
            annotation_df.insert(5, 'concept_name', annotation_df['cui'].map(self.cat.cdb.cui2preferred_name))
        exceptions: List[ValueError] = []
        # try the default format as well as the format specified above
        for format in [None, DATETIME_FORMAT]:
            try:
                annotation_df['last_modified'] = pd.to_datetime(annotation_df['last_modified'], format=format).dt.tz_localize(None)
                exceptions.clear()
                break
            except ValueError as e:
                exceptions.append(e)
        if exceptions:
            # if there's issues
            raise ValueError(*exceptions)
        return annotation_df

    def concept_summary(self, extra_cui_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Summary of only correctly annotated concepts from a mct export
        :return: DataFrame summary of annotations.
        """
        concept_output = self.annotation_df()
        concept_output = concept_output[concept_output['validated'] == True]
        concept_output = concept_output[(concept_output['correct'] == True) | (concept_output['alternative'] == True)]
        if self.cat:
            concept_count = concept_output.groupby(['cui', 'concept_name']).agg({'value': set, 'id': 'count'})
        else:
            concept_count = concept_output.groupby(['cui']).agg({'value': set, 'id': 'count'})
        concept_count_df = pd.DataFrame(concept_count).reset_index(drop=False)
        concept_count_df['variations'] = concept_count_df['value'].apply(lambda x: len(x))
        concept_count_df.rename({'id': 'concept_count'}, axis=1, inplace=True)
        concept_count_df = concept_count_df.sort_values(by='concept_count', ascending=False).reset_index(drop=True)
        concept_count_df['count_variations_ratio'] = round(concept_count_df['concept_count'] /
                                                           concept_count_df['variations'], 3)
        if self.cat:
            fps,fns,tps,cui_prec,cui_rec,cui_f1,cui_counts,examples = self.cat._print_stats(data=self.mct_export,
                                                                                            use_project_filters=True,
                                                                                            extra_cui_filter=extra_cui_filter)
            concept_count_df['fps'] = concept_count_df['cui'].map(fps)
            concept_count_df['fns'] = concept_count_df['cui'].map(fns)
            concept_count_df['tps'] = concept_count_df['cui'].map(tps)
            concept_count_df['cui_prec'] = concept_count_df['cui'].map(cui_prec)
            concept_count_df['cui_rec'] = concept_count_df['cui'].map(cui_rec)
            concept_count_df['cui_f1'] = concept_count_df['cui'].map(cui_f1)
            #concept_count_df['cui_counts'] = concept_count_df['cui'].map(cui_counts) # TODO check why cui counts is incorrect
            examples_df = pd.DataFrame(examples).rename_axis('cui').reset_index(drop=False).\
                rename(columns={'fp': 'fp_examples',
                                'fn': 'fn_examples',
                                'tp': 'tp_examples'})
            concept_count_df = concept_count_df.merge(examples_df, how='left', on='cui')

        return concept_count_df

    def user_stats(self, by_user: bool = True) -> pd.DataFrame:
        """
        Summary of user annotation work done

        :param by_user: User Stats grouped by user rather than day
        :return: DataFrame of user annotation work done
        """
        df = self.annotation_df()[['user', 'last_modified']]
        data = df.groupby([df['last_modified'].dt.year.rename('year'),
                           df['last_modified'].dt.month.rename('month'),
                           df['last_modified'].dt.day.rename('day'),
                           df['user']]).agg({'count'})  # type: ignore
        data = pd.DataFrame(data)
        data.columns = data.columns.droplevel()
        data = data.reset_index(drop=False)
        data['date'] = pd.to_datetime(data[['year', 'month', 'day']])
        if by_user:
            data = data[['user', 'count']].groupby(by='user').agg(sum)
            data = data.reset_index(drop=False).sort_values(by='count', ascending=False).reset_index(drop=True)
            return data
        return data[['user', 'count', 'date']]

    def plot_user_stats(self, save_fig: bool = False, save_fig_filename: str = ''):
        """
        Plot annotator user stats against time.
        An alternative method of saving the file is: plot_user_stats().write_image("path/filename.png")
        :param save_fig: Optional parameter to save the plot
        :param save_fig_filename: path/filename.html, default value is mct export projects names.
        :return: fig object
        """
        data = self.user_stats(by_user=False)
        total_annotations = data['count'].sum()
        fig = go.Figure()
        for user in data['user'].unique():
            fig.add_trace(
                go.Bar(x=data[data['user'] == user]['date'], y=data[data['user'] == user]['count'], name=user),
            )
        fig.update_layout(title={'text': f'MedCATtrainer Annotator Progress - Total annotations: {total_annotations}'},
                          legend_title_text='MedCAT Annotator',
                          barmode='stack')
        fig.update_xaxes(title_text='Date')
        fig.update_yaxes(title_text='Annotation Count')
        if save_fig:
            if save_fig_filename:
                filename = save_fig_filename
            else:
                filename = input("Please enter the export path/filename with no ext: ") + '.html'
            plotly.offline.plot(fig, filename=filename)
            print(f'The figure was saved at: {filename}')
        return fig

    def _rename_meta_ann_values(self, meta_anns: dict, name_replacement: str,
                                meta_ann_name: str, meta_values: list,
                                meta_ann_values2rename: dict):
        if meta_anns[name_replacement]['name'] == meta_ann_name:
            for value in meta_values:
                if meta_anns[name_replacement]['value'] == value:
                    meta_anns[name_replacement]['value'] = meta_ann_values2rename[meta_ann_name][value]

    def _rename_meta_ann_for_name(self, meta_anns: dict, name2replace: str, name_replacement: str,
                                  meta_ann_values2rename: dict):
        meta_anns[name_replacement] = meta_anns.pop(name2replace)
        meta_anns[name_replacement]['name'] = name_replacement
        for meta_ann_name, meta_values in meta_ann_values2rename.items():
            self._rename_meta_ann_values(meta_anns, name_replacement, meta_ann_name, meta_values,
                                         meta_ann_values2rename)

    def _rename_meta_ann(self, meta_anns: dict,
                         meta_anns2rename=dict(), meta_ann_values2rename=dict()):
        for meta_name2replace in meta_anns2rename:
            try:
                self._rename_meta_ann_for_name(meta_anns, meta_name2replace,
                                               meta_anns2rename[meta_name2replace],
                                               meta_ann_values2rename)
            except KeyError:
                pass

    def rename_meta_anns(self, meta_anns2rename: dict = dict(), meta_ann_values2rename: dict = dict()):
        """Rename the names and/or values of meta annotations.

        :param meta_anns2rename: Example input: `{'Subject/Experiencer': 'Subject'}`
        :param meta_ann_values2rename: Example input: `{'Subject':{'Relative':'Other'}}`
        :return:
        """
        # if we want to rename the values, but haven't specified any names to rename
        # we need to use a names dict to map the names to themselves due to the way
        # the current implementation works
        if meta_ann_values2rename and not meta_anns2rename:
            meta_anns2rename = dict((name, name) for name in meta_ann_values2rename)
        for _, _, ann in self._iter_anns(False, False):
            meta_anns = ann['meta_anns']
            if len(meta_anns) > 0:
                self._rename_meta_ann(meta_anns, meta_anns2rename, meta_ann_values2rename)
        self.annotations = self._annotations()
        return

    def _eval_model(self, model: nn.Module, data: List, config: ConfigMetaCAT, tokenizer: TokenizerWrapperBase) -> Dict:
        device = torch.device(config.general['device'])  # Create a torch device
        batch_size_eval = config.general['batch_size_eval']
        pad_id = config.model['padding_idx']
        ignore_cpos = config.model['ignore_cpos']
        class_weights = config.train['class_weights']

        if class_weights is not None:
            class_weights = torch.FloatTensor(class_weights).to(device)
            criterion = nn.CrossEntropyLoss(weight=class_weights)  # Set the criterion to Cross Entropy Loss
        else:
            criterion = nn.CrossEntropyLoss()  # Set the criterion to Cross Entropy Loss

        y_eval = [x[2] for x in data]
        num_batches = math.ceil(len(data) / batch_size_eval)
        running_loss = []
        all_logits = []
        model.to(device)
        model.eval()

        with torch.no_grad():
            for i in range(num_batches):
                x, cpos, y = create_batch_piped_data(data,
                                                     i*batch_size_eval,
                                                     (i+1)*batch_size_eval,
                                                     device=device,
                                                     pad_id=pad_id)
                logits = model(x, cpos, ignore_cpos=ignore_cpos)
                loss = criterion(logits, y)

                # Track loss and logits
                running_loss.append(loss.item())
                all_logits.append(logits.detach().cpu().numpy())

        predictions = np.argmax(np.concatenate(all_logits, axis=0), axis=1)
        return predictions

    def _eval(self, metacat_model, mct_export) -> dict:
        g_config = metacat_model.config.general
        t_config = metacat_model.config.train
        t_config['test_size'] = 0
        t_config['shuffle_data'] = False
        t_config['prerequisites'] = {}
        t_config['cui_filter'] = {}

        # Prepare the data
        assert metacat_model.tokenizer is not None
        data = prepare_from_json(mct_export, g_config['cntx_left'], g_config['cntx_right'], metacat_model.tokenizer,
                                 cui_filter=t_config['cui_filter'],
                                 replace_center=g_config['replace_center'], prerequisites=t_config['prerequisites'],
                                 lowercase=g_config['lowercase'])

        # Check is the name there
        category_name = g_config['category_name']
        if category_name not in data:
            warnings.warn(f"The meta_model {category_name} does not exist in this MedCATtrainer export.", UserWarning)
            return {category_name: f"{category_name} does not exist"}

        data = data[category_name]

        # We already have everything, just get the data
        category_value2id = g_config['category_value2id']
        data, data_undersampled, _ = encode_category_values(data, existing_category_value2id=category_value2id)
        print(_)
        print(len(data))
        # Run evaluation
        assert metacat_model.tokenizer is not None
        result = self._eval_model(metacat_model.model, data, config=metacat_model.config, tokenizer=metacat_model.tokenizer)

        return {'predictions': result, 'meta_values': _}

    def full_annotation_df(self) -> pd.DataFrame:
        """
        DataFrame of all annotations created including meta_annotation predictions.
        This function is similar to annotation_df with the addition of Meta_annotation predictions from the medcat model.
        prerequisite Args: MedcatTrainer_export([mct_export_paths], model_pack_path=<path to medcat model>)
        :return: DataFrame
        """
        if not self.cat or not self.model_pack_path:  # mostly for typing so flake8 knows it's not None down below
            raise ValueError("No model pack specified")
        anns_df = self.annotation_df()
        meta_df = anns_df[(anns_df['validated'] == True) & (anns_df['deleted'] == False) & (anns_df['killed'] == False)
                          & (anns_df['irrelevant'] != True)]
        meta_df = meta_df.reset_index(drop=True)

        for meta_model_card in self.cat.get_model_card(as_dict=True)['MetaCAT models']:
            meta_model = meta_model_card['Category Name']
            print(f'Checking metacat model: {meta_model}')
            _meta_model = MetaCAT.load(self.model_pack_path + '/meta_' + meta_model)
            meta_results = self._eval(_meta_model, self.mct_export)
            _meta_values = {v: k for k, v in meta_results['meta_values'].items()}
            pred_meta_values = []
            counter = 0
            for meta_value in meta_df[meta_model]:
                if pd.isnull(meta_value):
                    pred_meta_values.append(np.nan)
                else:
                    pred_meta_values.append(_meta_values.get(meta_results['predictions'][counter], np.nan))
                    counter += 1

            loc = meta_df.columns.get_loc(meta_model)
            if isinstance(loc, int):
                meta_df.insert(loc + 1, f'predict_{meta_model}', pred_meta_values)
            else:
                print(f"Warning: Unexpected column location type: {type(loc)}")
            meta_df.insert(1, f'predict_{meta_model}', pred_meta_values)

        return meta_df

    def meta_anns_concept_summary(self) -> pd.DataFrame:
        if not self.cat:
            raise ValueError("No model pack specified")
        meta_df = self.full_annotation_df()
        meta_performance = {}
        for cui in meta_df.cui.unique():
            temp_meta_df = meta_df[meta_df['cui'] == cui]
            meta_task_results = {}
            for meta_model_card in self.cat.get_model_card(as_dict=True)['MetaCAT models']:
                meta_task = meta_model_card['Category Name']
                list_meta_anns = list(zip(temp_meta_df[meta_task], temp_meta_df['predict_' + meta_task]))
                counter_meta_anns = Counter(list_meta_anns)
                meta_value_results: Dict[Tuple[Dict, str, str], Union[int, float]] = {}
                for meta_value in meta_model_card['Classes'].keys():
                    total = 0
                    fp = 0
                    fn = 0
                    tp = 0
                    for meta_value_result, count in counter_meta_anns.items():
                        if meta_value_result[0] == meta_value:
                            if meta_value_result[1] == meta_value:
                                tp += count
                                total += count
                            else:
                                fn += count
                                total += count
                        elif meta_value_result[1] == meta_value:
                            fp += count
                        else:
                            pass  # Skips nan values
                    meta_value_results[(meta_task, meta_value, 'total')] = total
                    meta_value_results[(meta_task, meta_value, 'fps')] = fp
                    meta_value_results[(meta_task, meta_value, 'fns')] = fn
                    meta_value_results[(meta_task, meta_value, 'tps')] = tp
                    try:
                        meta_value_results[(meta_task, meta_value, 'f-score')] = tp / (tp + (1 / 2) * (fp + fn))
                    except ZeroDivisionError:
                        meta_value_results[(meta_task, meta_value, 'f-score')] = 0
                meta_task_results.update(meta_value_results)
            meta_performance[cui] = meta_task_results

        meta_anns_df = pd.DataFrame.from_dict(meta_performance, orient='index')
        col_lst = []
        for col in meta_anns_df.columns:
            if col[2] == 'total':
                col_lst.append(col)
        meta_anns_df['total_anns'] = meta_anns_df[col_lst].sum(axis=1)
        meta_anns_df = meta_anns_df.sort_values(by='total_anns', ascending=False)
        meta_anns_df = meta_anns_df.rename_axis('cui').reset_index(drop=False)
        meta_anns_df.insert(1, 'concept_name', meta_anns_df['cui'].map(self.cat.cdb.cui2preferred_name))
        return meta_anns_df

    def generate_report(self, path: str = 'mct_report.xlsx', meta_ann=False, concept_filter: Optional[List] = None):
        """
        :param path: Outfile path
        :param meta_ann: Include Meta_annotation evaluation in the summary as well
        :param concept_filter: Filter the report to only display select concepts of interest. List of cuis.
        :return: A full excel report for MedCATtrainer annotation work done.
        """
        if not self.cat:
            raise ValueError("No model pack specified")
        if concept_filter:
            with pd.ExcelWriter(path) as writer:
                print('Generating report...')
                # array-like is allowed by documentation but not by typing
                df = pd.DataFrame.from_dict([self.cat.get_model_card(as_dict=True)]).T.reset_index(drop=False)  # type: ignore
                df.columns = ['MCT report', f'Generated on {date.today().strftime("%Y/%m/%d")}']  # type: ignore
                df = pd.concat([df, pd.DataFrame([['MCT Custom filter', concept_filter]], columns=df.columns)],
                               ignore_index = True)
                df.to_excel(writer, index=False, sheet_name='medcat_model_card')
                self.user_stats().to_excel(writer, index=False, sheet_name='user_stats')
                print('Evaluating annotations...')
                if meta_ann:
                    ann_df = self.full_annotation_df()
                    ann_df = ann_df[ann_df['cui'].isin(concept_filter)].reset_index(drop=True)
                    ann_df['timestamp'] = ann_df['timestamp'].dt.tz_localize(None)  # Remove timezone information
                    ann_df.to_excel(writer, index=False, sheet_name='annotations')
                else:
                    ann_df = self.annotation_df()
                    ann_df = ann_df[ann_df['cui'].isin(concept_filter)].reset_index(drop=True)
                    ann_df['timestamp'] = ann_df['timestamp'].dt.tz_localize(None)  # Remove timezone information
                    ann_df.to_excel(writer, index=False, sheet_name='annotations')
                performance_summary_df = self.concept_summary()
                performance_summary_df = performance_summary_df[performance_summary_df['cui'].isin(concept_filter)]\
                    .reset_index(drop=True)
                performance_summary_df.to_excel(writer, index=False, sheet_name='concept_summary')
                if meta_ann:
                    print('Evaluating meta_annotations...')
                    meta_anns_df = self.meta_anns_concept_summary()
                    meta_anns_df = meta_anns_df[meta_anns_df['cui'].isin(concept_filter)].reset_index(drop=True)
                    meta_anns_df.to_excel(writer, index=True, sheet_name='meta_annotations_summary')
        else:
            with pd.ExcelWriter(path) as writer:
                print('Generating report...')
                df = pd.DataFrame.from_dict([self.cat.get_model_card(as_dict=True)]).T.reset_index(drop=False)  # type: ignore
                df.columns = ['MCT report', f'Generated on {date.today().strftime("%Y/%m/%d")}']  # type: ignore
                df.to_excel(writer, index=False, sheet_name='medcat_model_card')
                self.user_stats().to_excel(writer, index=False, sheet_name='user_stats')
                print('Evaluating annotations...')
                if meta_ann:
                    self.full_annotation_df().to_excel(writer, index=False, sheet_name='annotations')
                else:
                    self.annotation_df().to_excel(writer, index=False, sheet_name='annotations')
                self.concept_summary().to_excel(writer, index=False, sheet_name='concept_summary')
                if meta_ann:
                    print('Evaluating meta_annotations...')
                    self.meta_anns_concept_summary().to_excel(writer, index=True, sheet_name='meta_annotations_summary')

        return print(f"MCT report saved to: {path}")
