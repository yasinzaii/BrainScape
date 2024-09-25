# src/utils/common_utils.py

from pathlib import Path
from typing import List, Union


def merge_settings(defaults, overrides):
    """
    Merges two dictionaries, with overrides taking precedence over defaults.

    Args:
        defaults (dict): The default settings.
        overrides (dict): The overriding settings.

    Returns:
        dict: The merged settings.

    Raises:
        TypeError: If either defaults or overrides is not a dictionary.
    """
    if not isinstance(defaults, dict):
        raise TypeError("defaults must be a dictionary")
    if not isinstance(overrides, dict):
        raise TypeError("overrides must be a dictionary")
    final_settings = defaults.copy()
    final_settings.update(overrides)
    return final_settings



def get_subdirectories(path: Union[str, Path], basename_only: bool = False) -> List[str]:
    """
    Retrieves all subdirectories within the given path.

    Args:
        path (str or Path): The directory path to search.
        basename_only (bool, optional): 
            If True, returns only the names of the subdirectories in that directory.
            If False, returns the absolute paths of the subdirectories in that directory.
            Defaults to False.

    Returns:
        List[str]: A list of subdirectories either as absolute paths or just their names.

    Raises:
        ValueError: If the provided path does not exist or is not a directory.
    """
    p = Path(path)

    if not p.exists():
        raise ValueError(f"The directory '{path}' does not exist.")
    if not p.is_dir():
        raise ValueError(f"The path '{path}' is not a directory.")

    subdirs = [x for x in p.iterdir() if x.is_dir()]

    if basename_only:
        return [x.name for x in subdirs]
    return [str(x.resolve()) for x in subdirs]
