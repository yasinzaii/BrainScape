import sys
from pathlib import Path

# Determine the project root directory
PROJECT_DIR = Path(__file__).resolve().parents[2]  
PAPER_DIR = Path(__file__).resolve().parents[1] / "research_paper" 



CONFIG_FILE = PROJECT_DIR / "config" / "config.json"

# Add 'src' to sys.path
SRC_DIR = PROJECT_DIR / 'src'
if SRC_DIR not in sys.path:
    sys.path.append(str(SRC_DIR))

# Importing Modules from Main Project.    
from utils.json_handler import JsonHandler


# Configuration from Config.json File
jsonConfig = JsonHandler(CONFIG_FILE).get_data()
# Dataset Dir 
datasetDir = PROJECT_DIR / jsonConfig["pathDataset"]
# Dataset Mapping from dataset.json file
datasets_mapping = JsonHandler(datasetDir/jsonConfig["datsetMriJson"]).get_data()
info_file_name = jsonConfig["datasetInfoYaml"]


data_dict = {
    "project_path": PROJECT_DIR,
    "papaer_path": PAPER_DIR, 
    "dataset_path": datasetDir,
    "config": jsonConfig, 
    "mapping": datasets_mapping
}

# Generating Supplementary table for datasets info.
from gen_supp_datasets_table import datasets_info_table
TABLE_NAME = "supp_datasets_details_table.tex"
table_path = Path(PAPER_DIR) / "tables" / TABLE_NAME
datasets_info_table(
    datasets_mapping = datasets_mapping, 
    caption="Comprehensive List of Integrated Anatomical MRI Datasets", 
    label="suppDataTable",
    table_path = str(table_path),
    dataset_path = str(datasetDir),
    info_file_name = info_file_name
    )


# Generating Supplementary Bibliography for datasets info.
from gen_supp_bibliography import supplimentary_bibliography
name_datasets = datasets_mapping.keys()
out_bib_path = Path(PAPER_DIR) / "bibliography" / "supplementary_references.bib"
supplimentary_bibliography(
    out_bib_path=out_bib_path,
    dataset_path=str(datasetDir),
    name_datasets=name_datasets,
    info_file_name=info_file_name
    )


# Generate Data file for LaTeX;
from gen_data_file import gen_data
out_data_path = Path(PAPER_DIR) / "data" / "variables.tex"

gen_data(
    data_dict=data_dict,
    out_data_path=out_data_path
)


# Generate the Dropped Subjects Figure
from gen_dropped_subjects_fig import generate_dropped_mris_figure
out_figure_path = Path(PAPER_DIR) / "figures" / "dropped_subjects.png"
generate_dropped_mris_figure(
    datasetDir=datasetDir, 
    out_figure_path=out_figure_path
)

# Generate the Example Figure
from gen_example_fig import generate_multimodal_figure
out_figure_path = Path(PAPER_DIR) / "figures" / "example_multimodal_mri.png"
generate_multimodal_figure(
    datasetDir=datasetDir, 
    out_figure_path=out_figure_path
)



# Generate Demographcis File as well as figure
from gen_demographics_file_fig import gen_demographics
out_demographics_path = PAPER_DIR / "data" / "demographics.tex"
out_figure_path = Path(PAPER_DIR) / "figures" / "age_group_sex_histogram.png"
gen_demographics(
    data_dict=data_dict,
    out_data_path=out_demographics_path,
    out_figure_path = out_figure_path
)