# src/export_preprocessed_split.py

"""
Export a *slim* BrainScape dataset that contains **only** the pre-processed
NIfTI files for DL projects and create subject-level train/val/test splits.

Special case
------------
*BRATS* subjects whose folder begins with

*  ``training-``   → **train** and val set.
*  ``validation-`` → split between **val** and **test**
                     using the global --val / --test ratios.

All other datasets are split independently with the supplied ratios
(default 80 / 10/ 10).

Example
-------
python src/export_preprocessed_split.py        \
       --dataset-root  BrainScape/             \
       --dataset-json  BrainScape/dataset.json \
       --output-root   BrainScape_prep         \
       --train-ratio 0.80    \
       --val-ratio   0.10    \
       --test-ratio 0.10     \
       --seed 42
"""

import json
import math
import random
import shutil
import argparse
import pandas as pd

from pathlib import Path
from typing import Dict, List, Tuple


SPLITS = ("train", "val", "test")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
            prog="export_preprocessed_split.py",
            description=(
                "Copy *pre-processed* images referenced in a BrainScape "
                "dataset.json to <output-root> and generate subject-level "
                "train / val / test splits."
            ),
    )
    
    p.add_argument(
        "--dataset-root",
        type=Path,
        required=True,
        help="Path to the *input* BrainScape Root Dir",
    )
    
    p.add_argument(
        "--dataset-json",
        type=Path,
        required=True,
        help="Path to the *input* BrainScape dataset.json",
    )
    p.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Destination folder for the slim BrainScape dataset",
    )
    p.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Destination output json record (default: <output-root>/dataset.json)",
    )
    p.add_argument(
        "--preprocessed-dir",
        type=Path,
        default="preprocessed",
        help="Path to preprocessed directory, Relative to BrainScape/<Dataset ID>/ directory",
    )
    
    p.add_argument("--train-ratio", type=float, default=0.80, help="Train ratio")
    p.add_argument("--val-ratio",   type=float, default=0.10, help="Validation ratio")
    p.add_argument("--test-ratio",  type=float, default=0.10, help="Test ratio")
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    
    return p


def _check_ratios(train: float, val: float, test: float) -> None:
    """Ensure the three split ratios sum to (approximately) one."""
    if not math.isclose(train + val + test, 1.0, abs_tol=1e-6):
        raise ValueError("--train-ratio + --val-ratio + --test-ratio must sum to 1.0")


def _extract_modalities(rec: dict) -> List[str]:
    """Return lower-cased modality names in *rec*."""
    if "mris" in rec:
        return [m.lower() for m in rec["mris"].keys()]
    raise KeyError("Record missing 'mris' key: %s" % rec)


def _group_subjects(records: List[dict]) -> Dict[str, List[int]]:
    """Return a mapping: *subject* → list[record_idx]."""
    groups: Dict[str, List[int]] = {}
    for idx, rec in enumerate(records):
        groups.setdefault(rec["subject"].lower(), []).append(idx)
    return groups


def _allocate_subjects_random(subjects: List[str],
                              ratios: Tuple[float, float, float],
                              rng: random.Random) -> Dict[str, List[str]]:
    """Random split respecting ratios; returns {split: [subjects]}."""
    train_ratio, val_ratio, test_ratio = ratios
    _check_ratios(train_ratio, val_ratio, test_ratio)

    rng.shuffle(subjects)  
    n_total = len(subjects)
    n_train = math.floor(n_total * train_ratio)
    n_val   = math.floor(n_total * val_ratio)
    n_test  = n_total - n_train - n_val

    split_of = {"train":subjects[:n_train]}
    split_of.update({"val": subjects[n_train:n_train + n_val]})
    split_of.update({"test": subjects[n_train + n_val:]})
    return split_of



