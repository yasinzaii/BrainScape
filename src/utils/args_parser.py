# src/utils/args_parser.py

import argparse


def str2bool(v):
    """
    Convert a string representation of truth to True or False.

    Args:
        v (str or bool): The value to convert to a boolean.

    Returns:
        bool: The boolean value corresponding to the input.
    """
    if isinstance(v, bool):
        return v
    if v.lower().strip() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower().strip() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def get_parser(**parser_kwargs):
    """
    Create and configure an ArgumentParser for the script.

    Args:
        **parser_kwargs: Arbitrary keyword arguments passed to ArgumentParser().
    """
    
    # Initialize the parser with any provided keyword arguments
    parser = argparse.ArgumentParser(**parser_kwargs)
    
    # Argument to remove and re-download all datasets
    parser.add_argument(
        "-rd",
        "--re-download",
        type=str2bool,
        const=True,
        default=False,
        nargs="?",
        help="Removes and Re-downloads all Datasets",
    )
    
    # Argument to remove and re-process all datasets
    parser.add_argument(
        "-rp",
        "--re-process",
        type=str2bool,
        const=True,
        default=False,
        nargs="?",
        help="Removes and Re-processes all Datasets",
    )
    
    # Argument to specify the path to the configuration JSON file
    parser.add_argument(
        "-cp",
        "--config-path",
        type=str,
        default="./config/config.json",
        help="Path to the configuration JSON file",
    )
    
    # Argument to specify the path to the credentials.ini file
    parser.add_argument(
        "-ip",
        "--credential-path",
        type=str,
        default="./config/credentials.ini",
        help="Path to the credentials.ini file",
    )
    
    
    # Argument to validate all downloaded files with corresponding source files
    parser.add_argument(
        "-cd",
        "--check-download-files",
        type=str2bool,
        const=True,
        default=True,
        nargs="?",
        help="Validate all downloaded file with corresponding Source Files",
    )
    
    # Argument to specify the path to the logger configuration file
    parser.add_argument(
        "-lc",
        "--logger-config-file",
        type=str,
        default="./config/logging.json",
        help="Path to the logger configuration file",
    )
    
    return parser