import os
import shutil
import random
import logging
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt
import nibabel as nib  # For loading MRI images
import json


from omegaconf import OmegaConf
from typing import Dict, Any, List
from utils.json_handler import JsonHandler
from utils.common_utils import merge_settings

# For Loading Preprocessor Plugins
from utils.plugin_loader import PluginLoader
from preprocess.preprocessor.base_plugin import PreprocessorPlugin



class VisualizerManager:
    
    def __init__(
        self,
        config: OmegaConf,
        target_datasets: List[str],
        default_dataset_settings: Dict[str, Any],
        mapping: Dict[str, Any],
    ):
        self.config = config
        self.target_datasets = target_datasets
        self.default_dataset_settings = default_dataset_settings
        self.mapping = mapping
        self.logger = logging.getLogger(__name__)

    def initiate_vis(self):
        for dataset_name in self.target_datasets:
            
            self.logger.info(f"Visualization Manager - Visualizing dataset: {dataset_name}")
            
            # Merging Default Settings with Dataset Settings.
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings = JsonHandler(dataset_path / self.config.datasetSettingsJson)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )
            
            # Acquiring the Mapping 
            dataset_mapping  = self.mapping[dataset_name]

            """
            # Acquiring Preprocessor Plugin Name
            try:
                preprocessor_name = final_settings['preprocess']['preprocessor']
            except KeyError as e:
                self.logger.error(f"Preprocessor (Key: 'preprocessor') missing from dataset '{dataset_name}' settings. Skipping preprocessing. Error: {e}")
                continue  # Skip to the next dataset

            # Check if preprocessing is already done
            if final_settings.get("isPreprocessed", False):
                self.logger.info(f"Dataset '{dataset_name}' is already preprocessed. Skipping.")
                continue

            # Get the preprocessor plugin class
            preprocessor_cls = self.plugin_loader.get_plugin_by_name(preprocessor_name)
            if not preprocessor_cls:
                self.logger.error(f"Requested preprocessor plugin '{preprocessor_name}' not found. Skipping dataset '{dataset_name}'.")
                continue

            # Initialize the preprocessor
            preprocessor = preprocessor_cls(dataset_settings=final_settings, dataset_path=dataset_path, mapping=mapping, config=self.config)

            # Perform preprocessing
            success = preprocessor.run()
            if success:
                self.logger.info(f"Preprocessing completed for dataset '{dataset_name}'. Updating 'isPreprocessed' flag.")
                dataset_settings.update_json({"isPreprocessed": True}).save_json()
            else:
                self.logger.error(f"Preprocessing failed for dataset '{dataset_name}'.")
                dataset_settings.update_json({"isPreprocessed": False}).save_json()
            """
            
            # Initialize and run the visualizer
            visualizer = Visualizer(
                dataset_settings=final_settings,
                dataset_path=dataset_path,
                mapping=dataset_mapping,
                config=self.config,
            )

            success = visualizer.run()
            if success:
                self.logger.info(f"Visualization completed for dataset '{dataset_name}'.")
            else:
                self.logger.error(f"Visualization failed for dataset '{dataset_name}'.")


