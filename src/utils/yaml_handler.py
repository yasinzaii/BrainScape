import yaml
import logging
from typing import Union, List, Tuple

class YamlHandler:
    """
    A handler class for loading, updating, saving, and managing YAML data.
    """
    
    def __init__(self, yaml_path: str, create_if_missing: bool = False):
        """
        Initialize the YamlHandler with the specified YAML file path.

        Args:
            yaml_path (str): The path to the YAML file to be managed.
            create_if_missing (bool, optional): Whether to create the YAML file if it doesn't exist. Defaults to False.
        """

        self.yaml_path = yaml_path
        self.is_path_valid = True
        self.create_if_missing = create_if_missing
        self.logger = logging.getLogger(__name__)
        
        self.data = self.load_yaml()


    def load_yaml(self) -> dict:
        """
        Load YAML data from the specified file.

        Returns:
            dict: The loaded YAML data. Returns an empty dictionary if loading fails.
        """
        
        try:
            with open(self.yaml_path, 'r') as file:
                data = yaml.safe_load(file) or {}
            return data
        except FileNotFoundError:
            self.logger.error(f"YamlHandler - File not found: '{self.yaml_path}'.")
            self.is_path_valid = False
            return {}  
        except PermissionError:
            self.logger.error(f"YamlHandler - Permission denied for file '{self.yaml_path}'.")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"YamlHandler - The file '{self.yaml_path}' contains invalid YAML. Error: {e}")
            return {}
        except Exception as e:
            self.logger.exception(f"YamlHandler - An unexpected error occurred while loading YAML file: '{self.yaml_path}'.")
            return {}
    
    
    def is_loaded(self) -> bool:
        """
        Check if the YAML data has been successfully loaded.

        Returns:
            bool: True if data is loaded, False otherwise.
        """
        return bool(self.data)


    def _validate_data(self, data: dict) -> None:
        """
        Validate that the provided data is a dictionary and YAML-serializable.

        Args:
            data (dict): The data to validate.
        """
        if not isinstance(data, dict):
            self.logger.error(f"YamlHandler - Data must be provided as a dictionary. Provided type: {type(data).__name__}")
            raise TypeError("Data must be provided as a dictionary.")
        try:
            yaml.dump(data)  # Test if data is YAML serializable
        except yaml.YAMLError as e:
            self.logger.error(f"YamlHandler - Data contains non-serializable values. Error: {e}")
            raise ValueError(f"Data contains non-serializable values: {e}")
        
     
    def update_yaml(self, updates: dict) -> 'YamlHandler':
        """
        Update the YAML data with the provided dictionary.

        Args:
            updates (dict): A dictionary containing updates to be applied to the YAML data.

        Returns:
            YamlHandler: The instance itself after updating.
        """
        self._validate_data(updates) 
        self.data.update(updates)
        self.logger.info(f"YamlHandler - YAML data updated successfully for file '{self.yaml_path}'. Updates: {updates}")
        return self


    def save_yaml(self) -> bool:
        """
        Save the current YAML data back to the file.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        if self.is_path_valid or self.create_if_missing:
        
            try:
                with open(self.yaml_path, 'w') as file:
                    yaml.dump(self.data, file, default_flow_style=False)
                self.logger.info(f"YamlHandler - Saved data into the YAML file: '{self.yaml_path}'")
                return True
            except Exception as e:
                self.logger.exception(f"YamlHandler - Error saving YAML data to file: '{self.yaml_path}'.")
                return False
        else:
            self.logger.error(f"YamlHandler - Unable to save YAML due to invalid file path: '{self.yaml_path}'")
            return False
            
    
    def delete_keys(self, keys: Union[str, List[str], Tuple[str]]) -> None:
        """
        Delete specified keys from the YAML data.

        Args:
            keys (Union[str, List[str], Tuple[str]]): A single key or a list/tuple of keys to be deleted.
        """
        
        if not isinstance(keys, (list, tuple)):
            keys = [keys]
        
        deleted_keys, ignored_keys = [], []
        for key in keys:
            if key in self.data:
                self.data.pop(key)
                deleted_keys.append(key)
            else:
                ignored_keys.append(key)
                
        self.logger.info(f"YamlHandler - Deleted keys from YAML data: {deleted_keys} in file '{self.yaml_path}'")
        if ignored_keys:
            self.logger.info(f"YamlHandler - Ignored missing keys: {ignored_keys} in file '{self.yaml_path}'")
            
 
    def set_data(self, new_data: dict) -> 'YamlHandler':
        """
        Override the existing YAML data with new data.

        Args:
            new_data (dict): The new data to set.
            
        Returns:
            YamlHandler: The instance itself after updating.
        """
        self._validate_data(new_data)
        self.data = new_data.copy()
        self.logger.info(f"YamlHandler - YAML data has been overridden successfully for file '{self.yaml_path}'.")
        return self
                    
    def get_data(self) -> dict:
        """
        Get a copy of the current YAML data.

        Returns:
            dict: A copy of the YAML data.
        """
        return self.data.copy()
