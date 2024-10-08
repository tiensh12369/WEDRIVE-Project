import os
import ast
import numpy as np
import pandas as pd

from scipy.stats import iqr
from sklearn.metrics import silhouette_score
from sklearn.metrics import davies_bouldin_score

# Paths of all the datasets
labeled_data_path = os.getcwd()+'\\Label'
test_dataset_path = os.getcwd()+'\\Test'
evaluation_file = os.getcwd()+'\\evaluation.csv'
test_label_evaluation_file = os.getcwd()+'\\test_label_evaluation.csv'

# Create a new list with non-consecutive duplicates removed
def CollapseRecurringLabels(original_list):

    # Initialize the result list with the first element of the original list
    result_list = [original_list[0]]  

    for i in range(1, len(original_list)):
        if original_list[i] != original_list[i - 1]:
            result_list.append(original_list[i])

    return result_list

def compute_threshold(frequencies):
    data = frequencies
    median_value = np.median(data)
    iqr_value = iqr(data)
    k = 2

    threshold = median_value + k * iqr_value

    return threshold

def find_label_for_point(lat, lng, grid_info):
    for index, row in grid_info.iterrows():
        # Convert string representations to tuples
        min_lat, min_lng = ast.literal_eval(row['Min Latitude, Min Longitude'])
        max_lat, max_lng = ast.literal_eval(row['Max Latitude, Max Longitude'])

        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
            return row['Grid Name']

    return None

# Step 1: Load Data and Collapse Recursive Data
frequency_dict = {}

for file_name in os.listdir(labeled_data_path):
    if file_name.endswith('.csv'):
        file_path = os.path.join(labeled_data_path, file_name)
        df = pd.read_csv(file_path)

        # Collapse recursive data in 'grid_label' column
        labels = df['grid_label'].tolist()
        unique_labels = CollapseRecurringLabels(labels)
        df_ = pd.DataFrame(unique_labels, columns=['grid_label'])

        # Step 2: Compute Frequency of Each Label
        label_counts = df_['grid_label'].value_counts().to_dict()

        # Step 3: Update Frequency Dictionary
        for label, count in label_counts.items():
            frequency_dict[label] = frequency_dict.get(label, 0) + count

# Check if the file exists
if os.path.isfile(evaluation_file):
    # Read the CSV file into a DataFrame
    evaluation_df = pd.read_csv(evaluation_file)
else:
    # Create an empty DataFrame
    evaluation_df = pd.DataFrame(columns=['cell_GeoLabel', 'lF', 'F1'])
    evaluation_df.to_csv(evaluation_file, index=False)
    
if os.path.isfile(test_label_evaluation_file):
    # Read the CSV file into a DataFrame
    evaluation_df = pd.read_csv(test_label_evaluation_file)
else:
    # Create an empty DataFrame
    evaluation_df = pd.DataFrame(columns=['cell_GeoLabel', 'cell_Answer', 'pair_GeoLabel', 'pair_Answer'])
    evaluation_df.to_csv(test_label_evaluation_file, index=False)

# Save Frequency Dictionary to CSV
frequency_df = pd.DataFrame(list(frequency_dict.items()), columns=['Label', 'Frequency'])
frequency_df.to_csv('label_frequencies.csv', index=False)

# Compute the threshold based on Frequency Dictionary
labels = frequency_df['Frequency'].tolist()
threshold = 3 #compute_threshold(labels)

# Load the grid information from the CSV file
grid_info_file = 'grid_information_with_paths.csv'
grid_info = pd.read_csv(grid_info_file)

latitudes = list()
longitudes = list()
anomalies = list()

