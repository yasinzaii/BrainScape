# **Complete End‑to‑End Workflow Walkthrough**

> *This tutorial walks through every BrainScape pipeline stage on a **single example dataset** (ECStudy) and shows exactly where each plugin is invoked.*

---

## What you will learn

1. How BrainScape discovers and executes **Download → Mapping → Validation → Scanner → Preprocessing → Demographics → Visualisation → README-generation** in order.
2. Where to edit **default** versus **dataset‑specific** configuration files and how overrides work.
3. How to read *prepareDataset.log* / *errors.log* to confirm each stage completed.
4. How the incremental **`dataset.json`** record grows after every stage.

---

## 1. Repository paths recap

```
BrainScape/
├── config/
│   ├── config.json            # global paths & filenames
│   ├── index.json             # master include/exclude toggle
│   └── metadata.json          # default settings for every dataset
├── BrainScape/<DatasetID>/    # dataset‑specific folders & metadata
├── logs/                      # prepareDataset.log & errors.log
└── src/                       # managers & plugins (download, map …)
```

---

## 2. Tell BrainScape *which* dataset to run

For this walkthrough we restrict the pipeline to **ECStudy** only by editing *config/index.json*. All the other datasets in BrainScape will not be included:

```json
{
  "info": "Overrides Dataset inclusion|exclusion Settings, [Overrides 'includeDataset' key of individual metadata.json]",
  "include": [
    "ECStudy"
  ],
  "exclude": []
}
```

---

## 3. Dataset‑specific settings (`BrainScape/ECStudy/metadata.json`)

This file is the main dataset-specific configuration file. This file provides configurations/mapping rules for the plugins.
```jsonc
{
  "info": "Dataset Specific Settings",
  "isDownloaded": false,
  "isDatasetJsonCreated": false,
  "isPreprocessed": false,
  "includeDataset": true,
  "download": {
    "isDownloadable": true,
    "plugin": "OpenNeuroDownloader",
    "profile": "",
    "source": "s3://openneuro.org/ds004513",
    "include": [
      "CHANGES",
      "README",
      "dataset_description.json",
      "participants.json",
      "participants.tsv",
      "sub-*/ses-*/anat/*"
    ]
  },
  "mapping": {
    "plugin": "RegexMapper",
    "regex": {
      "subject": "^sub-.*$",
      "session": "^ses-.*$",
      "type": "^anat",
      "modality": {
        "t1w": "^.*T1w.nii.gz$"
      }
    },
    "excludeSub": [
      "sub-s037"
    ]
  },
  "isValidationCheckDone": false,
  "isVisualized": false,
  "isReadmeGenerated": false
}
```

Notice this file also includes `isDownloaded`, `isPreprocessed`, `isValidationCheckDone`, `isVisualized`, `isReadmeGenerated` status flags to keep track of the individual stage status information. TODO: take the flags out of this dataset-sepcific configuration files.

### 3.1 Over‑riding the default pre‑processor

The global *config/metadata.json* chooses **BRATS** by default. As in the above configuration for ECStudy we have not provided `preprocess` configs so the default will be used. However, for this run we did overided the default configurations:

```jsonc
"preprocess": {
  "preprocessor": "brats",
  "preprocessDirName": "preprocessed",
  "brats": {
    "tempDirName": "temp",
    "modPriority": ["t1w", "t2w", "t1ce", "flair"]
  }
}
```

For a *quick* run (this example) we switch ECStudy to the **Identity** pre‑processor (copies files untouched - just chosen for this example as it is fast) and mark the dataset as already preprocessed:

```jsonc
"preprocess": {
  "preprocessor": "identity",
  "preprocessDirName": "preprocessed",
  "alreadyPreprocessed": true
},
```

Add the block to the same *`BrainScape/ECStudy/metadata.json`* file of ECStudy dataset.

---

## 4. Workflow script

Here is main of the pipeline workflow:

