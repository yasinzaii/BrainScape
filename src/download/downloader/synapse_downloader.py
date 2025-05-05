#src/download/downloader/synapse_downloader.py

import os
import shutil
import zipfile
import logging
import configparser
import synapseclient

from pathlib import Path
from typing import List, Tuple, Any, Dict
from download.downloader.base_plugin import DownloaderPlugin

logger = logging.getLogger(__name__)

class SynapseDownloader(DownloaderPlugin):
    """
    A Synapse-based downloader plugin intended for BraTS-like datasets.
    It downloads one or more zip files (training/validation, etc.)
    from Synapse, extracts them, renames subject folders, and places
    them into the final download directory.
    """
    plugin_name = "SynapseDownloader"
    
    @classmethod
    def get_name(cls) -> str:
        return cls.plugin_name
    
    def __init__(
        self,
        dataset_settings: Dict[str, Any],
        dataset_path: str,
        config: Dict[str, Any]
    ):
        """
        Initialize the Synapse downloader.

        Args:
            dataset_settings (dict): Dataset-specific settings from metadata.json.
            dataset_path (str): The base path where the dataset folder is located.
            config (dict): Overall pipeline config.
        """
        
        self.dataset_settings = dataset_settings
        self.dataset_path = Path(dataset_path)
        self.download_dir_path = self.dataset_path / dataset_settings["downloadDirName"]
        # We'll store raw zips + extract to 'temp' inside the dataset folder
        self.temp_dir_path = self.dataset_path / "temp"
        self.config = config
        
        # Get the credential path from the config
        self.credential_path = self.config.get('credential_path')
        
        # Datasets to include (training/validation)
        self.datasets = self.dataset_settings["download"].get("include", [])
    
    
    def _login_synapse(self):
        """
        Logs into Synapse using the 'synapse_secret_token' from the credentials file.

        Returns:
            syn (synapseclient.Synapse) on success, or None if login fails.
        """
        
        # Verify that the profiles/credentials file exists
        if not os.path.isfile(self.credential_path):
            logger.error(f"SynapseDownloader - The specified profiles file does not exist: {self.credential_path}")
            return None
        
        # Parse credentials
        credentials_parser = configparser.ConfigParser()
        credentials_parser.read(self.credential_path)
        
        # Synapse secret token from your credentials file [synapse].
        synapse_token = credentials_parser["synapse"].get("synapse_secret_token", None)
        
        if not synapse_token:
            logger.error("SynapseDownloader - No 'synapse_secret_token' found in credentials.")
            return None
        
        try:
            syn = synapseclient.Synapse(debug = False)
            syn.login(authToken=synapse_token)
            return syn
        except Exception as e:
            logger.error(f"SynapseDownloader - Failed to login to Synapse: {e}")
            return None
        
    ## This function works but I have used simpler approach for zip extraction  
    # def _download_and_extract_zip(
    #     self,
    #     syn: synapseclient.Synapse,
    #     synapse_id: str,
    #     subset_name: str
    # ) -> Tuple[bool, str]:
    #     """
    #     Download a zip from Synapse (e.g. training or validation) into temp/<subset_name>,
    #     then extract it into the same folder.

    #     Args:
    #         syn (synapseclient.Synapse): Authenticated synapse client.
    #         synapse_id (str): e.g. "syn51514132"
    #         subset_name (str): e.g. "training" or "validation"

    #     Returns:
    #         (success, message)
    #     """
    #     try:
    #         logger.info(f"SynapseDownloader - Downloading zip from Synapse ID: {synapse_id}, subset={subset_name}")
            
    #         # Ensure a clean subset folder under 'temp'
    #         subset_temp_path = self.temp_dir_path / subset_name
    #         if subset_temp_path.exists():
    #             shutil.rmtree(subset_temp_path)
    #         subset_temp_path.mkdir(parents=True, exist_ok=True)
            
    #         # 1) Download the file to 'temp/<subset_name>'
    #         entity = syn.get(entity=synapse_id, downloadLocation=self.temp_dir_path, ifcollision="keep.local")
    #         #local_zip_path = Path(entity.path)
    #         local_zip_path = self.temp_dir_path / entity.name
    #         if not local_zip_path.is_file():
    #             msg = f"SynapseDownloader - No local zip file found after Synapse get job: {local_zip_path}"
    #             logger.error(msg)
    #             return False, msg
            
    #         # 2) Extract the zip into the same subset_temp_path
    #         with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
    #             for elem in zip_ref.namelist() :
                    
    #                 entity_name = entity.name.rsplit('.', 1)[0]
    #                 if elem.startswith(entity_name):
    #                     if not elem.split(os.sep,1)[1]:
    #                         logger.warning(f"SynapseDownloader - Unable to extract {elem} from the downloaded {entity.name} zip file.")
    #                         continue
    #                     target_path = str(subset_temp_path) + os.sep +  elem.split(os.sep,1)[1]
                    
    #                 if elem.endswith('/'):
    #                     Path(target_path).mkdir(parents=True, exist_ok=True)
    #                 else:
    #                     with zip_ref.open(elem) as source, open(target_path, "wb") as target:
    #                         shutil.copyfileobj(source, target)
            
    #         msg = f"SynapseDownloader - Download + unzip done: {local_zip_path} -> {subset_temp_path}"
    #         logger.info(msg)
    #         return True, msg
                        
    #     except Exception as e:
    #         msg = f"SynapseDownloader - Failed to download/extract from Synapse ID '{synapse_id}': {e}"
    #         logger.error(msg)
    #         return False, msg
    
    def _download_and_extract_zip(
        self,
        syn: synapseclient.Synapse,
        synapse_id: str,
        subset_name: str
    ) -> Tuple[bool, str]:
        """
        Download a zip from Synapse (e.g. training or validation) into temp/<subset_name>,
        then extract it into the same folder.

        Args:
            syn (synapseclient.Synapse): Authenticated synapse client.
            synapse_id (str): e.g. "syn51514132"
            subset_name (str): e.g. "training" or "validation"

        Returns:
            (success, message)
        """
        try:
            logger.info(f"SynapseDownloader - Downloading zip from Synapse ID: {synapse_id}, subset={subset_name}")
            
            # Ensure a clean subset folder under 'temp'
            subset_temp_path = self.temp_dir_path / subset_name
            if subset_temp_path.exists():
                shutil.rmtree(subset_temp_path)
            subset_temp_path.mkdir(parents=True, exist_ok=True)
            
            # 1) Download the file to 'temp/<subset_name>'
            entity = syn.get(entity=synapse_id, downloadLocation=self.temp_dir_path, ifcollision="keep.local")
            #local_zip_path = Path(entity.path)
            local_zip_path = self.temp_dir_path / entity.name
            if not local_zip_path.is_file():
                msg = f"SynapseDownloader - No local zip file found after Synapse get job: {local_zip_path}"
                logger.error(msg)
                return False, msg
            
            # 2) Extract the zip into the same subset_temp_path
            logger.info(f"SynapseDownloader - Unzipping from: {local_zip_path}, May take a while.")
            with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
                zip_ref.extractall(subset_temp_path)
            
            # 3) Removing Extra folder - Unzipped inside an extra folder with name = entity.name
            unzipped_contents = list(subset_temp_path.iterdir())
            entity_name = entity.name.rsplit('.', 1)[0] # Remove the extension from the zip filename.
            if len(unzipped_contents) == 1:
                extra_folder = unzipped_contents[0]
                if extra_folder.is_dir() and extra_folder.name == entity_name:
                    # Move each item from the extra folder to the parent folder (subset_temp_path)
                    for child in extra_folder.iterdir():
                        target = subset_temp_path / child.name
                        shutil.move(str(child), str(target))
                    # Remove the now-empty extra folder
                    extra_folder.rmdir()    
            
            msg = f"SynapseDownloader - Download + unzip done: {local_zip_path} -> {subset_temp_path}"
            logger.info(msg)
            return True, msg
                        
        except Exception as e:
            msg = f"SynapseDownloader - Failed to download/extract from Synapse ID '{synapse_id}': {e}"
            logger.error(msg)
            return False, msg
    
    def _rename_subject_folders(self, subset_name: str):
        """
        After extraction, rename each subject folder under 'temp/<subset_name>/'
        by prefixing the <subset_name> (e.g. 'training' or 'validation') to the subject folder.
        Also moves the final subject folders into 'download/'.
        """

        # e.g. training or validation 
        prefix = subset_name

        # Where we extracted the zip
        subset_temp_path = self.temp_dir_path / subset_name

        for item in subset_temp_path.iterdir():
            if item.is_dir():
                # e.g. if folder name is "BraTS-GLI-01774-000"
                new_name = f"{prefix}-{item.name}"
                new_path = item.parent / new_name
                # Rename in place
                item.rename(new_path)

                # Now move that entire folder into "download/"
                shutil.move(str(new_path), str(self.download_dir_path))

    
    
    def download(self) -> Tuple[bool, List[str]]:
        """
        Downloads the datasets via Synapse,
        unzips them, and organizes the data into a standard folder structure.

        Returns:
            (bool, List[str]):
                bool: success status
                List[str]: messages or paths from the download
        """

        # Login Synapse
        syn = self._login_synapse()
        if not syn:
            msg = "SynapseDownloader - Failed to login to Synapse - Skipping Download Job"
            logger.error(msg)
            return False, [msg]
        
        # Prepare the 'temp' and 'downloadDirName' folders
        if not self.temp_dir_path.exists():
            self.temp_dir_path.mkdir(parents=True, exist_ok=True)
        if not self.download_dir_path.exists():
            self.download_dir_path.mkdir(parents=True, exist_ok=True)
        
        success_overall = True
        messages = []
        
        # Download each zip from the "include" list
        for ds_item in self.datasets:
            syn_id = ds_item["dataset"]       # e.g. "syn51514132"
            subset_name = ds_item["type"]     # e.g. "training" or "validation"

            ok, msg = self._download_and_extract_zip(
                synapse_id=syn_id,
                syn=syn,
                subset_name=subset_name
            )
            messages.append(msg)
            if not ok:
                success_overall = False
                continue

            # Rename subject folders => "BRATS-<subjectName>"
            self._rename_subject_folders(subset_name)

        return success_overall, messages

        
    def get_source_file_list(self) -> List[str]:
        """
        This function was specifically coded for OpenneuroDownloader where list of files from remote/actual source are acquired
        which as then used for comparison with the downloaded files. Here we are just returning the directory contents of 
        downloaded datasets.

        Returns:
            List[str]: A list of paths
        """

        all_files = []
        for path_obj in self.download_dir_path.rglob("*"):
            if path_obj.is_file():
                rel_path = path_obj.relative_to(self.download_dir_path)
                all_files.append(str(rel_path))

        return all_files