# Creating a Custom Downloader Plugin for BrainScape

This tutorial provides detailed instructions on how to create, configure, and integrate your own custom downloader plugin into the BrainScape framework. 

This guide assumes you have reviewed the [**BrainScape API Overview**](https://github.com/yasinzaii/BrainScape/blob/main/tutorials/BrainScape-API-overview.md) tutorial, understanding how plugins are dynamically loaded and executed by the BrainScape.

---

## 1. Overview

BrainScape uses a plugin-based architecture for its pipeline stages (download, map, preprocess). Each stage has:

* An **Abstract Base Class** defining mandatory methods.
* A **Plugin Loader** that dynamically discovers and registers plugins.
* A **Stage Manager** that selects and executes plugins based on dataset-specific configurations.

For the download stage, your custom downloader must inherit from base `DownloaderPlugin` and implement:

* `download()` – the method responsible for fetching data.
* `get_source_file_list()` – optionally used for validating downloaded files against expected remote sources (added specifically for OpenNeuro - *Should be removed in future*).

---

## 2. Decide on File Verification

BrainScape’s `DownloadManager` verifies the downloaded files by comparing them to expected list of files path obtained from the source. 
For this option to work the remote source should be able to send a list of valid files that would be compared to the downloaded files.
However, acquiring a list of file may not be supported by the remote resource, therefore, in this tutoiral we will show how to skip it.

Therefore, consider:

* If you **can easily** retrieve a remote file list:

  * Implement `get_source_file_list()` to return file paths from the source.

* If it’s **difficult or unnecessary** to obtain a remote file list:

  * Implement `get_source_file_list()` to return the already downloaded local file paths, a hack for effectively skipping validation (Implemented in this example).

The second approach (passing the already downlaoded file list) is implemented when downloading from sources where acquiring list of valid file is not possible.

TODO: This file verification check will be moved to the individual plugins. Therefore `get_source_file_list()` check should be done by the plugins themselfs if possible. Plugins will not be required to provide implementation of this function and it will simplify the plugin interface.

---

## 3. Step-by-Step Custom Downloader Implementation

### Create Plugin File

Place your new plugin file within:

```
src/download/downloader/my_custom_downloader.py
```

### Example Downloader Plugin Template

Here's a template for a custom downloader:

```python
# src/download/downloader/my_custom_downloader.py
import logging
import requests
from pathlib import Path
from typing import List, Tuple, Dict, Any
from download.downloader.base_plugin import DownloaderPlugin

logger = logging.getLogger(__name__)

class MyCustomDownloader(DownloaderPlugin):
    """Downloader plugin to fetch Nifti files from example.com."""

    plugin_name = "MyCustomDownloader"

    @classmethod
    def get_name(cls) -> str:
        return cls.plugin_name

    def __init__(self, dataset_settings: Dict[str, Any], dataset_path: str, config: Dict[str, Any]):
        """
        Initialize your custom downloader.

        Args:
            dataset_settings (dict): Dataset-specific settings from metadata.json + defaults JSON.
            dataset_path (str): The base path where the dataset folder is located.
            config (dict): Overall pipeline config: default: <root-rep>/config/config.json.
        """

        # Common Data + Configs
        self.dataset_settings = dataset_settings  # Dataset metadata.json Path    
        self.dataset_path = Path(dataset_path)  # Dataset Path, Default: <root-rep>/BrainScape/<Dataset ID>
        self.download_dir_path = self.dataset_path / dataset_settings["downloadDirName"] # Dataset Download Dir, Default: 
        self.config = config 

        # Plugin Specific Configs
        # In the dataset configuration file you can add any configuration that your plugin needs.
        # For example: Consider this plugin requires a list of Nifti URLs to download. 
        # The URLs are provided as array in metadata.json under download.myInclude key 
        # "download"."myInclude": [
        #   "https://example.com/data/sub-001_T1w.nii.gz",
        #   "https://example.com/data/sub-001_T2w.nii.gz" ]
        self.urls = dataset_settings["download"]["myInclude"]

        # Ensure download directory exists
        self.download_dir_path.mkdir(parents=True, exist_ok=True)


    def _download_file(self, url: str) -> Tuple[bool, str]:
        # Your custom downloader implementation for downloading NiFI URLs
        # ...
        

    def download(self) -> Tuple[bool, List[str]]:
        overall_success = True

        # ------------------------------------
        # YOUR CUSTOM DOWNLOADER LOGIC
        for url in self.urls:
            success = self._download_file(url)
            overall_success = success if not success else overall_success
        #--------------------------------------

        # This function should return 
        #   * Status of Download Operation ('overall_success')
        #   * List of downloaded file paths relative to download folder (not required, Passing None here).  
        return overall_success, None

    def get_source_file_list(self) -> List[str]:
        """
        Since retrieving a remote file list isn't practical, this implementation
        returns downloaded local file paths to bypass remote-local validation.
        """
        return [
            str(file.relative_to(self.download_dir_path))
            for file in self.download_dir_path.rglob('*') if file.is_file()
        ]
```

### Explanation:

* **`plugin_name`**: Unique identifier referenced in dataset configurations.
* **Constructor (`__init__`)**: Initializes plugin and loads dataset-specific parameters.
* **`download()`**: Core method that fetches the files.
* **`get_source_file_list()`**: Provides a local file list, bypassing verification (Not required).

---

## 4. Configuring Dataset to Use Custom Downloader

Modify your dataset’s `metadata.json` file (`BrainScape/<DatasetID>/metadata.json`):

```json
"download": {
    "isDownloadable": true,
    "plugin": "MyCustomDownloader",
    "myInclude": [
        "https://example.com/data/sub-001_T1w.nii.gz",
        "https://example.com/data/sub-001_T2w.nii.gz"
    ]
}
```
Required Configs:

* `plugin`: Matches your downloader’s `plugin_name`.

Custom (Plugin Specific) Configs:

* `myInclude`: URLs of files to download.

---

## 5. Run and Validate Your Plugin

Activate your BrainScape environment and run the pipeline:

```bash
conda activate bs
python src/prepare_dataset.py
```

Check logs (`logs/prepareDataset.log` and `logs/errors.logs`) for plugin execution details. After successful execution:

* Files will be downloaded in dataset download directory.
* `isDownloaded` in `metadata.json` will update to `true`.

## 6. Important Consideration

Your download plugin is free to download the MRI data in any structure and It will be the responsibility 
of the Mapper plugin (Regex Mapper) to map individual Nifti files to subject, sesssion and modality bins.
However, if the downloader plugin downlods the dataset in BIDS format every subject and session has 
invidual folder and it requires very straight forward regex patterns to map such datasets.

