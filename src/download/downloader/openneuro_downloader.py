# src/download/downloader/openneuro_downloader.py

import os
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Any, Dict
from download.downloader.base_plugin import DownloaderPlugin
from download.utils import (
    execute_command, 
    filter_files_by_glob_patterns,
    execute_in_parallel
)


logger = logging.getLogger(__name__)

class OpenNeuroDownloader(DownloaderPlugin):
    """
    Downloader class for OpenNeuro datasets using AWS CLI.
    """
    
    # Class-specific plugin name (not instance-specific)
    plugin_name = "OpenNeuroDownloader"
    
    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name
    
    
    def __init__(self, dataset_settings: Dict[str, Any], dataset_path: str, config: Dict[str, Any] ):
        """
        Initializes the OpenNeuroDownloader with dataset settings and path.

        Args:
            dataset_settings (Dict[str, Any]): Configuration settings for the dataset.
            dataset_path (str): The base path where datasets will be downloaded.
        """
        
        self.dataset_settings = dataset_settings
        self.dataset_path = Path(dataset_path)
        self.download_dir_path = self.dataset_path / dataset_settings["downloadDirName"]
        self.config = config
        
        self.download_from = dataset_settings["download"]["source"]
        self.download_glob_patterns = dataset_settings["download"]["include"]
        self.profile=dataset_settings["download"]["profile"]
        
        # Get the credential path from the config
        self.credential_path = self.config.get('credential_path')
        
        
    def _check_aws_cli_installed(self) -> bool:
        """
        Checks if AWS CLI is installed on the system.

        Returns:
            bool: True if AWS CLI is installed, False otherwise.
        """
        
        try:
            subprocess.run(["aws", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            logger.error("- OpenNeuro DL - AWS CLI is not installed. Please install AWS CLI to download datasets requiring it.")
            return False
    
    
    def _get_download_command(self, pattern: str) -> List[str]:
        """
        Constructs the AWS CLI command to download files matching a specific pattern.

        Args:
            pattern (str): The glob pattern to include in the download.

        Returns:
            List[str]: The AWS CLI command as a list of arguments.
        """
    
        aws_download_command = [
            "aws", "s3", "sync", self.download_from, str(self.download_dir_path),
            "--exclude", "*", "--include", pattern
        ]
        
        # Add '--profile' if profile is provided
        if self.profile:
            aws_download_command.extend(['--profile', self.profile])
        else:
            aws_download_command.append('--no-sign-request')

        
        
        return aws_download_command
    
    
    def _set_aws_profiles(self):
        # Verify that the profiles file exists
        if not os.path.isfile(self.credential_path):
            logger.error(f"The specified profiles file does not exist: {self.credential_path}")
            return False

        # Set the AWS_SHARED_CREDENTIALS_FILE environment variable
        abs_path = os.path.abspath(self.credential_path)
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = abs_path
        logger.info(f"AWS_SHARED_CREDENTIALS_FILE set to: {abs_path}")

    
    def download(self) -> Tuple[bool, List[str]]:
        """
        Executes the download process for the dataset.

        Returns:
            Tuple[bool, List[str]]: A tuple containing the success status and a list of outputs from each download command.
        """
        
        logger.info(f"Starting download for dataset:{self.dataset_path.name}, from '{self.download_from}'")
        
        # open neuro datasets require AWS CLI
        if not self._check_aws_cli_installed():
            logger.critical("- OpenNeuro DL - AWS CLI is not installed. Cannot download OpenNeuro datasets.")
            return False, []
        
        
        # Set the enviroment for file containing aws profiles
        self._set_aws_profiles()

        # Downloads each pattern sequentially [AWS CLI]
        outputs = []
        for pattern in self.download_glob_patterns:
            download_command = self._get_download_command(pattern)
            status, output = execute_command(download_command) 
            outputs.append(output)
            if not status:
                logger.error(f"- OpenNeuro DL - Download failed for pattern: '{pattern}', Dataset: '{self.dataset_path}'.")

                return False, outputs
        return True, outputs
    
    
    
    # The Download AWS Command in _get_download_command() can be used along with --dryrun 
    # Flag to dryrun the download without downloading any files. The output of the command
    # will be a list of File Paths. However, with large dataset I have found it to be super slow.
    # I have found "ls" command to be much more effective, and can be easily be run in parallel
    # to speed up the process.
    def _get_list_aws_dir_command(self, path: str, recursive: bool = True) -> List[str]:
        """
        Constructs the AWS CLI command to list contents of an S3 directory.

        Args:
            path (str): The S3 path to list.
            recursive (bool, optional): Whether to list directories recursively. Defaults to True.

        Returns:
            List[str]: The AWS CLI command as a list of arguments.
        """
        aws_list_command = ["aws", "s3", "ls", path]

         
        if recursive: 
            aws_list_command.append("--recursive")
        
        # Add '--profile' if profile is provided
        if self.profile:
            aws_list_command.extend(['--profile', self.profile])
        else:
            aws_list_command.append('--no-sign-request')
        
        return aws_list_command
    
    
    def _list_aws_dir_contents(self, path: str, recursive=False) -> list:
        """
        Lists the contents of an AWS S3 directory. 

        Args:
            path (str): The S3 path to list.
            recursive (bool, optional): Whether to list directories recursively. Defaults to False.

        Returns:
            List[str]: A list of file paths within the specified S3 directory.
        """
        path = path if path.endswith("/") else path + "/"
        list_command = self._get_list_aws_dir_command(path=path, recursive=recursive)
        status, output = execute_command(list_command) 
        
        # Get Files/Directories + Check if there are spaces in File Names
        ret_output  = []
        for line in output.splitlines():
            if "PRE" in line: # Contains Directory Path
                parts = line.strip().split()
                if len(parts) != 2: # Spaces in Name
                    logger.warning(f"- OpenNeuro DL - List AWS Dir - Spaces Detected in Dir Path: {line}, Dataset: {self.dataset_path}, Command: {' '.join(list_command)}")
                ret_output.append(" ".join(parts[1:])) # If Space in Path Join and Append, else Append.
                
            else: # Contains File Path
                parts = line.strip().split()
                if len(parts) != 4: # Spaces in Name
                    logger.warning(f"- OpenNeuro DL - List AWS Dir - Spaces Detected in File Path: {line}, Dataset: {self.dataset_path}, Command: {' '.join(list_command)}")
                ret_output.append(" ".join(parts[3:])) # If Space in Path Join and Append, else Append.
        
        if not status:
            logger.error(f"- OpenNeuro DL - List AWS Dir - Unable to List AWS S3 directory contents for '{path}': {output}")
            return [] 
        return ret_output
    
    
    def get_source_file_list(self)-> List[str]:
        """
        Retrieves a list of source files from the S3 bucket based on the provided glob patterns.

        Returns:
            List[str]: A filtered list of file paths that match the glob patterns.
        """
    
        # Note:
        # Download Manager expects an actual list of File which were supposed to be downloaded.
        # This is possible for Open Neuro Dataset. Furthermore, The Human Connectome Project 
        # is also using open Neuro Downloader. But I have disabled the download check by passing 
        # the actually downloaded files which is what the download manager compares with. So if the
        # if the verifyFiles key is false in the metadata.json for the dataset. The check will be off.
        # else if verifyFiles == true or not provided (defaults to true) then it will skip checking
        verify_downlaoded_files = self.dataset_settings["download"].get("verifyFiles", True)
        if not verify_downlaoded_files:
            return [str(p.relative_to(self.download_dir_path)) for p in self.download_dir_path.rglob('*') if p.is_file()]
        
        
        
        # Just List The Parent Diretory Content
        main_dir_contents = self._list_aws_dir_contents(path=self.download_from, recursive=False)
        
        # Removing the Contents that does not follow the glob pattern
        filtered_contents = filter_files_by_glob_patterns(
            fileList=main_dir_contents, 
            patterns=self.download_glob_patterns , 
            only_match_first_level=True)
        

        # Recursively get all of the contents from the folders
        filtered_files = [file for file in filtered_contents if not file.endswith("/")]
        filtered_dirs = [file for file in filtered_contents if file.endswith("/")] 
        filtered_paths = [os.path.join(self.download_from, filt_dir) for filt_dir in filtered_dirs]
        

        # Acquiring the Paths for all of the Files under Filtered directories
        args_list = [(path, True) for path in filtered_paths ] # path, recursive=True
        valid_paths_dataset = execute_in_parallel(target_function=self._list_aws_dir_contents, args_list=args_list)
        combined_paths = [path for path_list in valid_paths_dataset for path in path_list]
        valid_paths = ['/'.join(path.split('/')[1:]) for path in combined_paths]
        valid_paths.extend(filtered_files) 
        
        # Removing the Contents that does not follow the glob pattern
        filtered_contents = filter_files_by_glob_patterns(
            fileList=valid_paths, 
            patterns=self.download_glob_patterns , 
            only_match_first_level=False)

        return filtered_contents
