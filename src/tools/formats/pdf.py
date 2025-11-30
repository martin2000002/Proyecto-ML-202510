import pdfplumber
import base64
import os
from agents import function_tool
from tools.shared import log

def file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

@function_tool
def save_csv_from_pdf(content: str, output_filename: str) -> str:
    """
    Saves the extracted CSV content to a file in data/preprocessed/.
    
    Args:
        content: The CSV string content.
        output_filename: The name of the file to save (e.g., 'risk_matrix.csv').
    """
    output_path = os.path.join("data/preprocessed", output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(content)
    
    log(f"💾 Saved PDF extraction to: {output_path}")
    return f"Successfully saved CSV to {output_path}"

@function_tool
def update_csv_with_correction(content: str, output_filename: str) -> str:
    """
    Updates an existing CSV file with corrected content and logs the differences.
    Use this tool ONLY when correcting an already saved CSV after verification.
    
    Args:
        content: The new corrected CSV string content.
        output_filename: The name of the file to update (e.g., 'risk_matrix.csv').
    """
    output_path = os.path.join("data/preprocessed", output_filename)
    
    if not os.path.exists(output_path):
        return save_csv_from_pdf(content, output_filename)
        
    # Read old content for comparison
    with open(output_path, "r", encoding="utf-8-sig") as f:
        old_lines = f.readlines()
        
    new_lines = content.splitlines(keepends=True)
    
    # Simple diff count
    diff_count = 0
    # Compare line by line (basic heuristic)
    min_len = min(len(old_lines), len(new_lines))
    for i in range(min_len):
        if old_lines[i].strip() != new_lines[i].strip():
            diff_count += 1
            
    diff_count += abs(len(old_lines) - len(new_lines))
    
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(content)
    
    log(f"🛠️ Correcting CSV: {output_filename}")
    log(f"   -> Updated {diff_count} lines with corrections based on text verification.")
    
    return f"Successfully updated CSV with {diff_count} line changes."

@function_tool
def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file using pdfplumber for high accuracy.
    
    Args:
        file_path: The path to the PDF file.
        
    Returns:
        A string containing all the text extracted from the PDF.
    """
    log(f"📖 Extracting text from PDF: {file_path}")
    try:
        text_content = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        
        full_text = "\n".join(text_content)
        return full_text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"
