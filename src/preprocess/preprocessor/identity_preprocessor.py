# src/preprocess/preprocessor/identity_preprocessor.py

import shutil
import logging

from pathlib import Path
from preprocess.preprocessor.base_plugin import PreprocessorPlugin


class IdentityPreprocessor(PreprocessorPlugin):
    # Note This plugin should be used for the datasets which are already preprocessed. 
    # Furthermore, the "alreadyPreprocessed" Flag should also be set in the metadata.json file. 
    # This plugin just copies the content of the Downlaod Directory to Preprocessed Directory.
    
    
    # Class-specific plugin name
    plugin_name = "identity"

    @classmethod
    def get_name(cls) -> str:
        return cls.plugin_name

    def __init__(self, dataset_settings: dict, dataset_path: Path, mapping: list, config: dict):
        super().__init__(dataset_settings, dataset_path, mapping, config)
        self.logger = logging.getLogger(__name__)

        self.dataset_path = dataset_path

        self.download_dir_name = self.dataset_settings.get("downloadDirName", "Download")
        self.download_dir = self.dataset_path / self.download_dir_name

        # Preprocessed Directory (where files will be copied)
        self.preprocess_dir_name = self.dataset_settings.get("preprocessDirName", "preprocessed")
        self.preprocess_dir = self.dataset_path / self.preprocess_dir_name
        
        # Preprocessor settings 
        self.plugin_config = self.dataset_settings["preprocess"].get("identity", {})
        
                
    def run(self) -> bool:
        
        # Check if the dataset is marked as already preprocessed
        if not self.dataset_settings.get("alreadyPreprocessed", False):
            error_msg = "Dataset is not marked as already preprocessed. Aborting identity preprocessing."
            self.logger.error(error_msg)
            self.preprocessor_logger.error(error_msg)
            return False

        # Iterate over each entry in the mapping
        for entry in self.mapping:
            preprocessed_mris = {}
            
            subject = entry.get('subject')
            session = entry.get('session')
            type = entry.get('type')
            group = entry.get('group')

            for modality, mod_image_name in entry['mris'].items():
                
                # Absolute path to the downloaded file
                download_file_path = self.download_dir / entry['download'][modality]

                # Preprocessed Image Path Structure - Intermediate Structure - Same as BRATS Plugin.
                out_inter_path = f"{entry['subject']}.{entry['session']}.{entry['type']}.{entry['group']}"
                
                # Absolute path in the preprocessed directory
                preprocessed_file_path = self.preprocess_dir / out_inter_path / mod_image_name

                # Ensure the destination directory exists
                preprocessed_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy the file from download to preprocessed directory
                try:
                    shutil.copy2(download_file_path, preprocessed_file_path)
                    self.preprocessor_logger.info(f"Copied '{download_file_path}' to '{preprocessed_file_path}'")
                except Exception as e:
                    error_msg = f"Failed to copy '{download_file_path}' to '{preprocessed_file_path}': {e}" 
                    self.logger.error(error_msg)
                    self.preprocessor_logger.error(error_msg)
                    return False

                # Update the preprocessed MRI paths relative to the preprocessed directory
                preprocessed_mris[modality] = str(preprocessed_file_path.relative_to(self.preprocess_dir))

            # Update the entry with preprocessed MRI paths
            entry['preprocessed'] = preprocessed_mris
            self.preprocessor_logger.info(f"Added Preprocessed mapping for subject: {subject}, session: {session}, type: {type}, group: {group}  with preprocessed paths.")

        self.logger.info(f"Preprocesed Mapping for all of the subjects has been added. Dataset: {self.dataset_path.name}")
        return True
