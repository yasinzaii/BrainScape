#tests/download/downloader/test_openneuro_downloader.py

import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple, Any, Dict
from unittest.mock import patch, MagicMock



# --- Add src to sys.path at the module level ---
# Calculate the path to the project root and src directory
project_root = Path(__file__).resolve().parents[3]  # Adjust based on your directory structure
src_path = project_root / 'src'
src_path_str = str(src_path)

# Add src_path to sys.path
if src_path_str not in sys.path:
    sys.path.insert(0, src_path_str)

from src.download.utils import (
    execute_command, 
    filter_files_by_glob_patterns,
    execute_in_parallel
)

# Now import OpenNeuroDownloader
from src.download.downloader.openneuro_downloader import OpenNeuroDownloader


class TestOpenNeuroDownloaderMocked(unittest.TestCase):
    
    def setUp(self):
        """
        Test cases for OpenNeuroDownloader using mocked dependencies.
        """
        # Define dummy dataset settings
        self.dataset_settings = {
            "downloadDirName": "Download",
            "downloadFrom": "s3://openneuro.org/ds005503/",
            "download": [
                "CHANGES",
                "dataset_description.json",
                "sub-02*anat*.json"
                "sub-01/ses-01/anat/*.json"
            ]
        }
        
        # Define a dummy dataset path
        self.dataset_path="/dummy/path"
        
    
        # Initialize the OpenNeuroDownloader instance
        self.downloader = OpenNeuroDownloader(
            dataset_settings=self.dataset_settings,
            dataset_path=self.dataset_path
        )
        
    def tearDown(self):
        # Remove src_path from sys.path
        if src_path_str in sys.path:
            sys.path.remove(src_path_str)
            
        
    @patch('src.download.downloader.openneuro_downloader.execute_command')
    @patch.object(OpenNeuroDownloader, '_get_download_command')
    @patch.object(OpenNeuroDownloader, '_check_aws_cli_installed', return_value=True)
    def test_download_success(self, mock_check_aws_cli, mock_get_download_command, mock_execute_command):
        """
        Test the download method when all download commands succeed.
        """
        # Define dummy return values for _get_download_command
        mock_get_download_command.return_value = ["Dummy Command"]
        
        # Define dummy return values for execute_command (status=True)
        mock_execute_command.return_value = (True, "Download successful")
        
        # Call the download method
        success, outputs = self.downloader.download()
        
        # Assertions
        self.assertTrue(success)
        self.assertEqual(len(outputs), len(self.dataset_settings["download"]))
        self.assertListEqual(outputs, ["Download successful"]*len(self.dataset_settings["download"]))
        
        # Verify that _get_download_command was called twice with correct patterns
        expected_calls = [ unittest.mock.call(pattern) for pattern in self.dataset_settings["download"]]
        mock_get_download_command.assert_has_calls(expected_calls, any_order=False)
    
        # Verify that execute_command was called with correct commands
        expected_command_calls = [unittest.mock.call(["Dummy Command"]) for _ in range(len(self.dataset_settings["download"]))]
        mock_execute_command.assert_has_calls(expected_command_calls, any_order=False)


    @patch('src.download.downloader.openneuro_downloader.execute_command')
    @patch.object(OpenNeuroDownloader, '_get_download_command')
    @patch.object(OpenNeuroDownloader, '_check_aws_cli_installed', return_value=True)
    def test_download_failure(self, mock_check_aws_cli, mock_get_download_command, mock_execute_command):
        """
        Test the download method when one of the download commands fails.
        """

        # Define dummy return values for _get_download_command
        mock_get_download_command.side_effect = [
            ["Dummy Command 1"],
            ["Dummy Command 2"],
            ["Dummy Command 3"],
            ["Dummy Command 4"]
        ]
        
        # Define dummy return values for execute_command
        # First two commands succeed, third fails
        mock_execute_command.side_effect = [
            (True, "Download successful 1"),
            (True, "Download successful 2"),
            (False, "Download failed 3"),
            (True, "Download successful 4")
        ]
        
        # Call the download method
        success, outputs = self.downloader.download()
        
        # Assertions
        self.assertFalse(success)
        self.assertEqual(len(outputs), 3)  # Should stop after the first failure
        self.assertListEqual(outputs, ["Download successful 1", "Download successful 2", "Download failed 3"])
        
        # Verify that _get_download_command was called up to the failure
        expected_calls = [unittest.mock.call(pattern) for pattern in self.dataset_settings["download"][:3]]
        mock_get_download_command.assert_has_calls(expected_calls, any_order=False)
    
        # Verify that execute_command was called up to the failure
        expected_command_calls = [unittest.mock.call(["Dummy Command 1"]),
                                  unittest.mock.call(["Dummy Command 2"]),
                                  unittest.mock.call(["Dummy Command 3"])]
        mock_execute_command.assert_has_calls(expected_command_calls, any_order=False)
        

        

