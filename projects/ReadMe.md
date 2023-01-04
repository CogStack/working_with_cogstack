# Projects

This directory is a placeholder for where project workflows are organised and all relevant information relevant to a particular usecase is stored in a single location.

The [demo project structure](working_with_cogstack/projects/demo_project_stucture) is a template which you can copy and follow to meet the requirements of your usecase.

```
$ cp -r projects/demo_project_stucture projects/<name of new project>
```

The majority of this information is also held throughout other sections of this repository and thus this section is simply an alternative workflow which keeps all relevant data and file pertaining to a project together.

The folder names should correspond to the project and project ID for easy reference.

## Standarise Workflows (Optional)
The following is just guidelines/recommendations to standardise workflow:

- <p>Good practise is to name files with the following structure *YYYYMMDD_filename*
</p>


 This working directory, should be used to store temporary data files. With the final scripts (main.py and other analysis scripts...) held directly in the project folder outside of the sub-folders. Any raw or intermediate data that one may want to reference later should be stored in their respective directories.

A recommended format for the directory structure to efficiently manage each request is as follows: 
* Ideally the project_name should correspond to your CogStack request ID.


```
── project_name/
├── raw_data/                       # raw data files
│    └── cogstack_search_hits/      # search results
├──  processed_data/                # intermediate reference files 
│    └── ann_folder_path/           # annotated documents
├── results/                        # final results
├──  1_search.ipynb                 # functions to source
├──  2_run_model.ipynb              # intermediate data
├──  3_pipeline.ipynb               # convert annotation to output pipeline
├──  4_evaluation.ipynb             # evaluation of the output compared to a gold standard dataset
```


__[raw_data/]__: Contains the original, or raw, data files. Contents in this folder should be treated as read-only.

__[raw_data/cogstack_search_hits/]__: Contains the search results from cogstack. Once retreived from cogstack this dataset is static.

__[processed_data/]__: Contains manipulated files or partially processed files

__[processed_data/ann_folder_path/]__: All direct annotation output from a medcat model should be stored here. Acts as a checkpoint from which analysis can be conducted.

__[results/]__: Contains the final results and ideally explanatory markdown files.