def _get_group_containing_modality(groups: Dict[str, List[int]],
                                   records: List[dict],
                                   modality: str) -> List[str]:
    """Return a *list* of subject names that contain *modality*."""
    modality = modality.lower()
    subjects: List[str] = []
    for sub_name, idxs in groups.items():
        for i in idxs:
            if modality in _extract_modalities(records[i]):
                subjects.append(sub_name.lower())
                break
    # sanity: no duplicate subjects
    if len(subjects) != len(set(subjects)):
        raise ValueError("Duplicate subject encountered in _get_group_containing_modality")
    return subjects


def _get_group_modality_count(groups: Dict[str, List[int]],
                              records: List[dict],
                              modality: str) -> int:
    """How many *subjects* (not records) contain *modality*."""
    return len(_get_group_containing_modality(groups, records, modality))



def split_dataset(dataset_id: str,
                  records: List[dict],
                  ratios: Tuple[float, float, float],
                  rng: random.Random) -> Dict[str, List[dict]]:
    """Return {"train": [...], "val": [...], "test": [...]} for this dataset.

    *Special BRATS rule* is applied here**.
    """
    train_ratio, val_ratio, test_ratio = ratios
    _check_ratios(train_ratio, val_ratio, test_ratio)

    if dataset_id.upper() == "BRATS":
        
        train_pool, val_pool = [], []
        for rec in records:
            sub = rec["subject"]
            if sub.startswith("training-"):
                train_pool.append(rec)
            elif sub.startswith("validation-"):
                val_pool.append(rec)
            else:
                raise RuntimeError(f"Unrecognised BRATS subject: {sub}")

        rng.shuffle(val_pool)
        rng.shuffle(train_pool)
        

        # Aquiring the test set first
        n_total = len(train_pool) + len(val_pool)
        test_cut = int(round(test_ratio*n_total))
        
        if test_cut > len(val_pool):
            raise ValueError(
                f"BRATS test split ({test_cut} subjects) cannot exceed the number of validation-* subjects ({len(val_pool)})"
            )
        test_recs = val_pool[:test_cut]
        val_recs  = val_pool[test_cut:]

        # The remaining records will be acquired from Training set.
        val_cut = int(round(val_ratio*n_total)) - len(val_recs) 
        if(val_cut > 0):
            val_recs.extend(train_pool[:val_cut])
        train_recs = train_pool[val_cut:]

        return {"train": train_recs, "val": val_recs, "test": test_recs}

    # Generic dataset 
    groups = _group_subjects(records)  # subject → list[record_idx]
    remaining_subs: set[str] = set(groups) 

    all_modalities = {m for rec in records for m in _extract_modalities(rec)}
    
    modality_coverage = {m: _get_group_modality_count(groups, records, m)
                         for m in all_modalities}

    buckets: Dict[str, List[dict]] = {s: [] for s in SPLITS}
    for modality in sorted(modality_coverage, key=modality_coverage.get):

        # only consider subjects that are still unsplit
        target_subjects = [
            s for s in _get_group_containing_modality(groups, records, modality)
            if s in remaining_subs
        ]

        split_of = _allocate_subjects_random(target_subjects, ratios, rng)

        for split, split_subjects in split_of.items():
            for split_sub in split_subjects:
                for idx in groups[split_sub]:
                    buckets[split].append(records[idx])            

        remaining_subs.difference_update(target_subjects)

    return buckets


def _check_slitting(split_out, records):
    
    # verify all subject are covered
    all_subs = {rec["subject"].lower() for rec in records}
    all_subs_out = {rec["subject"].lower() for bucket in split_out.values() for rec in bucket}
    if all_subs != all_subs_out:
        raise ValueError(f"Input and output subjects mismatch, # input sub:{all_subs}, # output sub:{all_subs_out}")

    # verify no subjects are repeated in trian/val/test set.
    for indx_to in range(len(SPLITS)):
        for indx in range(indx_to+1, len(SPLITS)):
            comp_to = split_out[SPLITS[indx_to]] 
            comp = split_out[SPLITS[indx]]

            subs_to = {rec["subject"].lower() for rec in comp_to} 
            subs = {rec["subject"].lower() for rec in comp}

            overlap = subs_to & subs
            if overlap:  # if subjects overlap
                raise ValueError(f"Subjects overlap found in {comp_to} and {comp} sets, overalpping subjects: {overlap}")

    # Verify the total length of records match
    all_recs_out = sum([len(bucket) for bucket in split_out.values() ])
    if (all_recs_out != len(records)):
        raise ValueError(f"Mismatch between # of actual dataset records: {len(records)} and splitted records: {all_recs_out}")