```python
# src/prepare_dataset.py (simplified)

# 1 ─ Download raw data
download_man = DownloadManager(config, target_datasets, default_dataset_settings)
download_man.initiate_downloads()

# 2 ─ Map folder → JSON
dataset_man = DatasetManager(config, target_datasets, default_dataset_settings)
dataset_man.initiate_mapping()

# 3 ─ Validate NIfTIs
validate_man = ValidateManager(config, target_datasets, default_dataset_settings,
                              mapping=dataset_man.get_mapping())
validate_man.validate_nifti()

dataset_man.scanner_mapping()

# 4 ─ Pre‑process
preprocess_man = PreprocessManager(config, target_datasets, default_dataset_settings,
                                   mapping=dataset_man.get_mapping())
preprocess_man.initiate_preprocessing()

dataset_man.preprocessed_mapping()

# 5 ─  Dempgraphics Attachment
dataset_man.demographic_mapping()

# 6 ─ Visuals & README
visualizer_man = VisualizerManager(config, target_datasets, default_dataset_settings,
                                   mapping=dataset_man.get_mapping())
visualizer_man.initiate_visualization()

readme_gen_man = ReadmeGeneratorManager(config, target_datasets, default_dataset_settings,
                                        mapping=dataset_man.get_mapping())
readme_gen_man.initiate_readme_generation()

# 7 ─ Persist final JSON
dataset_man.save_mapping()
```

---

## 5. Stage‑by‑Stage execution & artefacts

### 5.1 DownloadManager

In the first stage the ECStudy dataset is downloaded from the remote repository via the configured download plugin and settings (see `BrainScape/ECStudy/metadata.json` above for configuration settings for downlod step).

*Plugin involved*: **OpenNeuroDownloader** (configured in `download.plugin`).

<details>
<summary>Full logs</summary>

```text
2025-07-28 21:18:21 - INFO - Logging configuration loaded successfully from './config/logging.json'.
2025-07-28 21:18:21 - INFO - Target Datasets: ['ECStudy']
2025-07-28 21:18:22 - INFO - Loaded plugin 'SynapseDownloader' from class 'SynapseDownloader'
2025-07-28 21:18:22 - INFO - Loaded plugin 'OpenNeuroDownloader' from class 'OpenNeuroDownloader'
2025-07-28 21:18:22 - INFO - DownloadManager - Created download directory: 'BrainScape/ECStudy/Download'
2025-07-28 21:18:22 - INFO - OpenNeuroDownloader - Starting download for dataset:ECStudy, from 's3://openneuro.org/ds004513'
2025-07-28 21:18:23 - INFO - OpenNeuroDownloader - AWS_SHARED_CREDENTIALS_FILE set to: /home/yas/BrainScape/config/credentials.ini
2025-07-28 21:18:36 - INFO - OpenNeuroDownloader - Download Completed for pattern: 'CHANGES', Dataset: 'BrainScape/ECStudy'.
2025-07-28 21:18:46 - INFO - OpenNeuroDownloader - Download Completed for pattern: 'README', Dataset: 'BrainScape/ECStudy'.
2025-07-28 21:18:55 - INFO - OpenNeuroDownloader - Download Completed for pattern: 'dataset_description.json', Dataset: 'BrainScape/ECStudy'.
2025-07-28 21:19:05 - INFO - OpenNeuroDownloader - Download Completed for pattern: 'participants.json', Dataset: 'BrainScape/ECStudy'.
2025-07-28 21:19:18 - INFO - OpenNeuroDownloader - Download Completed for pattern: 'participants.tsv', Dataset: 'BrainScape/ECStudy'.
2025-07-28 21:19:59 - INFO - OpenNeuroDownloader - Download Completed for pattern: 'sub-*/ses-*/anat/*', Dataset: 'BrainScape/ECStudy'.
2025-07-28 21:19:59 - INFO - DownloadManager - Download Job Completed for Dataset: 'BrainScape/ECStudy', Verifying Downlaoded Contents.
2025-07-28 21:20:09 - INFO - DownloadManager - The Source and Downloaded File Match for Dataset: 'BrainScape/ECStudy', Verification Completed, setting Dataset 'isDownlaoded' Flag to True
```

</details>

**Resulting folder Structure**

```
BrainScape/ECStudy/Download/
├── CHANGES
├── README
├── dataset_description.json
├── participants.{json,tsv}
└── sub‑s007/
│   ├── ses‑closed/
│   │   └── anat/sub‑s007_ses‑closed_T1w.nii.gz
│   └── ses‑open/
│       └── anat/sub‑s007_ses‑open_T1w.nii.gz
└── ...
```

> *Note — additional subjects (e.g. **sub‑s003**, **sub‑s012**) follow the identical layout.*

`metadata.json` flag automatically updated:

```jsonc
"isDownloaded": true
```

---

### 5.2 DatasetManager – RegexMapper

After downloading the dataset the donwloaded MRI are then mapped to the Dataset JSON record via regex mapper plugin.
The mapper plugin maps the MRI datset into subject, session and type bins and it keeps the record for all the 
MRI modalities, downlaod paths for all modalities, preprocess paths for all modalities, demographic info, scanner info etc.


