# **BrainScape API Overview**

This tutorial explains BrainScape’s internal Python plugin interface and shows how the framework discovers, loads, and executes any downloader, mapper, or pre-processor plugin.

---

## 1 · What kind of API does BrainScape use?

BrainScape exposes an **internal plugin interface** written entirely in Python.
Each pipeline stage such as download, map, or preprocess includes:

* an **abstract base class** that declares the methods every plugin must implement
* a **plugin loader** that scans a stage-specific folder, imports each module, registers every subclass of the base class under a unique identifier (the plugin name)
* a **stage manager** that reads a dataset’s configuration, requests the plugin class whose name matches with the value of the identifier in the dataset-sepcifc configuration, creates an instance, then calls the standard method (`download`, `map`, or `run`).

Because every decision is stored in dataset-specific configuration files, the core code never changes when you swap or add functionality.

---

## 2 · Directory layout

```
<repository-root>/
│
├─ src/
│   ├─ utils/
│   │   └─ plugin_loader.py
│   ├─ download/
│   │   ├─ downloader/            ← downloader plugins
│   │   └─ download_manager.py
│   ├─ dataset/
│   │   ├─ mapper/                ← mapper plugins
│   │   └─ dataset_manager.py
│   └─ preprocess/
│       ├─ preprocessor/          ← pre-processor plugins
│       └─ preprocess_manager.py
│
└─ BrainScape/<DatasetID>/        ← one folder per dataset
```

Every stage has its own plugin sub-folder and abstract plugin base class in that folder (e.g. `src/preprocess/preprocessor`). The Plugin loader in `src/utils/plugin_loader.py` is shared by all stages.

A **stage manager** (for example `PreprocessManager` in `preprocess_manager.py`) reads dataset settings, resolves a plugin name, asks the loader for the matching class, instantiates it, then calls its standard method.
The **plugin loader** scans the relevant folder, imports every module, registers subclasses, and stores a map of `name → class`.


## 3 · The plugin contract

Below is the simplified abstract base class for pre-processors; downloaders and mappers follow similar pattern.

```python
class PreprocessorPlugin(ABC):
    plugin_name = "BasePreprocessor"

    @classmethod
    def get_name(cls):
        return cls.plugin_name

    @abstractmethod
    def __init__(self, dataset_settings, dataset_path, mapping, config):
        """
        Args:
            dataset_settings (dict): Dataset-specific settings
            dataset_path     (Path): Root directory of the dataset
            mapping          (dict): Mapping produced by the mapper stage
            config           (dict): Global configuration
        """
        ...

    @abstractmethod
    def run(self) -> bool:
        """Return True if preprocessing succeeds."""
```

* **`plugin_name`** or **`get_name`** provides the plugin name and its is the identifier that appears in configuration files for a dataset for plugin selection.
* The preprocessor plugin's constructor receives all context (dataset settings, dataset root, mapping record, global config) - abstract class for other stages might be different.
* The `run` method performs the preprocesing and returns `True` on success.

Any concrete plugin must implement every abstract method.


## 4 · Dynamic discovery – how the loader works

```python
loader = PluginLoader(plugin_dir, PreprocessorPlugin)
loader.load_plugins()
```

`PluginLoader.load_plugins()` performs four actions:

1. Check that the plugin directory exists.
2. Import every `.py` file in that directory except `__init__.py`.
3. For each imported module, find classes that inherit from the requested base class (e.g. `PreprocessorPlugin`) and ignore the base class itself.
4. Obtain the identifier from `get_name()` or `plugin_name` and store `{identifier: plugin class}` in `plugin_map`.

The loader logs every plugin it registers, which simplifies troubleshooting.

---

## 5 · Dataset-specific Configurations decide everything

Each dataset owns `BrainScape/<DatasetID>/metadata.json`.
Global defaults live in `config/metadata.json`. 
The two files are merged, with dataset values overriding defaults, if available.

Example dataset-specific configs for preprocessing block:

```json
"preprocess": {
  "preprocessor": "brats",
  "preprocessDirName": "preprocessed",
  "brats": {
    "tempDirName": "temp",
    "modPriority": ["t1w", "t2w", "t1ce", "flair"]
  }
}
```

* The value for `preprocess.preprocessor` selects the plugin.
* The child object `brats` passes parameters directly to that `brats` plugin via `dataset_settings`.
* Replacing  `preprocess.preprocessor` with `"smriprep"` would load `SmriprepPreprocessor` instead, no code changes required.


## 6 · Manager workflow in detail

`PreprocessManager.initiate_preprocessing()` repeats the following for every dataset:

1. Merge dataset settings with global defaults.
2. Skip if `isPreprocessed` key in dataset-secific `metadata.json` file is `true` and the preprocessed folder already contains files.
3. Read the plugin name from configuration, ask the loader for the class, and instantiate it.
4. Call `run()` and update `isPreprocessed` according to the result.

`DownloadManager` and `DatasetManager` follow the same pattern with their own method names.

---

## 7 · Concrete example: `BratsPreprocessor`

```python
class BratsPreprocessor(PreprocessorPlugin):
    plugin_name = "brats"

    def __init__(self, dataset_settings, dataset_path, mapping, config):
        super().__init__(dataset_settings, dataset_path, mapping, config)
        self.skip_brain_extraction = dataset_settings["preprocess"]["brats"].get(
            "skipBrainExtraction", False
        )

    def run(self):
        # 1   Iterate over mapping entries
        # 2   Co-register modalities
        # 3   Warp to SRI-24 atlas
        # 4   Brain-extract with HD-BET unless skip flag is true
        # 5   Normalise intensities
        # 6   Write results to the preprocessed directory
        return True
```

All paths, flags, and parameters come from `dataset_settings`, so the same class can run unchanged on many datasets.


## 8 · Status flags

Each dataset’s `metadata.json` tracks progress with Boolean keys (`isDownloaded`, `isPreprocessed`, and others). Managers consult these keys before starting work, allowing the pipeline to resume if interrupted and preventing processing again if the dataset already preprocessed.

Note: The script `src/reset_status_flags.py` can reset any subset of flags across all datasets to reprocess or redownload all datasets.

---

## 9 · Writing your own plugin

1. Choose the stage and open its plugin folder.
2. Copy the template below (for preprocessor plugin), rename the class, and insert your logic.

```python
from preprocess.preprocessor.base_plugin import PreprocessorPlugin
from pathlib import Path
from typing import Dict, Any

class MyNewPreprocessor(PreprocessorPlugin):
    plugin_name = "my_new_preprocessor"

    def __init__(self, dataset_settings: Dict[str, Any],
                 dataset_path: Path,
                 mapping: Dict[str, Any],
                 config: Any):
        super().__init__(dataset_settings, dataset_path, mapping, config)

    def run(self) -> bool:
        # implement your algorithm here
        return True
```

3. Save the file in the plugin folder (in this case src/preprocess/preprocessor).
4. Add `"preprocessor": "my_new_preprocessor"` to the dataset’s `metadata.json`.
5. Execute `python src/prepare_dataset.py`.
   The loader will find the new class automatically; no engine edits are needed.

---

## 10 · Why this approach works

The plugin interface keeps the engine compact and stable, lets researchers mix different strategies on a per-dataset basis, and guarantees reproducibility because every choice is stored in human-readable dataset-specific configuration files.

---

## 11 · Useful references

* `src/utils/plugin_loader.py` – plugin loader for dynamic discovery and plugin registration
* `src/preprocess/preprocessor/base_plugin.py` – abstract contract for pre-processors plugins
* `src/preprocess/preprocess_manager.py` – manager logic for preprocessor stage
