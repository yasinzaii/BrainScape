#scanner_summary.py  -  Summarise scanner information in a BrainScape dataset.json
import sys
import pandas as pd
from pathlib import Path
from tabulate import tabulate
from collections import defaultdict, Counter


REQ_FIELDS   = ["Manufacturer", "ManufacturersModelName", "MagneticFieldStrength"]
CAPTION  = "Distribution of scanner manufacturers and field strength across modalities"
LABEL    = "tab:scanner_info"


LATEX_SPECIALS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}"
}

def latex_escape(text: str) -> str:
    """Escape LaTeX-special characters in a string."""
    for char, repl in LATEX_SPECIALS.items():
        text = text.replace(char, repl)
    return text


def build_table(df: pd.DataFrame) -> str:
    """Return nicely indented LaTeX code."""

    header_row = r"\textbf{Modality} & \textbf{Manufacturer} & \textbf{Model} & \textbf{Field (T)} & \textbf{Count} & \textbf{Missing} & \textbf{Total} \\"

    lines = [
        r"\begin{center}",
        r"\scriptsize",  
        r"\setlength{\LTpre}{0pt}\setlength{\LTpost}{0pt}",
        r"\begin{longtable}{@{}l c c c r r r@{}}",  # 7 columns
        fr"    \caption{{{CAPTION}}}\label{{{LABEL}}}\\",
        r"    \toprule",
        f"    {header_row}",
        r"    \midrule",
        r"    \endfirsthead",
        r"    \multicolumn{7}{@{}l}{\textit{Continued from previous page}}\\",
        r"    \toprule",
        f"    {header_row}",
        r"    \midrule",
        r"    \endhead",
        r"    \midrule",
        r"    \multicolumn{7}{@{}r}{\textit{Continued on next page}}\\",
        r"    \endfoot",
        r"    \bottomrule",
        r"    \endlastfoot",
    ]


    for modality, grp in df.groupby("Modality", sort=False):
        total_rows = int(grp["Total"].iloc[0])
        missing_rows = int(grp["Missing"].iloc[0])
        pad = " " * (len(modality) + 2)
        first = True

        for _, row in grp.iterrows():
            mod_cell = modality.title() if first else pad
            miss_cell = str(missing_rows) if first else ""
            tot_cell = str(total_rows) if first else ""
            first = False

            lines.append(
                "    "
                + latex_escape(mod_cell)
                + " & "
                + latex_escape(row["Manufacturer"])
                + " & "
                + latex_escape(row["Model"])
                + " & "
                + str(row["Strength"])
                + " & "
                + str(int(row["Count"]))
                + " & "
                + miss_cell
                + " & "
                + tot_cell
                + r" \\"  # <- proper row terminator
            )


    lines += [
        r"\end{longtable}",
        r"\end{center}",
        "",
    ]

    return "\n".join(lines)


def round_to_half(number):
  if not isinstance(number, (int, float)):
    if not number:
      return ''
    if number[-1] == "T":
      number = float(number[:-1])
  return str(round(number * 2) / 2)


def scanner_summary(data_dict, out_table_path):

    datasets_mapping = data_dict["mapping"]

    combo_counter  = Counter()                    # (modality, MFR, MODEL, B0) → count
    missing_by_mod = defaultdict(int)             # modality → cnt with missing scanner info
    total_by_mod   = defaultdict(int)             # modality → cnt of mapping entries

    for dataset, entries in datasets_mapping.items():
        for entry in entries:                     # each mapping row
            scanner_blk = entry.get("scanner", {})
            for modality in entry.get("mris", {}):
                total_by_mod[modality] += 1

                scan_info = scanner_blk.get(modality, {})
                if any(scan_info.get(f, "") for f in REQ_FIELDS):
                    combo = (
                        modality,
                        scan_info["Manufacturer"].upper(),
                        scan_info["ManufacturersModelName"].title(),
                        round_to_half(scan_info["MagneticFieldStrength"]),
                    )
                    combo_counter[combo] += 1
                else:
                    missing_by_mod[modality] += 1

    # Build pandas DataFrame
    rows = []
    for (mod, manuf, model, b0), n in combo_counter.items():
        rows.append({
            "Modality": mod.upper(),
            "Manufacturer": manuf,
            "Model": model,
            "Strength": b0,
            "Count":        n,
            "Missing": missing_by_mod.get(mod, 0),
            "Total":   total_by_mod.get(mod, 0)
        })

    df = pd.DataFrame(rows).sort_values(
        ["Modality", "Manufacturer", "Model", "Strength"],
        ignore_index=True
    )

    print("\n=== Scanner summary (per modality) ===")
    print(tabulate(df, headers="keys", tablefmt="github", showindex=False))

    # --- Print overall statistics ---
    total_mris = sum(total_by_mod.values())
    mris_with_info = df["Count"].sum()
    missing_total = sum(missing_by_mod.values())

    # Field‑strength
    strength_counts = (
        df[df["Strength"] != ""]
        .groupby("Strength")["Count"]
        .sum()
        .sort_index(key=lambda x: x.astype(float))
    )

    unique_manufacturers = sorted(
        m for m in df["Manufacturer"].unique().tolist() if m
    )
    
    print("\n=== Overall statistics ===")
    print(f"Total MRI series: {total_mris:,}")
    print(
        f"With complete scanner info: {mris_with_info:,} "
        f"({mris_with_info/total_mris:.1%})"
    )
    print(
        f"Missing scanner info: {missing_total:,} "
        f"({missing_total/total_mris:.1%})"
    )
    strengths_fmt = ", ".join(
        f"{s} ({c:,})" for s, c in strength_counts.items()
    )
    print(
        f"Distinct magnetic field strengths: {len(strength_counts)} "
        f"({strengths_fmt})"
    )
    print(
        f"Manufacturers found ({len(unique_manufacturers)}): "
        f"{', '.join(unique_manufacturers)}"
    )

    latex_str = build_table(df)
    Path(out_table_path).write_text(latex_str, encoding="utf-8")

if __name__ == "__main__":
    
  # Determine the project root directory
  PROJECT_DIR = Path(__file__).resolve().parents[2]  
  PAPER_DIR = Path(__file__).resolve().parents[1] / "research_paper" 
  CONFIG_FILE = PROJECT_DIR / "config" / "config.json"

  # Add 'src' to sys.path
  SRC_DIR = PROJECT_DIR / 'src'
  if SRC_DIR not in sys.path:
      sys.path.append(str(SRC_DIR))
  
  # Importing Modules from Main Project.    
  from utils.json_handler import JsonHandler

  # Configuration from Config.json File
  jsonConfig = JsonHandler(CONFIG_FILE).get_data()
  # Dataset Dir 
  datasetDir = PROJECT_DIR / jsonConfig["pathDataset"]
  # Dataset Mapping from dataset.json file
  datasets_mapping = JsonHandler(datasetDir/jsonConfig["datsetMriJson"]).get_data()

  data_dict = {
    "project_path": PROJECT_DIR,
    "papaer_path": PAPER_DIR, 
    "dataset_path": datasetDir,
    "config": jsonConfig, 
    "mapping": datasets_mapping
  }
  
  out_table_path = Path(PAPER_DIR) / "tables" / "supp_scanner_summary.tex"

  scanner_summary(
    data_dict=data_dict,
    out_table_path=out_table_path
  )