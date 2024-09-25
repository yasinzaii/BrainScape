# tests/download/test_utils.py
import time
import unittest
import subprocess
from unittest.mock import patch, Mock
from src.download.utils import (
    execute_command,
    filter_files_by_glob_patterns,
    execute_in_parallel
)
    


class TestExecuteCommand(unittest.TestCase):
    """Unit tests for the execute_command function in src/download/utils.py."""

    @patch('src.download.utils.subprocess.run')
    def test_execute_command_success_stdout(self, mock_run):
        """
        Test that execute_command returns (True, stdout) when the command executes successfully
        and produces output in stdout.
        """
        # Arrange
        mock_result = Mock()
        mock_result.stdout = "Command executed successfully."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        command = ['echo', 'Hello, World!']

        # Act
        success, output = execute_command(command)

        # Assert
        self.assertTrue(success)
        self.assertEqual(output, "Command executed successfully.")
        mock_run.assert_called_once_with(
            command,
            check=True,
            capture_output=True,
            text=True
        )
    
    def test_execute_command_success_stdout_real(self):
        """
        Test that execute_command returns (True, stdout) when the command executes successfully
        and produces output in stdout.
        """

        command = ['echo', 'Hello, World!']

        # Act
        success, output = execute_command(command)

        # Assert
        self.assertTrue(success)
        self.assertEqual(output, "Hello, World!\n")
        

    @patch('src.download.utils.subprocess.run')
    def test_execute_command_success_stderr(self, mock_run):
        """
        Test that execute_command returns (False, stderr) when the command executes successfully
        but produces no output in stdout, except it returns only in stderr.
        """
        # Arrange
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "Error."
        mock_run.return_value = mock_result

        command = ['ls', '/non_existent_directory']

        # Act
        success, output = execute_command(command)

        # Assert
        self.assertFalse(success)
        self.assertEqual(output, "Error.")
        mock_run.assert_called_once_with(
            command,
            check=True,
            capture_output=True,
            text=True
        )

    @patch('src.download.utils.subprocess.run')
    def test_execute_command_failure(self, mock_run):
        """
        Test that execute_command returns (False, error_message) when the command fails
        and raises CalledProcessError.
        """
        # Arrange
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=['false'],
            output='',
            stderr='Command failed.'
        )

        command = ['false']

        # Act
        success, output = execute_command(command)

        # Assert
        self.assertFalse(success)
        self.assertEqual(output, 'Command failed.')
        mock_run.assert_called_once_with(
            command,
            check=True,
            capture_output=True,
            text=True
        )

    @patch('src.download.utils.subprocess.run')
    def test_execute_command_empty_command(self, mock_run):
        """
        Test that execute_command handles empty command lists gracefully.
        """
        # Arrange
        command = []

        # Depending on how you want to handle this,
        # subprocess.run with an empty command list raises an exception.

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=command,
            output='',
            stderr='No command provided.'
        )

        # Act
        success, output = execute_command(command)

        # Assert
        self.assertFalse(success)
        self.assertEqual(output, 'No command provided.')
        mock_run.assert_called_once_with(
            command,
            check=True,
            capture_output=True,
            text=True
        )

    @patch('src.download.utils.subprocess.run')
    def test_execute_command_both_stdout_and_stderr(self, mock_run):
        """
        Test that execute_command prioritizes stderr over stdout when both are present.
        """
        # Arrange
        mock_result = Mock()
        mock_result.stdout = "Success output."
        mock_result.stderr = "Error output."
        mock_run.return_value = mock_result

        command = ['some_command']

        # Act
        success, output = execute_command(command)

        # Assert
        self.assertFalse(success)
        self.assertEqual(output, "Error output.")
        mock_run.assert_called_once_with(
            command,
            check=True,
            capture_output=True,
            text=True
        )



