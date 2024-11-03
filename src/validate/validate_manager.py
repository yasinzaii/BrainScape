# src/validate/validate_manager.py

import logging
from pathlib import Path
from omegaconf import OmegaConf
from typing import Dict, Any, List

from utils.json_handler import JsonHandler
from utils.common_utils import merge_settings

# Import the NiftiValidator
from validate.validator.nifti_validator import NiftiValidator




class ValidateManager:
    def __init__(
        self,
        config: OmegaConf,
        target_datasets: List[str],
        default_dataset_settings: Dict[str, Any],
        mapping: Dict[str, Any],
    ):
        """
        Initialize the ValidateManager.

        Parameters:
        - config (OmegaConf): Configuration object.
        - target_datasets (List[str]): List of dataset names to validate.
        - default_dataset_settings (Dict[str, Any]): Default settings for datasets.
        - mapping (Dict[str, Any]): Mapping information for datasets.
        """
        self.config = config
        self.target_datasets = target_datasets
        self.default_dataset_settings = default_dataset_settings
        self.mapping = mapping
        
        self.logger = logging.getLogger(__name__)
        
        # Define expected values for NIfTI validation (Hardcoded for now)
        self.expected_values = {
            'data_shape_min': (80, 80, 60),     # Minimum expected dimensions
            'data_shape_max': (512, 512, 512),  # Maximum expected dimensions
            'voxel_sizes': (1.2, 1.2, 1.2),     # Expected voxel size (should be less than expectation)
            'data_type': 'float32',
            'space_unit': 'mm',
            'qfac': [-1.0, 1.0],
            'data_min': 0.0,
            'data_max': 1000000.0,              # Some datasets have large scared Values, most of them has MAX Value < 30K
            'data_mean_min': 4.0,
            'data_mean_max': 100000.0,          
            'sform_code': 1,                    # NIFTI_XFORM_SCANNER_ANAT Preffered
            'qform_code': 1,                    # NIFTI_XFORM_SCANNER_ANAT Preffered
            'orientation': ['R', 'A', 'S']
        }

    
    def validate_nifti(self):
        """
        Perform NIfTI validation using NiftiValidator.
        """
        # Use NiftiValidator class as the validator
        validator_cls = NiftiValidator
        self.initiate_validation(validator_cls=validator_cls)
        
    
    def initiate_validation(self, validator_cls):
        """
        Initiate the validation process for all target datasets.

        Parameters:
        - validator_cls: The validator class to instantiate and use.
        """
        for dataset_name in self.target_datasets:
            self.logger.info(f"Starting validation for dataset '{dataset_name}'")

            # Merging Default Settings with Dataset Settings.
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings = JsonHandler(dataset_path / self.config.datasetSettingsJson)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )

            # Acquiring the Mapping
            mapping = self.mapping.get(dataset_name)
            if not mapping:
                self.logger.error(f"Mapping not found for dataset '{dataset_name}'. Skipping.")
                continue  # Skip to the next dataset


            # Instantiate the validator
            validator = validator_cls(
                expected_values=self.expected_values,
                dataset_settings=final_settings,
                dataset_path=dataset_path,
                mapping=mapping,
                config=self.config,
                logger=self.logger
            )
            
            # Run validator
            status = validator.run()
            if status:
                self.logger.info(f"Dataset '{dataset_name}' passed {validator_cls.__name__} validation.")
            else:
                self.logger.warning(f"Dataset '{dataset_name}' failed {validator_cls.__name__} validation.")
            
            
            """
            # Update dataset settings based on validation result
            dataset_settings.update_json({"isValidated": status}).save_json()
            if status:
                self.logger.info(f"Dataset '{dataset_name}' passed validation.")
            else:
                self.logger.warning(f"Dataset '{dataset_name}' failed validation.")
            """