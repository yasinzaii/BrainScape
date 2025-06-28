# Adding New Demographics Fields to a BrainScape Dataset

This tutorial provides a step-by-step guide for researchers on how to **add new demographic fields** to a target BrainScape dataset.

*In this tutorial, we specifically demonstrate adding the **Autism Spectrum Disorder (ASD)** demographic information, which was initially missed in the **ABIDE** dataset. You can refer to the actual commit [cc879fd
](https://github.com/yasinzaii/BrainScape/commit/cc879fd9efda4e0b12f1d334dde240008cbf7cbc) where we added ASD info to ABIDE dataset.*

---

## Overview

To include a new demographic field such as "ASD" diagnosis status into your target (``ABIDE``) dataset, you will:

1. **Update** the `participants.tsv` file for ABIDE with the additional demographic information.
2. **Define** the new demographic field in the global `mapping.yaml`.
3. **Run** the BrainScape pipeline.
4. **Verify** the new demographics have been correctly integrated into the output (``dataset.json``) JSON.

Detailed instructions are provided below.

---

## Step 1: Update `participants.tsv` for ABIDE

Locate (or create if it does not exist) the `participants.tsv` file at the following location within your BrainScape directory:

```
BrainScape/demographics/ABIDE/participants.tsv
```

This file must follow **TSV format** (Tab-Separated Values), with headers matching the fields or their defined aliases in your `mapping.yaml`.

### Example `participants.tsv`

Initially, `participants.tsv` looked like this (without the `ASD` column):

```tsv
ID	sex	handedness	Age
NYU_51079	M	R	7
UCLA_51277	M	R	12
```

To include the ASD diagnosis, we added an additional `ASD` column, resulting in:

```tsv
ID	sex	handedness	Age	ASD
NYU_51079	M	R	7	Y
UCLA_51277	M	R	12	N
```

**Important**:

* Ensure you **use tabs**, not spaces or commas, between fields.
* Provide values for every subject. If information is missing, use `n/a`.

---

## Step 2: Update the `mapping.yaml` File

Define your new demographic field explicitly in BrainScape’s global demographics schema file located at:

```
BrainScape/demographics/mapping.yaml
```

### Add the ASD Demographic Definition

Add the mapping rule for the new "ASD" demographic field as shown:

```yaml
- name: ASD
  aliases:   # Optional alternative column names
    - autism
    - autism-spectrum-disorder
  description: >
    Autism Spectrum Disorder diagnosis status.
  valid_values: *YES_NO_NA
```

* **`name`**: Main demographic key used in the BrainScape output JSON.
* **`aliases`**: Optional alternate column names accepted in the `participants.tsv`.
* **`description`**: Provides info on the demographic field.
* **`valid_values`**: Specifies permissible values. Here, we reuse the predefined `YES_NO_NA` value set.

The definition for the value mapping `YES_NO_NA` is defined at the top of the `mapping.yaml` file:

```yaml
mappings:
  yes_no_na_values: &YES_NO_NA
    - main_value: "Y"
      aliases:
        - "Yes"
        - "1"
    - main_value: "N"
      aliases:
        - "No"
        - "0"
    - main_value: "n/a"
      aliases:
        - "N/A"
        - "na"
```

This setup means:

* Values **Y / Yes / 1** map to `"Y"`.
* Values **N / No / 0** map to `"N"`.
* Values **N/A / n/a / na** map to `"n/a"`.

---

## Step 3: Run the BrainScape Pipeline

Activate your BrainScape environment (`bs`) and run the pipeline:

```bash
conda activate bs
python src/prepare_dataset.py 
```

The demographics-mapper of BrainScape pipeline performs these actions:

* Loads your updated `participants.tsv`.
* Applies column mappings based on definitions in `mapping.yaml`.
* Includes the demographics detais in the target output `dataset.json` file.

---

## Step 4: Verify the Output JSON

After the pipeline runs successfully, verify that the demographics have been correctly integrated into the resulting `dataset.json`. You should now see the new demographic information structured similarly to:



```json
{
  "ABIDE": [
    {
      "subject": "NYU_51079",
      "session": "",
      "type": "anat/NIfTI",
      "group": 0,
      "mris": {
        "t1w": "mprage.nii.gz"
      },
      "download": {
        "t1w": "NYU_51079/anat/NIfTI/mprage.nii.gz"
      },
      "preprocessed": {
        "t1w": "NYU_51079..anat/NIfTI.0/norm_bet/mprage_norm_bet_t1w.nii.gz"
      },
      "demographics": {
        "participant_id": "NYU_51079",
        "sex": "male",
        "handedness": "R",
        "age": "7",
        "ASD": "Y"
      }
    },
    {
      "subject": "UCLA_51277",
      "session": "",
      "type": "anat/NIfTI",
      "group": 0,
      "mris": {
        "t1w": "mprage.nii.gz"
      },
      "download": {
        "t1w": "UCLA_51277/anat/NIfTI/mprage.nii.gz"
      },
      "preprocessed": {
        "t1w": "UCLA_51277..anat/NIfTI.0/norm_bet/mprage_norm_bet_t1w.nii.gz"
      },
      "demographics": {
        "participant_id": "UCLA_51277",
        "sex": "male",
        "handedness": "R",
        "age": "12",
        "ASD": "N"
      }
    }
  ]
}
```

---

## Further Info

* **Adding multiple demographics**:
  Add extra columns in `participants.tsv` and corresponding fields in `mapping.yaml`.

* **Customizing value mappings**:
  Instead of using predefined `*YES_NO_NA`, create your own custom value sets directly in `mapping.yaml`.

---

## Contributing Your Changes Back

BrainScape is a community-driven framework. If you find incorrect or missing demographic information for any dataset:

* Fork the main repository.
* Make corrections to `participants.tsv` and `mapping.yaml`.
* Open a pull request with clear details about your updates.

Your contributions help improve data quality and accuracy of BrainScape.
