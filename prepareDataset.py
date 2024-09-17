maxAwsCliWorkers = 32 

requiredSettingsKeys = [
    "isDownloadable",
    "includeDataset",
    "downloadDirName",
    "preprocessDirName",
    "preprocessing",
    "isDownloaded",
    "isPreprocessed",
    "datasetSource",
    "download",
    "downloadFrom", 
    "mriDataMapping"
]

import argparse, os, sys, glob  
import json, shutil, subprocess
import fnmatch, logging
from pathlib import Path
from threading import Lock
from omegaconf import OmegaConf
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging based on the provided log level.
def configure_logging(logLevel: str, logFileName: str):
    numericLevel = getattr(logging, logLevel.upper(), None)
    if not isinstance(numericLevel, int):
        raise ValueError(f"Invalid log level: {logLevel}")

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(numericLevel)
        
    # Configure logging
    logging.basicConfig(
        level=numericLevel,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # Log to console
            logging.FileHandler(logFileName)  # Log to a file
        ]
    )
    logger = logging.getLogger(__name__)
    return logger

# Returns Arguments Parser
def get_parser(**parser_kwargs):
    
    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ("yes", "true", "t", "y", "1"):
            return True
        elif v.lower() in ("no", "false", "f", "n", "0"):
            return False
        else:
            raise argparse.ArgumentTypeError("Boolean value expected.")

    parser = argparse.ArgumentParser(**parser_kwargs)
    
    parser.add_argument(
        "-d",
        "--reDownload",
        type=str2bool,
        const=True,
        default=False,
        nargs="?",
        help="Removes and Redownloads all Datasets",
    )
    
    parser.add_argument(
        "-p",
        "--reProcess",
        type=str2bool,
        const=True,
        default=False,
        nargs="?",
        help="Removes and Reprocesses all Datasets",
    )
    
    parser.add_argument(
        "-c",
        "--configPath",
        type=str,
        default="./config.json",
        help="Path to the configuration JSON file",
    )
    
    parser.add_argument(
        "-k",
        "--checkDownloadFiles",
        type=str2bool,
        const=True,
        default=True,
        nargs="?",
        help="Validate all downloaded file with corresponding File-Hashs",
    )
    
    parser.add_argument(
        "-l",
        "--logLevel",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level"
    )
    
    parser.add_argument(
        "-l",
        "--logFilePath",
        type=str,
        default="./prepareDataset.log",
        help="Path to the log file",
    )
    
    return parser

# Return all Subdiretories - {Paths | Dir-Names}
def get_subdirs(path, basenameOnly = False):
    subdirs = [d for d in get_paths(path) if os.path.isdir(d)]
    if basenameOnly:
        return [os.path.basename(d) for d in subdirs]
    return subdirs

# Return all Paths Satisfying Pattern
def get_paths(pathPattern):
    return glob.glob(pathPattern)

