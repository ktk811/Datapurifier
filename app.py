from flask import jsonify, request
import pandas as pd
import json

# Assume 'app' and a 'dataframes' dictionary are defined elsewhere in your file
# For example:
# app = Flask(__name__)
# dataframes = {'current': None}

@app.route('/clean', methods=['POST'])
def clean_data():
    """
    Handles various data cleaning operations on the current DataFrame.
    Accepts a JSON payload with 'operation' and 'params'.
    """
    df = dataframes.get('current')
    if df is None:
        return jsonify({"error": "No data has been loaded yet."}), 400

    # Get the operation and parameters from the incoming JSON request
    operation = request.json.get('operation')
    params = request.json.get('params', {})
    
    try:
        response_data = {}  # Dictionary to hold our JSON response

        # --- OPERATION: Remove Duplicate Rows ---
        if operation == 'remove_duplicates':
            rows_before = len(df)
            # Use pandas' drop_duplicates(). `params` can include 'subset', 'keep', etc.
            df = df.drop_duplicates(**params)
            rows_after = len(df)
            response_data['removed_count'] = rows_before - rows_after
            message = f"{rows_before - rows_after} duplicate rows removed."
        
        # --- OPERATION: Handle Missing Values ---
        elif operation == 'handle_missing':
            strategy = params.pop('strategy', 'drop') # e.g., 'drop', 'fill'
            if strategy == 'drop':
                # Use pandas' dropna(). `params` can include 'axis', 'how', 'subset', etc.
                df = df.dropna(**params)
                message = "Rows with missing values have been dropped."
            elif strategy == 'fill':
                # Use pandas' fillna(). `params` can include 'value', 'method', etc.
                df = df.fillna(**params)
                message = "Missing values have been filled."
            else:
                raise ValueError("Invalid strategy for handling missing values.")

        # --- OPERATION: Standardize Text Columns ---
        elif operation == 'standardize_text':
            column = params.get('column')
            if not column or column not in df.columns:
                raise ValueError(f"Column '{column}' not found.")
            
            # Apply common text cleaning functions using pandas .str accessor
            df[column] = df[column].str.lower()
            df[column] = df[column].str.strip()
            # You could add more, like removing punctuation: .str.replace(r'[^\w\s]', '')
            message = f"Text in column '{column}' has been standardized (lowercase, stripped whitespace)."

        # --- OPERATION: Convert Data Type ---
        elif operation == 'convert_type':
            column = params.get('column')
            to_type = params.get('to_type')
            if not all([column, to_type]) or column not in df.columns:
                raise ValueError("Both 'column' and 'to_type' parameters are required.")

            # Use pandas' astype() to convert column type
            if to_type == 'numeric':
                df[column] = pd.to_numeric(df[column], errors='coerce') # Coerce errors will turn non-numbers into NaN
            else:
                df[column] = df[column].astype(to_type)
            message = f"Data type of column '{column}' converted to {to_type}."
        
        else:
            return jsonify({"error": f"Unknown operation: {operation}"}), 400
        
        # Update the DataFrame in our server's memory
        dataframes['current'] = df
        
        # Prepare the final JSON response
        response_data['message'] = message
        # Convert the first 50 rows of the DataFrame to JSON for a preview
        response_data['preview'] = json.loads(df.head(50).to_json(orient='split'))
        
        return jsonify(response_data), 200

    except Exception as e:
        # Return a generic error if anything goes wrong
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
