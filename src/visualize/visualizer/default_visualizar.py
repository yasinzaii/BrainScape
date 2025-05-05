# src/visualize/visualizer/default_visualizer.py
import logging

import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt

from pathlib import Path
from typing import Dict, Any, List

from .base_plugin import VisualizerPlugin

class DefaultVisualizer(VisualizerPlugin):
    """
    A default plugin for visualizing MRI volumes. .
    """
    
    # Class-specific plugin name
    plugin_name = "default_visualizer"
    
    @classmethod
    def get_name(cls) -> str:
        """Return the unique name of this plugin."""
        return cls.plugin_name
    
    def __init__(
        self,
        dataset_settings: Dict[str, Any],
        dataset_path: Path,
        mapping: List,
        config: Any
    ):
        """
        Initialize the DefaultVisualizerPlugin.

        Args:
            dataset_settings (Dict[str, Any]): Final merged settings for the dataset.
            dataset_path (Path): Path object pointing to the dataset root folder.
            mapping (list): Mappings of the dataset.
            config (OmegaConf): Main configuration object.
        """
        self.logger = logging.getLogger(__name__)
        
        self.dataset_settings = dataset_settings
        self.dataset_path = dataset_path
        self.mapping = mapping
        self.config = config
        
        # dataset visualize directory
        self.visualize_dir = self.dataset_path / self.config.visualizeDirName
        self.visualize_dir.mkdir(exist_ok=True, parents=True)
        
        # Path of the download directory
        self.download_dir_name = self.dataset_settings.get("downloadDirName")
        self.download_dir = dataset_path / self.download_dir_name
        
        # Path of the preprocessed directory
        self.preprocessed_dir_name = self.dataset_settings["preprocess"]["preprocessDirName"]
        self.preprocessed_dir_path = dataset_path / self.preprocessed_dir_name
    
    
    def _make_entry_output_dir(self, entry: Dict[str, Any]) -> Path:
        """
        Creates a directory for storing this entry's images.

        Args:
            entry (Dict[str, Any]): Info for a single subject/session.
        
        Returns:
            Path: The newly created directory.
        """
        subject = entry['subject']
        session = entry['session']
        entry_type = entry['type']
        group = entry['group']

        entry_out_dir_name = f"{subject}.{session}.{entry_type}.{group}"
        entry_out_dir = self.visualize_dir / entry_out_dir_name
        entry_out_dir.mkdir(parents=True, exist_ok=True)
        return entry_out_dir
    
    
    def run(self) -> bool:
        """
        Execute the visualization routine for the dataset.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Visualization for each entry in the dataset mapping
            for entry in self.mapping:

                # Prepare an output directory for this entry
                out_dir = self._make_entry_output_dir(entry)
                if not out_dir:
                    self.logger.error(f"DefaultVisualizerPlugin - Failed to create output dir for dataset:{self.dataset_path}, entry: {entry}")
                    return False
                
                # Original/Downloaded + Preprocessed modality images
                success = self._plot_and_save_entry(entry, out_dir)
                if not success:
                    self.logger.error(f"DefaultVisualizerPlugin - Failed to visualize entry, dataset:{self.dataset_path}, entry: {entry}")
                    return False
                
            return True
        
        except Exception as e:
            self.logger.error(f"DefaultVisualizerPlugin - Failed to complete visualization: {e}", exc_info=True)
            return False     
                    


    def _plot_and_save_entry(self, entry: Dict[str, Any], out_dir: Path) -> bool:
        """
        Load original and preprocessed NIfTI images, extract center slices, 
        and plot them side-by-side.

        Args:
            entry (Dict[str, Any]): Single mapping entry with paths for different modalities.
            out_dir (Path): Where the final figure should be stored.

        Returns:
            bool: True if the plotting/saving is successful.
        """
        
        subject = entry["subject"]
        session = entry["session"]
        entry_type = entry["type"]
        group = entry["group"]

        # Acquire all modalities
        modalities = entry["mris"].keys()
        
        # Gather slices for each modality
        download_slices = {}
        preprocessed_slices = {}
        
        for mod in modalities:
            
            # Original/Downloaded
            down_rel_path = entry["download"].get(mod)
            mri_path_down = self.download_dir / down_rel_path
            if not mri_path_down.exists():
                self.logger.error(f"DefaultVisualizerPlugin - Downloaded file does not exist: {mri_path_down}")
                return False

            # Preprocessed
            prep_rel_path = entry[self.preprocessed_dir_name].get(mod)
            mri_path_prep = self.preprocessed_dir_path / prep_rel_path
            if not mri_path_prep.exists():
                self.logger.error(f"DefaultVisualizerPlugin - Preprocessed file does not exist: {mri_path_prep}")
                return False

            # Load data
            try:
                data_down = nib.load(str(mri_path_down)).get_fdata()
                data_prep = nib.load(str(mri_path_prep)).get_fdata()
            except Exception as e:
                self.logger.error(f"DefaultVisualizerPlugin - Failed to load NIfTI data: {e}")
                return False

            # Get center slices
            download_slices[mod] = self._get_center_slices(data_down)
            preprocessed_slices[mod] = self._get_center_slices(data_prep)

        # Now, create the figure with subplots
        success = self._save_figure(
            subject, session, entry_type, group, 
            modalities, download_slices, preprocessed_slices, out_dir
        )
        return success
    
    
    def _get_center_slices(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Extract the center slice in each plane.

        Args:
            data (np.ndarray): 3D MRI volume data.
        
        Returns:
            Dict[str, np.ndarray]: The center slices in 'axial', 'coronal', and 'sagittal' planes.
        """
        slices = {}
        z_center = data.shape[2] // 2
        y_center = data.shape[1] // 2
        x_center = data.shape[0] // 2

        slices["axial"] = data[:, :, z_center]
        slices["coronal"] = data[:, y_center, :]
        slices["sagittal"] = data[x_center, :, :]
        return slices
    
    def _save_figure(
        self,
        subject: str,
        session: str,
        entry_type: str,
        group: str,
        modalities,
        download_slices,
        preprocessed_slices,
        out_dir: Path
    ) -> bool:
        """
        Generate and save the figure for original vs preprocessed images.
        """
        num_modalities = len(modalities)
        num_planes = 3  # axial, coronal, sagittal
        images_per_modality = num_planes
        num_cols = num_modalities * images_per_modality
        num_rows = 2  # Original images (row 0), preprocessed images (row 1)

        # Determine maximum image dimensions to scale the figure
        max_height, max_width = 0, 0
        for mod in modalities:
            for plane in ["axial", "coronal", "sagittal"]:
                slice_img = download_slices[mod][plane]
                h, w = slice_img.shape
                max_height = max(max_height, h)
                max_width = max(max_width, w)

        # Adjust figure size
        fig_width = (num_cols * max_width) / 50.0
        fig_height = (num_rows * max_height) / 50.0

        fig, axes = plt.subplots(
            num_rows, num_cols, figsize=(fig_width, fig_height), squeeze=False
        )

        # Plot
        for row_idx, img_type in enumerate(["original", "preprocessed"]):
            for mod_idx, mod in enumerate(modalities):
                for plane_idx, plane in enumerate(["axial", "coronal", "sagittal"]):
                    col_idx = mod_idx * images_per_modality + plane_idx
                    ax = axes[row_idx, col_idx]
                    if img_type == "original":
                        slice_img = download_slices[mod][plane]
                    else:
                        slice_img = preprocessed_slices[mod][plane]

                    ax.imshow(slice_img.T, cmap="gray", origin="lower")
                    ax.axis("off")
                    if row_idx == 0:
                        ax.set_title(f"{mod} {plane}")

        fig.subplots_adjust(wspace=0.2, hspace=0.2)
        fig.suptitle(f"{subject} | {session} | {entry_type} | {group}", fontsize=10)

        # Save figure
        out_filename = f"{subject}_{session}_{entry_type}_{group}.png".replace("/", "-")
        output_path = out_dir / out_filename

        try:
            plt.savefig(output_path, bbox_inches="tight")
            plt.close(fig)
        except Exception as e:
            self.logger.error(f"DefaultVisualizerPlugin - Failed to save figure to {output_path}: {e}")
            plt.close(fig)
            return False

        self.logger.debug(f"DefaultVisualizerPlugin - Saved visualization to {output_path}")

        return True