# JsonHandler class can Loads | Updates | Saves JSON
class JsonHandler:
    def __init__(self, jsonPath):
        self.jsonPath = jsonPath
        self.data = self.load_json()

    def load_json(self):
        try:
            with open(self.jsonPath, 'r') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            logger.error(f"File not found, file:'{self.jsonPath}'.")
            return {}  
        except PermissionError:
            logger.error(f"Permission denied for file '{self.jsonPath}'.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"The file '{self.jsonPath}' contains invalid JSON.")
            return {}
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading JSON file: '{self.jsonPath}' {e}")
            return {}

    def update_json(self, updates: dict) -> 'JsonHandler':
        if not isinstance(updates, dict):
            raise TypeError("Updates must be provided as a dictionary.")
        try:
            json.dumps(updates)  # Test if updates are JSON serializable
        except (TypeError, OverflowError) as e:
            raise ValueError(f"Updates contain non-serializable values: {e}")
        self.data.update(updates)
        return self

    def save_json(self):
        try:
            with open(self.jsonPath, 'w') as file:
                json.dump(self.data, file, indent=4)
        except Exception as e:
            logger.error(f"Error Saving JSON data: {e}")
            
    def delete_keys(self, keys):
        if not isinstance(keys, (list, tuple)):
            keys = [keys]
        for key in keys:
            self.data.pop(key, None)
                    
    def get_data(self):
        return self.data.copy()

# Returns Merged settings {Defaults, Overrides}
def merge_settings(defaults, overrides):
    if not isinstance(defaults, dict):
        raise TypeError("defaults must be a dictionary")
    if not isinstance(overrides, dict):
        raise TypeError("overrides must be a dictionary")
    finalSettings = defaults.copy()
    finalSettings.update(overrides)
    return finalSettings

# Validate Dataset Settings/Parameters provided in metadata.json
def validate_parameters(datasets, defaultSettings, config):
    if config.reDownload:
        logger.warning("Force Redownload Enabled, downloaded datasets will be removed (if downloadable) and redownloaded.")
    if config.reProcess:
        logger.warning("Force reProcess Enabled, preprocessed datasets will be removed and reprocessed.")
    
    # TO-DO 
    # Add logs to the preprocessed/downloaded folders and compare
    # if there are some settings/parameter change that does not match.
    
    # Checking the defaults (For All Datasets) Dataset Settings
    if not defaultSettings["isDownloadable"]:
        logger.warning(f"DefaultDatasetSettings['isDownloadable'] is set to {defaultSettings['isDownloadable']}")
    if not defaultSettings["includeDataset"]:
        logger.warning(f"DefaultDatasetSettings['includeDataset'] is set to {defaultSettings['includeDataset']}")
        
    datasetRemoveList = []
    for dataset in datasets:
        datasetPath = os.path.join(config.pathDataset, dataset)
        
        # Getting Dataset Specific Settings
        datasetSettings = JsonHandler(os.path.join(datasetPath, config.datasetSettingsJson))
        if not datasetSettings.get_data():
            logger.error(f"Unable to load settings for '{datasetPath}' dataset, Skipping this dataset")
            datasetRemoveList.append(dataset)
            continue       
        finalSettings =  merge_settings(defaults=defaultSettings, overrides=datasetSettings.get_data())

        # Check if All required Settings Keys are Present
        missingKeys = [key for key in requiredSettingsKeys if key not in finalSettings]
        if missingKeys:
            missingKeysStr = ', '.join(missingKeys)
            logger.error(f"Skipping '{dataset}' because of missing mandatory settings: {missingKeysStr}")
            datasetRemoveList.append(dataset)
            continue
        
        # Check if Dataset should be included
        if not finalSettings["includeDataset"]:
            logger.warning(f"Dataset: '{datasetPath}' set to excluded in {os.path.join(datasetPath, config.datasetSettingsJson)}")
            datasetRemoveList.append(dataset)
            continue 
        
        # Remove downloadDir and update settings if enforced
        if config.reDownload: 
            downloadPath = Path(os.path.join(datasetPath, finalSettings["downloadDirName"]))
            if downloadPath.exists() and downloadPath.is_dir():
                try:
                    shutil.rmtree(downloadPath)
                    logger.info(f"Directory '{downloadPath}' has been removed successfully ('reDownload' ON).")
                except Exception as e:    
                    logger.error(f"Failed to remove directory '{downloadPath}': {e}, ('reDownload' ON)")
                    datasetSettings.update_json({"isDownloaded":False}).save_json()
            
        # Remove datasetDir[pre-processed] and update settings if enforced
        if config.reProcess:
            preprocessPath = Path(os.path.join(datasetPath, finalSettings["preprocessDirName"]))
            if preprocessPath.exists() and  preprocessPath.is_dir():
                try:
                    shutil.rmtree(preprocessPath)
                    logger.info(f"Directory '{preprocessPath}' has been removed successfully.")
                except Exception as e:
                    logger.error(f"Failed to remove directory '{preprocessPath}': {e}, ('reProcess' ON)")
                datasetSettings.update_json({"isPreprocessed":False}).save_json()
                
        # Check if Dataset is Predownloaded if not isDownloadable 
        if not finalSettings["isDownloadable"]:
            downloadPath = Path(os.path.join(datasetPath, finalSettings["downloadDirName"]))  
            if not (downloadPath.exists() and downloadPath.is_dir() and any(downloadPath.iterdir())):
                logger.error(f"Undownloadable Dataset: '{downloadPath}', is not predownloaded, skipping this dataset")
                datasetRemoveList.append(dataset)    
                
    # Return list of datasets with valid settings
    return [d for d in datasets if d not in datasetRemoveList]


# Class Download Dataset based on dataset source
class DownloadDataset:

    def __init__(self, config: OmegaConf, targetDatasets: list, defaultDatasetSettings: dict):
        
        self.config = config
        self.targetDatasets = targetDatasets
        self.defaultDatasetSettings = defaultDatasetSettings
        self.aws_cli_installed = self.check_aws_cli_installed()
        
    def check_aws_cli_installed(self) -> bool:
        try:
            subprocess.run(["aws", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            logger.error("AWS CLI is not installed. Please install AWS CLI to download datasets requiring it.")
            return False

    def initiate_downloads(self) -> None:
        for datasetName in self.targetDatasets:
            self.download(datasetName)
    
    def download(self, datasetName: str) -> None:
        
        # TO-DO
        # Fix Force Redownload Logic
        
        # Path to this specific dataset
        datasetPath = os.path.join(self.config.pathDataset, datasetName)
        
        # Getting Dataset Specific Settings
        datasetSettings = JsonHandler(os.path.join(datasetPath, self.config.datasetSettingsJson))  
        finalSettings =  merge_settings(defaults=self.defaultDatasetSettings, overrides=datasetSettings.get_data())

        # Path of the download directory
        downloadDirPath = os.path.join(datasetPath, finalSettings["downloadDirName"])
        
        # Check if the dataset is marked downloaded but folder is empty
        if finalSettings["isDownloaded"] and ( not Path(downloadDirPath).is_dir() or not any(Path(downloadDirPath).iterdir())):
            logger.error(f"{datasetPath} Dataset 'isDownloaded' settings set to True, yet Download folder ('{downloadDirPath}') is Missing or Empty")
            logger.warning(f"Resetting 'isDownloaded' of '{datasetPath}' Dataset to False and Redownloading")
            datasetSettings.update_json({"isDownloaded":False}).save_json() 
            finalSettings["isDownloaded"] = False
                  
        # TO-DO 
        # Maybe Thorough checks is required even to match the contents as well. 
        # Now at the moment I am just trustin the falg. 
        
        # If downloaded Skip Downloadig
        if finalSettings["isDownloaded"] and Path(downloadDirPath).is_dir() and any(Path(downloadDirPath).iterdir()):
            if self.config.checkDownloadFiles:
                logger.info(f"'checkDownloadFiles' ON - Verifiying validity of downloaded files")
            else:
                logger.info(f"'{datasetPath}' Dataset already downloaded skipping download job")
                return  # Skip Downloaded
        
        # If not downloadable check if already downloaded
        if not finalSettings["isDownloadable"]:
            if Path(downloadDirPath).is_dir() and any(Path(downloadDirPath).iterdir()):
                logger.info(f"'{datasetPath}' Dataset is not downloadable and but already downloaded skipping download/Check job")
                return
            else :
                logger.error(f"'{datasetPath}' Dataset is not downloadable and the download folder is empty, skipping download Job")
            
        # Call the appropriate download method based on datasetSource
        downloadMethodName = f"download_from_{finalSettings['datasetSource'].lower()}"
        downloadMethod = getattr(self, downloadMethodName, None)
        if callable(downloadMethod):
            status = downloadMethod(finalSettings=finalSettings, datasetPath=datasetPath)
            # Update the 'isDownloaded' flag in dataset settings
            if status:
                datasetSettings.update_json({"isDownloaded":True}).save_json() # Note not updating final settings
            else:
                logger.error(f"Download Failed for {datasetPath} Dataset.")
                datasetSettings.update_json({"isDownloaded":False}).save_json()
                try:
                    shutil.rmtree(downloadDirPath)    
                except Exception as e:
                    logger.error(f"Failed to Remove the Download Directory: {downloadDirPath}")
                
        else:
            logger.error(f"No download method defined for datasetSource '{finalSettings['datasetSource']} of {datasetPath} Dataset.")

    
    # Execute AWS CLI command and return success status and output.
    def execute_aws_command(self, awsCommand: list, captureOutput: bool = True) -> tuple[bool, str]:
        logger.debug(f"Executing command: {' '.join(awsCommand)}")
        try:
            result = subprocess.run(awsCommand, check=True, capture_output=captureOutput, text=True)
            output = result.stdout if result.stdout else result.stderr
            return True, output
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed Executing AWS Command: {e}")
            return False, str(e)

    
    
    # Downloads each pattern sequentially [AWS CLI]
    def download_patterns_aws_cli(self, s3Path: str, downloadPath: str,  downloadPatterns: list, dryrun: bool) -> tuple[bool,list]:
        outputs = []
        for pattern in downloadPatterns:
            awsCommand = [
                "aws", "s3", "sync", "--no-sign-request", s3Path, downloadPath,
                "--exclude", "*", "--include", pattern
            ]
            awsCommand.append("--dryrun") if dryrun else None
            
            status, output = self.execute_aws_command(awsCommand)
            outputs.append(output)
            if not status:
                return False, outputs
        return True, outputs
    
    # Match File with Patterns and return only valid patterns
    def filter_files_by_download_pattern(self, fileList: list, patterns: list, onlyMatchFirstLevel: bool):
        includedFiles = []
        for file in fileList:
            compFile = file.split("/")[0] if onlyMatchFirstLevel else file  # First-level dir/file in the list
            for pattern in patterns:
                compPattern = pattern.split("/")[0] if onlyMatchFirstLevel else pattern
                if fnmatch.fnmatch(compFile, compPattern):
                    includedFiles.append(file)
                    break
        return includedFiles
    

    # List aws dir contents 
    def list_aws_dir_contents(self, s3Path: str, recursive: bool = True): 
        s3Path = s3Path if s3Path.endswith("/") else s3Path + "/"
        awsCommand = ["aws", "s3", "--no-sign-request", "ls", s3Path]
        if recursive: 
            awsCommand.append("--recursive") 
            
        status, output = self.execute_aws_command(awsCommand)
        if not status:
            logger.error(f"Unable to List AWS S3 directory contents for '{s3Path}': {output}")
            return [] 
        return [line.strip().split(" ")[-1] for line in output.splitlines()]
    
    # Run Multiple AWS Command 
    def run_multiple_aws_commands_list_dir(self, s3Paths, recursive):
        combinedData = [] 
        lock = Lock()
        # Create a thread pool to run multiple AWS commands concurrently
        with ThreadPoolExecutor(max_workers=min(len(s3Paths), maxAwsCliWorkers)) as executor:
            futureToPath = {
                    executor.submit(self.list_aws_dir_contents, path, recursive): path for path in s3Paths
            }
            for future in as_completed(futureToPath):
                path = futureToPath[future]
                try:
                    data = future.result()  # Get the result from the completed future
                    if data:
                        logger.debug(f"Completed processing for {path}")
                        with lock:
                            combinedData.extend(data)  # Append data from each command to the combined list
                except Exception as exc:
                    logger.error(f"{path} generated an exception: {exc}")
        return combinedData  # Return the combined data
    
    # Download Files/Folder names in OpenNeuro Dataset Main Directory
    def get_valid_dataset_contents(self, s3Path: str, downloadPatterns: list):
        
        # Just List The Parent Diretory Content
        mainDirContents = self.list_aws_dir_contents(s3Path=s3Path, recursive=False)
        
        # Removing the Contents that does not follow the pattern
        filteredContents = self.filter_files_by_download_pattern(fileList=mainDirContents, 
                                                                 patterns=downloadPatterns, 
                                                                 onlyMatchFirstLevel=True)
        # Recursively get all of the contents from the folders
        filteredFiles = [file for file in filteredContents if not file.endswith("/")]
        filteredDirs = [file for file in filteredContents if file.endswith("/")] 
        filteredPaths = [os.path.join(s3Path, filtDir) for filtDir in filteredDirs]
        
        # Acquiring the Paths for all of the Files under Filtered directories
        validPathsDataset = self.run_multiple_aws_commands_list_dir(s3Paths=filteredPaths, recursive=True)
        validPaths = ['/'.join(path.split('/')[1:]) for path in validPathsDataset]
        validPaths.extend(filteredFiles) 
        
        # Removing the Contents that does not follow the pattern
        filteredContents = self.filter_files_by_download_pattern(fileList=validPaths, 
                                                                 patterns=downloadPatterns, 
                                                                 onlyMatchFirstLevel=False)
        
        return filteredContents
        
        
        

    def download_from_openneuro(self, finalSettings: dict, datasetPath: str):
        
        # Path for download directory
        downloadPath = Path(datasetPath) / finalSettings["downloadDirName"]
        
        # Check if download directory is present
        if downloadPath.exists():
            if any(downloadPath.iterdir()):
                if not self.config.checkDownloadFiles:
                    logger.error(f"Dataset Download Folder '{datasetPath}' already exists and not empty, Skipping Download")
            else: 
                logger.warning(f"'{downloadPath}' exists but is empty. Proceeding with download.")
        else:
            # Create a download directory
            try: 
                downloadPath.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created download directory: '{downloadPath}'")
            except Exception as e:
                logger.error(f"Error creating download directory '{downloadPath}': {e}")
                return False

        # open neuro datasets require AWS CLI
        if not self.aws_cli_installed:
            logger.critical("AWS CLI is not installed. Cannot download OpenNeuro datasets.")
            return False

        # Get the s3 path and patterns from the dataset settings
        s3Path = finalSettings["downloadFrom"]
        downloadPatterns = finalSettings["download"]
        
        # Acuire Open Neuro Dataset Main Directory Contents [Not Downloading]
        selectedFilesPaths = self.get_valid_dataset_contents(s3Path=s3Path, downloadPatterns=downloadPatterns) 
        
        # Download The Dataset from Open Neuro
        status = False
        if not finalSettings["isDownloaded"]:
            logger.info(f"Downoading Dataset from {s3Path} to {str(downloadPath)}")
            status, cliOutputs = self.download_patterns_aws_cli(s3Path, str(downloadPath),  downloadPatterns, dryrun=False)
            if status:
                logger.info(f"Downoading Dataset Successful! from {s3Path} to {str(downloadPath)}")
            else:
                logger.error(f"Downoading Dataset Failed! from {s3Path} to {str(downloadPath)}")
        else:
            status = True
        
        # Verify the downloaded files and the selectedFilesPaths match 
        targetFiles = set(selectedFilesPaths) 
        downloadedFiles = set([str(p.relative_to(downloadPath)) for p in downloadPath.rglob('*') if p.is_file()])
        filePresenceCheck = True if targetFiles == downloadedFiles else False
        if filePresenceCheck:
            logger.info(f"filePresenceCheck Passed, Files from {s3Path} is present in {str(downloadPath)}.")
        if not filePresenceCheck:
            missingFiles = targetFiles - downloadedFiles
            extraFiles = downloadedFiles - targetFiles
            if missingFiles:
                logger.error(f"filePresenceCheck failed, Missing Files: {missingFiles}")
            if extraFiles:
                logger.error(f"filePresenceCheck failed, Extra Files: {extraFiles}")

        # Redownloading if Checks Fail
        if not filePresenceCheck or not status:
            logger.error(f"Error: Download or filePresenceCheck failed Resetting 'isDownload' Flag, '{downloadPath}'")
            return False
        
        
        # If Files are already downloaded and checkDownloadFiles just comparing paths as above is enough.
        #filePresenceCheck = False
        #if finalSettings["isDownloaded"] and self.config.checkDownloadFiles:
        #    pass
            
            
            
        
        # Check All Paths is compareAllFiles == True
        #status, cliOutputs = self.download_patterns_aws_cli(s3Path, str(downloadPath),  downloadPatterns, dryrun=True)
        
        # Download Code Should be here
        #status, cliOutputs = self.download_patterns_aws_cli(s3Path, str(downloadPath),  downloadPatterns, dryrun=False)
        return True

    def download_from_custom_source(self):
        # TO-DO 
        # Implement custom download logic here
        raise NotImplementedError("Custom download sources are not yet implemented.")



if __name__ == "__main__":
            
    # Parsing Args | Omega Config
    parser = get_parser()
    args = parser.parse_args()
    argsConfig = OmegaConf.create(vars(args))
    
    # Configure logging - Make sure logger is not called Before.
    logger = configure_logging(args.logLevel, argsConfig.logFilePath)
    
    # Loading the Config File | Merging
    jsonConfig = JsonHandler(argsConfig.configPath).get_data()
    config = OmegaConf.merge(jsonConfig, argsConfig)
    
    # Getting Dataset Lists and applying Overrides
    targetDatasets = []
    pathAllDatasets = os.path.join(os.path.normpath(config.pathDataset), '*' if not config.pathDataset.endswith('*') else '')
    datasets = get_subdirs(pathAllDatasets, basenameOnly=True)
    datasetOverrides = JsonHandler(config.pathOverrides).get_data()
    if "include" in datasetOverrides:
        targetDatasets = datasetOverrides["include"]
    elif "exclude" in datasetOverrides:
        targetDatasets = datasets.copy()
        for ex in datasetOverrides["exclude"]:
            if ex in targetDatasets:
                targetDatasets.remove(ex)
            else:
                raise ValueError(f"{ex} Dataset to exclude not found.")
    else:
        targetDatasets =  datasets   
    
    # Getting the Default Settings 
    defaultDatasetSettings = JsonHandler(config.pathDefaults).get_data()
    
    logger.info(f"Target Datasets: {targetDatasets}")
    
    # Validate Parameters, Returns list of dataset with valid Parameters/settings.
    targetDatasets = validate_parameters(datasets = targetDatasets.copy(), 
                                         defaultSettings = defaultDatasetSettings, 
                                         config = config)
    
    
    downloadDS = DownloadDataset(config = config, 
                    targetDatasets=targetDatasets, 
                    defaultDatasetSettings=defaultDatasetSettings)
    downloadDS.initiate_downloads()
    exit()
    
    print(targetDatasets)
    
    
    #pathAllDatasets = os.path.join(os.path.normpath(pathDataset.strip()), '*' if not pathAllDatasets.strip().endswith('*') else '')
    print(pathAllDatasets)
    exit()
    
    #print(datasets)
    
    
    subdirs = [d for d in ps]
    print(subdirs)
    config = OmegaConf.create(vars(args))
    
 
    
    # Read all 
    get_subdirs = get_subdirs(pathDS, basenameOnly=True)
    
    print(json.dumps(get_subdirs))
    
    
    print(config.reDownload)
    print(config.reProcess)

