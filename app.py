@app.route('/clean', methods=['POST'])
def clean_data():
    df = dataframes.get('current')
    if df is None:
        return jsonify({"error": "No data loaded."}), 400

    operation = request.json.get('operation')
    params = request.json.get('params', {})
    
    try:
        response_data = {} # Prepare a dictionary for our response
        
        if operation == 'remove_duplicates':
            rows_before = len(df)
            # This is a guess for the purifier function name. Check the library docs!
            df = purifier.handle_duplicates(df, action='remove')
            rows_after = len(df)
            response_data['removed_count'] = rows_before - rows_after
            message = "Duplicate rows removed."
            
        elif operation == 'handle_missing':
            # This is a guess for the purifier function name.
            df = purifier.handle_missing_values(df, **params)
            message = "Missing values handled."
            
        elif operation == 'standardize_text':
            # This is a guess for the purifier function name.
            df = purifier.clean_text(df, **params)
            message = "Text standardized."
        
        elif operation == 'convert_type':
             # This is a guess for the purifier function name.
            df = purifier.convert_data_type(df, **params)
            message = "Data type converted."
        else:
            return jsonify({"error": f"Unknown operation: {operation}"}), 400
        
        dataframes['current'] = df
        
        # Add the standard data to our response
        response_data['message'] = message
        response_data['preview'] = json.loads(df.head(50).to_json(orient='split'))
        
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred during cleaning: {str(e)}"}), 500
