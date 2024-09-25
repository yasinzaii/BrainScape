import json
import logging

class JsonHandler:
    """
    A handler class for loading, updating, saving, and managing JSON data.
    """
    
    def __init__(self, json_path, create_if_missing: bool = False):
        """
        Initialize the JsonHandler with the specified JSON file path.

        Args:
            json_path (str): The path to the JSON file to be managed.
            create_if_missing (bool, optional): Whether to create the JSON file if it doesn't exist. Defaults to False.
        """

        self.json_path = json_path
        self.is_path_valid = True
        self.create_if_missing = create_if_missing
        self.logger = logging.getLogger(__name__)
        
        self.data = self.load_json()


    def load_json(self) -> dict:
        """
        Load JSON data from the specified file.

        Returns:
            dict: The loaded JSON data. Returns an empty dictionary if loading fails.
        """
        
        try:
            with open(self.json_path, 'r') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            self.logger.error(f"JsonHandler - File not found, file:'{self.json_path}'.")
            self.is_path_valid = False
            return {}  
        except PermissionError:
            self.logger.error(f"JsonHandler - Permission denied for file '{self.json_path}'.")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"JsonHandler - The file '{self.json_path}' contains invalid JSON.")
            return {}
        except Exception as e:
            self.logger.exception(f"JsonHandler - An unexpected error occurred while loading JSON file: '{self.json_path}'.")
            return {}
    
    
    def is_loaded(self) -> bool:
        """
        Check if the JSON data has been successfully loaded.

        Returns:
            bool: True if data is loaded, False otherwise.
        """
        return bool(self.data)


    def _validate_data(self, data: dict) -> None:
        """
        Validate that the provided data is a dictionary and JSON-serializable.

        Args:
            data (dict): The data to validate.
        """
        if not isinstance(data, dict):
            self.logger.error(f"JsonHandler - Data must be provided as a dictionary. Provided type: {type(data).__name__}")
            raise TypeError("Data must be provided as a dictionary.")
        try:
            json.dumps(data)  # Test if data is JSON serializable
        except (TypeError, OverflowError) as e:
            self.logger.error(f"JsonHandler - Data contains non-serializable values. Error: {e}")
            raise ValueError(f"Data contains non-serializable values: {e}")
        
         
    def update_json(self, updates: dict) -> 'JsonHandler':
        """
        Update the JSON data with the provided dictionary.

        Args:
            updates (dict): A dictionary containing updates to be applied to the JSON data.

        Returns:
            JsonHandler: The instance itself after updating.
        """
        self._validate_data(updates) 
        self.data.update(updates)
        self.logger.info(f"JsonHandler - JSON data updated successfully for file '{self.json_path}'. Updates: {updates}")
        return self


    def save_json(self) -> bool:
        """
        Save the current JSON data back to the file.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        if self.is_path_valid or self.create_if_missing:
        
            try:
                with open(self.json_path, 'w') as file:
                    json.dump(self.data, file, indent=4)
                self.logger.info(f"JsonHandler - Saved Data into the Json File, Json File {self.json_path}")
                return True
            except Exception as e:
                self.logger.exception(f"JsonHandler - Error Saving JSON data, Json File: '{self.json_path}'.")
                return False
        else:
            self.logger.error(f"JsonHandler - Unable to save Json because of invalid File Path, {self.json_path}")
            
    
    def delete_keys(self, keys: str | list | tuple) -> None:
        """
        Delete specified keys from the JSON data.

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
                
        self.logger.info(f"JsonHandler - Popping Config Keys from Saved Dict, Relevant Json File {self.json_path}, Deleted Keys: {deleted_keys}")
        if len(ignored_keys) > 0:
            self.logger.info(f"JsonHandler - Ignored Missing Popping Config Keys, Relevant Json File {self.json_path}, Ignored Keys: {ignored_keys}")
            
    
 
    def set_data(self, new_data: dict) -> 'JsonHandler':
        """
        Override the existing JSON data with new data.

        Args:
            new_data (dict): The new data to set.
            
        Returns:
            JsonHandler: The instance itself after updating.
        """
        self._validate_data(new_data)
        self.data = new_data.copy()
        self.logger.info(f"JsonHandler - JSON data has been overridden successfully for file '{self.json_path}'.")
        return self
                    
    def get_data(self) -> dict:
        return self.data.copy()