<details>
<summary>Full logs</summary>

```text
2025-07-28 21:20:09 - INFO - Loaded plugin 'RegexMapper' from class 'RegexMapper'
2025-07-28 21:20:09 - INFO - Loaded plugin 'DemographicsMapper' from class 'DemographicsMapper'
2025-07-28 21:20:09 - INFO - Loaded plugin 'ScannerMapper' from class 'ScannerMapper'
2025-07-28 21:20:09 - INFO - RegexMapper - Started creating dataset JSON for ECStudy Dataset.
2025-07-28 21:20:09 - INFO - RegexMapper - ECStudy - Subject 'sub-s037' in excludeSub list; Skipping.
2025-07-28 21:20:09 - INFO - RegexMapper - ECStudy - Skipping 'dataset_description.json': as it does not match 'subject' pattern '^sub-.*$'.
2025-07-28 21:20:09 - INFO - RegexMapper - ECStudy - Skipping 'CHANGES': as it does not match 'subject' pattern '^sub-.*$'.
2025-07-28 21:20:09 - INFO - RegexMapper - ECStudy - Skipping 'participants.json': as it does not match 'subject' pattern '^sub-.*$'.
2025-07-28 21:20:09 - INFO - RegexMapper - ECStudy - Subject 'sub-s037' in excludeSub list; Skipping.
2025-07-28 21:20:09 - INFO - RegexMapper - ECStudy - Skipping 'README': as it does not match 'subject' pattern '^sub-.*$'.
2025-07-28 21:20:09 - INFO - RegexMapper - ECStudy - Skipping 'participants.tsv': as it does not match 'subject' pattern '^sub-.*$'.
2025-07-28 21:20:09 - INFO - RegexMapper - Completed creating dataset JSON for ECStudy Dataset.
```

</details>

The following is the result dataset JSON record after this regex mapping step:

```jsonc
{
    "ECStudy": [
        {
            "subject": "sub-s007",
            "session": "ses-closed",
            "type": "anat",
            "group": 0,
            "mris": {
                "t1w": "sub-s007_ses-closed_T1w.nii.gz"
            },
            "download": {
                "t1w": "sub-s007/ses-closed/anat/sub-s007_ses-closed_T1w.nii.gz"
            }
        },
        {
            "subject": "sub-s007",
            "session": "ses-open",
            "type": "anat",
            "group": 0,
            "mris": {
                "t1w": "sub-s007_ses-open_T1w.nii.gz"
            },
            "download": {
                "t1w": "sub-s007/ses-open/anat/sub-s007_ses-open_T1w.nii.gz"
            }
        },
        ...
    ]
}

```

---

### 5.3 ValidateManager – NIfTI header checks

In this step the nifti files are validated and their header and data info are checked.

<details>
<summary>Logs</summary>

```text
2025-07-28 21:20:09 - INFO - ValidateManager - Starting validation for dataset 'ECStudy'
2025-07-28 21:20:16 - INFO - ValidateManager - Dataset 'ECStudy' passed NiftiValidator validation.
```

</details>

`metadata.json`:

```jsonc
"isValidationCheckDone": true
```

---

### 5.4 ScannerMapper

The next step includes the MRI scanner information for each of the MRI in the dataset JSON record.

<details>
<summary>Logs</summary>

```text
2025-07-28 21:20:16 - INFO - Scanner Mapping - Dataset: ECStudy
2025-07-28 21:20:16 - INFO - ScannerMapper - attached scanner info to ECStudy mapping rows
```

</details>

Mapping rows now include:

```jsonc
{
    "ECStudy": [
        {
            "subject": "sub-s007",
            "session": "ses-closed",
            "type": "anat",
            "group": 0,
            "mris": {
                "t1w": "sub-s007_ses-closed_T1w.nii.gz"
            },
            "download": {
                "t1w": "sub-s007/ses-closed/anat/sub-s007_ses-closed_T1w.nii.gz"
            },
            "scanner": {
                "t1w": {
                    "Manufacturer": "Siemens",
                    "ManufacturersModelName": "Biograph_mMR",
                    "MagneticFieldStrength": 3
                }
            }
        }
        ...
    ]
}

```

---

### 5.5 PreprocessManager – Identity pre‑processor

Preprocessing is performed in this step and the preprocessed MRI images are stored in the preprocessed folder.
Furthermore, the preprocessed images are also mapped into the datset JSON record.

