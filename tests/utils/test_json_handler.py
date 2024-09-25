# tests/utils/test_json_handler.py
import os
import json
import logging
import unittest
from src.utils.json_handler import JsonHandler

class TestJsonHandler(unittest.TestCase):
    def setUp(self):
        """
        Setup a temporary JSON file for testing.
        """
        self.test_json_path = 'tests/utils/test_sample.json'
        os.makedirs(os.path.dirname(self.test_json_path), exist_ok=True)
        with open(self.test_json_path, 'w') as file:
            json.dump({"key1": "value1"}, file)
        
        # Setup a logger
        self.logger = logging.getLogger('TestJsonHandler')
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def tearDown(self):
        """
        Remove the temporary JSON file after testing.
        """
        if os.path.exists(self.test_json_path):
            os.remove(self.test_json_path)

    def test_load_json_success(self):
        """
        Test loading a valid JSON file.
        """
        handler = JsonHandler(self.test_json_path)
        self.assertTrue(handler.is_loaded())
        self.assertEqual(handler.get_data(), {"key1": "value1"})

    def test_load_json_file_not_found(self):
        """
        Test loading a non-existent JSON file.
        """
        handler = JsonHandler('tests/utils/non_existent.json')
        self.assertFalse(handler.is_loaded())
        self.assertEqual(handler.get_data(), {})

    def test_load_json_invalid_json(self):
        """
        Test loading an invalid JSON file.
        """
        # Create an invalid JSON file
        with open(self.test_json_path, 'w') as file:
            file.write("{invalid_json: True}")
        
        handler = JsonHandler(self.test_json_path)
        self.assertFalse(handler.is_loaded())
        self.assertEqual(handler.get_data(), {})

    def test_update_json_valid(self):
        """
        Test updating JSON data with valid dictionary.
        """
        handler = JsonHandler(self.test_json_path)
        handler.update_json({"key2": "value2"})
        self.assertEqual(handler.get_data(), {"key1": "value1", "key2": "value2"})

    def test_update_json_invalid_type(self):
        """
        Test updating JSON data with invalid type (non-dictionary).
        """
        handler = JsonHandler(self.test_json_path)
        with self.assertRaises(TypeError):
            handler.update_json("not_a_dict")

    def test_update_json_non_serializable(self):
        """
        Test updating JSON data with non-serializable values.
        """
        handler = JsonHandler(self.test_json_path)
        with self.assertRaises(ValueError):
            handler.update_json({"key3": set([1, 2, 3])})  # Sets are not JSON serializable

    def test_save_json_success(self):
        """
        Test saving JSON data successfully.
        """
        handler = JsonHandler(self.test_json_path)
        handler.update_json({"key2": "value2"})
        result = handler.save_json()
        self.assertTrue(result)
        with open(self.test_json_path, 'r') as file:
            data = json.load(file)
        self.assertEqual(data, {"key1": "value1", "key2": "value2"})

    def test_save_json_failure(self):
        """
        Test saving JSON data with an invalid file path.
        """
        handler = JsonHandler('/invalid_path/test_sample.json')
        handler.update_json({"key2": "value2"})
        result = handler.save_json()
        self.assertFalse(result)

    def test_delete_keys_existing(self):
        """
        Test deleting existing keys from JSON data.
        """
        handler = JsonHandler(self.test_json_path)
        handler.update_json({"key2": "value2"})
        handler.delete_keys(['key1'])
        self.assertEqual(handler.get_data(), {"key2": "value2"})

    def test_delete_keys_non_existing(self):
        """
        Test deleting non-existing keys from JSON data.
        """
        handler = JsonHandler(self.test_json_path)
        handler.update_json({"key2": "value2"})
        handler.delete_keys(['key3'])
        self.assertEqual(handler.get_data(), {"key1": "value1", "key2": "value2"})

    def test_delete_keys_mixed(self):
        """
        Test deleting a mix of existing and non-existing keys.
        """
        handler = JsonHandler(self.test_json_path)
        handler.update_json({"key2": "value2"})
        handler.delete_keys(['key1', 'key3'])
        self.assertEqual(handler.get_data(), {"key2": "value2"})

    def test_get_data_immutable(self):
        """
        Test that get_data returns a copy, not the original dictionary.
        """
        handler = JsonHandler(self.test_json_path)
        data = handler.get_data()
        data['key3'] = 'value3'
        self.assertNotIn('key3', handler.get_data())
    
    def test_set_data_valid(self):
        """
        Test setting new valid data.
        """
        handler = JsonHandler(self.test_json_path)
        new_data = {"new_key": "new_value", "key2": "value2"}
        handler.set_data(new_data)
        self.assertEqual(handler.get_data(), new_data)

    def test_set_data_empty_dict(self):
        """
        Test setting an empty dictionary.
        """
        handler = JsonHandler(self.test_json_path)
        new_data = {}
        handler.set_data(new_data)
        self.assertEqual(handler.get_data(), new_data)

    def test_set_data_invalid_type(self):
        """
        Test setting data with a non-dictionary type.
        """
        handler = JsonHandler(self.test_json_path)
        new_data = ["not", "a", "dict"]
        with self.assertRaises(TypeError):
            handler.set_data(new_data)

    def test_set_data_non_serializable(self):
        """
        Test setting data with non-JSON-serializable values.
        """
        handler = JsonHandler(self.test_json_path)
        new_data = {"key3": set([1, 2, 3])}  # Sets are not JSON serializable
        with self.assertRaises(ValueError):
            handler.set_data(new_data)

    def test_set_data_mutable_input(self):
        """
        Ensure that modifying the input dictionary after setting does not affect the internal state.
        """
        handler = JsonHandler(self.test_json_path)
        new_data = {"key4": "value4"}
        handler.set_data(new_data)
        new_data["key5"] = "value5"
        self.assertNotIn("key5", handler.get_data())
        self.assertEqual(handler.get_data(), {"key4": "value4"})

    def test_set_data_overwrites_previous_data(self):
        """
        Test that set_data replaces the existing data entirely.
        """
        handler = JsonHandler(self.test_json_path).update_json({"key4": "value4"})
        new_data = {"key2": "value2"}
        handler.set_data(new_data)
        self.assertEqual(handler.get_data(), new_data)

    def test_set_data_with_existing_keys(self):
        """
        Test setting data that contains keys already present in the existing data.
        """
        handler = JsonHandler(self.test_json_path)
        new_data = {"key1": "updated_value1", "key2": "value2"}
        handler.set_data(new_data)
        self.assertEqual(handler.get_data(), new_data)


if __name__ == '__main__':
    unittest.main()