class Visualizer():
    
    # Class-specific plugin name
    plugin_name = "visualizer"

    @classmethod
    def get_name(cls) -> str:
        return cls.plugin_name
    
    
    def __init__(self, dataset_settings: dict, dataset_path: Path, mapping: dict, config: OmegaConf):

        
        self.logger = logging.getLogger(__name__)
        
        self.dataset_settings = dataset_settings
        self.dataset_path = dataset_path
        self.mapping = mapping 
        self.config = config

        self.visualize_dir_name = "visualize"
        self.visualize_dir = dataset_path / self.visualize_dir_name
        self.visualize_dir.mkdir(exist_ok=True, parents=True)
        
        # Path of the download directory
        self.download_dir_name = self.dataset_settings.get("downloadDirName")
        self.download_dir = dataset_path / self.download_dir_name
        
        # Path of the preprocessed directory
        self.preprocessed_dir_name = self.dataset_settings["preprocess"]["preprocessDirName"]
        self.preprocessed_dir_path = dataset_path / self.preprocessed_dir_name
        
        # Path to the main visualization directory
        self.summary_vis_path = Path("Visualize/") / Path(dataset_path).name
        
        if self.summary_vis_path.exists():
            if self.summary_vis_path.is_dir():
                shutil.rmtree(self.summary_vis_path)
                self.logger.info(f"Existing directory '{self.summary_vis_path}' removed.")
            else:
                raise NotADirectoryError(f"The path '{self.summary_vis_path}' exists and is not a directory.")
        
        self.summary_vis_path.mkdir(exist_ok=True, parents=True)
        self.logger.info(f"Directory '{self.summary_vis_path}' created fresh.")
        
    def run(self) -> bool:
        
        # Randomly choose 10 groups
        rand_mapping = random.sample(self.mapping, 10)
        rand_record = {} # [subject][download/preprocessed][modality][slices] 
        
        rand_mapping_mris = [item['mris'] for item in rand_mapping]
        
        # Loop through entries in mapping
        for entry in self.mapping:
            
            save_record = False
            if entry['mris'] in rand_mapping_mris:
                save_record = True
             
            
            # Get avaliable modalities
            modalities = entry['mris'].keys()
            
            # Specify Intermediate output directories
            entry_out_dir = self.visualize_dir / f"{entry['subject']}.{entry['session']}.{entry['type']}.{entry['group']}"
            entry_out_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare data structures for original and preprocessed images
            download_slices = {}  # modality -> plane -> slice
            preprocessed_slices = {}
            for mod in modalities:
                
                
                #TODO - MATCH NAME of DOWNLOAD DIRECTORY AND DOWNLOAD INDEX
                # dir - "Download" <- self.download_dir
                # idx - "download" 
                
                # Get the Downloaded/Orignal MRI file path from Download Mapping
                mri_rel_path_down = entry["download"][mod]
                mri_path_down = self.download_dir / mri_rel_path_down
                
                # Load the MRI image
                if not mri_path_down.exists():
                    self.logger.error(f"Visualizer - MRI file {mri_path_down} does not exist. Skipping entry.")
                    break
                img_down = nib.load(str(mri_path_down))
                data_down = img_down.get_fdata()
                
                # Get the center slices for original image
                slices_down = self.get_center_slices(data_down)
                download_slices[mod] = slices_down
                
                # Get the MRI file path from the preprocessed mapping
                mri_rel_path_prep = entry[self.preprocessed_dir_name][mod]
                mri_path_prep = self.preprocessed_dir_path / mri_rel_path_prep
            
                # Load the MRI image
                if not mri_path_prep.exists():
                    self.logger.error(f"Visualizer - MRI file {mri_path_prep} does not exist. Skipping entry.")
                    break
                img_prep = nib.load(str(mri_path_prep))
                data_prep = img_prep.get_fdata()
                
                
                # Get the center slices for preprocessed image
                slices_prep = self.get_center_slices(data_prep)
                preprocessed_slices[mod] = slices_prep
                
                # Update Rand Record
                if save_record:
                    rand_record[entry['subject']] = {'download':{mod: slices_down}, 
                                                     'preprocessed':{mod: slices_prep}}

            # Now, create the figure and plot the images
            num_modalities = len(modalities)
            num_planes = 3  # axial, coronal, sagittal
            images_per_modality = num_planes 
            num_cols = num_modalities * images_per_modality
            num_rows = 2  # Original images on top row, preprocessed images on bottom row
            
            # Determine the maximum image dimensions to set figure size appropriately
            max_height = max_width = 0
            for mod in modalities:
                for plane in ['axial', 'coronal', 'sagittal']:
                    slice_img_original = download_slices[mod][plane]
                    height, width = slice_img_original.shape
                    max_height = max(max_height, height)
                    max_width = max(max_width, width)
            
            # Calculate figure size
            fig_width = (num_cols * max_width) / 50  # Adjust scaling factor as needed
            fig_height = (num_rows * max_height) / 50
            
            
            # Create figure and axes
            fig, axes = plt.subplots(num_rows, num_cols, figsize=(fig_width, fig_height), squeeze=False)
            
            
            # Now plot the images
            for row_idx, img_type in enumerate(['original', 'preprocessed']):
                for mod_idx, mod in enumerate(modalities):
                    for plane_idx, plane in enumerate(['axial', 'coronal', 'sagittal']):
                        # Calculate the column index
                        col_idx = mod_idx * images_per_modality + plane_idx
                        ax = axes[row_idx, col_idx]
                        if img_type == 'original':
                            slice_img = download_slices[mod][plane]
                        else:
                            slice_img = preprocessed_slices[mod][plane]
                        ax.imshow(slice_img.T, cmap='gray', origin='lower')
                        ax.axis('off')
                        if row_idx == 0:
                            ax.set_title(f'{mod} {plane}')
                
            fig.subplots_adjust(wspace=0.2, hspace=0.2)
            fig.suptitle(f"{entry['subject']} {entry['session']} {entry['type']} {entry['group']}", fontsize=12)
            
            # Save the figure
            fileName = f"{entry['subject']}_{entry['session']}_{entry['type']}_{entry['group']}.png".replace("/", "-")
            output_filename = entry_out_dir / fileName
            plt.savefig(output_filename, bbox_inches='tight')
            plt.close(fig)
            
            # Copying the visualization file to the Summary Visualization Folder
            if save_record:
                shutil.copyfile(src=output_filename, dst=self.summary_vis_path/output_filename.name)
            
            self.logger.debug(f"Saved visualization to {output_filename}")

            
        # Plot Summary Figs
        # TODO - maybe creating a seperate imge per subject per dataset is better.
        #self.plot_rand_record(rand_record=rand_record, output_path=self.summary_vis_path)
        
        # Collect stats
        num_subjects = len(set(entry['subject'] for entry in self.mapping))
        num_sessions = len(set((entry['subject'], entry['session']) for entry in self.mapping))
        num_mris = len(self.mapping)
        modalities = set()
        for entry in self.mapping:
            modalities.update(entry.get('mris', {}).keys())

        # Save stats
        stats_file = self.summary_vis_path / 'stats.txt'
        with open(stats_file, 'w') as f:
            f.write(f"Dataset: {self.dataset_path.name}\n")
            f.write(f"Number of subjects: {num_subjects}\n")
            f.write(f"Number of sessions: {num_sessions}\n")
            f.write(f"Number of multi-modal MRIs: {num_mris}\n")
            f.write(f"Modalities: {', '.join(sorted(modalities))}\n")
        
        return True    
        

    def plot_rand_record(self, rand_record, output_path, num_subjects_to_plot=None):
        """
        Plot images from rand_record as per the specified layout.
        
        Parameters:
        - rand_record: Dictionary containing image data.
        - output_path: Path to save the output plot.
        - num_subjects_to_plot: Number of subjects to include in the plot.
        """
        
        if output_path.exists():
            if output_path.is_dir():
                shutil.rmtree(output_path)
                self.logger.info(f"Existing directory '{output_path}' removed.")
            else:
                raise NotADirectoryError(f"The path '{output_path}' exists and is not a directory.")
        
        output_path.mkdir(exist_ok=True, parents=True)
        self.logger.info(f"Directory '{output_path}' created fresh.")
        
        try:
            # If num_subjects_to_plot is None, plot all subjects
            subjects = list(rand_record.keys())
            if num_subjects_to_plot is not None and num_subjects_to_plot < len(subjects):
                subjects = subjects[:num_subjects_to_plot]
            else:
                num_subjects_to_plot = len(subjects)
            
            # Collect data and determine modalities and planes
            all_modalities = set()
            all_planes = ['axial', 'coronal', 'sagittal']
            
            # Collect modalities
            for subject in subjects:
                modalities = rand_record[subject]['download'].keys()
                all_modalities.update(modalities)
            all_modalities = sorted(all_modalities)
            num_modalities = len(all_modalities)
            
            # Define figure dimensions
            images_per_modality = len(all_planes)
            num_cols = num_modalities * images_per_modality
            num_rows = num_subjects_to_plot * 2  # Each subject has two rows
            
            # Set figure size
            fig_width = num_cols * 3  # Adjust scaling factor as needed
            fig_height = num_rows * 3
            
            # Create figure and axes
            fig, axes = plt.subplots(num_rows, num_cols, figsize=(fig_width, fig_height), squeeze=False)
            
            for subj_idx, subject in enumerate(subjects):
                subject_data = rand_record[subject]
                # Get the modalities available for this subject
                modalities = sorted(subject_data['download'].keys())
                
                # Calculate row indices for this subject
                row_start = subj_idx * 2  # Original images row
                row_end = row_start + 1   # Preprocessed images row
                
                # Plot images for each modality and plane
                for mod_idx, mod in enumerate(all_modalities):
                    if mod in modalities:
                        for plane_idx, plane in enumerate(all_planes):
                            col_idx = mod_idx * images_per_modality + plane_idx
                            
                            # Original image
                            ax_orig = axes[row_start, col_idx]
                            slice_img_orig = subject_data['download'][mod][plane]
                            ax_orig.imshow(slice_img_orig.T, cmap='gray', origin='lower')
                            ax_orig.axis('off')
                            
                            # Preprocessed image
                            ax_prep = axes[row_end, col_idx]
                            slice_img_prep = subject_data['preprocessed'][mod][plane]
                            ax_prep.imshow(slice_img_prep.T, cmap='gray', origin='lower')
                            ax_prep.axis('off')
                            
                            # Set titles on the top row
                            if row_start == 0:
                                ax_orig.set_title(f'{mod} {plane}')
                    else:
                        # If modality is not available for this subject, leave the space blank
                        for plane_idx in range(len(all_planes)):
                            col_idx = mod_idx * images_per_modality + plane_idx
                            axes[row_start, col_idx].axis('off')
                            axes[row_end, col_idx].axis('off')
                
                # Add subject labels
                axes[row_start, 0].set_ylabel(f"Subject: {subject}\nOriginal", rotation=0, size='large', labelpad=80)
                axes[row_end, 0].set_ylabel("Preprocessed", rotation=0, size='large', labelpad=80)
            
            # Adjust layout
            fig.subplots_adjust(wspace=0.1, hspace=0.1)
            fig.suptitle(f"Visualization of {num_subjects_to_plot} Subjects", fontsize=16)
            
            # Save the figure
            plt.savefig(output_path, bbox_inches='tight')
            plt.close(fig)
            
            self.logger.info(f"Saved summary visualization to {output_path}")
            
        except Exception as e:
            self.logger.error(f"An error occurred during plotting: {e}")
            raise


 
        
        
        
    """                # Determine the maximum image dimensions to set figure size appropriately
                max_height = max_width = 0
                for plane in ['axial', 'coronal', 'sagittal']:
                    slice_img = slices[plane]
                    height, width = slice_img.shape
                    max_height = max(max_height, height)
                    max_width = max(max_width, width)

                num_rows = 1 #len(images_list)
                modalities = sorted(modalities)
                num_modalities = len(modalities)
                num_planes = 3  # axial, coronal, sagittal
                images_per_modality = num_planes 
                num_cols = num_modalities * images_per_modality
                
                # Calculate figure size
                fig_width = (num_cols * max_width) / 100  # Adjust scaling factor as needed
                fig_height = (num_rows * max_height) / 100
                
                # Create figure and axes
                fig, axes = plt.subplots(num_rows, num_cols, figsize=(fig_width, fig_height))
                
                col_idx = 0
                for plane in ['axial', 'coronal', 'sagittal']:
                    ax = axes[col_idx]
                    slice_img = slices[plane]
                    ax.imshow(slice_img.T, cmap='gray', origin='lower')
                    ax.axis('off')
                    col_idx += 1
                    
                fig.subplots_adjust(wspace=0, hspace=0)
                fig.suptitle(mri_path.name, fontsize=16)
                
                
            
                
        
        
        # Collect stats
        num_subjects = len(set(entry['subject'] for entry in self.mapping))
        num_sessions = len(set((entry['subject'], entry['session']) for entry in self.mapping))
        num_mris = len(self.mapping)
        modalities = set()
        for entry in self.mapping:
            modalities.update(entry.get('mris', {}).keys())

        # Save stats
        stats_file = self.visualize_dir / 'stats.txt'
        with open(stats_file, 'w') as f:
            f.write(f"Dataset: {self.dataset_path.name}\n")
            f.write(f"Number of subjects: {num_subjects}\n")
            f.write(f"Number of sessions: {num_sessions}\n")
            f.write(f"Number of MRIs: {num_mris}\n")
            f.write(f"Modalities: {', '.join(sorted(modalities))}\n")
            
            
            
        return True

    """


    def get_center_slices(self, data):
        """
        Get the center slice from the MRI data in each plane.
        """
        slices = {}
        # Axial plane
        z_center = data.shape[2] // 2
        slices['axial'] = data[:, :, z_center]

        # Coronal plane
        y_center = data.shape[1] // 2
        slices['coronal'] = data[:, y_center, :]

        # Sagittal plane
        x_center = data.shape[0] // 2
        slices['sagittal'] = data[x_center, :, :]

        return slices


