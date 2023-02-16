# CogStack search results/requests.

Add subdirectories to more efficiently manage and collate search results relating to a single CogStack Search request.


## Standarise Workflows (Optional)

The following is just guidelines/recommendations to standardise workflow:

- <p>Good practise is to name files with the following structure *YYYYMMDD_filename*
</p>

A recommended format for the directory structure to efficiently manage each request is as follows:
Ideally the *project_name* should correspond to your CogStack request ID.


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

__[work/]__: The working directory, should be used to store temporary data files.
With the final scripts (main.py and other analysis scripts...) held directly in the project folder outside of the sub-folders.
Any intermediate data that one may want to reference later should be stored in the work sub-folder.
