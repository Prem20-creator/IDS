# app.py
from flask import Flask, render_template, request
import numpy as np
import pandas as pd
import joblib

# Initialize Flask app
app = Flask(__name__, template_folder="templates")

# Load models and scaler (joblib files)
binary_model = joblib.load("binary_ids_model.joblib")
attack_model = joblib.load("attack_type_model.joblib")
scaler = joblib.load("scaler.joblib")

# Feature names 
FEATURE_COLS = [
    "duration", "src_bytes", "dst_bytes", "count", "srv_count",
    "serror_rate", "same_srv_rate", "diff_srv_rate", "dst_host_count", "dst_host_srv_count"
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Read inputs from the form and convert to floats
        values = []
        for col in FEATURE_COLS:
            raw = request.form.get(col, "")
            try:
                val = float(raw)
            except:
                # If conversion fails, default to 0.0
                val = 0.0
            values.append(val)

        # Create a DataFrame with proper column names (removes scaler warning)
        input_df = pd.DataFrame([values], columns=FEATURE_COLS)

        # Scale the DataFrame (scaler was fitted with column names)
        input_scaled = scaler.transform(input_df)

        # Binary classification: Normal or Attack
        binary_pred = binary_model.predict(input_scaled)[0]

        # Interpret the binary label robustly (accepts 0/1 or 'normal'/'attack')
        is_normal = False
        # handle integer labels
        if isinstance(binary_pred, (int, np.integer, float, np.floating)):
            is_normal = (int(binary_pred) == 0)
        else:
            is_normal = str(binary_pred).strip().lower() == "normal"

        if is_normal:
            result = "Normal"
            attack_type = "None"
        else:
            # Predict attack type (string label expected)
            attack_type_pred = attack_model.predict(input_scaled)[0]
            attack_type = str(attack_type_pred)
            result = "Attack"

        return render_template(
            'index.html',
            prediction_text=f"Prediction: {result}",
            attack_text=f"Attack Type: {attack_type}"
        )

    except Exception as e:
        # For debugging, return the error message in the template
        return render_template('index.html', prediction_text=f"Error: {e}", attack_text="")

if __name__ == "__main__":
    app.run(debug=True)