def plot_mri_slices(images_list, modalities):
    """
    Plot the MRI slices as per the specified layout.

    Args:
        images_list (list): A list of dictionaries containing slices for each MRI.
                            Each item corresponds to one MRI and contains a dict of modalities.
        modalities (set): The set of modality names.

    Returns:
        matplotlib.figure.Figure: The figure containing the plotted images.
    """
    num_rows = len(images_list)
    modalities = sorted(modalities)
    num_modalities = len(modalities)
    num_planes = 3  # axial, coronal, sagittal
    slices_per_plane = 3  # 3 slices per plane
    images_per_modality = num_planes * slices_per_plane
    num_cols = num_modalities * images_per_modality

    # Determine the maximum image dimensions to set figure size appropriately
    max_height = max_width = 0
    for mri_slices in images_list:
        for modality in modalities:
            slices = mri_slices[modality]
            for plane in ['axial', 'coronal', 'sagittal']:
                for slice_img in slices[plane]:
                    height, width = slice_img.shape
                    max_height = max(max_height, height)
                    max_width = max(max_width, width)

    # Calculate figure size
    fig_width = (num_cols * max_width) / 100  # Adjust scaling factor as needed
    fig_height = (num_rows * max_height) / 100

    # Create figure and axes
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(fig_width, fig_height))

    # Ensure axes is 2D
    if num_rows == 1:
        axes = np.expand_dims(axes, axis=0)
    if num_cols == 1:
        axes = np.expand_dims(axes, axis=1)

    for row_idx, mri_slices in enumerate(images_list):
        col_idx = 0
        for modality in modalities:
            slices = mri_slices[modality]
            for plane in ['axial', 'coronal', 'sagittal']:
                for slice_img in slices[plane]:
                    ax = axes[row_idx, col_idx]
                    ax.imshow(slice_img.T, cmap='gray', origin='lower')
                    ax.axis('off')
                    if row_idx == 0:
                        ax.set_title(f"{modality} - {plane.capitalize()}", fontsize=8)
                    col_idx += 1

    fig.subplots_adjust(wspace=0, hspace=0)
    fig.suptitle(f"Visualization of 10 Random MRIs with All Modalities", fontsize=16)
    return fig

# Example usage:
if __name__ == "__main__":
    # Assuming you have a configuration object and default settings
    from omegaconf import OmegaConf

    # Load your configuration
    config = OmegaConf.load('config.yaml')  # Replace with your config file path
    datasets_folder = config.pathDataset
    default_dataset_settings = {
        # Include your default dataset settings here
    }

    visualize_mri_images(config, datasets_folder, default_dataset_settings)
