# Projects

This directory is a placeholder for where project workflows are organised and all relevant information relevant to a particular usecase is stored in a single location.

The [demo project structure](working_with_cogstack/projects/demo_project_stucture) is a template which you can copy and follow to meet the requirements of your usecase.

The majority of this information is also held throughout other sections of this repository and thus this section is simply an alternative workflow which keeps all relevant data and file pertaining to a project together.

The folder names should correspond to the project and project ID for easy reference.

## Standarise Workflows (Optional)
The following is just guidelines/recommendations to standardise workflow:

- <p>Good practise is to name files with the following structure *YYYYMMDD_filename*
</p>

A recommended format for the directory structure to efficiently manage each request is as follows: Ideally the project_name should correspond to your CogStack request ID.

```
project_name/
--- input/    # raw data files
--- ref/      # reference files 
--- result/   # final results
--- src/      # functions to source
--- work/     # intermediate data
--- main.py
--- analysis.py
```

__[input/]__: Contains the original, or raw, data files. Contents in this folder should be treated as read-only.

__[ref/]__: Contains reference files, i.e. from research.

__[result/]__: Contains the final results and explanatory markdown files.

__[src/]__: Contains functions that are sourced from the main console code.

__[work/]__: This working directory, should be used to store temporary data files. With the final scripts (main.py and other analysis scripts...) held directly in the project folder outside of the sub-folders. Any intermediate data that one may want to reference later should be stored in the work sub-folder.