class TestExecuteInParallel(unittest.TestCase):
    def setUp(self):
        pass 
    
    def test_execute_in_parallel_normal_execution(self):
        # Define a simple target function
        def add(a, b):
            return a + b

        args_list = [(1, 2), (3, 4), (5, 6), (7, 8)]
        expected_results = [3, 7, 11, 15]

        # Execute in parallel
        results = execute_in_parallel(target_function=add, args_list=args_list)
        self.assertCountEqual(results, expected_results)


    def test_execute_in_parallel_empty_args_list(self):
        # Define a dummy target function
        def dummy_func():
            return "dummy"

        args_list = []
        expected_results = []

        # Execute in parallel
        results = execute_in_parallel(dummy_func, args_list)

        # Verify the results
        self.assertEqual(results, expected_results)
        
    @patch('src.download.utils.logger')
    def test_execute_in_parallel_with_exceptions(self, logger_run):
        # Define a target function that raises an exception for a specific input
        def divide(a, b):
            return a / b
        
        # Supressing divide by zero logs 
        logger_run.return_value = ""
        
        args_list = [(10, 2), (5, 0), (8, 4)]
        expected_results = [5.0, 2.0]
        
        # Execute in parallel
        results = execute_in_parallel(divide, args_list)
        
        self.assertCountEqual(results, expected_results)

    def test_execute_in_parallel_with_various_max_workers(self):
        def multiply(a, b):
            return a * b
        
        args_list = [(2, 3), (4, 5), (6, 7)]
        expected_results = [6, 20, 42]
        
        # Test with max_workers less than the number of tasks
        results = execute_in_parallel(multiply, args_list, max_workers=2)
        self.assertCountEqual(results, expected_results)
        
        # Test with max_workers equal to the number of tasks
        results = execute_in_parallel(multiply, args_list, max_workers=3)
        self.assertCountEqual(results, expected_results)
        
        # Test with max_workers greater than the number of tasks
        results = execute_in_parallel(multiply, args_list, max_workers=10)
        self.assertCountEqual(results, expected_results)
        
        # Test with max_workers=1 (serial execution)
        results = execute_in_parallel(multiply, args_list, max_workers=1)
        self.assertCountEqual(results, expected_results)


    def test_execute_in_parallel_various_return_types(self):
        def return_none():
            return None
        
        def return_dict(key, value):
            return {key: value}
        
        args_list_none = [(), (), ()]
        expected_results_none = [None, None, None]
        results_none = execute_in_parallel(return_none, args_list_none)
        self.assertCountEqual(results_none, expected_results_none)
        
        args_list_dict = [('a', 1), ('b', 2), ('c', 3)]
        expected_results_dict = [{'a': 1}, {'b': 2}, {'c': 3}]
        results_dict = execute_in_parallel(return_dict, args_list_dict)
        self.assertCountEqual(results_dict, expected_results_dict)

    def test_execute_in_parallel_variable_args(self):
        def concatenate(*args):
            return ''.join(map(str, args))
        
        args_list = [(1,), (2, 3), (4, 5, 6)]
        expected_results = ['1', '23', '456']
        results = execute_in_parallel(concatenate, args_list)
        self.assertCountEqual(results, expected_results)

    @patch('src.download.utils.logger') # For log supression
    def test_execute_in_parallel_all_exceptions(self, logger_run):
        def faulty_function(x):
            raise ValueError("Intentional Error")

        args_list = [(1,), (2,), (3,)]
        expected_results = []
        results = execute_in_parallel(faulty_function, args_list)
        self.assertEqual(results, expected_results)

    

def test_execute_in_parallel_long_running_tasks(self):
    def long_task(duration):
        time.sleep(duration)
        return duration + 1
    
    args_list = [(1,), (2,), (3,)]
    expected_results = [2, 3, 4]
    results = execute_in_parallel(long_task, args_list)
    self.assertCountEqual(results, expected_results)

    
