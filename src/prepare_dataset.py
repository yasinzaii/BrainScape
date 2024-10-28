#src/prepare_dataset.py

from utils.args_parser import get_parser
from omegaconf import OmegaConf
from utils.logging_setup import configure_logging
from utils.json_handler import JsonHandler

from download.download_manager import DownloadManager
from dataset.dataset_manager import DatasetManager
from preprocess.preprocess_manager import PreprocessManager

from utils.common_utils import get_subdirectories


def prepare_dataset():
    """
    Main function to prepare the dataset.
    """
    
    # Parsing Args | Omega Config
    parser = get_parser()
    args = parser.parse_args()
    argsConfig = OmegaConf.create(vars(args))
    
    # Configure logging - Make sure logger is not called Before.
    # Find "Logging configuration loaded successfully" in logs for easier navigation with multiple Program runs.
    logger = configure_logging(argsConfig.logger_config_file)
    
    # Loading the Config File | Merging
    jsonConfig = JsonHandler(argsConfig.config_path).get_data()
    config = OmegaConf.merge(jsonConfig, argsConfig)
    
    # Getting All Possible Datasets List
    all_datasets = get_subdirectories(path=config.pathDataset, basename_only=True)

    # Acquire Target Datsets based on the "index.json" overide file.
    target_datasets = []
    dataset_overrides = JsonHandler(config.pathOverrides).get_data()
    if "include" in dataset_overrides:   # if incude Key Present only Consider those datasets.
        target_datasets = dataset_overrides["include"]
    elif "exclude" in dataset_overrides: 
        target_datasets = all_datasets.copy()
        for ex in dataset_overrides["exclude"]:
            if ex in target_datasets:
                target_datasets.remove(ex)
            else:
                raise ValueError(f"{ex} Dataset to exclude not found.")
    else:
        target_datasets =  all_datasets   
    
    # Logging Target Datasets.
    logger.info(f"Target Datasets: {target_datasets}")
    

    # Getting the Default Settings for all Datasets
    default_dataset_settings = JsonHandler(config.pathDefaults).get_data()
    if not default_dataset_settings:
        logger.error("Unable to load Default Settings. Exiting!")
        return()    
    
    # Dowloading Datasets via "download" Module.
    download_man = DownloadManager(config=config, 
                                   target_datasets=target_datasets, 
                                   default_dataset_settings=default_dataset_settings)
    download_man.initiate_downloads()

    # Create Mapping/Record of The Dataset via "dataset" Module
    dataset_man = DatasetManager(config=config, 
                                 target_datasets=target_datasets, 
                                 default_dataset_settings=default_dataset_settings)
    dataset_man.initiate_mapping()

    # Preprocessing Datasets via "preprocess" Module 
    preprocess_man = PreprocessManager(config=config, 
                                    target_datasets=target_datasets, 
                                    default_dataset_settings=default_dataset_settings,
                                    mapping = dataset_man.get_mapping())
    
    preprocess_man.initiate_preprocessing()


if __name__ == "__main__":
    prepare_dataset()
