# Medical <img src="../data/media/medcat_logo.png" width=45>oncept Annotation Tool

This directory contains information on retrieving data and creating models
All details regarding creating, building and running the NLP model are stored here.

## Locations for storing data:

- The [data](data) directory stores textual content. 
Methods for retrieving data should be stored in the [retrieve_data](search) folder.

- The [MedCAT models](data/medcat_models) directory holds models.

## Order of processing steps

#### [__Step 1__](medcat/1_create_model): Create the model

Each of the model components are found [here.](medcat/1_create_model)
This directory contains all the components required to initialise a model pack.

All models should be stored [here.](data/medcat_models)


#### [__Step 2__](medcat/2_train_model): Perform training

- [__Step 2.1__](medcat/2_train_model/1_unsupervised_training): Unsupervised training

    The unsupervised training steps can be found within unsupervised_training folder.


 - [__Step 2.2__](medcat/2_train_model/2_supervised_training): Supervised training

    After providing supervised labels with MedCATtrainer.
    The supervised training steps can be found within supervised_training folder.
 
#### [__Step 3__](medcat/3_run_model): Run model

Run model on your corpus of documents and write to csv/sql db.
Instructions on how to do this can be found within [run_model](medcat/3_run_model/run_model.ipynb)



