# File: app.py - Hardened Version
import json
import io
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import datapurifier as purifier

app = Flask(__name__)

# This allows your app to accept requests from ANY domain.
CORS(app, origins="*")

# WARNING: This simple in-memory storage is NOT multi-user safe.
# If two people use the app at once, they will overwrite each other's data.
# This is okay for a personal tool, but not for a public website.
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

        # BUG FIX: Prevent division by zero if an empty file is uploaded.
        total_cells = len(df) * len(df.columns)
        missing_pct = round((df.isnull().sum().sum() / total_cells) * 100, 2) if total_cells > 0 else 0

        profile = {
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values_pct": missing_pct
        }

        # Use json.loads with to_json to correctly handle NaN -> null conversion.
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

    # This is where you will implement the logic to call the purifier
    # library based on what the user selects in the frontend.
    # The code below is a placeholder for that future logic.
    operation = request.json.get('operation')
    params = request.json.get('params', {})
    
    # Example: df = purifier.handle_duplicates(df)
    message = f"Operation '{operation}' would be applied here."
    
    dataframes['current'] = df

    # BUG FIX: The original code used .to_json(), which sends a string.
    # This now correctly sends a JSON object and handles NaN -> null conversion.
    return jsonify({
        "message": message,
        "preview": json.loads(df.head(50).to_json(orient='split'))
    }), 200

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
