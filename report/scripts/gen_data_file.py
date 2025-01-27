import json
from pathlib import Path

def gen_data(data_dict, out_data_path):

    
    # acquire mapping
    datasets_mapping = data_dict["mapping"] 
    
    
    # Count how many datasets we have
    num_datasets = len(datasets_mapping)

    # Count total number of unique subjects across all datasets
    total_subjects = 0
    for dataset_name, dataset_entries in datasets_mapping.items():
        subject_ids = {entry['subject'] for entry in dataset_entries}
        total_subjects += len(subject_ids)

    # Convert out_data_path to Path (in case a string was passed)
    out_data_path = Path(out_data_path)
    
    
    # Number of datasets already skull stripped. 
    NumDatasetsAlreadySkullStripped = 0 
    for dataset_name, dataset_entries in datasets_mapping.items():
        metadata_path = Path(data_dict["dataset_path"]) / dataset_name /  data_dict["config"]["datasetSettingsJson"] 
        with open(metadata_path) as json_file:
            json_data = json.load(json_file)
            already_preprocessed = json_data.get("alreadyPreprocessed", False)
            if already_preprocessed:
                NumDatasetsAlreadySkullStripped += 1
                

    # Total Number of subject removed
    TotalNumSubjectsRemoved = 0 
    TotalNumDatasetsWithSubjectsRemoved = 0 
    for dataset_name, dataset_entries in datasets_mapping.items():
        metadata_path = Path(data_dict["dataset_path"]) / dataset_name /  data_dict["config"]["datasetSettingsJson"] 
        with open(metadata_path) as json_file:
            json_data = json.load(json_file)
            exclude_sub_list = json_data["mapping"].get("excludeSub", [])
            if exclude_sub_list:
                TotalNumDatasetsWithSubjectsRemoved += 1 
                TotalNumSubjectsRemoved += len(exclude_sub_list)
    

    # Generate .dat file content
    # These commands can be used directly in LaTeX via \input{variables.dat}
    content_lines = []
    content_lines.append(r"\newcommand\NumDatasets{" + f"{num_datasets}" + r"}")
    content_lines.append(r"\newcommand\TotalNumSubjects{" + f"{total_subjects}" + r"}")
    content_lines.append(r"\newcommand\NumDatasetsAlreadySkullStripped{" + f"{NumDatasetsAlreadySkullStripped}" + r"}")
    content_lines.append(r"\newcommand\TotalNumSubjectsRemoved{" + f"{TotalNumSubjectsRemoved}" + r"}")
    content_lines.append(r"\newcommand\TotalNumDatasetsWithSubjectsRemoved{" + f"{TotalNumDatasetsWithSubjectsRemoved}" + r"}")
    
    # Write to .dat file
    out_data_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    with open(out_data_path, 'wb') as f:
        f.write(("\n".join(content_lines) + "\n").encode('utf-8'))

    print(f"Data variables file successfully generated at {out_data_path}")