# Read the test CSV file
for filename in os.listdir(test_dataset_path):
    if filename.endswith('.csv'):
        csv_file_path = os.path.join(test_dataset_path, filename)
        df = pd.read_csv(csv_file_path)
        previous_label = ""

        # Iterate over rows in a streaming way
        for index, row in df.iterrows():
            # Process the current row
            lat = row['lat']
            lng = row['lng']

            label = find_label_for_point(lat, lng, grid_info)

            # Check if the label exists in label_frequencies.csv
            if label == previous_label:
                pass
            else:
                previous_label = label

                latitudes.append(lat)
                longitudes.append(lng)

                if pd.notna(label):
                    if label in frequency_df['Label'].values:
                        # Get the corresponding frequency
                        frequency = frequency_df.loc[frequency_df['Label'] == label, 'Frequency'].values[0]

                        # Compare with the threshold
                        if frequency >= threshold:
                            Anomaly_type = "N"
                            anomalies.append(0)
                        else:
                            print(f"Label: {label} does not meet the frequency threshold (Frequency: {frequency})")
                            Anomaly_type = "AN"
                            anomalies.append(1)
                    else:
                        print(f"Label: {label} is not in label_frequencies.csv")
                        frequency = 0
                        Anomaly_type = "AN"
                        anomalies.append(1)
                else:
                    print(f'The point ({lat}, {lng}) is not in any grid.')
                    frequency = 0
                    Anomaly_type = "AN"
                    anomalies.append(1)

                current_data = pd.DataFrame({'cell_GeoLabel': [label], 'F1': [Anomaly_type], 'lF': [frequency]})
                evaluation_df = pd.concat([evaluation_df, current_data], ignore_index=True)

coordinates = list(zip(latitudes, longitudes))

# Calculating the Davies-Bouldin Index
db_index = davies_bouldin_score(coordinates, anomalies)
print(f"Davies-Bouldin Index: {db_index}")
# Calculating the silhouette score
silhouette_avg = silhouette_score(coordinates, anomalies)
print(f"Silhouette Score: {silhouette_avg}")

evaluation_df.to_csv(evaluation_file, index=False)

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, precision_recall_curve, roc_curve, auc

Method = 'F1'

# Read the CSV file
df = pd.read_csv('evaluation.csv')
df_test = pd.read_excel('test_label_evaluation.xlsx', engine='openpyxl')

# Replace 'AN' with 1 and 'N' with 0 in the 'F1' column
df[Method] = df[Method].replace({'AN': 1, 'N': 0})

if Method != 'F2':
    result_df = df[['cell_GeoLabel', Method]]
    result_df_test = df_test[['cell_GeoLabel', 'cell_Answer']]
    accuracy = accuracy_score(result_df[Method], result_df_test['cell_Answer'])
    conf_matrix = confusion_matrix(result_df[Method], result_df_test['cell_Answer'])
    recall = recall_score(result_df[Method], result_df_test['cell_Answer'], pos_label = 0)
    precision = precision_score(result_df[Method], result_df_test['cell_Answer'], pos_label = 0)
    
    precision_curve, recall_curve, _ = precision_recall_curve(result_df_test['cell_Answer'], result_df[Method])
    fpr, tpr, _ = roc_curve(result_df_test['cell_Answer'], result_df[Method])
    roc_auc = auc(fpr, tpr)
else:
    result_df = df[['pair_GeoLabel', Method]]
    result_df_test = df_test[['pair_GeoLabel', 'pair_Answer']]
    accuracy = accuracy_score(result_df[Method], result_df_test['pair_Answer'])
    conf_matrix = confusion_matrix(result_df[Method], result_df_test['pair_Answer'])
    recall = recall_score(result_df[Method], result_df_test['pair_Answer'], pos_label = 0)
    precision = precision_score(result_df[Method], result_df_test['pair_Answer'], pos_label = 0)
    
    precision_curve, recall_curve, _ = precision_recall_curve(result_df_test['pair_Answer'], result_df[Method])
    fpr, tpr, _ = roc_curve(result_df_test['pair_Answer'], result_df[Method])
    roc_auc = auc(fpr, tpr)

# Precision-Recall 곡선 시각화
plt.figure()
plt.step(recall_curve, precision_curve, where='post')
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Precision-Recall Curve')
plt.ylim([0.0, 1.05])
plt.xlim([0.0, 1.0])
plt.show()

# ROC 곡선 시각화
plt.figure()
plt.plot(fpr, tpr, color='darkorange', lw=2, label='ROC curve (area = %0.2f)' % roc_auc)
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic Curve')
plt.legend(loc="lower right")
plt.show()

print("Accuracy:", accuracy)
print("Confusion Matrix:")
print(conf_matrix)
print("Recall:", recall)
print("Precision:", precision)