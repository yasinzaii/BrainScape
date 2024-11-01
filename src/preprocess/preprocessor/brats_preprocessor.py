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
        
        # Temp Directory
        self.temp_dir_name = self.dataset_settings.get("tempDirName", "preprocessed")
        self.temp_dir = self.dataset_path / self.temp_dir_name
        
        # Preprocessor settings (if any)
        self.brats_config = self.dataset_settings["preprocess"].get("brats", {})
        
        # Processor Logger configuration
        self.preprocessor_log_file = self.output_dir / "preprocess.log"
        self.preprocessor_logger = configure_session_logging(
            session_log_file=self.preprocessor_log_file,
            log_config_path=self.config.logger_config_file,
            logger_name=f'preprocess.{self.download_dir_name}',
        )

    def run(self) -> bool:
        
        # Loop through entries in mapping
        for entry in self.mapping:
            
            # Get avaliable modalities
            modalities = entry['mris'].keys()

            # Aquire the ceter modality based on preference
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
            norm_bet = entry_out_dir / "norm_bet"  # Nomalized Brain Extracted MRI
            #raw_skull = entry_out_dir / "raw_skull"  # Raw with Skull MRI
            #norm_skull = entry_out_dir / "norm_skull" # Normalized with Skull MRI
            
            temp_dir = entry_out_dir / "temp" # Temperor Directory
             
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
            
            # Preprocessor Object
            preprocessor = Preprocessor(
                center_modality=center_modality,
                moving_modalities=moving_modalities,
                registrator=ANTsRegistrator(),
                brain_extractor=HDBetExtractor(),
                temp_folder=temp_dir,
                limit_cuda_visible_devices="0",
            )
            
            # Preprocessor File Logging
            self.preprocessor_logger.info(f"Processing Subject: {entry['subject']}, Session: {entry['session']}")
            
            
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
            self.preprocessor_logger.warning(f"Temporary directory {temp_dir} does not exist. Skipping cleanup.")
            return

        self.preprocessor_logger.info(f"Cleaning up temporary directory: {temp_dir}")
        nii_files = list(temp_dir.rglob("*.nii.gz"))

        if not nii_files:
            self.preprocessor_logger.info("No .nii.gz files found in temporary directory.")
            return

        for nii_file in nii_files:
            try:
                nii_file.unlink()
            except Exception as e:
                self.preprocessor_logger.error(f"Failed to remove temporary file {nii_file}: {e}")