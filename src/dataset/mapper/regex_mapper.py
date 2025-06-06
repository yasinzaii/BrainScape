# src/dataset/mapper/regex_mapper.py

import os
import re
import logging
import fnmatch
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Any, Dict
from dataset.mapper.base_plugin import DatasetMapperPlugin


logger = logging.getLogger(__name__)


class RegexMapper(DatasetMapperPlugin):
    """
    Maps and saves the Subject-Session-MRI Modality paths into a JSON file based on REGEX Patterns Provided In Settings.
    """
    
    # Class-specific plugin name
    plugin_name = "RegexMapper"
    
    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name
    
    
    def __init__(self, dataset_settings: Dict[str, Any], dataset_path: str):
        """
        Initializes the RegexMapper with dataset settings and path.

        Args:
            dataset_settings (Dict[str, Any]): Configuration settings for the dataset.
            dataset_path (str): The base path where datasets will be downloaded.
        """
        self.dataset_settings = dataset_settings
        self.dataset_path = Path(dataset_path)
        self.download_dir_path = self.dataset_path / dataset_settings["downloadDirName"]


    def _compile_regex_patterns(self, patterns: Dict[str, Any], context: str = "") -> Tuple[Dict[str, Any], bool]:
        """
        Recursively compiles regex patterns from a dictionary.

        Args:
            patterns (Dict[str, Any]): The dictionary containing regex patterns.
            context (str): A string representing the dataset Mapping Path [Dataset Name . Mapping] for logging purposes.

        Returns:
            Tuple[Dict[str, Any], bool]: A tuple containing the dictionary with compiled regex patterns
                                        and a boolean indicating overall success.
        """
        is_successful = True
        compiled_patterns = {}

        for key, value in patterns.items():
            current_context = f"{context}.{key}" 

            if isinstance(value, dict):
                compiled_subpatterns, status = self._compile_regex_patterns(value, context=current_context)
                compiled_patterns[key] = compiled_subpatterns
                if not status:
                    is_successful = False
            
            elif isinstance(value, str):
                if value.strip() == "":
                    # Treat empty string as no filtering (None)
                    compiled_patterns[key] = None
                    logger.debug(f"RegexMapper - '{current_context}' is set to None (no filtering).")
                else:
                    try:
                        compiled_patterns[key] = re.compile(value)
                        logger.debug(f"RegexMapper - Successfully compiled regex for '{current_context}': {value}")
                    except re.error as e:
                        logger.error(f"RegexMapper - Error compiling regex for pattern '{current_context}': {value} | Error: {e}")
                        is_successful = False
            else:
                logger.error(f"RegexMapper - Unsupported type at '{current_context}': Expected dict or str, got {type(value).__name__}")
                is_successful = False

        return compiled_patterns, is_successful


    def _match_path_parts(self, regex, path_parts, path_index):
        """
        Attempts to match the regex against combinations of path parts starting from path_index.
        Returns (matched_value, new_path_index) if a match is found, else (None, path_index).
        """
        max_parts = len(path_parts)  # Including the filename
        for end_index in range(path_index + 1, max_parts + 1):
            candidate = '/'.join(path_parts[path_index:end_index])
            if regex.match(candidate):
                return candidate, end_index
        return None, path_index
    
    
    def map(self) -> Dict[str, Any]:
        """
        Maps and saves the Subject-Session-MRI Modality paths into a JSON file.

        Returns:
            dict: A dictionary with dataset information including paths to all MRIs.
        """
    
        dataset_name = self.dataset_path.name
        logger.info(f"RegexMapper - Started creating dataset JSON for {dataset_name} Dataset.")


        # Gather all downloaded files
        downloaded_files = set([
            str(p.relative_to(self.download_dir_path))
            for p in self.download_dir_path.rglob('*') if p.is_file()
        ])

        regex_patterns = self.dataset_settings["mapping"]["regex"]

        # Compile regex patterns recursively
        regex_compiled, status = self._compile_regex_patterns(patterns=regex_patterns, context=dataset_name)
        if not status:
            logger.error(f"RegexMapper - Failed Compiling Regex Patterns for {dataset_name} Dataset. Invalid Regex Mapping, Skipping Dataset")
            return {}
        
        # Get includeSub and excludeSub lists
        include_subs = self.dataset_settings["mapping"].get("includeSub", [])
        exclude_subs = self.dataset_settings["mapping"].get("excludeSub", [])
        
        # Get Flag for mapFirstGroupOnly for only mapping a single copy of Modality if there are multiple MRIs of same modality inside (sub/ses/type) dir
        map_first_group_only = self.dataset_settings["mapping"].get("mapFirstGroupOnly", False)  # Defaults to False.
        if map_first_group_only:
            logger.warning(f"RegexMapper - 'mapFirstGroupOnly' is set for Dataset:{dataset_name}, will only Map Firs Group (Group Index == 0).")
        
        # Initialize nested defaultdict
        # Subject -> Sessions -> Type -> Images (T1W, T2W, FLAR) -> list of image files.
        grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))


        for file_path in downloaded_files:
            
            path_parts = Path(file_path).parts
            
            # Initialized Vars
            subject = None
            session = None
            type_ = None
            modality = None
            path_index = 0  # Path Parts index

            # Match subject
            matched_subject, new_path_index = self._match_path_parts(regex_compiled["subject"], path_parts, path_index)
            if matched_subject:
                subject = matched_subject
                path_index = new_path_index
            else:
                logger.info(f"RegexMapper - {dataset_name} - Skipping '{file_path}': as it does not match 'subject' pattern '{regex_compiled['subject'].pattern}'.")
                continue

            # Check includeSub and excludeSub - Supports simple wildcard matching
            if include_subs and not any(fnmatch.fnmatch(subject, pattern) for pattern in include_subs):
                logger.info(f"RegexMapper - {dataset_name} - Subject '{subject}' not in includeSub list; Skipping.")
                continue
            if exclude_subs and any(fnmatch.fnmatch(subject, pattern) for pattern in exclude_subs):
                logger.info(f"RegexMapper - {dataset_name} - Subject '{subject}' in excludeSub list; Skipping.")
                continue
            
            # Match Session if regex is provided
            if regex_compiled["session"] is not None: 
                matched_session, new_path_index = self._match_path_parts(regex_compiled["session"], path_parts, path_index)
                if matched_session:
                    session = matched_session
                    path_index = new_path_index
                else:
                    logger.info(f"RegexMapper - {dataset_name} - Skipping '{file_path}': as it does not match 'session' pattern {regex_compiled['session'].pattern}.")
                    continue
            else: 
                logger.debug(f"RegexMapper - {dataset_name} - Regex pattern for session is empty - session = '' ")
                session = "" 

            
            # Match Type if regex is provided
            if regex_compiled["type"] is not None:
                matched_type, new_path_index = self._match_path_parts(regex_compiled["type"], path_parts, path_index)
                if matched_type:
                    type_ = matched_type
                    path_index = new_path_index
                else:
                    logger.info(f"RegexMapper - {dataset_name} - Skipping '{file_path}': as it does not match 'type' pattern {regex_compiled['type'].pattern}.")
                    continue
            else: 
                logger.debug(f"RegexMapper - {dataset_name} - Regex pattern for type is empty - type = '' ")
                type_ = ""     
            
            # Ensure path_index is within bounds before accessing file_name
            if path_index >= len(path_parts):
                logger.error(f"RegexMapper - {dataset_name} - Skipping '{file_path}': insufficient path parts for 'modality' matching.")
                continue

            # Match modalities
            image_matched = False
            rem_path_file_name = '/'.join(path_parts[path_index:])
            
            
            for modality, modality_pattern in regex_compiled["modality"].items():
                
                matched_rem_path, _ = self._match_path_parts(modality_pattern, path_parts, path_index)
                
                if matched_rem_path:
                    
                    #grouped[subject][session][type_][modality].append(str(rem_path_file_name))
                    grouped[subject][session][type_][modality].append(str(file_path))

                    image_matched = True
                    logger.debug(f"RegexMapper - {dataset_name} - Matched modality '{modality}' for file '{file_path}'.")
                    
                    # Verifying if the combination of subject/session and pathParts[-1] rebuilds the path
                    if os.path.join(subject, session, type_, rem_path_file_name) != file_path:
                        logger.error(f"RegexMapper - {dataset_name} - Invalid Grouping/Mapping of MRI for Subject='{subject}', Session='{session}', Modality='{modality}', FilePath={file_path}")
                    break # Stop after matching the first modality
                    
            if not image_matched:
                logger.debug(f"RegexMapper - Unable to Match the File, Dataset: {dataset_name},  Subject='{subject}', Session='{session}', FilePath={file_path}")

        # Max Number of MRI per Modality (for Grouping MRI's)
        max_mri_mod = 0
        for sub_data in grouped.values():
            for ses_data in sub_data.values():
                for type_data in ses_data.values():
                    for mod_data in type_data.values():
                        max_mri_mod = max(max_mri_mod, len(mod_data))
        if max_mri_mod == 0:
            logger.error(f"RegexMapper - Missing MRI data in the Mapped Modalities, Dataset: {dataset_name}")
        elif max_mri_mod > 1:
            logger.info(f"RegexMapper - {dataset_name} - Multiple MRI's per Modality found in the Mapped Dataset. Will be further divided into groups of one MRI per modality")

        # Extracting & Returning Mappings
        dataset_mapping = []
        for subject, subject_data in grouped.items():
            for session, session_data in subject_data.items():
                for type_, type_data in session_data.items():
                    
                    # Dividing Multiples of MRI's into Groups
                    for group_indx in range(max_mri_mod):
                        
                        # Creating an Entry
                        entry = {
                            'subject': subject,   # Subject Info (Subject Directory)
                            'session': session,   # Session Info (Session Directory)
                            'type': type_,        # MRI Type Info ('anat' for this Project)
                            'group': group_indx,  # MRI's group Index - Maintains 1 MRI per Modality in a group
                            'mris': {},           # Keep Record of File Names of Each MRI Modality
                            'download': {}        # Keep Record of Download Locations of Each MRI Modalities
                        }
                        
                        # acquiring all modalities
                        entry_flag = False
                        for modality, modality_list in type_data.items():
                            if group_indx < len(modality_list):
                                entry['download'][modality] = modality_list[group_indx]
                                entry['mris'][modality] = Path(modality_list[group_indx]).name
                                entry_flag = True 
                        
                        # Check if mapFirstGroupOnly is Set. Will have to skip adding the group into Mapping.
                        if map_first_group_only and entry_flag and group_indx > 0:
                            logger.warning(f"RegexMapper - {dataset_name} - Skipping Group:{group_indx}, sub:{entry['subject']}, ses:{entry['session']}, type:{entry['type']}, MRIs:{entry['mris']}")
                            continue
                            
                        # Appending The Entry to the Dataset Mapping
                        if entry_flag:
                            dataset_mapping.append(entry)

        logger.info(f"RegexMapper - Completed creating dataset JSON for {dataset_name} Dataset.")
        return dataset_mapping