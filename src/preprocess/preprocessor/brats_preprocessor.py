# src/preprocess/preprocessor/brats_preprocessor.py
import logging
from pathlib import Path
from utils.logging_setup import configure_session_logging
from preprocess.preprocessor.base_plugin import PreprocessorPlugin
from brainles_preprocessing.normalization.percentile_normalizer import PercentileNormalizer
from brainles_preprocessing.brain_extraction import HDBetExtractor
from brainles_preprocessing.modality import Modality
from brainles_preprocessing.preprocessor import Preprocessor
from brainles_preprocessing.constants import PreprocessorSteps
from brainles_preprocessing.registration import ANTsRegistrator


class BratsPreprocessor(PreprocessorPlugin):
    """
    Preprocessing pipeline similar to that of the BRATS dataset.

    Preprocessing steps include:
        1. Co-registration: Align moving modalities to the central modality (e.g., T1w if available).
        2. Atlas Registration: Align the central modality to a predefined atlas.
        3. Atlas Correction: Apply additional corrections in atlas space if specified.
        4. Brain Extraction: Extract the brain from the downloaded MRI.
        5. Normalization: Normalize image intensities.

    NOTE: Some downloaded MRIs have already undergone brain extraction.
          Brain extraction will be skipped for those datasets.
    """
    

    # Class-specific plugin name
    plugin_name = "brats"

    @classmethod
    def get_name(cls) -> str:
        return cls.plugin_name
    
    
    def __init__(self, dataset_settings: dict, dataset_path: Path, mapping: dict, config: dict):
        super().__init__(dataset_settings, dataset_path, mapping, config=config)
        
        
        self.logger = logging.getLogger(__name__)
        
        self.dataset_path = dataset_path

        self.download_dir_name = self.dataset_settings.get("downloadDirName")
        self.download_dir = dataset_path / self.download_dir_name
        
        # Output Diretcory
        self.output_dir_name =  self.dataset_settings.get("preprocessedDirName", "preprocessed")
        self.output_dir = dataset_path / self.output_dir_name
        
        # Preprocessor settings 
        self.brats_config = self.dataset_settings["preprocess"].get("brats", {})
        
        # Settings for skipping brain extraction. 
        self.skip_brain_extraction = self.brats_config.get("skipBrainExtraction", False)
        

    def run(self) -> bool:
        
        # Loop through entries in mapping
        for entry in self.mapping:
            
            # Get available modalities
            modalities = entry['mris'].keys()

            # Acquire the center modality based on preference
            center_mod_name = None
            for mod_pref in self.brats_config["modPriority"]:
                if mod_pref in modalities:
                    center_mod_name = mod_pref
                    break
            if not center_mod_name:
                self.logger.error(f"BRATS Preprocessor - No matching center modality found for entry {entry['subject']}")
                continue

            # Specify Intermediate output directories
            entry_out_dir = self.output_dir / f"{entry['subject']}.{entry['session']}.{entry['type']}.{entry['group']}"
            #raw_bet = entry_out_dir / "raw_bet"  # Raw Brain Extracted MRI
            
            # Note: Same file name is used for Dataset which skips brain extraction.
            # TODO: This should be improved.
            norm_bet = entry_out_dir / "norm_bet"  # Normalized Brain Extracted MRI
            #raw_skull = entry_out_dir / "raw_skull"  # Raw with Skull MRI
            #norm_skull = entry_out_dir / "norm_skull" # Normalized with Skull MRI
            
            temp_dir = entry_out_dir / "temp" # Temporary Directory
             
            # Initialize normalizer
            percentile_normalizer = PercentileNormalizer(
                lower_percentile=0.1,
                upper_percentile=99.9,
                lower_limit=0,
                upper_limit=1,
            )
            

            # Center + Other Modalities
            center_modality = None
            moving_modalities = []
            for mod_name in modalities:
                
                if self.skip_brain_extraction:
                    
                    mod_obj = Modality(
                        modality_name=mod_name,
                        input_path=self.download_dir / entry['download'][mod_name],
                        # Still Saving in norm_bet folder as already skull stripped
                        normalized_skull_output_path= norm_bet / f"{entry['mris'][mod_name].split('.')[0]}_raw_skull_{mod_name}.nii.gz",
                        atlas_correction=True,
                        normalizer=percentile_normalizer,
                    )
                
                else:
                    mod_obj = Modality(
                        modality_name=mod_name,
                        input_path=self.download_dir / entry['download'][mod_name],
                        #raw_bet_output_path=raw_bet / f"{entry['mris'][mod_name].split('.')[0]}_raw_bet_{mod_name}.nii.gz",
                        normalized_bet_output_path=norm_bet / f"{entry['mris'][mod_name].split('.')[0]}_norm_bet_{mod_name}.nii.gz",
                        #raw_skull_output_path= raw_skull / f"{entry['mris'][mod_name].split('.')[0]}_raw_skull_{mod_name}.nii.gz",
                        #normalized_skull_output_path=norm_skull / f"{entry['mris'][mod_name].split('.')[0]}_norm_skull_{mod_name}.nii.gz",
                        atlas_correction=True,
                        normalizer=percentile_normalizer,
                    )
                
                
                
                if mod_obj.modality_name == center_mod_name:
                    center_modality = mod_obj
                else:
                    moving_modalities.append(mod_obj)
                    
                all_modalities = moving_modalities + [center_modality]
            
            
            # Passing brain extractor as None If Skipping Required
            brain_extractor = None if self.skip_brain_extraction else HDBetExtractor()
            
            # Preprocessor Object
            preprocessor = Preprocessor(
                center_modality=center_modality,
                moving_modalities=moving_modalities,
                registrator=ANTsRegistrator(),
                brain_extractor=brain_extractor,
                temp_folder=temp_dir,
                limit_cuda_visible_devices="0",
            )
            
            # Preprocessor File Logging
            self.preprocessor_logger.info(f"BratsPreprocessor - Processing Subject: {entry['subject']}, Session: {entry['session']}")
            
            
            # Preprocessor Run   
            preprocessor.run(
                log_file=self.preprocessor_log_file
            )
            
            
            # This should be done by the Mapper
            """
            # Acquiring Preprocessed Images
            for mod in all_modalities:
                normalized_bet_output_path=norm_bet / f"{entry['mris'][mod.modality_name].split('.')[0]}_norm_bet_{mod.modality_name}.nii.gz"
                relative_path = normalized_bet_output_path.relative_to(self.output_dir)
                entry[self.dataset_path["preprocessDirName"]] = str(relative_path)
                pass
            """
            
            # Clean The Temp Dir 
            self._cleanup_temp_dir(temp_dir=temp_dir)
            
            # Preprocessor File Logging -Empty lines at the End
            self.preprocessor_logger.info("\n\n")
            
        return True
            
            
    # Just Remove .nii.gz from Temp Directory
    def _cleanup_temp_dir(self, temp_dir: Path) -> None:
        """
        Removes all .nii.gz files from the specified temporary directory.

        Args:
            temp_dir (Path): Path to the temporary directory.
        """
        if not temp_dir.exists():
            self.preprocessor_logger.warning(f"BratsPreprocessor - Temporary directory {temp_dir} does not exist. Skipping cleanup.")
            return

        self.preprocessor_logger.info(f"BratsPreprocessor - Cleaning up temporary directory: {temp_dir}")
        nii_files = list(temp_dir.rglob("*.nii.gz"))

        if not nii_files:
            self.preprocessor_logger.info("BratsPreprocessor - No .nii.gz files found in temporary directory.")
            return

        for nii_file in nii_files:
            try:
                nii_file.unlink()
            except Exception as e:
                self.preprocessor_logger.error(f"BratsPreprocessor - Failed to remove temporary file {nii_file}: {e}")