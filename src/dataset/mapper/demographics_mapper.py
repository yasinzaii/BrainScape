# src/dataset/mapper/demographics_mapper.py

import os
import re
import csv
import random
import logging

from pathlib import Path
from typing import Dict, Any, List

from utils.yaml_handler import YamlHandler
from dataset.mapper.base_plugin import DatasetMapperPlugin

logger = logging.getLogger(__name__)

class DemographicsMapper(DatasetMapperPlugin):
    """
    A plugin that reads participant demographic data (participants.tsv) from a dataset-specific
    demographics folder and merges it into the existing dataset mapping (subject/session).
    The data is validated against a global mapping schema (mapping.yaml).
    """

    # Class-specific plugin name
    plugin_name = "DemographicsMapper"

    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name


    def __init__(self,
                 dataset_settings: Dict[str, Any],
                 dataset_name: str,
                 demogr_schema_path: str,
                 demogr_data_path: str):
        """
        Initializes the DemographicMapper.

        Args:
            dataset_settings (Dict[str, Any]): Configuration/settings for the dataset.
            dataset_name (str): The name of the dataset. 
            demogr_schema_path (str): The path for the demographics YAML schema file (mapping.yaml)
            demogr_data_path (str): The path for the demographics data file (participants.tsv)
        """
        self.dataset_settings = dataset_settings
        self.dataset_name = Path(dataset_name)
        self.demogr_schema_path = Path(demogr_schema_path)
        self.demogr_data_path = Path(demogr_data_path)
        
        if not Path(demogr_schema_path).is_file():
            message = f"DemographicsMapper - Provided schema path '{demogr_schema_path}' is invalid. Dataset:{dataset_name}"
            logger.error(message)
            raise FileNotFoundError(message)
        
        if not Path(demogr_data_path).is_file():
            message = f"DemographicsMapper - Provided participants path '{demogr_data_path}' is invalid. Dataset:{dataset_name}"
            logger.error(message)
            raise FileNotFoundError(message)   

        logger.debug(f"DemographicsMapper initialized for dataset at: {dataset_name}")


    def _build_schema_map(self, schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Convert the 'demographics' section of the schema into a dict for quick lookup:
          {
            '<standard_col_name>': {
              'aliases': [...],
              'valid_values': [
                  { 'main_value': '...', 'aliases': [...] },
                  ...
              ]
            },
            ...
          }
        """
        result = {}
        demographics_section = schema.get('demographics', [])
        for field_spec in demographics_section:
            name = field_spec['name']
            result[name] = {
                'aliases': field_spec.get('aliases', []),
                'valid_patterns': field_spec.get('valid_patterns', None),
                'valid_values': field_spec.get('valid_values', None),
                'description': field_spec.get('description', "")
            }
        return result


    def _load_participants_data(self) -> List[Dict[str, Any]]:
        """
        Reads participants.tsv and stores data into a list of dict rows.

        Returns:
            List[Dict[str, Any]]: Rows are converted into Dict, 
            Where key:value pairs are {column_name: value} from the TSV row.
        """
        if not self.demogr_data_path.is_file():
            logger.warning(f"DemographicsMapper - No participants.tsv found at {self.demogr_data_path}.")
            return []

        participants_data = []
        with open(self.demogr_data_path, 'r', encoding='utf-8') as tsv_file:
            reader = csv.DictReader(tsv_file, delimiter='\t')
            for row in reader:
                participants_data.append(row)

        logger.debug(f"DemographicsMapper - Loaded {len(participants_data)} participant records.")
        return participants_data


    def _normalize_column_name(self, col: str, schema_map: Dict[str, Dict[str, Any]]) -> str:
        """
        Attempts to find the standard column name from the schema based on `col` or its aliases.
        If no match is found, return the original col name (so we can warn or handle it).
        """
        col_lower = col.strip().lower()
        for standard_name, spec in schema_map.items():
            # Check the "main" name
            if standard_name.lower() == col_lower:
                return standard_name
            # Check the aliases
            for alias in spec.get('aliases', []):
                if alias.strip().lower() == col_lower:
                    return standard_name
        
        # Return original if not found -> Will produce a warning later
        logger.warning(f"DemographicsMapper - Column '{col}' not found in schema aliases.")
        return col

    def _normalize_value(self, value: str, valid_values: List[Dict[str, Any]]) -> str:
        """
        Converts 'value' into a standard main_value if found in the 'valid_values' definition.
        Example:
          valid_values = [
            { 'main_value': 'male', 'aliases': ['m','1'] },
            { 'main_value': 'female', 'aliases': ['f','0'] },
          ]
        If 'value' matches 'm', '1' or 'male', we return 'male'.
        """
        
        if not valid_values:
            return value.strip()
        
        if value.strip() == "":
            logger.error(f"DemographicsMapper - Value '{value}' cannot be empty")

        val_lower  = value.strip().lower()
        for item in valid_values:
            if item['main_value'].lower() == val_lower :
                return item['main_value']
            for alias in item.get('aliases', []):
                if alias.lower() == val_lower:
                    return item['main_value']

        # Create a list of lists containing main_value and aliases
        list_of_valid_values = [[item['main_value']] + item['aliases'] for item in valid_values]

        # Not matched
        logger.error(f"DemographicsMapper - Value '{value}' not found in valid_values. Valid Values: {list_of_valid_values}")
        raise ValueError(f"DemographicsMapper - Invalid choice '{value}', expected one of {list_of_valid_values}.")


    def _value_checks_and_convert(self, column: str, value: str):
        """
        Converts special placeholders 'n/a', 'N/A', 'na' to empty string ('').
        Attempts to convert the value to float if it is expected to be numeric 
        (e.g. age, height, weight, BMI). Logs or raises if conversion fails.
        
        Returns the (possibly converted) string or empty string.
        """
        # Replace 'n/a', 'N/A', 'na' with ''.
        if value.strip().lower() in ["n/a", "na"]:
            return ""  
        
        # Returns if value == empty or no digit in value string.
        if not value or not any(char.isdigit() for char in value):
            return value.strip()
        
        # Verify float conv of numeric columns like 'age', 'height', 'weight', 'BMI', etc.
        numeric_columns = {"age", "height", "weight", "BMI"}
        if column in numeric_columns:
            
            # Attempt float conversion
            try:
                numeric_val = float(value)
            except ValueError:
                # Not convertible to float
                logger.error(f"DemographicsMapper - Column '{column}' expects a numeric value but got '{value}'.")
                raise ValueError(f"Invalid numeric value '{value}' for column '{column}'.")
        
            # RANGE CHECKS
            if column == "height":
                if numeric_val > 2.5:
                    logger.warning(f"DemographicsMapper - Suspicious height '{numeric_val}' (expected <= 2.5 m).")

            elif column == "weight":
                if numeric_val < 20 or numeric_val > 200:
                    logger.warning(f"DemographicsMapper - Suspicious weight '{numeric_val}' (expected 20-200 kg).")
                    
            elif column == "age":
                if numeric_val < 0 or numeric_val > 120:
                    logger.warning(f"DemographicsMapper - Suspicious age '{numeric_val}' (expected 0-120).")
        
            elif column == "BMI":
                if numeric_val < 10 or numeric_val > 70:
                    logger.warning(f"DemographicsMapper - Suspicious BMI '{numeric_val}' (expected 10-70).")
        
        return value.strip()


    @classmethod
    def _standardize_demographic_field(cls, value: str, valid_patterns: List[str]) -> str:
        """
        Standardizes a demographic field (e.g., participant_id or session) based on regex patterns
        by stripping known prefixes or patterns from the start of the string.

        For example, if valid_patterns includes ["^sub[-_]?", "^subject[-_]?"], then
        a raw value like "sub-001" -> "001"
        or "subject_abc123" -> "abc123"

        Args:
            value (str): The raw field value to be standardized (e.g., "sub-001").
            valid_patterns (List[str]): A list of regex strings that define acceptable or recognizable
                                        prefixes to remove.

        Returns:
            str: The standardized/normalized value after removing matched prefixes.

        Raises:
            ValueError: If the final result is empty or if no pattern is provided at all.
        """
        
        original_value = value
        if not value:
            logger.error("DemographicsMapper - The input value is empty or None.")
            raise ValueError("Cannot standardize an empty or None value.")

        if not valid_patterns:
            logger.warning("DemographicsMapper - No valid patterns provided. Returning value as-is.")
            return value

        # Trim leading/trailing whitespace and lowercase
        value = value.strip().lower()

        # Try each pattern to see if we can remove it from the start
        for pattern in valid_patterns:
            # Matched patterns will be removed
            new_val = re.sub(pattern, '', value, count=1)
            if new_val != value:
                logger.debug(f"DemographicsMapper - Stripped prefix using pattern '{pattern}'. "
                    f"'{value}' -> '{new_val}'"
                )
                value = new_val.strip()
                break
        
        # If the result is empty
        if not value:
            logger.error(
                f"DemographicsMapper - After removing known prefixes, nothing remains "
                f"from '{original_value}'."
            )
            raise ValueError(
                f"Cannot standardize field '{original_value}': all content removed by patterns."
            )
        return value


    
    
    def map(self, existing_mapping: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merges demographic data into an existing mapping list.

        The `existing_mapping` is typically a list of dicts where each dict has:
            {
              'subject': <str>,
              'session': <str>,
              'type': <str>,
              'group': <int>,
              'mris': { ... },
              'download': { ... }
              ...
            }

        We'll:
          1) Load the schema (mapping.yaml).
          2) Load participants.tsv and validate/normalize its data.
          3) Build a dictionary of demographics keyed by 'participant_id_session'.
          4) For each entry in existing_mapping, find a match in demographics (by subject & session)
             and attach the data under entry['demographics'].

        Returns:
            List[Dict[str, Any]]: The updated mapping with demographics included if found.
        """
        
        logger.info(f"DemographicsMapper - Merging demographics for dataset for dataset: {self.dataset_name}")
        
        # 1) Load the YAML schema
        schema_yaml_handler = YamlHandler(self.demogr_schema_path)
        self.demogr_schema = schema_yaml_handler.get_data()

        # 1) Load the schema
        if not self.demogr_schema:
            logger.error("DemographicMapper - Failed to load mapping.yaml schema. Demographics not added. Dataset:{self.dataset_name}")
            return existing_mapping

        # Build a quick-lookup structure from the 'demographics' section
        schema_map = self._build_schema_map(self.demogr_schema)
        if not schema_map:
            logger.error("DemographicMapper - Failed to create schema map. Demographics not added. Dataset:{self.dataset_name}")
            return existing_mapping

        # Standardize/Acceptable 'participant_id' or subject and 'session' patterns 
        pid_patterns = schema_map['participant_id'].get('valid_patterns', [])
        ses_patterns = schema_map['session'].get('valid_patterns', [])

        # 2) Load participants data
        participants_data = self._load_participants_data()
        if not participants_data:
            logger.warning(f"DemographicMapper - No participant data found for '{self.dataset_name}'.")
            return existing_mapping
        
        
        # 3) Normalize/standardize and validate participants data
        demographic_dict = {}
        for row_index, row in enumerate(participants_data):
            standardized_row = {}
            
            for col_name, raw_value in row.items():
                # Find standard column name
                std_col = self._normalize_column_name(col_name, schema_map)

                # If this col isn't in the schema map and not recognized as an alias
                if std_col == col_name and std_col not in schema_map:
                    logger.error(f"DemographicMapper - Unrecognized column '{col_name}' at row {row_index}.")
                    raise ValueError(f"Unrecognized column '{col_name}' in demographics data.")
                
                # If known, handle valid_values or aliases
                valid_values = schema_map[std_col].get('valid_values', [])
                normalized_value = self._normalize_value(raw_value, valid_values)
                
                # Optional range checks (height, weight, etc.)
                normalized_value = self._value_checks_and_convert(std_col, normalized_value)
                
                standardized_row[std_col] = normalized_value
                
            # Acquiring and Standardizing 'participant_id'.
            pid_value = standardized_row.get("participant_id", None)
            if not pid_value:
                logger.error(f"DemographicMapper - Missing 'participant_id' in row {row_index}. Dataset: {self.dataset_name}")
                raise ValueError(f"Missing participant_id in row {row_index}. Dataset: {self.dataset_name}")
            standardized_pid = DemographicsMapper._standardize_demographic_field(pid_value, pid_patterns)
    
            # Acquiring and Standardizing 'session'.
            ses_value = standardized_row.get("session", "")
            if not ses_value:
                standardized_ses = ""
            else:
                standardized_ses = DemographicsMapper._standardize_demographic_field(ses_value, ses_patterns)
            
            # Key that matches 'subject' + 'session' in existing_mapping
            key = f"{standardized_pid}_{standardized_ses}"

            if key in demographic_dict:
                logger.warning(f"DemographicsMapper - Key '{key}' is duplicated. Overwriting older data. Dataset: {self.dataset_name}")
            demographic_dict[key] = standardized_row
        
        # 4) Merge the demographics into the existing mapping
        updated_mapping = []
        for entry in existing_mapping:
            
            sub = entry.get('subject', '')
            sub_standardized = DemographicsMapper._standardize_demographic_field(sub, pid_patterns)
            
            # Check if demographics info includes session data.
            ses=""
            ses_standardized = ""
            if 'session' in next(iter( demographic_dict.values() )).keys():
                ses = entry.get('session', '')
                ses_standardized = DemographicsMapper._standardize_demographic_field(ses, ses_patterns)
            
            # Construct the same key
            sub_ses_key = f"{sub_standardized}_{ses_standardized}"
            
            if sub_ses_key in demographic_dict:
                entry['demographics'] = demographic_dict[sub_ses_key]
                logger.debug(f"DemographicMapper - Attached demographics to subject: '{sub}', session: '{ses}'.")
            else:
                # No matching demographics for this subject/session
                logger.warning(f"DemographicMapper - Demographics not found for, subject: '{sub}', session: '{ses}'.")
                entry['demographics'] = {}
                
            updated_mapping.append(entry)
        
        # 5) Debugging: Randomly select 20 entries and pretty print them
        self._debug_print_random_entries(updated_mapping, sample_size=20)
        
        logger.info(f"DemographicMapper - Finished demographics merging for dataset: '{self.dataset_name}'")
        return updated_mapping       
    
    @classmethod
    def _debug_print_random_entries(cls, updated_mapping: List[Dict[str, Any]], sample_size: int = 20):
        """
        Randomly selects a specified number of entries from the updated_mapping and logs them
        in a tree-like format for debugging purposes.

        Additionally, it also logs the first 10 entries for comparison.

        Args:
            updated_mapping (List[Dict[str, Any]]): The list of updated mapping entries.
            sample_size (int): The number of random entries to display.
        """
        if not updated_mapping:
            logger.warning("DemographicMapper - No entries available for debugging.")
            return
        
        # Define sample sizes
        first_entries_size = 10
        random_entries_size = 20

        # Adjust sample sizes based on available data
        first_entries_size = min(first_entries_size, len(updated_mapping))
        random_entries_size = min(random_entries_size, len(updated_mapping))
        
        # Get first 10 entries
        first_entries = updated_mapping[:first_entries_size]

        # Get random 20 entries
        random_entries = random.sample(updated_mapping, random_entries_size)
        
         # Generate debug output for first 10 entries
        debug_output = "\n\n===== DEMOGRAPHIC DEBUGGING (First 10 Entries) =====\n"
        debug_output = cls._generate_display_output(debug_output, first_entries)

        # Generate debug output for random 20 entries
        debug_output += "\n\n===== DEMOGRAPHIC DEBUGGING (Random 20 Entries) =====\n"
        debug_output = cls._generate_display_output(debug_output, random_entries)
        
        # Log the combined debug output
        logger.debug(debug_output)

        
    @classmethod           
    def _format_dict_tree(cls, d: Dict[str, Any], indent: int = 0) -> str:
        """
        Recursively formats a dictionary into a tree-like string.

        Args:
            d (Dict[str, Any]): The dictionary to format.
            indent (int): Current indentation level.

        Returns:
            str: Formatted string representing the tree.
        """
        tree_str = ""
        for key, value in d.items():
            if isinstance(value, dict):
                tree_str += "  " * indent + f"{key}:\n"
                tree_str += cls._format_dict_tree(value, indent + 1)
            else:
                tree_str += "  " * indent + f"{key}: {value}\n"
        return tree_str
    
    @classmethod
    def _generate_display_output(cls, incoming_str: str, entries_to_display: List[Dict[str, Any]]) -> str:
        """
        Generates the formatted debug output string for a list of entries.

        Args:
            incoming_str (str): The initial string to append to.
            entries_to_display (List[Dict[str, Any]]): The list of entries to format.

        Returns:
            str: The updated debug output string.
        """
        debug_output = incoming_str
        for i, entry in enumerate(entries_to_display):

            # Extract 'subject' and 'session'
            subject = entry.get("subject", "")
            session = entry.get("session", "")
            debug_output += f"subject: {subject}\n"
            debug_output += f"session: {session}\n"

            # Exclude 'subject' and 'session' to avoid duplication
            entry_copy = {k: v for k, v in entry.items() if k not in ("subject", "session")}
            tree_str = cls._format_dict_tree(entry_copy, indent=1)
            debug_output += tree_str

            debug_output += "\n"  # Blank line separating each entry
        return debug_output

        
