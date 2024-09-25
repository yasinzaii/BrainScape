# tests/utils/test_args_parser.py

import unittest
import argparse
from src.utils.args_parser import get_parser, str2bool

class TestStr2Bool(unittest.TestCase):
    """Tests for the str2bool function."""

    def test_true_values(self):
        """Test that true string representations return True."""
        true_values = ['yes', 'true', 't', 'y', '1', 'YES', 'True', 'Y']
        for val in true_values:
            with self.subTest(val=val):
                self.assertTrue(str2bool(val))

    def test_false_values(self):
        """Test that false string representations return False."""
        false_values = ['no', 'false', 'f', 'n', '0', 'NO', 'False', 'N']
        for val in false_values:
            with self.subTest(val=val):
                self.assertFalse(str2bool(val))

    def test_boolean_input(self):
        """Test that boolean inputs return themselves."""
        self.assertTrue(str2bool(True))
        self.assertFalse(str2bool(False))

    def test_invalid_values(self):
        """Test that invalid inputs raise an ArgumentTypeError."""
        invalid_values = ['maybe', '2', '', ' ', 'hello']
        for val in invalid_values:
            with self.subTest(val=val):
                with self.assertRaises(argparse.ArgumentTypeError):
                    str2bool(val)



class TestArgsParser(unittest.TestCase):
    """Tests for the argument parser."""

    def setUp(self):
        """Set up the parser before each test."""
        self.parser = get_parser()

    def test_default_arguments(self):
        """Test that default arguments are set correctly."""
        args = self.parser.parse_args([])
        self.assertFalse(args.re_download)
        self.assertFalse(args.re_process)
        self.assertEqual(args.config_path, "./config/config.json")
        self.assertTrue(args.check_download_files)
        self.assertEqual(args.logger_config_file, "./config/logging.json")

    def test_re_download_true(self):
        """Test the --re-download argument with a true value."""
        args = self.parser.parse_args(['--re-download', 'true'])
        self.assertTrue(args.re_download)

    def test_re_download_false(self):
        """Test the --re-download argument with a false value."""
        args = self.parser.parse_args(['--re-download', 'false'])
        self.assertFalse(args.re_download)

    def test_re_process_true(self):
        """Test the --re-process argument with a true value."""
        args = self.parser.parse_args(['--re-process', 'True'])
        self.assertTrue(args.re_process)

    def test_re_process_false(self):
        """Test the --re-process argument with a false value."""
        args = self.parser.parse_args(['--re-process', 'No'])
        self.assertFalse(args.re_process)

    def test_config_path(self):
        """Test setting a custom configuration path."""
        args = self.parser.parse_args(['--config-path', '/path/to/config.json'])
        self.assertEqual(args.config_path, '/path/to/config.json')

    def test_check_download_files_false(self):
        """Test the --check-download-files argument with a false value."""
        args = self.parser.parse_args(['--check-download-files', 'no'])
        self.assertFalse(args.check_download_files)

    def test_logger_config_file(self):
        """Test setting a custom logger configuration file path."""
        args = self.parser.parse_args(['--logger-config-file', '/path/to/logging.json'])
        self.assertEqual(args.logger_config_file, '/path/to/logging.json')

    def test_short_arguments(self):
        """Test using short argument options."""
        args = self.parser.parse_args(['-rd', 'yes', '-rp', '1', '-cp', 'config.json', '-cd', '0', '-lc', 'logging.json'])
        self.assertTrue(args.re_download)
        self.assertTrue(args.re_process)
        self.assertEqual(args.config_path, 'config.json')
        self.assertFalse(args.check_download_files)
        self.assertEqual(args.logger_config_file, 'logging.json')
        
    def test_short_arguments_without_bool_values(self):
        """Test using short argument options."""
        args = self.parser.parse_args(['-rd', '-rp', '-cp', '/test/config.json', '-cd', '0', '-lc', '/test/logging.json'])
        self.assertTrue(args.re_download)
        self.assertTrue(args.re_process)
        self.assertEqual(args.config_path, '/test/config.json')
        self.assertFalse(args.check_download_files)
        self.assertEqual(args.logger_config_file, '/test/logging.json')

    def test_invalid_boolean(self):
        """Test that invalid boolean strings raise an error."""
        
        # argparse will call string to bool for argument parsing, which will rase ArgumentTypeError
        # argparese will then raise SystemExit(2) exception 
        with self.assertRaises(SystemExit):
            self.parser.parse_args(['--re-download', 'maybe'])

    def test_re_download_without_value(self):
        """Test that --re-download without a value sets it to True."""
        args = self.parser.parse_args(['--re-download'])
        self.assertTrue(args.re_download)

    def test_re_process_without_value(self):
        """Test that --re-process without a value sets it to True."""
        args = self.parser.parse_args(['--re-process'])
        self.assertTrue(args.re_process)

    def test_check_download_files_without_value(self):
        """Test that --check-download-files without a value sets it to True."""
        args = self.parser.parse_args(['--check-download-files'])
        self.assertTrue(args.check_download_files)

if __name__ == '__main__':
    unittest.main()