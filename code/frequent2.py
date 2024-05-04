import os
import ast
import numpy as np
import pandas as pd

from scipy.stats import iqr
from collections import defaultdict

# Paths of all the datasets
labeled_data_path = os.getcwd()+'\\Label'
test_dataset_path = os.getcwd()+'\\Test'

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


# Load Data and Collapse Recursive Data
pair_frequency = defaultdict(int)

for file_name in os.listdir(labeled_data_path):
    if file_name.endswith('.csv'):
        file_path = os.path.join(labeled_data_path, file_name)
        df = pd.read_csv(file_path)
        
        # Collapse recursive data in 'grid_label' column
        labels = df['grid_label'].tolist()
        unique_labels = CollapseRecurringLabels(labels)
        
        # Iterate through the list to create pairs and count frequencies
        previous_label = None
        
        for label in unique_labels:
            if previous_label is not None:
                pair = (previous_label, label)
                pair_frequency[pair] += 1

            # Update the previous label for the next iteration
            previous_label = label
        
# Save Frequency Dictionary to CSV
frequency_df = pd.DataFrame(list(pair_frequency.items()), columns=['Label', 'Frequency'])
frequency_df.to_csv('pair_frequencies.csv', index=False)

# Compute the threshold based on Frequency Dictionary
f_labels = frequency_df['Frequency'].tolist()
threshold = compute_threshold(f_labels)

# Load the grid information from the CSV file
grid_info_file = 'grid_information_with_paths.csv'
grid_info = pd.read_csv(grid_info_file)

# Read the test CSV file
for filename in os.listdir(test_dataset_path):
    if filename.endswith('.csv'):
        csv_file_path = os.path.join(test_dataset_path, filename)
        df = pd.read_csv(csv_file_path)
        previous_label = ""
        RecurringLabels = ""

        # Iterate over rows in a streaming way
        for index, row in df.iterrows():
            # Process the current row
            lat = row['lat']
            lng = row['lng']

            label = find_label_for_point(lat, lng, grid_info)

            # Check if the pair exists in pair_frequencies.csv
            if label == RecurringLabels:
                pass
            else:
                RecurringLabels = label

                if previous_label == '' and pd.notna(label):
                    pass
                elif pd.notna(label) and pd.notna(previous_label):
                    pair = (previous_label, label)

                    if frequency_df['Label'].isin([pair]).any():
                        # Get the corresponding frequency
                        frequency = frequency_df.loc[frequency_df['Label'] == pair, 'Frequency'].values[0]

                        # Compare with the threshold
                        if frequency >= threshold:
                            pass
                        else:
                            print(f"Pair: {pair} does not meet the frequency threshold (Frequency: {frequency})")
                    else:
                        print(f"Pair: {pair} is not in label_frequencies.csv")

                else:
                    print(f'The point ({lat}, {lng}) is not in any grid.')

                # Update previous_label for the next iteration
                previous_label = label

