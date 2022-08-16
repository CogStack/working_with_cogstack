import json
import pandas as pd
import plotly
import plotly.graph_objects as go
from medcat.cat import CAT
from copy import deepcopy


class MedcatTrainer_export(object):
    """
    Class to analyse MedCATtrainer exports
    """

    def __init__(self, mct_export_paths, model_pack_path=None):
        """
        :param mct_export_paths: List of paths to MedCATtrainer exports
        :param model_pack_path: Path to medcat modelpack
        """
        self.cat = None
        if model_pack_path:
            self.cat = CAT.load_model_pack(model_pack_path)
        self.mct_export_paths = mct_export_paths
        self.mct_export = self._load_mct_exports(self.mct_export_paths)
        self._mct_export = deepcopy(self.mct_export)
        self.project_names = []
        self.document_names = []
        self.annotations = self._annotations()
        
    def _annotations(self):
        ann_lst=[]
        for proj in self._mct_export['projects']:
            self.project_names.append(proj)
            for doc in proj['documents']:
                self.document_names.append(doc['name'])
                for anns in doc['annotations']:
                    meta_anns_dict = dict()
                    for meta_ann in anns['meta_anns'].items():
                        meta_anns_dict.update({meta_ann[0]: meta_ann[1]['value']})
                    anns.pop('meta_anns')
                    output = dict()
                    output['project'] = proj['name']
                    output['document_name'] = doc['name']
                    output.update(anns)
                    output.update(meta_anns_dict)
                    ann_lst.append(output)
        return ann_lst

    def _load_mct_exports(self, list_of_paths_to_mct_exports):
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

    def annotation_df(self):
        """
        DataFrame of all annotations created
        :return: DataFrame
        """
        annotation_df = pd.DataFrame(self.annotations)
        if self.cat:
            annotation_df.insert(5, 'concept_name', annotation_df['cui'].map(self.cat.cdb.cui2preferred_name))
        annotation_df['last_modified'] = pd.to_datetime(annotation_df['last_modified']).dt.tz_localize(None)
        return annotation_df

    def concept_summary(self, extra_cui_filter=None):
        """
        Summary of only correctly annotated concepts from a mct export
        :return: DataFrame summary of annotations.
        """
        concept_output = self.annotation_df()
        concept_output = concept_output[concept_output['validated'] == True]
        concept_output = concept_output[(concept_output['correct'] == True) | (concept_output['alternative'] == True)]
        if self.cat:
            concept_count = concept_output.groupby(['cui','concept_name']).agg({'value': set, 'id': 'count'})
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
            concept_count_df['cui_counts'] = concept_count_df['cui'].map(cui_counts)
            examples_df = pd.DataFrame(examples).rename_axis('cui').reset_index(drop=False).\
                rename(columns={'fp': 'fp_examples',
                                'fn': 'fn_examples',
                                'tp': 'tp_examples'})
            concept_count_df = concept_count_df.merge(examples_df, how='left', on='cui')
            
        return concept_count_df

    def user_stats(self, by_user: bool = True):
        """
        Summary of user annotation work done

        :param by_user: User Stats grouped by user rather than day
        :return: DataFrame of user annotation work done
        """
        df = self.annotation_df()[['user', 'last_modified']]
        data = df.groupby([df['last_modified'].dt.year.rename('year'),
                           df['last_modified'].dt.month.rename('month'),
                           df['last_modified'].dt.day.rename('day'),
                           df['user']]).agg({'count'})
        data = pd.DataFrame(data)
        data.columns = data.columns.droplevel()
        data = data.reset_index(drop=False)
        data['date'] = pd.to_datetime(data[['year', 'month', 'day']])
        if by_user:
            data = data[['user', 'count']].groupby(by='user').agg(sum)
            data = data.reset_index(drop=False).sort_values(by='count', ascending=False).reset_index(drop=True)
            return data
        return data[['user', 'count', 'date']]

    def plot_user_stats(self, save_fig: bool = False, save_fig_filename: str = False):
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
        
    def generate_report(self, path: str='mct_report.xlsx'):
        with pd.ExcelWriter(path, engine_kwargs={'options':{'remove_timezone': True}}) as writer:
            df = pd.DataFrame.from_dict([self.cat.get_model_card(as_dict=True)]).T.reset_index(drop=False)
            #df.columns = {0:"MedCAT Model card"}
            df.to_excel(writer, index=False, sheet_name='medcat_model_card')
            self.user_stats().to_excel(writer, index=False, sheet_name='user_stats')
            #self.plot_user_stats().to_excel(writer, index=False, sheet_name='user_stats_plot')
            self.annotation_df().to_excel(writer, index=False, sheet_name='annotations')
            self.concept_summary().to_excel(writer, index=False, sheet_name='concept_summary')
        return print(f"MCT report save to: {path}")
    
    def rename_meta_anns(self,
                        meta_anns2rename=dict(),
                        meta_ann_values2rename=dict()):
        for proj in self.mct_export['projects']:
            for doc in proj['documents']:
                for anns in doc['annotations']:
                    if len(anns['meta_anns'])>0:
                        for meta_name2replace in meta_anns2rename:
                            try:
                                anns['meta_anns'][meta_anns2rename[meta_name2replace]] = anns['meta_anns'].pop(meta_name2replace)
                                anns['meta_anns'][meta_anns2rename[meta_name2replace]]['name'] = meta_anns2rename[meta_name2replace]
                                for meta_ann_name, meta_values in meta_ann_values2rename.items():
                                    if anns['meta_anns'][meta_anns2rename[meta_name2replace]]['name'] == meta_ann_name:
                                        for value in meta_values:
                                            if anns['meta_anns'][meta_anns2rename[meta_name2replace]]['value'] == value:
                                                anns['meta_anns'][meta_anns2rename[meta_name2replace]]['value'] = meta_ann_values2rename[meta_ann_name][value]
                            except KeyError:
                                pass
        self._mct_export = deepcopy(self.mct_export)
        self.annotations = self._annotations()
        return


'''
    def get_all_children(self, terminology, pt2ch):
        """
        Get all children concepts from a specified terminology

        :param terminology:
        :param pt2ch:
        :return:
        """
        result = []
        stack = [terminology]
        while len(stack) != 0:
            # remove last element from stack
            current_snomed = stack.pop()
            current_snomed_parent = pt2ch.get(current_snomed, [])
            stack.extend(current_snomed_parent)
            result.append(current_snomed)
        result = list(set(result))
        return result
'''


