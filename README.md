# BrainScape

*BrainScape: An Open-Source Framework for Integrating and Preprocessing Anatomical MRI Datasets*

> BrainScape automates the download, collation, and preprocessing of **45880 multimodal MRI scans** (T1w, T2w, T1Gd, FLAIR) from **157 independent projects**, spanning **26783 unique participants**.

---

## Table of Contents
1. [Overview](#overview)
2. [Why BrainScape?](#why-brainscape)
3. [Key Features](#key-features)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Quick Start](#quick-start)
7. [Configuration Guide](#configuration-guide)
8. [Adding a New Dataset](#adding-a-new-dataset)
9. [License](#license)

---

## Overview
Large, diverse MRI collections are critical for generalizability and reporducability of analysis, yet researchers spend months in collating and preprocessing such datasets. BrainScape provides an easy solution to effectively pool diverse datasets.

BrainScape's pipeline has already incorporated **45880 MRI images** across **157 datasets**. Furthermore, additional dataset can be easily included by adding dataset specific configurations.

---

## Why BrainScape?

Modern neuroimaging studies require large, diverse, multi-modal MRI dataset that span various scanners, protocols, demographics, and pathologies. Such datasets can be prepared by pooling thousands of MRI scans from numerous repositories. However, manually pooling data from multiple sources is slow, error-prone, and difficult to reproduce reliably when done with ad hoc scripts.

BrainScape addresses these challenges by offering a fully automated, plugin-based pipeline that:

* **Downloads** source datasets from repositories such as OpenNeuro, Synapse, HCP using dedicated plugins.
* **Maps** heterogeneous dataset folder structures into a unified JSON record through configurable regular-expression rules.
* **Validates** NIfTI headers and files to identify and exclude corrupt or problematic scans early in the process.
* **Preprocesses** with pluggable pipelines (BRATS, smriprep, identity etc).
* **Attaches demographics** for each participant from the corresponding demographics tables (participants.tsv) via a flexible YAML mapping schema.
* **Generates visuals & auto‑READMEs** for every dataset.

---

## Key Features
| Category | Details |
|----------|---------|
| **Modalities** | T1-weighted, T2-weighted, T1-Gd, FLAIR |
| **Datasets Included** | 157 public projects |
| **Plugin Architecture** | 📥 **Download** → 🗂 **Map** → ✅ **Validate** → 🧽 **Preprocess** → 👤 **Demographics** |
| **Config-driven** | YAML / JSON – no code changes required  |

---

## Prerequisites
| Requirement |  Notes |
|-------------| -------|
| **Linux** (Ubuntu 20.04 +) **or** Windows 10/11 with [WSL 2] | WSL 2 [Installation Process](https://learn.microsoft.com/windows/wsl/install#install-wsl-command) | 
| **Miniconda** | Miniconda [Installation Process](https://www.anaconda.com/docs/getting-started/miniconda/install#linux-terminal-installer) | – | 
| **Git** | | 
| **Python** | 3.10 (managed by Conda) | 
| **AWS CLI v2** | Required for OpenNeuro / HCP downloads |      

---

## Installation
```bash

# 1 Download and Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 2 Clone the repo
git clone https://github.com/yasinzaii/BrainScape.git
cd BrainScape

# 3 Create & activate the Conda environment
conda env create -f environment.yaml
conda activate bs

```

> **Update env later:** `conda env update -f environment.yaml -n bs`

---

## Quick Start
```bash
# Run the end-to-end pipeline (defaults to ECStudy dataset only)
python src/prepare_dataset.py
```

### Including more datasets

Add or exclude datasets by editing `config/index.json`:

* **Download & Process specific datasets:**

  Add your target datasets into the `include` list inside `config/index.json`.

  ```json
  { "include": ["ECStudy", "VASP"] }
  ```
* **Download & Process *all* datasets:** 

  Omit `include` key from `config/index.json` to process **all** of the remaining datasets.

---

## Configuration Guide
| File | Purpose |
|------|---------|
| `config/config.json` | Generic configurations (Global paths & filenames) |
| `config/metadata.json` | Default per‑dataset settings (inherited) |
| `config/index.json` | **Master toggle** for which datasets to include or exclude |
| `credentials.ini` | AWS & Synapse tokens |
| `BrainScape/<dataset>/metadata.json` | Datset specific configuration (overides `config/metadata.json`) |
| `demographics/<dataset>/participants.tsv` | Raw demographic table |
| `demographics/mapping.yaml` | Column/alias mapping schema |

---

## Adding a New Dataset

Note: Assuming downloading from OpenNeuro as the download plugin for OpenNeuro is available. (Available Plugins for Platforms: OpenNeuro, Synapse)

1. **Create a folder** under `BrainScape/<DatasetID>` and drop a minimal `metadata.json` (copy `BrainScape/<any-dataset>/metadata.json` and tweak).
2. **Specify**:

   Download Plugin Settings:

   * `download.isDownloadable` - Set to true 
   * `download.plugin` - Set to OpenNeuroDownloader
   * `download.source` – S3 path or Synapse ID
   * `download.include` – glob patterns to keep or download

   Regex Mapper Settings:
   * `mapping.regex.subject` – provide regex pattern to recognise subject
   * `mapping.regex.session` – provide regex pattern to recognise session if available
   * `mapping.regex.type` – provide regex pattern to recognise type folder. Such as *Anatomical MRI folder* if available.
   * `mapping.regex.modality` – under this modality object list each of the available modalities and their regex patterns as key value pairs.

   Preprocess Settings (Usually not provided - the default config file `config/metadata.json` provides these settings ):
   * `preprocess.preprocessor` - provide the target preprocessor plugin name such as brats.
   * `preprocess.preprocessDirName` - provide directory name to keep preprocessed MRIs
  
   Status Flags:
   * `isDownloaded` - set to false as dataset is not downloaded
   * `isDatasetJsonCreated` - set to false as output JSON record is not generated
   * `isPreprocessed` - set to false as dataset is not preprocessed
   * `isValidationCheckDone` - set to false as validation is not yet done
   * `isVisualized` - set to false as visualization for the dataset is not generated yet
   * `isReadmeGenerated` - set to false as the README for the dataset is not yet generated

3. Add `demographics/<DatasetID>/participants.tsv` if available.
4. Run `python src/prepare_dataset.py` – BrainScape will take it from there.

---

## License
BrainScape is released under the **MIT License**. See `LICENSE` for details.
