import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from brainles_preprocessing.normalization.percentile_normalizer import PercentileNormalizer
from PIL import Image, ImageOps


def generate_dropped_mris_figure(datasetDir, out_figure_path):
    """Generate and save figure of problematic MRIs."""
    label_mris = [
        {"label": "Motion Artifact",       "path": datasetDir / "ABIDE/Download/UM_50309/anat/NIfTI/mprage.nii.gz",       "slice_index": 62 , "y_center": 180},
        {"label": "Gibbs Ringing Artifact",   "path": datasetDir / "ABIDE2/Download/GU_28823_1/anat_1/NIfTI-1/anat.nii.gz", "slice_index": 158, "y_center": 180},
        {"label": "Poorly Extracted Brain", "path": datasetDir / "ADHD200/Download/WashU_15002_1/anat_1/NIfTI/rest.nii.gz","slice_index": 139, "y_center": 180},
        {"label": "Poorly defaced MRI",  "path": datasetDir / "SDIOA/Download/sub-12034/anat/sub-12034_T1w.nii",       "slice_index": 123, "y_center": 190},
        {"label": "Voids",                 "path": datasetDir / "OIAStudy/Download/sub-2509/anat/sub-2509_T1w.nii.gz",    "slice_index": 170, "y_center": 180}
    ]

    fig = plot_problematic_mris(label_mris, fig_width=12, fig_height=3.6)
    fig.savefig(out_figure_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none', transparent=False)


    #plt.show()
    print(f"Artifacts Figure successfully generated at {out_figure_path}")
    
    return fig


def plot_problematic_mris(
        mri_dicts, 
        fig_width=12, 
        fig_height=8, 
        img_width = 300,
        img_height = 420,
        alphabetical_labels=("A", "B", "C", "D", "E")
    ):
    """Plot five MRIs side by side."""
    if len(mri_dicts) != 5:
        raise ValueError("Provide exactly 5 MRI dictionaries.")
    fig, axes = plt.subplots(1, 5, figsize=(fig_width, fig_height))
    norm = PercentileNormalizer(lower_percentile=0.1, upper_percentile=99.9, lower_limit=0, upper_limit=1)

    for idx, info in enumerate(mri_dicts):
        label_label = info["label"]
        file_path = info["path"]
        slice_index = info["slice_index"]
        y_center = info["y_center"]
        
        nib_image = nib.load(file_path)
        oriented_img = nib.as_closest_canonical(nib_image)
        data = oriented_img.get_fdata()
        slice_img = np.array(norm.normalize(get_axial_slice(data, slice_index))).T

        img = Image.fromarray(np.uint8(slice_img * 255), 'L')
        cropped = _smart_crop(img, threshold=1, margin=10)
        resized = _resize_to_width(cropped, img_width)
        final_img = _padd_y_axis(resized, img_height, y_center)

        axes[idx].imshow(final_img, cmap='gray', origin='lower')
        axes[idx].axis('off')
        axes[idx].set_title(f"{alphabetical_labels[idx]}: {label_label}", fontsize=10, loc="left")

    plt.tight_layout()
    plt.style.use("dark_background")
    return fig

def get_axial_slice(data, z_index, zloc=2):
    """Return one axial slice from 3D MRI data at z_index."""
    if z_index < 0 or z_index >= data.shape[zloc]:
        raise ValueError(f"z_index={z_index} is out of bounds for shape={data.shape}")
    if z_index == 0:
        return data[z_index, :, :]
    elif z_index == 1:
        return data[:, z_index, :]
    return data[:, :, z_index]


def _smart_crop(img, threshold=1, margin=10):
    arr = np.array(img)
    mask = arr > threshold
    if not mask.any():
        return img
    coords = np.argwhere(mask)
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    x_min = max(x_min - margin, 0)
    x_max = min(x_max + margin, arr.shape[1] - 1)
    y_min = max(y_min - margin, 0)
    y_max = min(y_max + margin, arr.shape[0] - 1)
    return img.crop((x_min, y_min, x_max + 1, y_max + 1))

def _resize_to_width(img, target_width):
    w, h = img.size
    if w == 0:
        return img
    new_h = int((target_width / w) * h)
    return img.resize((target_width, new_h), Image.Resampling.LANCZOS)

def _padd_y_axis(img, target_height, y_center, fill_color=0):
    
    arr = np.array(img)
    h, w = arr.shape[:2]
    
    half = target_height // 2
    top = y_center - half
    bottom = top + target_height

    if top < 0:
        top_padding = abs(top)
        padding = (0, top_padding, 0, 0)  # (left, top, right, bottom)
        img = ImageOps.expand(img, border=padding, fill=fill_color)
        top = 0
        y_center = y_center + top_padding
        bottom = target_height
        h = h + top_padding 
    
    if bottom > h:
        bot_padding = target_height - h 
        padding = (0, 0, 0, bot_padding)  # (left, top, right, bottom)
        img = ImageOps.expand(img, border=padding, fill=fill_color)
    
    return img.crop((0, top, w, bottom))
        

if __name__ == "__main__":
    PROJECT_DIR = Path(__file__).resolve().parents[2]
    PAPER_DIR = Path(__file__).resolve().parents[1] / "research_paper"
    out_figure_path = PAPER_DIR / "figures" / "dropped_subjects.png"
    datasetDir = PROJECT_DIR / "BrainScape"
    generate_dropped_mris_figure(datasetDir, out_figure_path)