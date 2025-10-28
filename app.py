# File: app.py - Final Version with Cleaning Logic
import json
import io
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import datapurifier as purifier

app = Flask(__name__)
CORS(app, origins="*")

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

        total_cells = len(df) * len(df.columns)
        missing_pct = round((df.isnull().sum().sum() / total_cells) * 100, 2) if total_cells > 0 else 0

        profile = {
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values_pct": missing_pct
        }

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
    # params = request.json.get('params', {}) # For future use if operations need options

    try:
        # --- THIS IS THE NEW LOGIC ---
        # We check which operation the frontend requested and call the correct function.
        # NOTE: The function names like 'purifier.handle_duplicates' are guesses.
        # You must check the data-purifier library's documentation for the real names.
        
        if operation == 'remove_duplicates':
            df = purifier.handle_duplicates(df, action='remove')
            message = "Duplicate rows removed."
        elif operation == 'handle_missing':
            # This is a guess for a function that fills missing values.
            df = purifier.handle_missing_values(df, strategy='mean')
            message = "Missing values handled."
        elif operation == 'standardize_text':
             # This is a guess for a text standardization function.
            df = purifier.clean_text(df, case='lower')
            message = "Text standardized."
        else:
            return jsonify({"error": f"Unknown operation: {operation}"}), 400
        
        dataframes['current'] = df
        
        return jsonify({
            "message": message,
            "preview": json.loads(df.head(50).to_json(orient='split'))
        }), 200

    except Exception as e:
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
