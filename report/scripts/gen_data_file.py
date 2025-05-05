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
        
        
    # Count total number of MRI, and each modality MRI
    totalNumMris = 0 
    totalNumT1wMris = 0
    totalNumT2wMris = 0
    totalNumT1GdMris = 0
    totalNumFlairMris = 0
    # Count total number of Datasets
    numDatasetsWithTOneScans = 0
    numDatasetsWithTTwoScans = 0
    numDatasetsWithTOneGdScans = 0
    numDatasetsWithTFlairScans = 0    
    for dataset_name, dataset_entries in datasets_mapping.items():
        hasT1 = False
        hasT2 = False
        hasT1Gd = False
        hasFlair = False
        for entry in dataset_entries:
            mris = entry['mris']
            totalNumMris += len(mris)
        
            if 't1w' in mris:
                totalNumT1wMris += 1
                hasT1 = True
            if 't2w' in mris:
                totalNumT2wMris += 1
                hasT2 = True
            if 'flair' in mris:
                totalNumFlairMris += 1
                hasFlair = True
            if 't1ce' in mris:
                totalNumT1GdMris += 1
                hasT1Gd = True
            if 'seg' in mris:
                totalNumMris -= 1 # Seg map is not MRI modality
                
                 
            
            
        # If the dataset had T1/T2/FLAIR in at least one subject/session, increment respective counters
        if hasT1:
            numDatasetsWithTOneScans += 1
        if hasT2:
            numDatasetsWithTTwoScans += 1
        if hasFlair:
            numDatasetsWithTFlairScans += 1
        if hasT1Gd:
            numDatasetsWithTOneGdScans += 1
            
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
    
    content_lines.append(r"\newcommand\TotalNumMRIs{" + f"{totalNumMris}" + r"}")
    content_lines.append(r"\newcommand\TotalTOneMRIs{" + f"{totalNumT1wMris}" + r"}")
    content_lines.append(r"\newcommand\TotalTTwoMRIs{" + f"{totalNumT2wMris}" + r"}")
    content_lines.append(r"\newcommand\TotalTOneGdMRIs{" + f"{totalNumT1GdMris}" + r"}")
    content_lines.append(r"\newcommand\TotalFlairMRIs{" + f"{totalNumFlairMris}" + r"}")
    
    content_lines.append(r"\newcommand\NumDatasetsWithTToneScans{" + str(numDatasetsWithTOneScans) + r"}")
    content_lines.append(r"\newcommand\NumDatasetsWithTTwoScans{" + str(numDatasetsWithTTwoScans) + r"}")
    content_lines.append(r"\newcommand\NumDatasetsWithTOneGdScans{" + str(numDatasetsWithTOneGdScans) + r"}")
    content_lines.append(r"\newcommand\NumDatasetsWithTFlairScans{" + str(numDatasetsWithTFlairScans) + r"}")
    
    
    # Compute percentages
    t1_percent = (totalNumT1wMris / totalNumMris * 100) 
    t2_percent = (totalNumT2wMris / totalNumMris * 100) 
    t1gd_percent = (totalNumT1GdMris / totalNumMris * 100) 
    flair_percent = (totalNumFlairMris / totalNumMris * 100) 
    # Format them to 2 decimal places
    t1_percent_str = f"{t1_percent:.2f}"
    t2_percent_str = f"{t2_percent:.2f}"
    t1gd_percent_str = f"{t1gd_percent:.2f}"
    flair_percent_str = f"{flair_percent:.2f}"
        
    # Create LaTeX commands
    content_lines.append(r"\newcommand\TOnePercent{" + t1_percent_str + r"}")
    content_lines.append(r"\newcommand\TTwoPercent{" + t2_percent_str + r"}")
    content_lines.append(r"\newcommand\TOneGdPercent{" + t1gd_percent_str + r"}")
    content_lines.append(r"\newcommand\FlairPercent{" + flair_percent_str + r"}")
    
    
    # Write to .dat file
    out_data_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    with open(out_data_path, 'wb') as f:
        f.write(("\n".join(content_lines) + "\n").encode('utf-8'))

    print(f"Data variables file successfully generated at {out_data_path}")