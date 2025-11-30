import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from agents import function_tool
from tools.shared import log

RATING_ORDER = ["AAA","AA","A","BBB","BB","B","C","D","E"]
RATING_MAP = {r: i for i, r in enumerate(RATING_ORDER)}

def _normalize_rating(r: str) -> str:
    if not isinstance(r, str):
        return ""
    # Remove source markers like '*', whitespace
    r = r.replace("*", "").strip()
    # Split by '/' and other delimiters
    parts = [p.strip() for p in r.split('/') if p.strip()]
    candidates = []
    for p in parts:
        # Remove + or -
        base = p.rstrip('+-')
        # Extract main group, sometimes have subgroups like 'AA-1' (take leftmost non-digit/char)
        # We'll keep letters until a non-letter is found
        main = ''.join([c for c in base if c.isalpha()])
        main = main.upper()
        if main in RATING_MAP:
            candidates.append(main)
    if not candidates:
        return ""
    # choose worst (highest index)
    worst = max(candidates, key=lambda x: RATING_MAP.get(x, -1))
    return worst

@function_tool
def get_first_column(file_path: str) -> List[str]:
    """
    Returns the list of values in the first column of a CSV file.
    """
    log(f"🔍 Reading first column of {file_path}")
    try:
        df = pd.read_csv(file_path, usecols=[0], encoding='utf-8-sig')
        # Return as list of strings, filtering NaNs
        return df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
    except Exception as e:
        return [f"Error: {str(e)}"]

@function_tool
def create_dataset(cooperatives: List[str], abbreviations: List[str], output_path: str = "data/processed/dataset.csv") -> str:
    """
    Initializes the dataset CSV with two columns: 'cooperativa' and 'abreviacion'.
    """
    log(f"🆕 Creating dataset at {output_path} with {len(cooperatives)} rows")
    try:
        if len(cooperatives) != len(abbreviations):
            return f"Error: Length mismatch. Cooperatives: {len(cooperatives)}, Abbreviations: {len(abbreviations)}"
        
        df = pd.DataFrame({
            "cooperativa": cooperatives,
            "abreviacion": abbreviations
        })
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return f"Successfully created dataset at {output_path}"
    except Exception as e:
        return f"Error creating dataset: {str(e)}"

@function_tool
def append_aligned_columns(file_path: str, index_mapping: List[int], output_path: str = "data/processed/dataset.csv") -> str:
    """
    Appends columns from a source CSV to the dataset, reordering rows based on index_mapping.
    
    Args:
        file_path: Source CSV path.
        index_mapping: List of integers. The i-th element represents the index of the row in the SOURCE CSV 
                       that corresponds to the i-th row in the DESTINATION dataset. 
                       Use -1 if the destination row has no match in the source (will fill with NaN).
        output_path: Path to the dataset being built.
    """
    log(f"📎 Appending columns from {file_path} to {output_path}")
    try:
        if not os.path.exists(output_path):
            return "Error: Output dataset does not exist. Create it first."
            
        # Read source
        df_source = pd.read_csv(file_path, encoding='utf-8-sig')
        # Drop first column (names)
        df_source_data = df_source.iloc[:, 1:]
        
        # Read target to ensure length match
        df_target = pd.read_csv(output_path, encoding='utf-8-sig')
        if len(index_mapping) != len(df_target):
            return f"Error: Mapping length {len(index_mapping)} != Target length {len(df_target)}"
            
        # Reorder source data
        aligned_rows = []
        for src_idx in index_mapping:
            if src_idx == -1:
                # Empty row (NaNs)
                aligned_rows.append({col: None for col in df_source_data.columns})
            elif 0 <= src_idx < len(df_source):
                aligned_rows.append(df_source_data.iloc[src_idx].to_dict())
            else:
                return f"Error: Source index {src_idx} out of bounds (0-{len(df_source)-1})"
                
        df_aligned = pd.DataFrame(aligned_rows)
        
        # Concatenate horizontally
        df_target.reset_index(drop=True, inplace=True)
        df_aligned.reset_index(drop=True, inplace=True)
        
        df_final = pd.concat([df_target, df_aligned], axis=1)
        df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        return f"Successfully appended {len(df_aligned.columns)} columns from {file_path}"
    except Exception as e:
        return f"Error appending columns: {str(e)}"

