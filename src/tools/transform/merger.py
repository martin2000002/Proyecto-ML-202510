import pandas as pd
import os
import json
from typing import List
from agents import function_tool
from tools.shared import log


@function_tool
def merge_and_clean_csvs(temp_folder: str, output_folder: str, output_filename: str) -> str:
    """
    Merges all CSV files in a temporary folder into a single consolidated CSV file.
    
    The process involves:
    1. Iterating through CSVs in the temp folder.
    2. Merging them based on the first column (renamed to 'cooperativa').
    3. Performing a Left Join starting with the first CSV (Primary Key source).
    4. Cleaning the result: removing empty columns, all-zero columns, and constant columns.
    
    Args:
        temp_folder: Path to the folder containing CSVs to merge (e.g., 'data/preprocessed/temp/').
        output_folder: Path where the final CSV will be saved (e.g., 'data/preprocessed/').
        output_filename: The name of the final CSV file (e.g., '2025-EEFF-MEN.csv').
        
    Returns:
        A success message with the path of the created file.
    """
    log("🏗️ Starting CSV Merge and Clean process...")
    
    output_path = os.path.join(output_folder, output_filename)
    
    # 2. List CSV Files
    try:
        files = [f for f in os.listdir(temp_folder) if f.endswith('.csv')]
        files.sort() # Ensure deterministic order
        
        if not files:
            return "❌ No CSV files found in the temporary folder."
            
        log(f"📂 Found {len(files)} CSV files to merge.")
    except Exception as e:
        return f"❌ Error listing files: {str(e)}"

    # 3. Merge Process
    try:
        # Load the first CSV (Master)
        first_file_path = os.path.join(temp_folder, files[0])
        log(f"🔹 Loading Master CSV: {files[0]}")
        df_master = pd.read_csv(first_file_path, encoding='utf-8-sig')
        
        # Rename first column to 'cooperativa'
        if not df_master.empty:
            old_name = df_master.columns[0]
            df_master.rename(columns={old_name: 'cooperativa'}, inplace=True)
            log(f"   -> Renamed primary key column '{old_name}' to 'cooperativa'")
        
        # Iterate and Merge
        for filename in files[1:]:
            file_path = os.path.join(temp_folder, filename)
            log(f"🔹 Merging: {filename}")
            
            df_curr = pd.read_csv(file_path, encoding='utf-8-sig')
            
            if df_curr.empty:
                log(f"   ⚠️ Skipping empty file: {filename}")
                continue
                
            # Rename first column to 'cooperativa' for merging
            df_curr.rename(columns={df_curr.columns[0]: 'cooperativa'}, inplace=True)
            
            # Drop duplicates in the current file's key to avoid cartesian explosion if 1:Many is not desired
            # The user said "solo deben haber resgistros por cooperativas... que ya empezo a crear"
            # Assuming 1:1 relationship is expected for "cooperativa" across tables.
            if df_curr['cooperativa'].duplicated().any():
                log(f"   ⚠️ Found duplicate keys in {filename}. Keeping first occurrence.")
                df_curr.drop_duplicates(subset=['cooperativa'], keep='first', inplace=True)
            
            # Left Merge: Keep only rows present in df_master
            df_master = pd.merge(df_master, df_curr, on='cooperativa', how='left')
            
        log(f"✅ Merge complete. Shape: {df_master.shape}")
        
    except Exception as e:
        return f"❌ Error during merge process: {str(e)}"

    # 4. Cleaning Process
    try:
        log("🧹 Starting Post-Merge Cleaning...")
        initial_cols = df_master.shape[1]
        
        # Remove columns with all NaNs
        cols_before_nan = df_master.shape[1]
        df_master.dropna(axis=1, how='all', inplace=True)
        nan_dropped = cols_before_nan - df_master.shape[1]
        if nan_dropped > 0:
            log(f"   -> Dropped {nan_dropped} columns with all NaNs.")
        
        # Remove columns with all Zeros (numeric only)
        # We need to be careful with non-numeric columns.
        # Strategy: Select numeric columns, find those that are all 0, drop them.
        numeric_cols = df_master.select_dtypes(include=['number']).columns
        zero_cols = [col for col in numeric_cols if (df_master[col] == 0).all()]
        if zero_cols:
            df_master.drop(columns=zero_cols, inplace=True)
            log(f"   -> Dropped {len(zero_cols)} all-zero columns.")

        # Remove Constant Columns (nunique <= 1)
        # nunique(dropna=True) excludes NaNs. If a column has only 1 unique value (e.g. "0" or "A"), it's constant.
        # If it has [0, NaN, 0], nunique is 1 -> Constant.
        # If it has [0, 1, NaN], nunique is 2 -> Not constant.
        constant_cols = [col for col in df_master.columns if df_master[col].nunique(dropna=True) <= 1]
        if constant_cols:
            df_master.drop(columns=constant_cols, inplace=True)
            log(f"   -> Dropped {len(constant_cols)} constant columns.")
            
        final_cols = df_master.shape[1]
        log(f"✨ Cleaning complete. Removed {initial_cols - final_cols} columns in total.")
        
    except Exception as e:
        return f"❌ Error during cleaning process: {str(e)}"

    # 5. Save Result
    try:
        os.makedirs(output_folder, exist_ok=True)
        df_master.to_csv(output_path, index=False, encoding='utf-8-sig')
        log(f"💾 Saved consolidated file to: {output_path}")
        return f"Successfully merged and cleaned data. Saved to {output_path}"
    except Exception as e:
        return f"❌ Error saving file: {str(e)}"
