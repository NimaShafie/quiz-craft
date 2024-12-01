"""
Call function fetch_config_dict(file_path = "config.ini", section=None)
to read a config.ini file.

Date created 12 Jun 2024
"""

import configparser
import os


#Function to read a config INI file.
def fetch_config_dict(file_path = "config.ini", section=None):
    """
    Convert INI file to a dictionary.
    
    Args:
        file_path (str): Path to the INI file.
        section (str, optional): Name of the section to retrieve. If None, returns all sections.
    
    Returns:
        dict: Dictionary containing the configuration data.
    
    Raises:
        FileNotFoundError: If the INI file is not found.
        ValueError: If the specified section is not found.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The configuration file {file_path} was not found.")
    

    config = configparser.ConfigParser()
    config.read(file_path)
    
    config_dict = {}
    for section_name in config.sections():
        if section is None or section_name == section:
            for option, value in config.items(section_name):
                config_dict[option] = value
    
    return config_dict


#print(fetch_config_dict(section = 'DIRECTORIES_TASK_1'))