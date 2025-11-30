import pandas as pd
import os
import csv
import json
import warnings
from typing import List, Any, Union, Dict
from agents import function_tool
from tools.shared import log
from tools.utils.parsing import normalize_feature_name

# Suppress specific warnings from openpyxl
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

@function_tool
def get_excel_sheet_names(file_path: str) -> List[str]:
    """
    Gets the names of all sheets in an Excel file.
    
    Args:
        file_path: The path to the Excel file.
        
    Returns:
        A list of sheet names.
    """
    log(f"📑 Getting sheet names from {file_path}")
    try:
        xls = pd.ExcelFile(file_path)
        return xls.sheet_names
    except Exception as e:
        return [f"Error reading excel file: {str(e)}"]

@function_tool
def read_excel_range(file_path: str, sheet_name: str, start_row: int, start_col: int, end_row: int, end_col: int) -> List[List[Any]]:
    """
    Reads a range of cells from an Excel sheet.
    
    Args:
        file_path: The path to the Excel file.
        sheet_name: The name of the sheet to read.
        start_row: The starting row index (0-based).
        start_col: The starting column index (0-based).
        end_row: The ending row index (0-based).
        end_col: The ending column index (0-based).
        
    Returns:
        A list of lists containing the cell values.
    """
    log(f"🔍 Reading range {start_row},{start_col} to {end_row},{end_col} from {sheet_name} in {file_path}")
    try:
        # Read the specific sheet
        # We use header=None to read raw data without assuming a header
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        # Slice the dataframe
        # Ensure indices are within bounds
        max_row, max_col = df.shape
        
        s_row = max(0, start_row)
        e_row = min(max_row, end_row + 1) # +1 because iloc is exclusive at the end
        s_col = max(0, start_col)
        e_col = min(max_col, end_col + 1)
        
        if s_row >= max_row or s_col >= max_col:
            return []

        subset = df.iloc[s_row:e_row, s_col:e_col]
        
        # Convert to list of lists, handling NaNs
        return subset.where(pd.notnull(subset), None).values.tolist()
    except Exception as e:
        log(f"Error reading range: {str(e)}")
        return [[f"Error: {str(e)}"]]

@function_tool
def extract_range_to_csv(
    excel_path: str,
    sheet_name: str,
    start_row: int,
    start_col: int,
    end_row: int,
    end_col: int,
    output_csv_path: str,
    transpose: bool = False
) -> str:
    """
    Extracts a specific range from an Excel sheet and saves it as a CSV file.
    Handles reading large ranges efficiently without passing data through the agent.
    
    Args:
        excel_path: Path to the source Excel file.
        sheet_name: Name of the sheet.
        start_row: Starting row index (0-based).
        start_col: Starting column index (0-based).
        end_row: Ending row index (0-based).
        end_col: Ending column index (0-based).
        output_csv_path: Path where the CSV will be saved.
        transpose: If True, swaps rows and columns before saving.
        
    Returns:
        Success message.
    """
    log(f"💾 Extracting range {start_row},{start_col} to {end_row},{end_col} from {sheet_name} to {output_csv_path} (Transpose={transpose})")
    try:
        # Read specific range
        # Using header=None to treat everything as data
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        
        max_row, max_col = df.shape
        s_row = max(0, start_row)
        e_row = min(max_row, end_row + 1)
        s_col = max(0, start_col)
        e_col = min(max_col, end_col + 1)
        
        subset = df.iloc[s_row:e_row, s_col:e_col]
        
        if transpose:
            subset = subset.transpose()
            
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        # Save to CSV without index and header (since we read without header)
        # Use utf-8-sig to ensure Excel opens it correctly with special characters
        subset.to_csv(output_csv_path, index=False, header=False, encoding='utf-8-sig')
        
        return f"Successfully created CSV at {output_csv_path}"
    except Exception as e:
        return f"Error extracting to CSV: {str(e)}"

@function_tool
def extract_features_to_csv(
    excel_path: str,
    sheet_name: str,
    feature_row_indices: List[int],
    header_row_index: int,
    start_col: int,
    end_col: int,
    output_csv_path: str,
    feature_name_map_json: str = None
) -> str:
    """
    Extracts specific rows (features) from an Excel sheet and appends them as columns to a CSV.
    If the CSV doesn't exist, it initializes it using the header_row_index (Cooperatives) as the first column.
    
    Args:
        excel_path: Path to Excel file.
        sheet_name: Sheet name.
        feature_row_indices: List of row indices to extract as features.
        header_row_index: Row index containing the entity names (Cooperatives).
        start_col: Column index where feature names are located. Data starts at start_col + 1.
        end_col: Last column index of data.
        output_csv_path: Path to the output CSV.
        feature_name_map_json: Optional JSON string mapping row index (as string) to new feature name.
                               Example: '{"12": "new_name", "15": "other_name"}'
                               If provided, these names are used. Otherwise, names are normalized automatically.
    """
    log(f"🧪 Extracting {len(feature_row_indices)} features from {sheet_name} to {output_csv_path}")
    try:
        # Parse feature_name_map from JSON string
        feature_name_map = {}
        if feature_name_map_json:
            try:
                feature_name_map = json.loads(feature_name_map_json)
            except Exception as e:
                log(f"Warning: Failed to parse feature_name_map_json: {e}")

        # Read the sheet (header=None to handle indices manually)
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        
        # Initialize CSV if it doesn't exist
        if not os.path.exists(output_csv_path):
            # Extract Entity Names (Cooperatives)
            # Row: header_row_index
            # Cols: start_col + 1 to end_col (inclusive in logic, exclusive in iloc)
            # Note: end_col from user logic usually means the last column index.
            # In read_excel_range we used end_col + 1. Let's be consistent.
            
            entities = df.iloc[header_row_index, start_col + 1 : end_col + 1].tolist()
            
            # Create initial DataFrame
            df_out = pd.DataFrame({"cooperativa": entities})
            df_out.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
            log(f"Initialized CSV with {len(entities)} entities.")
        
        # Load existing CSV to append columns
        df_out = pd.read_csv(output_csv_path, encoding='utf-8-sig')
        
        # Extract and append features
        for row_idx in feature_row_indices:
            # Feature Name Logic
            str_idx = str(row_idx)
            if str_idx in feature_name_map:
                feature_name = feature_name_map[str_idx]
            else:
                raw_name = str(df.iloc[row_idx, start_col]).strip()
                feature_name = normalize_feature_name(raw_name)
            
            # Feature Data
            feature_data = df.iloc[row_idx, start_col + 1 : end_col + 1].tolist()
            
            # Check length alignment
            if len(feature_data) != len(df_out):
                if len(feature_data) < len(df_out):
                    feature_data.extend([None] * (len(df_out) - len(feature_data)))
                else:
                    feature_data = feature_data[:len(df_out)]
            
            # Add as new column
            if feature_name in df_out.columns:
                count = 1
                while f"{feature_name}_{count}" in df_out.columns:
                    count += 1
                feature_name = f"{feature_name}_{count}"
            
            df_out[feature_name] = feature_data
            
        # Save back
        df_out.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        return f"Successfully appended {len(feature_row_indices)} features."
        
    except Exception as e:
        return f"Error extracting features: {str(e)}"
