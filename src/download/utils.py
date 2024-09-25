# src/download/utils.py

import fnmatch
import logging
import subprocess

from pathlib import Path
from threading import Lock
from typing import Callable, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configure logger for the download module
logger = logging.getLogger(__name__)

def execute_command(command: list, capture_output: bool = True) -> tuple[bool, str]:
    """
    Executes a generic command using subprocess and returns the success status and output.

    Args:
        command (list): The command to execute as a list of strings.
        capture_output (bool, optional): Whether to capture the command's output. Defaults to True.

    Returns:
        tuple[bool, str]: A tuple containing a boolean indicating success, and the command's output or error message.
    """
    logger.debug(f"Executing command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=capture_output,
            text=True
        )

        if result.stderr:
            logger.error(f"Failed executing command '{' '.join(command)}': {result.stderr}")
            return False, result.stderr

        # Settings Return Status Ture if the command does not return any Ouput or Error
        if not result.stdout and not result.stderr:
            logger.warning(f"Command didn't returned any output or errror '{' '.join(command)}'")
            return True, result.stdout

        logger.debug(f"Command output: {result.stdout}")
        return True, result.stdout

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed executing command '{' '.join(command)}': {e}")
        return False, e.stderr if e.stderr else str(e)



def execute_in_parallel( 
    target_function: Callable, 
    args_list: List[Tuple[Any, ...]], 
    max_workers: int = 32 ) -> List[Any]:
    """
    Executes the target_function concurrently with different arguments.

    Args:
        target_function (Callable): The function to execute in parallel.
        args_list (List[Tuple[Any, ...]]): A list of argument tuples for each function call.
        max_workers (int, optional): The maximum number of threads to use. Defaults to 32.

    Returns:
        List[Any]: A list of results from the function executions.
    """
    
    if not args_list:
        logger.error("No arguments provided to execute_in_parallel.")
        return []
    
    results = []

    with ThreadPoolExecutor(max_workers=min(max_workers, len(args_list))) as executor:
    
        future_to_args = {executor.submit(target_function, *args): args for args in args_list}
        
        for future in as_completed(future_to_args):
            args = future_to_args[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Error executing '{target_function.__name__}' with args {args}: {e}",
                    exc_info=True  # Include traceback in the log
                )
                
        return results



def filter_files_by_glob_patterns( fileList: list, patterns: list, only_match_first_level: bool) -> list:
    """
    Filters a list of file paths based on provided UNIX wildcard patterns.

    Args:
        fileList (List[str]): List of file paths to filter.
        patterns (List[str]): List of wildcard patterns to match against.
            Supports Unix shell-style wildcards:
                - '*' matches any number of characters.
        only_match_first_level (bool): 
            If True, matches are performed only on the first-level directory or file name.
            If False, matches are performed on the entire path.

    Returns:
        List[str]: A list of file paths that match at least one of the provided patterns.
    """
    included_files = []
    for file_path in fileList:
        path = Path(file_path)
        
        # Extract the first-level directory or file name if only_match_first_level is True
        comp_file = path.parts[0] if only_match_first_level else str(path)
        
        for pattern in patterns:
            
            comp_pattern = Path(pattern).parts[0] if only_match_first_level else pattern
            
            # Perform shell-style wildcard matching
            if fnmatch.fnmatch(comp_file, comp_pattern):
                included_files.append(file_path)
                break  # Stop checking other patterns once a match is found
            
    return included_files
