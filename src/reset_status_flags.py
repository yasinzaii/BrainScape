# src/reset_status_flags.py
#
# Reset selected Boolean status flags (e.g. "isVisualized") in every
# BrainScape/<dataset>/metadata.json to False.
#
# Run `python src/reset_status_flags.py -h` for options.


from __future__ import annotations
import argparse
from pathlib import Path

from utils.json_handler import JsonHandler


def build_parser() -> argparse.ArgumentParser:
    """Return an ``argparse`` CLI parser."""
    
    parser = argparse.ArgumentParser(
        prog="reset_status_flags.py",
        description=(
            "Set selected Boolean status flags to false in every "
            "<datasets-root>/<dataset>/<meta-file>.json."
        ),
    )
    
    parser.add_argument(
        "-d",
        "--datasets-root",
        type=Path,
        default=Path("BrainScape"),
        help="Top-level BrainScape directory (default: %(default)s)",
    )
    
    parser.add_argument(
        "-m",
        "--meta-file",
        default="metadata.json",
        help="Metadata file name inside each dataset (default: %(default)s)",
    )
    
    parser.add_argument(
        "-k",
        "--keys",
        nargs="+",
        default=["isValidationCheckDone"],
        help="Flag names to reset (default: %(default)s)",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change but do not write files (default: %(default)s)",
    )
    
    return parser


def patch_file(
    meta_path: Path,
    target_keys: list[str],
    dry_run: bool
) -> bool:
    """
    For **every** *target_keys* in *meta_path* set the value to ``False``
    
    Returns
    -------
    bool
        ``True`` only when **all** keys exist, are boolean, and end up False.
        Otherwise returns ``False`` (the caller counts this as “failed”).
    """
    jh = JsonHandler(meta_path, create_if_missing=False)
    data = jh.get_data()

    changed = True
    for key in target_keys:
        if key not in data:
            changed = False
            print(f"  ⚠  missing key “{key}”")
        
        elif not isinstance(data[key], bool):
            changed = False
            print(f"  ⚠  key “{key}” is not boolean (type={type(data[key]).__name__})")
        
        # data[key] is bool and true, Set of False
        elif data[key]:
            data[key] = False
            # print(f"  ↳ {key}: True → False")
            print(f"  {key}: True → False")
        
        # data[key] is bool and already false
        else:
            print(f"  ✓ {key} already False")

    if changed and not dry_run:
        jh.set_data(data).save_json()

    return changed



def scan_datasets(
    root: Path,
    file_name: str,
    target_keys: list[str],
    dry_run: bool,
)  -> tuple[int, int]:
    """
    Walk *root* and patch every metadata file.

    Returns the number of patched and failed files.
    """
    patched = failed = 0
    for ds_dir in sorted(d for d in root.iterdir() if d.is_dir()):
        meta_path = ds_dir / file_name
        try:
            print(f"• {meta_path.relative_to(root)}")
            if patch_file(meta_path, target_keys, dry_run):
                patched += 1
            else:
                failed += 1
        except Exception as exc:  
            print(f"  ✗ unexpected error: {exc}")
    return patched, failed


if __name__ == "__main__":
    
    args = build_parser().parse_args()
    
    if args.dry_run:
        print(f"Note: CLI Argument --dry-run is set to {args.dry_run}, Metadata file will not be rewritten.")
    
    if not args.datasets_root.is_dir():
        raise SystemExit(f"✗ directory not found: {args.datasets_root}")


    patched, failed = scan_datasets(
        root=args.datasets_root,
        file_name=args.meta_file,
        target_keys=args.keys,
        dry_run=args.dry_run,
    )
    
    print(
        f"\nDone. {patched} file(s) patched"
        f"{' (dry-run)' if args.dry_run else ''}"
        + (f", {failed} failed." if failed else ".")
    )
    