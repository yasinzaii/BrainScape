# BrainScape

*BrainScape: An Open-Source Framework for Integrating and Preprocessing Anatomical MRI Datasets*

> To Date! BrainScape automates the download, collation, and preprocessing of **45880 multimodal MRI scans** (T1w, T2w, T1Gd, FLAIR) from **157 independent projects**, spanning **26783 unique participants**.

---

## Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Configuration Guide](#configuration-guide)
7. [License](#license)

---

## Overview
Large, diverse MRI collections are critical for generalizability and reporducability of analysis, yet researchers spend months in collating and preprocessing such datasets. BrainScape provides an easy solution to effectively pool diverse datasets.

BrainScape's pipeline has already incorporated **45880 MRI images** across **157 datasets**. Furthermore, additional dataset can be easily included by adding dataset specific configurations.

---

## Key Features
| Category | Details |
|----------|---------|
| **Modalities** | T1-weighted, T2-weighted, T1-Gadolinium, FLAIR |
| **Datasets Included** | 157 public projects |
| **Plugin Architecture** | 📥 **Download** → 🗂 **Map** → ✅ **Validate** → 🧽 **Preprocess** → 🧑‍🤝‍🧑 **Attach Demographics** |
| **Config-driven** | All behaviour governed by JSON/YAML configuration files |

---

## Prerequisites
| Requirement |  Notes |
|-------------| -------|
| **Linux** (Ubuntu 20.04 +) **or** Windows 10/11 with [WSL 2] | WSL 2 [Installation Process](https://learn.microsoft.com/windows/wsl/install#install-wsl-command) | 
| **Miniconda** | Miniconda [Installation Process](https://www.anaconda.com/docs/getting-started/miniconda/install#linux-terminal-installer) | – | 
| **Git** | | 
| **Python** | 3.10 (managed by Conda) | 

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
*Edit* `config/index.json`:
* **Process specific datasets:**
  ```json
  { "include": ["ECStudy", "VASP"] }
  ```
* **Process *all* datasets:** remove the `include` key entirely.

---

## Configuration Guide
| File | Purpose |
|------|---------|
| `config/config.json` | Generic configurations |
| `config/metadata.json` | Baseline default configs applied to each dataset |
| `config/index.json` | **Master toggle** for which datasets to include or exclude |
| `credentials.ini` | Login tokens for gated repositories |
| `BrainScape/<dataset>/metadata.json` | Datset specific configuration (overides `config/metadata.json`) |

---

## License
BrainScape is released under the **MIT License**. See `LICENSE` for details.