class TestFilterFilesByGlobPatterns(unittest.TestCase):
    """Unit tests for the filter_files_by_glob_patterns function."""

    def setUp(self):
            """Set up common test data."""
            self.fileList = [   
                "CHANGES",
                "dataset_description.json",
                "dataset_info.text",
                "task_information.json",
                "README",
                "research_article.pdf",              
                "sub-01/ses-01/anat/mri_T1w.nii.gz",
                "sub-01/ses-01/anat/mri_T1w.json",
                "sub-01/ses-01/anat/info.json",
                "sub-01/ses-01/random_info.txt",
                "sub-01/ses-01/session_info.txt",
                "sub-01/rand_subject_info.txt",
                "sub-01/ses-02/anat/mri_T1w.nii.gz",
                "sub-01/ses-02/anat/mri_T1w.json",
                "sub-01/ses-02/anat/info.json",
                "sub-01/ses-02/random_info.txt",
                "sub-01/ses-02/session_info.txt",
                "sub-02/ses-01/anat/mri_T1w.nii.gz",
                "sub-02/ses-01/anat/mri_T1w.json",
                "sub-02/ses-01/anat/info.json",
                "sub-02/ses-01/random_info.txt",
                "sub-02/ses-01/session_info.txt",
                "sub-02/rand_subject_info.txt",
            ]
            
            # Only match First Level == True
            self.pattern_1 = ["dataset_description.json", "sub-02/ses-02/*"]
            self.expect_1 = [
                "dataset_description.json",
                "sub-02/ses-01/anat/mri_T1w.nii.gz",
                "sub-02/ses-01/anat/mri_T1w.json",
                "sub-02/ses-01/anat/info.json",
                "sub-02/ses-01/random_info.txt",
                "sub-02/ses-01/session_info.txt",
                "sub-02/rand_subject_info.txt",
            ]
            
            # Only match First Level == False
            self.pattern_2 = ["CHANGES", "sub-02/ses-02/*"]
            self.expect_2 = ["CHANGES"]
            
            # Only match First Level == False
            self.pattern_3 = ["dataset*"]
            self.expect_3 = ["dataset_description.json",
                            "dataset_info.text"]
            
            # Only match First Level == False
            self.pattern_4 = ["sub-02/ses-01/anat/*"]
            self.expect_4 = [
                "sub-02/ses-01/anat/mri_T1w.nii.gz",
                "sub-02/ses-01/anat/mri_T1w.json",
                "sub-02/ses-01/anat/info.json"
            ]
            
            # Only match First Level == False
            self.pattern_5 = ["sub-*m_info*"]
            self.expect_5 = [
                "sub-01/ses-01/random_info.txt",
                "sub-01/ses-02/random_info.txt",
                "sub-02/ses-01/random_info.txt"
            ]
            
            # Only match First Level == False
            self.pattern_6 = ["sub-3*", "*.exe", "*.py"]
            self.expect_6 = []
            
            # Only match First Level == True
            self.pattern_7 = ["*", "sub-*"]
            self.expect_7 = self.fileList
            
            # Only match First Level == True
            self.pattern_8 = ["README", "CHANGES", "dataset_*", "research*", "sub*/ses-30", "task_*" ]
            self.expect_8 = self.fileList
            
            # Only match First Level == True (Empty test Pattern Check)
            self.pattern_9 = []
            self.expect_9 = []
            
            # Emplty File List Check [Note The Passed File list passed is empty]
            self.pattern_10 = ["CHANGES", "sub-02/ses-02/*"]
            self.expect_10 = []
            
    def test_only_match_first_level_true(self):
        """Test Case 1: only_match_first_level=True with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=self.fileList,
            patterns=self.pattern_1,
            only_match_first_level=True
        )
        self.assertEqual(sorted(result), sorted(self.expect_1))
            
    def test_only_match_first_level_false(self):
        """Test Case 2: only_match_first_level=False with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=self.fileList,
            patterns=self.pattern_2,
            only_match_first_level=False
        )
        self.assertEqual(sorted(result), sorted(self.expect_2))

    def test_case_3(self):
        """Test Case 3: only_match_first_level=False with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=self.fileList,
            patterns=self.pattern_3,
            only_match_first_level=False
        )
        self.assertEqual(sorted(result), sorted(self.expect_3))
        
    def test_case_4(self):
        """Test Case 4: only_match_first_level=False with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=self.fileList,
            patterns=self.pattern_4,
            only_match_first_level=False
        )
        self.assertEqual(set(result), set(self.expect_4))
        
    def test_case_5(self):
        """Test Case 5: only_match_first_level=False with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=self.fileList,
            patterns=self.pattern_5,
            only_match_first_level=False
        )
        self.assertEqual(sorted(result), sorted(self.expect_5))
    
    def test_case_6(self):
        """Test Case 6: only_match_first_level=False with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=self.fileList,
            patterns=self.pattern_6,
            only_match_first_level=False
        )
        self.assertEqual(sorted(result), sorted(self.expect_6))
    
    def test_case_7(self):
        """Test Case 7: only_match_first_level=True with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=self.fileList,
            patterns=self.pattern_7,
            only_match_first_level=True
        )
        self.assertEqual(sorted(result), sorted(self.expect_7))
    
    def test_case_8(self):
        """Test Case 8: only_match_first_level=True with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=self.fileList,
            patterns=self.pattern_8,
            only_match_first_level=True
        )
        self.assertEqual(sorted(result), sorted(self.expect_8))
    
    def test_case_9(self):
        """Test Case 9: only_match_first_level=True with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=self.fileList,
            patterns=self.pattern_9,
            only_match_first_level=True
        )
        self.assertEqual(sorted(result), sorted(self.expect_9))

    def test_case_10(self):
        """Test Case 10: only_match_first_level=True with patterns"""
        result = filter_files_by_glob_patterns(
            fileList=[],
            patterns=self.pattern_10,
            only_match_first_level=True
        )
        self.assertEqual(sorted(result), sorted(self.expect_10))
    
    
if __name__ == '__main__':
    unittest.main()
