# BrainScape Research Paper

This repository contains the LaTeX source files for the research paper titled **"BrainScape: An Open-Source Framework for Integrating and Preprocessing Anatomical Datasets."**

To build the research paper, ensure you have the following tools installed:

1. **LaTeX Distribution with `pdflatex`**  
   A complete LaTeX distribution is required, as it includes `pdflatex` and necessary packages. Recommended distribution:
   - [TeX Live](https://www.tug.org/texlive/) (cross-platform)

   Verify installation by running:
   ```bash
   pdflatex --version
   ```
   
   **Sample Output:**
   ```
   pdfTeX 3.141592653-2.6-1.40.22 (TeX Live 2022/dev/Debian)
   ...
   ```


2. **Biber**  
   Required for managing references using BibLaTeX with the `apa` style. Biber is typically included in modern LaTeX distributions like TeX Live.  
   Verify installation by running:
   ```bash
   biber --version
   ```

3. **GNU Make** (Optional)  
   To utilize the provided `Makefile` for automated builds. If GNU Make is not installed, you can build the PDF manually as described below.


### Compile PDF

#### Manually

Go to `research_paper/` directory, then create a `build/` directory if not present and
Execute the following commands sequentially:

```bash
pdflatex -output-directory=build main
biber -output-directory=build main
pdflatex -output-directory=build main
pdflatex -output-directory=build main
```

#### Using Makefile

From the `research_paper/` directory, run:

```bash
make pdf
```

**Output**:
- `main.pdf` will be generated and placed in the `build/` directory.
- Log files will be captured in the `logs/` directory.


### Clean Build and Logs Directories (Via Makefile)

To remove the generated files and start a fresh build, run:

```bash
make clean
```

**Effect**:
- Clears/deletes all contents in the `build/` and `logs/` directories.