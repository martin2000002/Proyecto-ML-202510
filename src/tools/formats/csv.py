import pandas as pd
import os
from typing import List, Any
from agents import function_tool
from tools.shared import log
from tools.utils.parsing import normalize_feature_name

@function_tool
def get_csv_shape(file_path: str) -> str:
    """
    Gets the number of rows and columns in a CSV file.
    
    Args:
        file_path: The path to the CSV file.
        
    Returns:
        A string describing the shape (e.g., "Rows: 100, Columns: 50").
    """
    log(f"📏 Calculating shape of {file_path}...")
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        rows, cols = df.shape
        log(f"   -> Found {rows} rows and {cols} columns")
        return f"Rows: {rows}, Columns: {cols}"
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

@function_tool
def get_csv_columns_headers(file_path: str, offset: int = 0, limit: int = 200) -> List[str]:
    """
    Gets the column names of a CSV file with pagination support.
    
    Args:
        file_path: The path to the CSV file.
        offset: The starting index (0-based) of the columns to return.
        limit: The maximum number of columns to return.
        
    Returns:
        A list of column names.
    """
    end_idx = offset + limit
    log(f"📊 Reading Headers (Cols {offset} to {end_idx}) from {file_path}")
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig', nrows=0)
        all_columns = df.columns.tolist()
        return all_columns[offset : offset + limit]
    except Exception as e:
        return [f"Error reading CSV file: {str(e)}"]

@function_tool
def read_csv_head(file_path: str, n_rows: int = 3) -> List[List[Any]]:
    """
    Reads the first n rows of a CSV file, INCLUDING the headers as the first row.
    
    Args:
        file_path: The path to the CSV file.
        n_rows: The number of data rows to read (headers are extra).
        
    Returns:
        A list of lists. The first list is the headers. The subsequent lists are the row values.
    """
    log(f"👀 Reading headers and first {n_rows} rows from {file_path}")
    try:
        df = pd.read_csv(file_path, nrows=n_rows, encoding='utf-8-sig')
        # Get headers
        headers = df.columns.tolist()
        # Get values
        values = df.where(pd.notnull(df), None).values.tolist()
        # Combine
        return [headers] + values
    except Exception as e:
        return [[f"Error reading CSV file: {str(e)}"]]

@function_tool
def get_csv_rows_headers(file_path: str, column_index: int = 0, offset: int = 0, limit: int = 200) -> List[Any]:
    """
    Reads values from a specific column in the CSV with pagination support.
    
    Args:
        file_path: The path to the CSV file.
        column_index: The index of the column to read (0-based). Default is 0.
        offset: The starting index (0-based) of the rows to read.
        limit: The maximum number of rows to return.
        
    Returns:
        A list containing the values of the specified column slice.
    """
    end_idx = offset + limit
    log(f"🧐 Reading First Column (Rows {offset} to {end_idx}) from {file_path}")
    try:
        # Read the full column (efficient enough for typical CSV sizes) and slice in memory
        # This avoids complex skiprows logic with headers
        df = pd.read_csv(file_path, usecols=[column_index], encoding='utf-8-sig')
        
        # Slice the dataframe
        subset = df.iloc[offset : offset + limit, 0]
        
        # Return the values as a list, handling NaNs
        return subset.where(pd.notnull(subset), None).tolist()
    except Exception as e:
        return [f"Error reading column: {str(e)}"]

@function_tool
def delete_columns(file_path: str, column_names: List[str]) -> str:
    """
    Deletes multiple columns from a CSV file by their names.
    
    Args:
        file_path: The path to the CSV file.
        column_names: A list of column names to delete.
        
    Returns:
        A success message.
    """
    log(f"🗑️ Deleting columns {column_names} from {file_path}")
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Filter columns that actually exist in the dataframe
        to_drop = [c for c in column_names if c in df.columns]
        
        if not to_drop:
            return "No matching columns found to delete."
            
        df.drop(columns=to_drop, inplace=True)
        
        # Clean column names by removing pandas duplicate suffixes (e.g., .1, .2)
        df.columns = df.columns.str.replace(r'\.\d+$', '', regex=True)

        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        rows, cols = df.shape
        return f"Successfully deleted {len(to_drop)} columns. New shape: Rows: {rows}, Columns: {cols}. WAIT for this confirmation before proceeding."
    except Exception as e:
        return f"Error deleting columns: {str(e)}"

