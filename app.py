# --- Add these lines to the top to fix the import path ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---------------------------------------------------------

from flask import Flask, request, render_template, jsonify
import numpy as np
import pandas as pd
import json

# This import should now work correctly on the server because the root is on the path
from pipeline.predict_pipeline import CustomData, PredictPipeline

# Create the Flask app instance
application = Flask(__name__)
app = application

# This dictionary will store the DataFrame in memory
dataframes = {'current': None}


# Define your routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predictdata', methods=['GET', 'POST'])
def predict_datapoint():
    if request.method == 'GET':
        return render_template('home.html')
    else:
        data = CustomData(
            gender=request.form.get('gender'),
            race_ethnicity=request.form.get('ethnicity'),
            parental_level_of_education=request.form.get('parental_level_of_education'),
            lunch=request.form.get('lunch'),
            test_preparation_course=request.form.get('test_preparation_course'),
            reading_score=float(request.form.get('reading_score')),
            writing_score=float(request.form.get('writing_score'))
        )
        pred_df = data.get_data_as_data_frame()
        print(pred_df)

        predict_pipeline = PredictPipeline()
        results = predict_pipeline.predict(pred_df)
        
        return render_template('home.html', results=results[0])

@app.route('/clean', methods=['POST'])
def clean_data():
    """Handles data cleaning operations on the currently loaded DataFrame."""
    df = dataframes.get('current')
    if df is None:
        return jsonify({"error": "No data has been loaded yet."}), 400

    operation = request.json.get('operation')
    params = request.json.get('params', {})
    
    try:
        response_data = {}
        if operation == 'remove_duplicates':
            rows_before = len(df)
            df = df.drop_duplicates(**params)
            rows_after = len(df)
            response_data['removed_count'] = rows_before - rows_after
            message = f"{rows_before - rows_after} duplicate rows removed."
        
        elif operation == 'handle_missing':
            strategy = params.pop('strategy', 'drop')
            if strategy == 'drop':
                df = df.dropna(**params)
                message = "Rows with missing values dropped."
            elif strategy == 'fill':
                df = df.fillna(**params)
                message = "Missing values filled."
            else:
                raise ValueError("Invalid strategy for handling missing values.")
        
        else:
            return jsonify({"error": f"Unknown operation: {operation}"}), 400
        
        dataframes['current'] = df
        response_data['message'] = message
        response_data['preview'] = json.loads(df.head(50).to_json(orient='split'))
        
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# Run the app if the script is executed directly
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

