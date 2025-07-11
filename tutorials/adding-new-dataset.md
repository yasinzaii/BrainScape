
# How to Add a New Dataset to BrainScape?

This tutorial walks through every step required to **integrate a new MRI dataset** into the BrainScape dataset.  
We will use the openly available **Adolescent Health and Development in Context (AHDC)** dataset from OpenNeuro as a worked example and finish by running the **BRATS** pre-processing plugin on this dataset's anatomical scans.

---

## Overview

* **Dataset:** [AHDC structural and functional MRI](https://openneuro.org/datasets/ds005896/versions/1.0.0)
* **License:** CC0 
* **Goals for this tutorial**

  * Download only the *anatomical* scans (`anat`) plus essential metadata files.
  * Map those files into BrainScape’s dataset JSON structure.
  * Pre-process the scans with the **BRATS** plugin.

> **Already in BrainScape:** The commit that added AHDC is visible at [https://github.com/yasinzaii/BrainScape/commit/5c9d96e](https://github.com/yasinzaii/BrainScape/commit/5c9d96e). 
> This commit also includes integration of 2 other datasets.
> Follow the guide below to reproduce that integration from scratch.

---

## 1 · Dataset Structure

OpenNeuro hosts AHDC in valid BIDS format with three modality folders (`anat`, `dwi`, `func`).  Because BrainScape currently focuses on anatomical MRI, we will limit the download to the `anat` tree:

**AHDC Dataset structure:**

```bash
.
├── CHANGES
├── README
├── dataset_description.json
├── participants.json
├── participants.tsv
├── sub-s002
│   ├── anat
│   │   ├── sub-s002_T1w.json
│   │   ├── sub-s002_T1w.nii.gz
│   │   ├── sub-s002_T2w.json
│   │   └── sub-s002_T2w.nii.gz
│   ├── dwi
│   │   ├── sub-s002_dwi.bval
│   │   ├── sub-s002_dwi.bvec
│   │   ├── sub-s002_dwi.json
│   │   └── sub-s002_dwi.nii.gz
│   └── func
│       ├── sub-s002_task-face_run-01_bold.json
│       ├── sub-s002_task-face_run-01_bold.nii.gz
│       ├── sub-s002_task-face_run-01_events.tsv
│       ├── sub-s002_task-face_run-01_sbref.json
│       └── ...
├── sub-s003
│   └── ...
│           
└── ...       
```

## 2 · Create the dataset folder and minimal metadata

1. Pick an ID for dataset(**Dataset ID**). Here we use `AHDC` for this dataset and then create a directory with name same as Dataset ID (`AHDC`) inside BrainScape dataset directory.

```bash
mkdir -p BrainScape/AHDC
```

2. Inside `AHDC` folder, create a file named **`metadata.json`**, which holds dataset-specific configurations and status flags:

```jsonc
// BrainScape/AHDC/metadata.json
{
  "info": "Dataset-specific settings for AHDC",
  "isDownloaded": false,
  "isPreprocessed": false,
  "isValidationCheckDone": false,
  "includeDataset": true
}
```
These Boolean status flags let BrainScape resume and skip completed steps when you rerun the pipeline.

| Field                   | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| `isDownloaded`          | Tracks dataset download status; skips re-download if `true`. |
| `isPreprocessed`        | Tracks preprocessing completion; skips if already done.      |
| `isValidationCheckDone` | Tracks NIfTI file validation; skips checks if completed.     |
| `includeDataset`        | Toggle to include (`true`) or exclude (`false`) the dataset. |

---

## 3 · Configure the downloader

Append a `download` block to `metadata.json` that tells BrainScape to
use the **OpenNeuroDownloader** plugin and to fetch only **anatomical scans** paths:

```json
{
    "download": {
        "isDownloadable": true,
        "plugin": "OpenNeuroDownloader",
        "profile": "",
        "source": "s3://openneuro.org/ds005896",
        "include": [
            "CHANGES",
            "README",
            "dataset_description.json",
            "participants.json",
            "participants.tsv",
            "sub-*/anat/*"
        ]
    }
}
```

| Parameter        | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| `isDownloadable` | If set `false`, expects manual dataset download.                 |
| `plugin`         | Specifies the downloader plugin (`OpenNeuroDownloader`).         |
| `profile`        | AWS profile credentials (empty for OpenNeuro, as not manditory). |
| `source`         | Source path for dataset on AWS S3 bucket.                        |
| `include`        | List of file/folder glob expressions to selectively download.    |

This configuration will results in the following downloaded structure inside the download folder after the BrainScape pipeline is executed:

```bash
AHDC/download
├── CHANGES
├── README
├── dataset_description.json
├── participants.json
├── participants.tsv
├── sub-s002
│   └── anat
│       ├── sub-s002_T1w.json
│       ├── sub-s002_T1w.nii.gz
│       ├── sub-s002_T2w.json
│       └── sub-s002_T2w.nii.gz
└── sub-s003
    └── anat
        └── ...
```

---

## 4 · Configure the mapper

BrainScape needs to map downloaded files to structured **subject-session-modality** bins. Add the following mapping configuration to your **`metadata.json`**:

Add a `mapping` section to dataset's `metadata.json` so BrainScape Mapper Plugin can translate folder paths into subject, session and modality labels. 


```json
{
    "mapping": {
        "plugin": "RegexMapper",
        "regex": {
            "subject": "^sub-.*$",
            "session": "",
            "type": "^anat$",
            "modality": {
                "t1w": "^.*T1w.nii.gz$",
                "t2w": "^.*T2w.nii.gz$"
            }
        },
        "excludeSub": []
    }
}
```

| Field        | Explanation                                                    |
| ------------ | -------------------------------------------------------------- |
| `plugin`     | Selects mapping plugin (`RegexMapper`).                        |
| `subject`    | Regex matching subjects (`sub-*`).                             |
| `session`    | Regex matching session folders (empty as no sessions exist for AHCD dataset). |
| `type`       | MRI scan type directory (`anat`).                              |
| `modality`   | Modality-specific NIfTI file regex patterns (`t1w`, `t2w`).    |
| `excludeSub` | List subjects or regex patterns to exclude (leave empty here). |

Note: AHDC dataset follows BIDS standards which makes these mappings very easy and straight 
forward. Feel free to checkout mapping configurations for other datasets as well.


The Mapper plugin will then generate JSON record for the dataset and will look this:

```json
{
  "AHDC": [
    {
      "subject": "sub-s002",
      "session": "",
      "type": "anat",
      "group": 0,
      "mris": {
        "t1w": "sub-s002_T1w.nii.gz",
        "t2w": "sub-s002_T2w.nii.gz"
      },
      "download": {
        "t1w": "sub-s002/anat/sub-s002_T1w.nii.gz",
        "t2w": "sub-s002/anat/sub-s002_T2w.nii.gz"
      }
    }, 
    ...
  ]
}
```

## 5 · Configure pre-processing

BrainScape includes default configurations for all datasets in `config/metadata.json` and it includes preprocessor configurations, but you can override them per dataset.  Add an explicit `preprocess` block that selects the **brats** plugin and passes a few plugin-specific options:

```json
{
    "preprocess": {
        "preprocessor": "brats",
        "preprocessDirName": "preprocessed",
        "brats": {
            "tempDirName": "temp",
            "modPriority": ["t1w", "t2w", "t1ce", "flair"]
        }
    }
}
```

| Field               | Description                                                  |
| ------------------- | ------------------------------------------------------------ |
| `preprocessor`      | Select preprocessing plugin (`brats`).                       |
| `preprocessDirName` | Directory name to save preprocessed files.                   |
| `brats.tempDirName` | Temporary directory for intermediate files.                  |
| `brats.modPriority` | Priority order for reference (center) modality (`t1w` highest priority). |


---

## 6 · Register the dataset in the master index

Open `config/index.json`.  Either remove the `"include"` key entirely (to process *all* datasets) or list the new ID explicitly to just run the pipline for `AHDC` dataset:

```json
{ 
    "include": ["AHDC"] 
}
```


---


## 7 · Run the pipeline

Activate the bs (see repo [README.md](https://github.com/yasinzaii/BrainScape/blob/main/README.md) on how to create BrainScape conda environment) environment and run the pipeline.

```bash
conda activate bs
python src/prepare_dataset.py
```

BrainScape pipeline will:

* Download selected files from OpenNeuro.
* Map files into structured subject/session/type/modality bins.
* Validate NIfTI files.
* Preprocess anatomical scans using BRATS.
* Generate a comprehensive `dataset.json`.

---

## 8 · Inspect the results

After completion you will find:


* `BrainScape/AHDC/Download/` – downloaded images
* `BrainScape/AHDC/preprocessed/` – preprocessed images.
* `BrainScape/dataset.json` – BrainScape dataset JSON record


Example of JSON record that BrainScape generates:

```json
{
  "AHDC": [
    {
      "subject": "sub-s002",
      "session": "",
      "type": "anat",
      "group": 0,
      "mris": {
        "t1w": "sub-s002_T1w.nii.gz",
        "t2w": "sub-s002_T2w.nii.gz"
      },
      "download": {
        "t1w": "sub-s002/anat/sub-s002_T1w.nii.gz",
        "t2w": "sub-s002/anat/sub-s002_T2w.nii.gz"
      },
      "preprocessed": {
        "t1w": "sub-s002/preprocessed/t1w_brats.nii.gz",
        "t2w": "sub-s002/preprocessed/t2w_brats.nii.gz"
      },
      "demographics": {
        "participant_id": "sub-s002",
        "sex": "female",
        "age": "15"
      }
    }
  ]
  ...
}
```




