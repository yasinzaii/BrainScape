# src/validate/validator/nifti_validator.py

import nibabel as nib
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, List

from .base_validator import Validator
from utils.logging_setup import configure_session_logging


class NiftiValidator(Validator):
    """Validaor class for NIfTI files."""
        
    def __init__(
        self,
        expected_values: Dict[str, Any],
        dataset_settings: Dict[str, Any],
        dataset_path: Path,
        mapping: List[Dict[str, Any]],
        config: Dict[str, Any],
        logger: logging.Logger = None
    ):
        """
        Initialize the validator with expected values.

        Parameters:
        - expected_values (dict): Dictionary of expected values for comparison.
        - dataset_settings (dict): Final merged settings for the dataset.
        - dataset_path (Path): Path to the dataset directory.
        - mapping (List[Dict[str, Any]]): Mapping information for the dataset.
        - logger (logging.Logger): Logger instance.
        """
        self.expected_values = expected_values
        self.dataset_settings = dataset_settings
        self.dataset_path = dataset_path
        self.config = config
        self.mapping = mapping
        
        self.main_logger = logger if logger else  logging.getLogger(__name__)
        
        self.errors = []

        self.download_dir_name = self.dataset_settings.get("downloadDirName", "")
        self.download_dir = self.dataset_path / self.download_dir_name
        
        
        # Nifti Validator Logger configuration
        self.dataset_log_file = self.dataset_path / "nifti_validator.log"
        
        # Delete the existing log file if it exists
        if self.dataset_log_file.exists():
            try:
                self.dataset_log_file.unlink()
                self.main_logger.info(f"Deleted existing log file: {self.dataset_log_file}")
            except Exception as e:
                self.main_logger.error(f"Failed to delete log file: {e}")
                
        self.logger = configure_session_logging(
            session_log_file=self.dataset_log_file,
            log_config_path=self.config.logger_config_file,
            logger_name=f'niftiValidator.{self.dataset_path.name}',
        )
        

    def run(self) -> bool:
        """
        Run the NIfTI validation.

        Returns:
        - bool: True if all files pass validation, False otherwise.
        """
        all_files_valid = True
        
        # Loop through entries in mapping
        for entry in self.mapping:
            
            # Get avaliable modalities
            modalities = entry['download'].keys()
            for mod_name in modalities:
                
                # Path to the downloaded NIFTI MRI image
                download_mri_relpath = entry['download'][mod_name]
                download_mri_path = self.download_dir / download_mri_relpath
                
                if not download_mri_path.exists():
                    self.logger.error(f"File '{download_mri_path}' does not exist.")
                    all_files_valid = False
                    continue
                
                hdr = self.check(download_mri_path)
                if self.has_errors():
                    all_files_valid = False
                    errors = self.get_errors() # Get all Error For That Nifti File
                    self.logger.error(f"Validation errors in file '{download_mri_path}':")
                    for error in errors:
                        self.logger.error(f"- Error: {error}")
                    self.reset_errors() # Clear all Error To Make it ready for New Nifti File
                    self.logger.info("\n") # Blank Line
                else:
                    self.logger.info(f"File '{download_mri_path}' passed validation.")
                    self.logger.info("\n") # Blank Line
                    
                    
                    # Include Valuable Niti Info to the Mapping.
                    if hdr:
                        # Including Voxel Sizes to the mapping info
                        if 'niftiInfo' not in entry:
                            entry['niftiInfo'] = {}
                        if mod_name not in entry['niftiInfo']:
                            entry['niftiInfo'][mod_name] = {}
                        entry['niftiInfo'][mod_name]['downloadVoxelSizes'] = hdr.get_zooms()[:3]    
                    else:
                        raise ValueError("File Header Empty, check function returned None.")
        return all_files_valid

    def has_errors(self):
        """Return True if any errors were found."""
        return len(self.errors) > 0

    def get_errors(self):
        """Return the list of errors found."""
        return self.errors

    def reset_errors(self):
        """Reset the errors list."""
        self.errors = []          

    def check(self, file_path: Path):
        """
        Perform checks on the given NIfTI file.

        Parameters:
        - file_path (Path): Path to the NIfTI file to check.
        """
        self.logger.debug(f"Checking file: {file_path}")

        # Attempt to load the NIfTI file
        try:
            nii_img = nib.load(str(file_path))
            hdr = nii_img.header
        except Exception as e:
            self.errors.append(f"Failed to load NIfTI file: {e}")
            return None

        # Perform all checks
        self.check_data_shape(hdr)
        self.check_voxel_sizes(hdr)
        #self.check_data_type(hdr)
        self.check_units(hdr)
        self.check_qfac(hdr)
        #self.check_affine(nii_img)
        self.check_data_range(nii_img)
        self.check_sform_qform_codes(hdr)
        self.check_intent_codes(hdr)
        self.check_empty_data(nii_img)
        self.check_data_mean_range(nii_img)
        #self.check_image_orientation(hdr)
        # Add more checks as needed
        
        # Returning header to save some info in mapping
        return hdr
        
        
        



    def check_data_shape(self, hdr):
        """Check the data shape and dimensionality."""
        data_shape = np.array(hdr.get_data_shape())
        expected_shape_max = np.array(self.expected_values.get('data_shape_max'))
        expected_shape_min = np.array(self.expected_values.get('data_shape_min'))
        if len(data_shape) != 3:
            self.errors.append(f"Data is not 3D: Data shape is {data_shape}")
        else:
            # Check if data shape is within the expected range
            if not np.all((data_shape >= expected_shape_min) & (data_shape <= expected_shape_max)):
                self.errors.append(
                    f"Data shape mismatch: Expected between {expected_shape_min} and {expected_shape_max}, got {data_shape}"
                )

    def check_voxel_sizes(self, hdr):
        """Check the voxel dimensions."""
        voxel_sizes = hdr.get_zooms()[:3]  # Only spatial dimensions
        expected_voxel_sizes = self.expected_values.get('voxel_sizes')

        # Check if voxel sizes is less than expected values
        if not np.all(voxel_sizes <= expected_voxel_sizes):
            self.errors.append(f"Voxel size mismatch: Expected {expected_voxel_sizes}, got {voxel_sizes}")


    def check_data_type(self, hdr):
        """Check the data type of the image."""
        data_type = hdr.get_data_dtype()
        expected_data_type = self.expected_values.get('data_type')

        if expected_data_type:
            if data_type != np.dtype(expected_data_type):
                self.errors.append(f"Data type mismatch: Expected {expected_data_type}, got {data_type}")

    def check_units(self, hdr):
        """Check the units of measurement."""
        xyzt_units = hdr.get('xyzt_units')
        space_unit_code = int(xyzt_units) & 0x07  # Bits 0-2
        time_unit_code = int(xyzt_units) & 0x38   # Bits 3-5

        # Mapping unit codes to unit names
        unit_codes = {
            0: 'unknown',
            1: 'meter',
            2: 'mm',
            3: 'micron'
        }

        space_unit = unit_codes.get(space_unit_code, 'unknown')
        expected_space_unit = self.expected_values.get('space_unit', 'mm')

        if space_unit != expected_space_unit:
            self.errors.append(f"Spatial units mismatch: Expected '{expected_space_unit}', got '{space_unit}'")


    def check_qfac(self, hdr):
        """Check that pixdim[0] (qfac) is either 1 or -1."""
        qfac = hdr['pixdim'][0]
        expected_qfac = self.expected_values.get('qfac')
        if qfac not in expected_qfac:
            self.errors.append(f"Invalid qfac value: Expected Valies {expected_qfac}, got {qfac}")


    def check_affine(self, nii_img):
        """Check the affine transformation matrix."""
        affine = nii_img.affine
        expected_affine = self.expected_values.get('affine')

        if expected_affine is not None:
            if not np.allclose(affine, expected_affine):
                self.errors.append("Affine matrix does not match expected values.")



    def check_data_range(self, nii_img):
        """Check that the data values are within expected ranges."""
        data = nii_img.get_fdata()
        data_min = np.min(data)
        data_max = np.max(data)
        expected_min = self.expected_values.get('data_min')
        expected_max = self.expected_values.get('data_max')

        if expected_min is not None and data_min < expected_min:
            self.errors.append(f"Data minimum value {data_min} is less than expected minimum {expected_min}.")
        if expected_max is not None and data_max > expected_max:
            self.errors.append(f"Data maximum value {data_max} is greater than expected maximum {expected_max}.")

            

    def check_sform_qform_codes(self, hdr):
        """Check sform_code and qform_code are valid."""
        sform_code = hdr['sform_code']
        qform_code = hdr['qform_code']
        expected_sform_code = self.expected_values.get('sform_code')
        expected_qform_code = self.expected_values.get('qform_code')

        if expected_sform_code is not None and sform_code != expected_sform_code:
            self.errors.append(f"sform_code mismatch: Expected {expected_sform_code}, got {sform_code}")
        if expected_qform_code is not None and qform_code != expected_qform_code:
            self.errors.append(f"qform_code mismatch: Expected {expected_qform_code}, got {qform_code}")


    def check_intent_codes(self, hdr):
        """Check intent codes if applicable."""
        intent_code = hdr['intent_code']
        expected_intent_code = self.expected_values.get('intent_code')

        if expected_intent_code is not None and intent_code != expected_intent_code:
            self.errors.append(f"intent_code mismatch: Expected {expected_intent_code}, got {intent_code}")


    def check_empty_data(self, nii_img):
        """Check if the image data is empty or contains only zeros."""
        data = nii_img.get_fdata()
        if not np.any(data):
            self.errors.append("Image data is empty or contains only zeros.")

    
    def check_data_mean_range(self, nii_img):
        """Check that the data mean is within expected ranges."""
        data = nii_img.get_fdata()
        data_mean = np.mean(data)
        expected_mean_min = self.expected_values.get('data_mean_min')
        expected_mean_max = self.expected_values.get('data_mean_max')

        if data_mean < expected_mean_min:
            self.errors.append(f"Data mean value {data_mean} is less than expected minimum {expected_mean_min}.")
        if data_mean > expected_mean_max:
            self.errors.append(f"Data mean value {data_mean} is greater than expected maximum {expected_mean_max}.")
    
    def check_image_orientation(self, hdr):
        """Check the image orientation."""
        # Extract orientation information
        affine = hdr.get_best_affine()
        orientation = nib.aff2axcodes(affine)
        expected_orientation = self.expected_values.get('orientation')

        if expected_orientation:
            if tuple(map(str.upper, orientation)) != tuple(map(str.upper, expected_orientation)):
                self.errors.append(f"Image orientation mismatch: Expected {expected_orientation}, got {orientation}")
       
            