@function_tool
def append_cleaned_risk_column(file_path: str, column_name: str, index_mapping: List[int], output_path: str = "data/processed/dataset.csv") -> str:
    """
    Appends a specific risk column from the source CSV, cleaning the values (worst rating logic), and renaming it to 'Label'.
    
    Args:
        file_path: Source CSV path (risk file).
        column_name: The specific column header to extract.
        index_mapping: Mapping array (target_i -> source_j).
        output_path: Path to dataset.
    """
    log(f"🏷️ Appending cleaned risk column '{column_name}' from {file_path}")
    try:
        if not os.path.exists(output_path):
            return "Error: Output dataset does not exist."
            
        df_source = pd.read_csv(file_path, encoding='utf-8-sig')
        if column_name not in df_source.columns:
            return f"Error: Column '{column_name}' not found in {file_path}"
            
        # Extract raw values
        raw_values = df_source[column_name].astype(str).tolist()
        
        # Align and clean
        cleaned_labels = []
        for src_idx in index_mapping:
            if src_idx == -1 or src_idx >= len(raw_values):
                cleaned_labels.append("")
            else:
                val = raw_values[src_idx]
                cleaned_labels.append(_normalize_rating(val))
                
        # Append to target
        df_target = pd.read_csv(output_path, encoding='utf-8-sig')
        if len(cleaned_labels) != len(df_target):
             return f"Error: Label count {len(cleaned_labels)} != Target length {len(df_target)}"
             
        df_target['Label'] = cleaned_labels
        df_target.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        return "Successfully appended cleaned 'Label' column."
    except Exception as e:
        return f"Error appending risk column: {str(e)}"

@function_tool
def finalize_and_clean_dataset(file_path: str) -> str:
    """
    Performs professional cleaning and normalization on the consolidated dataset.
    Steps:
    1. Correct data types (remove symbols, convert to float).
    2. Remove garbage columns (>50% nulls, constant).
    3. Impute nulls with median.
    4. Remove duplicates.
    5. Normalize features (StandardScaler logic), excluding 'cooperativa', 'abreviacion', 'Label'.
    
    Args:
        file_path: Path to the consolidated dataset CSV.
    """
    log(f"🧹 Starting professional cleaning and normalization for {file_path}")
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Identify special columns (case-insensitive check)
        special_names = {'cooperativa', 'abreviacion', 'label', 'entity', 'segmento'}
        
        non_feature_cols = [c for c in df.columns if c.lower() in special_names]
        feature_cols = [c for c in df.columns if c not in non_feature_cols]
        
        log(f"   -> Identified {len(feature_cols)} feature columns and {len(non_feature_cols)} metadata columns.")

        # 2. Correct Data Types
        for col in feature_cols:
            # Convert to string, remove symbols, convert to numeric
            # We use regex to remove common financial symbols
            df[col] = df[col].astype(str).str.replace(r'[%,$]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # 3. Remove Garbage Columns
        # > 50% Nulls
        threshold = len(df) * 0.5
        df = df.dropna(axis=1, thresh=threshold)
        
        # Update feature cols after drop
        feature_cols = [c for c in df.columns if c not in non_feature_cols]
        
        # Constant columns (std dev is 0 or all values same)
        # We can check nunique <= 1 (ignoring NaNs)
        cols_to_drop = [c for c in feature_cols if df[c].nunique(dropna=True) <= 1]
        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True)
            log(f"   -> Dropped {len(cols_to_drop)} constant columns.")
            
        feature_cols = [c for c in df.columns if c not in non_feature_cols]

        # 4. Treat Null Values
        # Impute with median
        for col in feature_cols:
            median_val = df[col].median()
            if pd.notnull(median_val):
                df[col] = df[col].fillna(median_val)
            else:
                df[col] = df[col].fillna(0) # Fallback if all NaN
            
        # Remove rows that might still be empty in metadata columns (e.g. Cooperativa is null)
        # We assume 'cooperativa' is critical
        coop_col = next((c for c in df.columns if c.lower() == 'cooperativa'), None)
        if coop_col:
            df.dropna(subset=[coop_col], inplace=True)
        
        # 5. Remove Duplicates
        if coop_col:
            initial_rows = len(df)
            df.drop_duplicates(subset=[coop_col], keep='first', inplace=True)
            if len(df) < initial_rows:
                log(f"   -> Removed {initial_rows - len(df)} duplicate rows.")
            
        # 7. Normalize (StandardScaler logic: (x - mean) / std)
        # We do this manually to avoid sklearn dependency if not present
        for col in feature_cols:
            mean_val = df[col].mean()
            std_val = df[col].std()
            
            if std_val != 0 and not pd.isna(std_val):
                df[col] = (df[col] - mean_val) / std_val
            else:
                # If std is 0 (constant), it should have been dropped, but just in case
                df[col] = 0.0
            
        # Save
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return f"Successfully cleaned and normalized dataset. Final shape: {df.shape}"
        
    except Exception as e:
        return f"Error in final cleaning: {str(e)}"
