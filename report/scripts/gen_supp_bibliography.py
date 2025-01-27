# This script generates a list of dict with required info for each of the DATASET
import pandas as pd
import yaml
import bibtexparser
from pathlib import Path
from pylatexenc.latexencode import utf8tolatex

import unicodedata

def supplimentary_bibliography(
        out_bib_path,
        dataset_path,
        name_datasets,
        info_file_name):

    bib_line = []

    # Arrange Asending Order
    sorted_name_datasets = sorted(name_datasets)

    for dataset_name in sorted_name_datasets:

        # acquring dataset information
        dataset_info_file = Path(dataset_path) / dataset_name / info_file_name
        
        # Load info.yaml
        with open(dataset_info_file, 'r', encoding='utf-8') as f:
            info = yaml.safe_load(f)

     
        # acquring dataset title with reference 
        citation_bibtex = info.get('citation', '')
        
        # convert to latex
        citation_bibtex_latex = unicodedata.normalize('NFC', citation_bibtex)
        
        bib_line.append(citation_bibtex_latex)
        bib_line.append('')
        
        # Join all lines into a single string
    latex_bib = '\n'.join(bib_line)
    
    # Write/Overwrite the LaTeX code to the specified output file
    with open(out_bib_path, 'w', encoding='utf-8') as file:
        file.write(latex_bib)
    
    print(f"LaTeX table successfully generated at {out_bib_path}")