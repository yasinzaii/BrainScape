# This script generates a list of dict with required info for each of the DATASET
import pandas as pd
import yaml
import bibtexparser
from pathlib import Path
from pylatexenc.latexencode import utf8tolatex

# Dict sample example
"""
datasets = [
    {
        "identifier": "AOMIC",
        "title": "Amsterdam Open MRI Collection (AOMIC) - AOMIC-ID1000",
        "url": "https://openneuro.org/datasets/ds003097/versions/1.2.1",
        "reference": "snoek2021amsterdam",
        "mris": "1000",
        "t1w": "2762",
        "t2w": "0",
        "flair": "0",
    },
    ...
]
"""

def get_citation_key(bibtex):

    bib_database = bibtexparser.loads(bibtex)
    keys = [entry['ID'] for entry in bib_database.entries]
    
    if len(keys) == 1:
        return f"(\\cite{{{keys[0]}}})"
    elif len(keys) == 0:
        return ""
    else:
        raise


def acq_dataset_table_values(datasets_mapping, dataset_path, info_file_name):

    table = [] 
    
    for dataset_name, dataset_mapping in datasets_mapping.items():
        
        
        
        # acquring dataset information
        dataset_info_file = Path(dataset_path) / dataset_name / info_file_name
        
        # Load info.yaml
        with open(dataset_info_file, 'r', encoding='utf-8') as f:
            info = yaml.safe_load(f)

 
        
        download_url = info.get('download','')
        
        # acquiring dataset identifier with download link
        identifier = f'\\mbox{{\\href{{{download_url}}}{{\\hspace{{0.1em}}\\rule{{0pt}}{{1.2em}}{dataset_name}\\rule{{0pt}}{{1.2em}}\\hspace{{0.1em}}}}}}'
        
        # acquring dataset title with reference 
        citation_bibtex = info.get('citation', '')
        title = utf8tolatex(info.get('title', '')) + ' ' + get_citation_key(citation_bibtex)
        
        # acquire dataset license
        license_info = utf8tolatex(info.get('license', ''))
        
        # Initialize counters
        mri_counts = {
            't1w': 0,
            't2w': 0,
            'flair': 0
        }
        
        # Iterate through each dataset entry
        entry_subjects = []
        for entry in dataset_mapping:
            mris = entry.get('mris', {})
            entry_subjects.append(entry['subject'])
            for mri_type in ['t1w', 't2w', 'flair']:
                if mri_type in mris and mris[mri_type]:
                    mri_counts[mri_type] += 1
        num_subjects = len(set(entry_subjects))
        
        
        table.append({
            "identifier": identifier,
            "title": title,
            "license": license_info,
            "subjects": num_subjects, 
            "t1w": mri_counts["t1w"],
            "t2w": mri_counts["t2w"],
            "flair": mri_counts["flair"]
        })
        
    return table

def datasets_info_table(
        datasets_mapping, 
        caption, 
        label,
        table_path,
        dataset_path,
        info_file_name):
    
    # Sorting Dataset Mapping - Array of Objects
    sorted_datasets_mapping_dict = dict(sorted(datasets_mapping.items(), key=lambda item: item[0]))
    
    
    table = acq_dataset_table_values(sorted_datasets_mapping_dict, dataset_path, info_file_name)
    
    # Define the table header
    headers = [
        r'\textbf{Identifier}',
        r'\textbf{Dataset Name}',
        r'\textbf{License}',
        r'\textbf{Subjects}',
        r'\textbf{T1w}',
        r'\textbf{T2w}',
        r'\textbf{Flair}',
    ]
    
    # Start building the LaTeX table
    latex_lines = []
    latex_lines.append( r'\begin{center}')
    latex_lines.append( r'\small')
    latex_lines.append( r'\begin{longtable}{@{}lp{8.5cm}p{1.4cm}llll@{}}')
    latex_lines.append( f'    \\caption{{{caption}}} \\label{{{label}}} \\\\')
    
    header_row = ' & '.join(headers) + r' \\' # Add header row

    latex_lines.append( r'    \toprule')
    latex_lines.append( f'    {header_row}')
    latex_lines.append( r'    \midrule')
    latex_lines.append( r'    \endfirsthead')
    
    latex_lines.append( r'    ')
    latex_lines.append( r'    \multicolumn{7}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\')
    latex_lines.append( r'    \toprule')
    latex_lines.append( f'    {header_row}')
    latex_lines.append( r'    \midrule')
    latex_lines.append( r'    \endhead')
    

    latex_lines.append( r'    ')
    latex_lines.append( r'    \midrule \multicolumn{7}{r}{{Continued on next page}} \\')
    latex_lines.append( r'    \endfoot')
    
    latex_lines.append( r'    \bottomrule')
    latex_lines.append( r'    \endlastfoot')
    latex_lines.append( r'    ')
    
    
    
    for row in table:
        row_list = [
            row["identifier"],
            row["title"],
            row["license"],
            str(row["subjects"]),
            str(row["t1w"]),
            str(row["t2w"]),
            str(row["flair"])
        ]
    
        row_line = ' & '.join(row_list) + r' \\'
        latex_lines.append(f'    {row_line}')
    

    

    
    # # Add a note if provided
    # if note:
    #    latex_lines.append( r'    \begin{tablenotes}[flushleft]\footnotesize')
    #    latex_lines.append(rf'    \item[${{a}}$]{note}')
    #    latex_lines.append( r'    \end{tablenotes}')
       
       
    latex_lines.append(r'\end{longtable}')
    latex_lines.append(r'\end{center}')
    
    # Join all lines into a single string
    latex_code = '\n'.join(latex_lines)
    
    # Write/Overwrite the LaTeX code to the specified output file
    with open(table_path, 'w') as file:
        file.write(latex_code)
    
    print(f"LaTeX table successfully generated at {table_path}")