@unittest.skip("Skipping all tests in TestOpenNeuroDownloaderIntegration - Takes long time.") 
class TestOpenNeuroDownloaderIntegration(unittest.TestCase):
    """
    Integration test for OpenNeuroDownloader that performs actual downloads.
    WARNING: This test will perform real downloads and can be slow or fail due to network issues.
    It is advisable to run this test separately or conditionally.
    """
    def setUp(self):
        """
        Set up the test environment before each test method.
        Creates a temporary directory for downloads.
        """
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Common Target Download Structure
        self.target_files_matching_pattern = [   
            "CHANGES",
            "dataset_description.json",          
            "sub-01/ses-01/anat/sub-01_ses-01_T1w.json",
            "sub-02/ses-02/anat/sub-02_ses-01_T1w.json",
            "sub-02/ses-02/anat/sub-02_ses-02_T1w.json"
        ]
        
        # Define dataset settings with the temporary directory
        self.dataset_settings: Dict[str, Any] = {
            "downloadDirName": "Download",  # Use temporary directory
            "downloadFrom": "s3://openneuro.org/ds005503",  # Small Open Neuro Dataset
            "download": [
                "CHANGES",
                "dataset_description.json",
                "sub-02/*anat*.json",
                "sub-01/ses-01/anat/*.json"
            ]
        }
        
        # Define a dummy dataset path (if needed by OpenNeuroDownloader)
        self.dataset_path: str = self.temp_dir
        
        # Initialize the OpenNeuroDownloader instance
        self.downloader = OpenNeuroDownloader(
            dataset_settings=self.dataset_settings,
            dataset_path=self.dataset_path
        )
        

    def tearDown(self):
        """
        Clean up the test environment after each test method.
        Removes the temporary directory and its contents.
        """
        shutil.rmtree(self.temp_dir)
        
    
    def test_download_and_get_source_file_list(self):
        """
        Test the download method by performing actual downloads to a temporary directory.
        Test the get_source_file_list method by getting actual file paths from remote source directory.
        """

        aws_cli_installed = self.downloader._check_aws_cli_installed()
        if not aws_cli_installed:
            self.skipTest("AWS CLI is not installed. Skipping actual download test.")

        # Call the download method
        success, outputs = self.downloader.download()
        
        # Assertions
        self.assertTrue(success)
        self.assertEqual(len(outputs), len(self.dataset_settings["download"]))        
        
        # Verify that the expected files exist in the temporary directory
        download_dir = Path(self.temp_dir) / self.dataset_settings["downloadDirName"] 
        downloaded_files = [ str(file.relative_to(download_dir)) for file in  download_dir.rglob('*') if file.is_file()]
        
        # Aquire All of the files from the Remote Source With Follows the Target Pattern and match with the downlaoded files
        valid_downlaodable_files = self.downloader.get_source_file_list() 
        self.assertEqual(sorted(downloaded_files), sorted(valid_downlaodable_files))
        