@function_tool
def delete_rows_by_values(file_path: str, column_index: int, values_to_delete: List[str]) -> str:
    """
    Deletes rows where the value in a specific column matches any of the provided values EXACTLY.
    
    Args:
        file_path: The path to the CSV file.
        column_index: The index of the column to check (0-based).
        values_to_delete: A list of exact values (strings) to identify rows for deletion.
        
    Returns:
        A success message.
    """
    log(f"✂️ Deleting rows in {file_path} where column {column_index} is in {values_to_delete}")
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        if column_index >= len(df.columns):
            return f"Column index {column_index} out of bounds"
            
        col_name = df.columns[column_index]
        
        # Filter rows
        original_count = len(df)
        
        # Convert column and values to string for comparison to be safe, or keep as is?
        # Let's try to match types if possible, but string comparison is safest for mixed types in CSVs.
        # We'll convert both to string for the mask.
        
        # Normalize values to delete to strings
        values_str = [str(v) for v in values_to_delete]
        
        # Create mask: True if value is in the list
        mask = df[col_name].astype(str).isin(values_str)
        
        df_clean = df[~mask]
        
        deleted_count = original_count - len(df_clean)
        
        df_clean.to_csv(file_path, index=False, encoding='utf-8-sig')
        rows, cols = df_clean.shape
        return f"Successfully deleted {deleted_count} rows. New shape: Rows: {rows}, Columns: {cols}. WAIT for this confirmation before proceeding."
    except Exception as e:
        return f"Error deleting rows: {str(e)}"

@function_tool
def get_unique_column_values(file_path: str, column_index: int) -> List[Any]:
    """
    Gets the unique values from a specific column in the CSV.
    
    Args:
        file_path: The path to the CSV file.
        column_index: The index of the column to check (0-based).
        
    Returns:
        A list of unique values found in that column.
    """
    log(f"🔍 Getting unique values from column {column_index} in {file_path}")
    try:
        df = pd.read_csv(file_path, usecols=[column_index], encoding='utf-8-sig')
        unique_values = df.iloc[:, 0].unique().tolist()
        # Filter out NaNs if desired, or keep them to let agent decide
        return [x for x in unique_values if pd.notnull(x)]
    except Exception as e:
        return [f"Error reading column: {str(e)}"]

@function_tool
def rename_column(file_path: str, column_index: int, new_name: str) -> str:
    """
    Renames a specific column by its index.
    
    Args:
        file_path: The path to the CSV file.
        column_index: The index of the column to rename (0-based).
        new_name: The new name for the column.
        
    Returns:
        A success message.
    """
    log(f"🏷️ Renaming column {column_index} to '{new_name}' in {file_path}")
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if column_index >= len(df.columns):
            return f"Column index {column_index} out of bounds"
            
        old_name = df.columns[column_index]
        df.rename(columns={old_name: new_name}, inplace=True)
        
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        return f"Successfully renamed column '{old_name}' to '{new_name}'."
    except Exception as e:
        return f"Error renaming column: {str(e)}"

@function_tool
def move_column_to_index(file_path: str, column_name: str, new_index: int) -> str:
    """
    Moves a column to a specific index (position) in the CSV.
    
    Args:
        file_path: The path to the CSV file.
        column_name: The name of the column to move.
        new_index: The new index (0-based) where the column should be placed.
        
    Returns:
        A success message.
    """
    log(f"🚚 Moving column '{column_name}' to index {new_index} in {file_path}")
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        if column_name not in df.columns:
            return f"Column '{column_name}' not found in CSV."
            
        if new_index < 0 or new_index >= len(df.columns):
            return f"New index {new_index} is out of bounds."
            
        cols = df.columns.tolist()
        cols.remove(column_name)
        cols.insert(new_index, column_name)
        
        df = df[cols]
        
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        return f"Successfully moved column '{column_name}' to index {new_index}."
    except Exception as e:
        return f"Error moving column: {str(e)}"

@function_tool
def normalize_csv_columns(file_path: str) -> str:
    """
    Normalizes all column names in a CSV file to snake_case using the standard normalization logic.
    Example: "Patrimonio / Activos" -> "patrimonio_sobre_activos"
    
    Args:
        file_path: The path to the CSV file.
        
    Returns:
        A success message with the number of renamed columns.
    """
    log(f"🐍 Normalizing column names in {file_path}")
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        original_columns = df.columns.tolist()
        new_columns = [normalize_feature_name(col) for col in original_columns]
        
        # Check if any changes are needed
        if original_columns == new_columns:
            return "All columns are already normalized."
            
        df.columns = new_columns
        
        # Handle duplicates if normalization created them
        # e.g. "Col A" and "Col_A" might both become "col_a"
        # Pandas handles this by not allowing duplicates easily, but let's ensure uniqueness
        if len(set(new_columns)) != len(new_columns):
            # Simple deduplication strategy
            counts = {}
            deduped_columns = []
            for col in new_columns:
                if col in counts:
                    counts[col] += 1
                    deduped_columns.append(f"{col}_{counts[col]}")
                else:
                    counts[col] = 0
                    deduped_columns.append(col)
            df.columns = deduped_columns
            
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        return f"Successfully normalized {len(original_columns)} columns."
    except Exception as e:
        return f"Error normalizing columns: {str(e)}"


