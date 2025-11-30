import os
import json
import zipfile
from typing import List, Dict, Any
from agents import function_tool
from tools.shared import log

import shutil

@function_tool
def clear_directories(directory_paths: List[str]) -> str:
    """
    Deletes all contents of multiple directories but keeps the directories themselves.
    
    Args:
        directory_paths: A list of paths to the directories to clear.
        
    Returns:
        A success message summarizing the results.
    """
    log(f"🧹 Clearing directories: {directory_paths}")
    results = []
    try:
        for directory_path in directory_paths:
            if not os.path.exists(directory_path):
                os.makedirs(directory_path, exist_ok=True)
                results.append(f"{directory_path}: Created (was missing)")
                continue
                
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    results.append(f"{directory_path}: Failed to delete {filename} ({e})")
            
            results.append(f"{directory_path}: Cleared")
                
        return f"Operation completed. Results: {', '.join(results)}"
    except Exception as e:
        return f"Error clearing directories: {str(e)}"

@function_tool
def list_files_recursive(directory_path: str) -> List[str]:
    """
    Lists all files in a directory recursively.
    
    Args:
        directory_path: The path to the directory to list.
        
    Returns:
        A list of relative file paths.
    """
    log(f"📂 Listing files in {directory_path}")
    file_list = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

@function_tool
def read_file_content(file_path: str) -> str:
    """
    Reads the content of a text file.
    
    Args:
        file_path: The path to the file to read.
        
    Returns:
        The content of the file as a string.
    """
    log(f"📄 Reading file {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@function_tool
def read_json_file(file_path: str) -> Any:
    """
    Reads a JSON file and returns the parsed data.
    
    Args:
        file_path: The path to the JSON file.
        
    Returns:
        The parsed JSON data (dict or list).
    """
    log(f"🧾 Reading JSON file {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return f"Error reading JSON file: {str(e)}"

@function_tool
def unzip_file(zip_path: str, extract_to: str) -> str:
    """
    Unzips a file to a specified directory.
    
    Args:
        zip_path: The path to the zip file.
        extract_to: The directory to extract the files to.
        
    Returns:
        A message indicating success or failure.
    """
    log(f"📦 Unzipping {zip_path} to {extract_to}")
    try:
        # Check if the directory already exists and is not empty
        if os.path.exists(extract_to) and os.listdir(extract_to):
            log(f"Directory {extract_to} already exists and is not empty. Skipping unzip.")
            return f"Directory {extract_to} already exists and is not empty. Skipping unzip."

        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return f"Successfully extracted {zip_path} to {extract_to}"
    except Exception as e:
        return f"Error unzipping file: {str(e)}"