<details>
<summary>Logs</summary>

```text
2025-07-28 21:20:16 - INFO - Loaded plugin 'identity' from class 'IdentityPreprocessor'
2025-07-28 21:20:16 - INFO - Loaded plugin 'smriprep' from class 'SMRIPrepPreprocessor'
2025-07-28 21:20:25 - INFO - Loaded plugin 'brats' from class 'BratsPreprocessor'
2025-07-28 21:20:25 - INFO - IdentityPreprocessor - Preprocesed Mapping for all of the subjects has been added. Dataset: ECStudy
2025-07-28 21:20:25 - INFO - PreprocessManager - Preprocessing completed for dataset 'ECStudy'. Updating 'isPreprocessed' flag.
2025-07-28 21:20:25 - INFO - JsonHandler - JSON data updated successfully for file 'BrainScape/ECStudy/metadata.json'. Updates: {'isPreprocessed': True}
2025-07-28 21:20:25 - INFO - JsonHandler - Saved Data into the Json File, Json File BrainScape/ECStudy/metadata.json
```

</details>

Mapping now contains a *preprocessed* block (paths shortened here):

```jsonc
{
    "ECStudy": [
        {
            "subject": "sub-s007",
            "session": "ses-closed",
            "type": "anat",
            "group": 0,
            "mris": {
                "t1w": "sub-s007_ses-closed_T1w.nii.gz"
            },
            "download": {
                "t1w": "sub-s007/ses-closed/anat/sub-s007_ses-closed_T1w.nii.gz"
            },
            "scanner": {
                "t1w": {
                    "Manufacturer": "Siemens",
                    "ManufacturersModelName": "Biograph_mMR",
                    "MagneticFieldStrength": 3
                }
            },
            "preprocessed": {
                "t1w": "sub-s007.ses-closed.anat.0/norm_bet/sub-s007_ses-closed_T1w_t1w.nii.gz"
            }
        }
        ...
    ]
}


```



---

### 5.6 DemographicsMapper

The demographics infomation is the attached to the dataset JSON record

<details>
<summary>Logs</summary>

```text
2025-07-28 21:20:25 - INFO - Demographic Mapping - Dataset: ECStudy
2025-07-28 21:20:25 - INFO - DemographicsMapper - Merging demographics for dataset for dataset: ECStudy
2025-07-28 21:20:26 - INFO - DemographicMapper - Finished demographics merging for dataset: 'ECStudy'
```

</details>

Example demographics block:

```jsonc
{
    "ECStudy": [
        {
            "subject": "sub-s007",
            "session": "ses-closed",
            "type": "anat",
            "group": 0,
            "mris": {
                "t1w": "sub-s007_ses-closed_T1w.nii.gz"
            },
            "download": {
                "t1w": "sub-s007/ses-closed/anat/sub-s007_ses-closed_T1w.nii.gz"
            },
            "scanner": {
                "t1w": {
                    "Manufacturer": "Siemens",
                    "ManufacturersModelName": "Biograph_mMR",
                    "MagneticFieldStrength": 3
                }
            },
            "preprocessed": {
                "t1w": "sub-s007.ses-closed.anat.0/norm_bet/sub-s007_ses-closed_T1w_t1w.nii.gz"
            },
            "demographics": {
                "participant_id": "sub-s007",
                "age": "46",
                "sex": "male",
                "handedness": "R",
                "weight": "70",
                "height": "1.8",
                "BMI": "21.6"
            }
        },
        ...
    ]
}

```

---

### 5.7 Visualiser & README generation

Images and Markdown are emitted in **BrainScape/ECStudy/visualize/** and **BrainScape/ECStudy/README.md** (logs omitted for brevity).

---

### 5.8 Saving the consolidated *dataset.json*

<details>
<summary>Logs</summary>

```text
2025-07-28 21:20:54 - INFO - JsonHandler - JSON data has been overridden successfully for file 'BrainScape/dataset.json'.
```

</details>

---

## 6. Where to find logs

* **logs/prepareDataset.log** – INFO level and above for every manager & plugin.
* **logs/errors.log** – ERROR level logs only.

---

## 7. Resetting status flags (optional reruns)

```bash
# Dry‑run: show which flags *would* be cleared
python src/reset_status_flags.py -k isDownloaded isPreprocessed --dry-run

# Actually reset the preprocessing flag for all datasets
python src/reset_status_flags.py -k isPreprocessed
```