import pandas as pd

def make_distribution_table(split_out: Dict[str, List[dict]]) -> pd.DataFrame:
    """
    Build a per-modality distribution table.

    Columns:
        Train n, Train %, Val n, Val %, Test n, Test %, Total n
    Rows:
        Each modality plus a final 'All' summary row.
    """
    # Explode every record→modality into flat rows
    flat_rows = []
    for split, recs in split_out.items():
        for rec in recs:
            for mod in rec["mris"]:
                if mod != 'seg': # Skipping Segmentation Labels                
                    flat_rows.append({"modality": mod.lower(), "split": split})
    df = pd.DataFrame(flat_rows)

    # Counts per modality × split  -> a tidy table
    counts = (
        df.value_counts(["modality", "split"])
          .unstack(fill_value=0)[["train", "val", "test"]]  # enforce column order
          .rename(columns=str.title)                       # Train / Val / Test
    )

    # Percentages within each modality
    pct = counts.div(counts.sum(axis=1), axis=0) * 100
    pct = pct.round(1).astype(str) + " %"                 # append % sign

    # Interleave counts and percentages
    table = pd.concat(
        [
            counts.rename(columns=lambda c: f"{c} n"),
            pct.rename(columns=lambda c: f"{c} %"),
        ],
        axis=1
    )

    # Total column
    table["Total n"] = counts.sum(axis=1)

    # Add an “All” summary row
    total_counts = counts.sum()
    total_pct    = (total_counts / total_counts.sum() * 100).round(1).astype(str) + " %"
    summary_row  = pd.concat(
        [total_counts.rename(lambda c: f"{c} n"),
         total_pct.rename(lambda c: f"{c} %"),
         pd.Series({"Total n": int(total_counts.sum())})]
    )
    table.loc["All"] = summary_row

    # Modality string capitalisation
    table.index = table.index.str.upper()

    return table



def main() -> None:
    args = build_parser().parse_args()
    rng = random.Random(args.seed)

    # Read input json
    with args.dataset_json.open() as fp:
        datasets: Dict[str, List[dict]] = json.load(fp)
    if not isinstance(datasets, dict):
        raise TypeError("--dataset-json must contain a dict of lists (datasets)")

    args.output_root.mkdir(parents=True, exist_ok=True)
    ratios = (args.train_ratio, args.val_ratio, args.test_ratio)

    merged: Dict[str, List[dict]] = {s: [] for s in SPLITS}
    for ds_id, records in datasets.items():
        # Adding datset ID to record.
        for rec in records:
            rec["dataset"] = ds_id

        split_out = split_dataset(ds_id, records, ratios, rng)

        # Some checks to verify splitting is done accurately
        print(f"verifying splits for dataset: {ds_id}")
        _check_slitting(split_out, records)

        for split in SPLITS:
            merged[split].extend(split_out[split])


    # Copy directory 
    for ds_id, records in datasets.items():
        src_dir = args.dataset_root / ds_id / args.preprocessed_dir
        dst_dir = args.output_root / ds_id / args.preprocessed_dir

        for rec in records:
            preproc = rec.get("preprocessed", {})
            for mod, rel_path in preproc.items():
                src_file = src_dir / rel_path
                dst_file = dst_dir / rel_path

                # Create parent directory if it doesn't exist
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)


    # Write output dataset json file
    out_json_path: Path = (
        args.output_json if args.output_json is not None else args.output_root / "dataset.json"
    )
    with out_json_path.open("w") as f:
        json.dump(merged, f, indent=4)

    # Report 
    tbl = make_distribution_table(merged)
    print(tbl.to_markdown()) 

if __name__ == "__main__":
    main()
