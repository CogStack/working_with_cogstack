# UMLS - The Unified Medical Language System®

Place holder for all UMLS related content and downloads here

--------

## About
The UMLS integrates and distributes key terminology, classification and coding standards,
 and associated resources to promote creation of more effective and interoperable biomedical information systems and services,
  including electronic health records.

The UMLS, or Unified Medical Language System, is a set of files and software that brings together many health and 
biomedical vocabularies and standards to enable interoperability between computer systems.

## Access

[Request a license](https://uts.nlm.nih.gov/uts/?_gl=1*1791eyk*_ga*MTkwNzE1ODcyOC4xNjYyOTcxNDg3*_ga_P1FPTH9PL4*MTY2Mjk3ODA3OS4yLjEuMTY2Mjk3OTQ4Mi4wLjAuMA..)
and sign up for a UMLS Terminology Services (UTS) account.

 - UMLS licenses are issued only to individuals and not to groups or organizations.
 - There is no charge for licensing the UMLS from NLM. NLM is a member of [SNOMED International](http://www.snomed.org/)
 (owner of SNOMED CT), and there is no charge for SNOMED CT use in the United States and other [member countries](http://www.snomed.org/our-customers/members).
  Some uses of the UMLS may require additional agreements with individual terminology vendors.
 - Your UTS account provides access to the Unified Medical Language System (UMLS), the Value Set Authority Center (VSAC),
  RxNorm downloads, SNOMED CT downloads and more.
 - For more, visit [how to license and access UMLS data](https://www.nlm.nih.gov/databases/umls.html)


Further information can be found on the [nlm website](https://www.nlm.nih.gov/research/umls/index.html)



## API Home

### Authentication 
All users of this terminology require registration with NLM, to download UMLS data (Warning: some restriction may apply depending on country; see UMLS licence and its SNOMED CT appendix):

https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html

Documentation for User Authentication can be found [here](https://documentation.uts.nlm.nih.gov/rest/authentication.html)


For further information about UMLS API Technical Documentation can be found [here.](https://documentation.uts.nlm.nih.gov/rest/home.html)


### Downloading UMLS

One can use the scripts found in [NLM_umls_download.py](data/umls/NLM_umls_download.py) to download the entire UMLS 
Knowledge Source.

Otherwise, one can access the UMLS Knowledge Sources directly: File Downloads can be found [here](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html)

Alternatively, you can simply follow the scripts in the [working with UMLS notebook](data/umls/working_with_umls.ipynb). This script will download UMLS and convert the
 MRCONSO.RFF.ZIP file to a DataFrame. You can then process this file to get ready to build a MedCAT Concept Database! 

## Citing the UMLS
If you use UMLS in your work, please cite the original article:

    Bodenreider O. The Unified Medical Language System (UMLS): integrating biomedical terminology. Nucleic Acids Res. 2004 Jan 1;32(Database issue):D267-70. doi: 10.1093/nar/gkh061. PubMed PMID: 14681409; PubMed Central PMCID: PMC308795.


