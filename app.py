# File: app.py
# This version imports and uses the REAL data-purifier library from PyPI

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import io
import datapurifier as purifier # <-- Importing the REAL data-purifier library

app = Flask(__name__)
CORS(app)

# This will hold the user's data while they work
dataframes = {'current': None}

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400
    try:
        # We can still use pandas to load the data initially
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.stream)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file.stream)
        else:
            return jsonify({"error": "Unsupported file type"}), 400
            
        dataframes['current'] = df
        return jsonify({"message": "File uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clean', methods=['POST'])
def clean_data():
    df = dataframes.get('current')
    if df is None:
        return jsonify({"error": "No data loaded."}), 400
    
    # NOTE: You will need to replace the function names below with the
    # EXACT function names from the data-purifier library's documentation.
    # The names below are educated guesses.
    
    try:
        # Example of how you would call the library's functions
        df = purifier.handle_duplicates(df, action='remove')
        df = purifier.handle_missing_values(df, strategy='mean')
        
        dataframes['current'] = df
        
        return jsonify({
            "message": "Data cleaned successfully using data-purifier!",
            "preview": df.head(50).to_json(orient='split')
        }), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

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
