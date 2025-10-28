# File: app.py - Final, Complete Version

import json # <--- ADDED/VERIFIED: Crucial for NaN to null conversion
import io
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import datapurifier as purifier # Verified import name

app = Flask(__name__)

# This allows your app to accept requests from ANY domain, solving CORS issues.
CORS(app, origins="*")

# WARNING: This simple in-memory storage is NOT multi-user safe.
dataframes = {'current': None}

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.stream)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file.stream)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        dataframes['current'] = df

        # Build the detailed column information the frontend modal needs
        column_details = []
        for col in df.columns:
            column_details.append({
                "name": col,
                "non_null_count": int(df[col].notna().sum()),
                "dtype": str(df[col].dtype)
            })

        total_cells = len(df) * len(df.columns)
        missing_pct = round((df.isnull().sum().sum() / total_cells) * 100, 2) if total_cells > 0 else 0

        profile = {
            "rows": len(df),
            "columns": column_details,  # Detailed list for modal
            "missing_values_pct": missing_pct
        }

        # FINAL FIX: Use json.loads(to_json) to send a perfect JSON object
        return jsonify({
            "message": "File uploaded successfully",
            "preview": json.loads(df.head(50).to_json(orient='split')),
            "profile": profile
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clean', methods=['POST'])
def clean_data():
    df = dataframes.get('current')
    if df is None:
        return jsonify({"error": "No data loaded."}), 400

    operation = request.json.get('operation')
    params = request.json.get('params', {})
    
    try:
        response_data = {}
        
        # --- CLEANING LOGIC (ASSUMED FUNCTIONS) ---
        if operation == 'remove_duplicates':
            rows_before = len(df)
            df = purifier.handle_duplicates(df, action='remove')
            rows_after = len(df)
            response_data['removed_count'] = rows_before - rows_after
            message = "Duplicate rows removed."
            
        elif operation == 'handle_missing':
            df = purifier.handle_missing_values(df, **params)
            message = "Missing values handled."
            
        elif operation == 'standardize_text':
            df = purifier.clean_text(df, **params)
            message = "Text standardized."
        
        elif operation == 'convert_type':
            df = purifier.convert_data_type(df, **params)
            message = "Data type converted."
        else:
            return jsonify({"error": f"Unknown operation: {operation}"}), 400
        
        dataframes['current'] = df
        
        # FINAL FIX: Send JSON object back to frontend
        response_data['message'] = message
        response_data['preview'] = json.loads(df.head(50).to_json(orient='split'))
        
        return jsonify(response_data), 200

    except Exception as e:
        # This catches errors from the purifier library and sends them to the frontend
        return jsonify({"error": f"An error occurred during cleaning: {str(e)}"}), 500

@app.route('/download', methods=['GET'])
def download_file():
    df = dataframes.get('current')
    if df is None: return jsonify({"error": "No data available"}), 400
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='cleaned_data.csv', mimetype='text/csv')

if __name__ == '__main__':
    app.run(debug=True)
