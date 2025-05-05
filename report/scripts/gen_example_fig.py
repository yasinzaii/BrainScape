import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path





def generate_multimodal_figure(datasetDir, out_figure_path):
    
    target_height = 210
    target_width  = 185
        
    selected_subjects = [
        {
            "label": "QTAB",
            "t1w": "QTAB/preprocessed/sub-0166.ses-01.anat.0/norm_bet/sub-0166_ses-01_UNIT1_denoised_norm_bet_t1w.nii.gz",
            "t2w": "QTAB/preprocessed/sub-0166.ses-01.anat.0/norm_bet/sub-0166_ses-01_T2w_norm_bet_t2w.nii.gz",
            "flair": "QTAB/preprocessed/sub-0166.ses-01.anat.0/norm_bet/sub-0166_ses-01_FLAIR_norm_bet_flair.nii.gz",
            "demographics": {
                "participant_id": "sub-0166",
                "age": "10",
                "sex": "female",
                "handedness": "R"
            }
        },
        {
            "label": "MPLMBB",
            "t1w": "MPLMBB/preprocessed/sub-010254.ses-01.anat.0/norm_bet/sub-010254_ses-01_acq-mp2rage_T1w_norm_bet_t1w.nii.gz",
            "t2w": "MPLMBB/preprocessed/sub-010254.ses-01.anat.0/norm_bet/sub-010254_ses-01_T2w_norm_bet_t2w.nii.gz",
            "flair": "MPLMBB/preprocessed/sub-010254.ses-01.anat.0/norm_bet/sub-010254_ses-01_acq-highres_FLAIR_norm_bet_flair.nii.gz",
            "demographics": {
                "participant_id": "sub-010254",
                "sex": "male",
                "age_group": "65-70"
            }
        },
        {
            "label": "ARCD",
            "t1w": "ARCD/preprocessed/sub-M2239.ses-1609.anat.0/norm_bet/sub-M2239_ses-1609_acq-tfl3p2_run-3_T1w_norm_bet_t1w.nii.gz",
            "t2w": "ARCD/preprocessed/sub-M2239.ses-1609.anat.0/norm_bet/sub-M2239_ses-1609_acq-spc3p2_run-4_T2w_norm_bet_t2w.nii.gz",
            "flair": "ARCD/preprocessed/sub-M2239.ses-1609.anat.0/norm_bet/sub-M2239_ses-1609_acq-spcir2_run-5_FLAIR_norm_bet_flair.nii.gz",
            "demographics": {
                "participant_id": "sub-M2239",
                "sex": "male",
                "age": "40",
                "race": "1",
                "stroke": "Y"
            }
        }
    ]

    num_subjects = len(selected_subjects)
    modalities = ["t1w", "t2w", "flair"]
    orientations = ["axial", "coronal", "sagittal"]
    
    plt.ion()
                    
    fig, axes = plt.subplots(
        nrows=num_subjects, ncols=len(modalities) * len(orientations),
        figsize=(16, 2 * num_subjects), 
        squeeze=False
    )
    
    
    # Loop through each subject (row)
    for row_idx, subject_info in enumerate(selected_subjects):
        subject_label = subject_info["label"]
        
        # For each modality: T1w, T2w, FLAIR
        for mod_idx, mod in enumerate(modalities):
            if mod not in subject_info:
                continue  # Skip if path isn't provided

            img_path = Path(datasetDir)/subject_info[mod]
            if not img_path.exists():
                print(f"Warning: File {img_path} not found for subject {subject_label}. Skipping.")
                continue

            # Load the image data
            nib_image = nib.load(str(img_path))
            oriented_img = nib.as_closest_canonical(nib_image)  # Ensure consistent orientation
            #oriented_img = nib_image
            data = oriented_img.get_fdata()

            # Simple min-max normalization for visualization
            # data_min, data_max = data.min(), data.max()
            # norm_data = (data - data_min) / (data_max - data_min + 1e-9)
            norm_data = data 
            
            # Get the middle indices for each dimension
            mid_x = data.shape[0] // 2
            mid_y = data.shape[1] // 2
            mid_z = data.shape[2] // 2

            # For each orientation (axial, coronal, sagittal), we pick the center slice
            for ori_idx, ori in enumerate(orientations):
                col_idx = mod_idx * len(orientations) + ori_idx  # which column in the row
                ax = axes[row_idx, col_idx]

                if ori == "axial":
                    slice_img = norm_data[:, :, mid_z]
                    slice_img = np.rot90(slice_img, k=-1) 
                    slice_img = _padd_y_axis(slice_img, target_height)
                    slice_img = center_crop_width(slice_img, target_width) 
                elif ori == "coronal":
                    slice_img = norm_data[:, mid_y, :]
                    slice_img = np.rot90(slice_img, k=-1)
                    slice_img = _padd_y_axis(slice_img, target_height) 
                    slice_img = center_crop_width(slice_img, target_width)  
                else:  # "sagittal"
                    slice_img = norm_data[mid_x, :, :]
                    slice_img = np.rot90(slice_img, k=-1)
                    slice_img = _padd_y_axis(slice_img, target_height)  
                    slice_img = center_crop_width(slice_img, target_width) 

                ax.imshow(slice_img, cmap="gray", origin="lower")
                ax.axis("off")

                # Create a concise label: e.g. "Subject1: T1w (Axial)"
                # Only label top row or left column as you prefer. 
                # Here we label the top for each column in row 0, 
                # and left side for each row's first column, but adjust as you like:
                if row_idx == 0:
                    ax.set_title(f"{mod.upper()} ({ori.capitalize()})", fontsize=14)
                if col_idx == 0:
                    ax.text(-0.2, 0.5, subject_label, va="center", ha="right", 
                            fontsize=20, rotation=90, transform=ax.transAxes)
                
                plt.draw()
                
    plt.tight_layout()
    fig.savefig(out_figure_path, dpi=300)
    plt.close(fig)
    print(f"Multi-modal figure generated: {out_figure_path}")
    
import numpy as np

def _padd_y_axis(img, target_height, fill_color=0):
    arr = np.array(img)
    h, w = arr.shape[:2]
    
    y_center = h // 2
    half = target_height // 2
    top = y_center - half
    bottom = top + target_height

    pad_top = 0
    pad_bottom = 0
    if top < 0:
        pad_top = -top
        top = 0
        bottom = target_height
    new_h = h + pad_top
    if bottom > new_h:
        pad_bottom = bottom - new_h

    padded = np.pad(arr, ((pad_top, pad_bottom), (0, 0)), mode='constant', constant_values=fill_color)
    cropped = padded[top:top+target_height, :]
    return cropped

def center_crop_width(arr, target_width):
    h, w = arr.shape[:2]
    
    # Ensure the target width is valid
    if target_width > w:
        raise ValueError("Target width cannot be greater than the image width.")
    
    # Calculate the left and right indices for cropping
    center = w // 2
    half = target_width // 2
    left = center - half
    right = left + target_width
    return arr[:, left:right]
 