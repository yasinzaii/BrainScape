
import logging

from pathlib import Path
from typing import Dict, Any, List

from utils.json_handler import JsonHandler
from dataset.mapper.base_plugin import DatasetMapperPlugin

log = logging.getLogger(__name__)


class ScannerMapper(DatasetMapperPlugin):
    """
    Extracts MRI-scanner info (“Manufacturer”, “ManufacturersModelName”)
    from BIDS-style Datasets and injects it into the existing mapping.
    """
    
    # Class-specific plugin name
    plugin_name = "ScannerMapper"

    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name


    def __init__(self,
                 dataset_settings: Dict[str, Any],
                 dataset_path: str):
        """
        Initializes the ScannerMapper.

        Args:
            dataset_settings (Dict[str, Any]): Configuration/settings for the dataset.
            dataset_path (str): Path to target dataset. 
        """
        self.dataset_settings = dataset_settings
        self.dataset_path = Path(dataset_path)
        self.download_dir = self.dataset_path / dataset_settings["downloadDirName"]

        self.fields: List[str] = dataset_settings.get(
            "scannerFields",
            ["Manufacturer", "ManufacturersModelName", "MagneticFieldStrength"]
        )

        # If root level T1w.json, T2w.json or FLAIR.json avaliable
        self.has_scanner_info = False
        all_modalities = {"t1w.json", "t2w.json", "flair.json"}
        self.root_scanner_info: Dict[str, Dict[str, Any]] = {}

        for jf in self.download_dir.glob("*.json"):
            if jf.name.lower() not in all_modalities:
                continue
            try:
                raw     = JsonHandler(str(jf)).get_data()
                cleaned = {k: raw.get(k, "") for k in self.fields}
                
                if any(v for v in cleaned.values()):
                    self.has_scanner_info = True

                self.root_scanner_info[jf.stem.lower()] = cleaned  # "t1w" → {...}
                log.debug(f"ScannerMapper - cached root JSON {jf.name}")
            except Exception as exc:
                log.error(f"ScannerMapper - could not parse {jf}: {exc}")


    @staticmethod
    def _nifti_to_json(path: Path) -> Path:
        """
        Convert a NIfTI path (…nii or …nii.gz) to its matching .json
        regardless of how many suffixes it carries.
        """
        p = path
        while p.suffix:
            if p.suffix.lower() in {".nii", ".gz"}:
                p = p.with_suffix("") 
            else:
                break
        return p.with_suffix(".json") 
    


    def _find_scanner_info(self, nifti_rel: str, modality: str) -> Dict[str, Any]:
        """
        Try finding sibling JSON for NifTi, if not avaliable  
        fallback to cached root-level JSON for that modality
        """
        sib_json = self.download_dir / self._nifti_to_json(Path(nifti_rel))
        meta     = {}
        
        if sib_json.is_file():
            try:
                meta = JsonHandler(str(sib_json)).get_data()
            except Exception as exc:
                log.warning(f"ScannerMapper - cannot read {sib_json}: {exc}")
        
        if any(meta.get(k, "") for k in self.fields):    
            self.has_scanner_info = True
            return {k: meta.get(k, "") for k in self.fields}
        else: #fallback
            return self.root_scanner_info.get(modality.lower(), {})
        

    def map(self, existing_mapping: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        updated_mapping = []
        for entry in existing_mapping:
            scanner_block: Dict[str, Dict[str, str]] = {}

            for modality, rel_path in entry.get("download", {}).items():
                scanner_info = self._find_scanner_info(rel_path, modality)
                scanner_block[modality] = scanner_info

            entry["scanner"] = scanner_block
            updated_mapping.append(entry)

        if self.has_scanner_info:
            log.info(f"ScannerMapper - attached scanner info to {self.dataset_path.name} mapping rows")
        else:
            log.info(f"ScannerMapper - unable to attach scanner info to {self.dataset_path.name} mapping rows")
        return updated_mapping

