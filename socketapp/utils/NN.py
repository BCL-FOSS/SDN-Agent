import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

class NN:
    def __init__(self):
        pass

    def preprocess_input(self, json_data):
        # JSON -> Pandas DataFrame 
        df = pd.DataFrame([json_data])

        # Scaling features before running predictions
        features = ['avg_ipt', 'bytes_in', 'bytes_out', 'dest_ip',	'entropy', 'num_pkts_out', 'num_pkts_in', 'proto', 'src_ip', 'time_end', 'time_start', 'total_entropy', 'duration', 'src_port', 'dest_port'] 
        df_cleaned = df[features].fillna(0)  # Fill missing values

        # Scale data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_cleaned)

        return X_scaled

    # Function to preprocess the data for inference
    def preprocess_file_for_inference(self, file_path):
        # Load the data
        data = pd.read_csv(file_path)

        # Drop rows with missing values in relevant columns (src_port, dest_port)
        data_cleaned = data.dropna(subset=['src_port', 'dest_port'])

        # Retain the original data for analysis after predictions
        original_data = data_cleaned.copy()

        # Drop the label column if present (in this case, for inference)
        if 'label' in data_cleaned.columns:
            data_cleaned = data_cleaned.drop(columns=['label'])

        # Scale the numerical features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(data_cleaned)

        return X_scaled, original_data

    def predict(self, processed_input=None, model=None):
        # Model determines if packet is malicious, benign or outlier
        predictions = model.predict(processed_input)

        # Prediction -> binary conversion (benign, malicious, outlier)
        predicted_classes = np.argmax(predictions, axis=1)

        # Response conversion to JSON
        prediction = predicted_classes.tolist()
        inference_value = json.dumps(prediction)
        return inference_value