# src/download/download_manager.py

import os
import shutil
import logging

from pathlib import Path
from omegaconf import OmegaConf
from utils.json_handler import JsonHandler
from utils.common_utils import merge_settings

# For Loading Downlaoder Plugins
from utils.plugin_loader import PluginLoader
from download.downloader.base_plugin import DownloaderPlugin

# Directory containing Downloader Plugins [in 'downloader' folder besides 'download_manager.py' ]
downloader_plugins_directory = Path(__file__).resolve().parent / 'downloader'


class DownloadManager:
    
    def __init__(self, config: OmegaConf, target_datasets: list, default_dataset_settings: dict):
        
        self.config = config
        self.target_datasets = target_datasets
        self.default_dataset_settings = default_dataset_settings

        self.logger = logging.getLogger(__name__)
        
        # Acquiring Downlaoder Plugins
        self.plugin_loader = PluginLoader(downloader_plugins_directory, DownloaderPlugin)
        self.plugin_loader.load_plugins() # Loading The Downloader Plugins.
        

    def initiate_downloads(self):
        for dataset_name in self.target_datasets:
            
            # Merging Default Settings With Dataset Settigs.
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings = JsonHandler(dataset_path / self.config.datasetSettingsJson)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )
            
            
            # Check if Dataset is downloadable...
            if not final_settings["download"]["isDownloadable"]:
                if Path(download_dir_path).is_dir() and any(Path(download_dir_path).iterdir()):
                    self.logger.info(f"'{dataset_path}' Dataset is not downloadable and but already downloaded skipping download/Check job")
                else :
                    self.logger.error(f"'{dataset_path}' Dataset is not downloadable and the download folder is empty, skipping download Job")
                continue
            
            
            # Acquiring Plugin Downloader Name
            # TO-DO
            # Move it to confgurtion File
            try:
                downloader_name = final_settings["download"]["plugin"]
            except Exception as e:
                self.logger.error(f"Downloader (Key:'plugin') Missing from Dataset:{dataset_name} Settings, Skipping Download Job, Error: {e}")
                continue # Skipping
            
            
            # Path of the download directory
            download_dir_path = dataset_path / final_settings["downloadDirName"]
            
            # If 'isDownloaded' Flag Set - Datset Settings.
            if final_settings["isDownloaded"]: 
                
                # Check if the dataset directory existance + if it has content.
                if  not download_dir_path.is_dir() or not any(download_dir_path.iterdir()):
                    
                    # Flag incorrectly set. Reset Flags & Redownload...
                    self.logger.error(f"{dataset_path} Dataset 'isDownloaded' settings set to True, yet Download folder ('{download_dir_path}') is Missing or Empty")
                    self.logger.warning(f"Resetting 'isDownloaded' of '{dataset_path}' Dataset to False and Redownloading")
                    dataset_settings.update_json({"isDownloaded":False, "isDatasetJsonCreated": False}).save_json() 
                    final_settings["isDownloaded"] = False
                
                # Falg is set correctly as dataset is in download directory
                else:
                    self.logger.info(f"'{dataset_path}' Dataset already downloaded skipping download job")
                    continue 
                
            
            

            
            # Creating download directory if not Present...
            if download_dir_path.exists():
                
                if self.config.re_download:
                    self.logger.critical(f"Dataset Download Folder '{dataset_path}' already exists and not empty yet 'isDownloaded' Flag not set, Force Redownload On, Redownloading!")
                    try:
                        shutil.rmtree(download_dir_path)
                        download_dir_path.mkdir(parents=True, exist_ok=True)    
                    except Exception as e:
                        self.logger.error(f"Failed to Remove and Recreate the Download Directory: {download_dir_path}")
                
                elif any(download_dir_path.iterdir()):
                    self.logger.critical(f"Dataset Download Folder '{dataset_path}' already exists and not empty yet 'isDownloaded' Flag not set, Skipping Download")
                    continue 
                else: 
                    self.logger.warning(f"'{dataset_path}' exists but is empty. Proceeding with download.")
            else:
                # Create a download directory
                try: 
                    download_dir_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created download directory: '{download_dir_path}'")
                except Exception as e:
                    self.logger.error(f"Error creating download directory '{download_dir_path}': {e}")
                    return False
            
            
            # Dynamically load correct downloader plugin based on 'downloader' Dataset Setting.
            downloader_cls = self.plugin_loader.get_plugin_by_name(downloader_name)
            if not downloader_cls:
                self.logger.error(f"Requested Downloader Plugin '{downloader_name}' not found, skipping download for dataset '{dataset_name}'")
                continue  # Skipping Download
            
            
            downloader = downloader_cls(
                dataset_settings=final_settings, 
                dataset_path=dataset_path, 
                config=self.config
            )
            
            if not downloader:
                self.logger.error(f"Requested Dowloader Plugin:{downloader_name} Not Found, Skipping Download! Dataset: {dataset_path}")
                continue # Skipping Download
            
            # Download the Dataset
            success, outputs = downloader.download()
            
            if success:
                
                self.logger.info(f"Download Job Completed for Dataset: '{dataset_path}', Verifying Downlaoded Contents.")
                
                
                # Validate The Downloaded Files
                
                # Getting The List of Valid Source Files, Passing Wildcard Pattern
                source_files = set(downloader.get_source_file_list())
                downloaded_files = set([str(p.relative_to(download_dir_path)) for p in download_dir_path.rglob('*') if p.is_file()])
                
                if source_files == downloaded_files:
                    self.logger.info(f"The Source and Downloaded File Match for Dataset: '{dataset_path}', Verification Completed, setting Dataset 'isDownlaoded' Flag")
                    dataset_settings.update_json({"isDownloaded":True}).save_json() 
                
                else:
                    missing_files =  source_files - downloaded_files
                    extra_files = downloaded_files - source_files
                    if missing_files:
                        self.logger.error(f"The Source and Downloaded File Match failed, Missing Files: {missing_files}")
                    if extra_files:
                        self.logger.error(f"The Source and Downloaded File Match Failed, Extra Files: {extra_files}") 

            else:
                self.logger.error(f"Download Failed for {dataset_path} Dataset.")
                dataset_settings.update_json({"isDownloaded":False, "isDatasetJsonCreated":False}).save_json()
                try:
                    shutil.rmtree(download_dir_path)    
                except Exception as e:
                    self.logger.error(f"Failed to Remove the Download Directory: {download_dir_path}")
            
