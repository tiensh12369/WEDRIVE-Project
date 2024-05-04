import os
import ast
import numpy as np
import pandas as pd

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
    q1 = np.quantile(frequencies, 0.25)

    # finding the 3rd quartile
    q3 = np.quantile(frequencies, 0.75)
    med = np.median(frequencies)

    # finding the iqr region
    iqr = q3-q1

    # finding upper and lower whiskers
    upper_bound = q3+(1.5*iqr)
    lower_bound = q1-(1.5*iqr)

    threshold = iqr+upper_bound-lower_bound

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

# Save Frequency Dictionary to CSV
frequency_df = pd.DataFrame(list(frequency_dict.items()), columns=['Label', 'Frequency'])
frequency_df.to_csv('label_frequencies.csv', index=False)

# Compute the threshold based on Frequency Dictionary
labels = frequency_df['Frequency'].tolist()
# threshold = compute_threshold(labels)
threshold = 3.0
# Load the grid information from the CSV file
grid_info_file = 'grid_information_with_paths.csv'
grid_info = pd.read_csv(grid_info_file)

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

                if pd.notna(label):
                    if label in frequency_df['Label'].values:
                        # Get the corresponding frequency
                        frequency = frequency_df.loc[frequency_df['Label'] == label, 'Frequency'].values[0]

                        # Compare with the threshold
                        if frequency >= threshold:
                            pass
                        else:
                            print(f"Label: {label} does not meet the frequency threshold (Frequency: {frequency})")
                    else:
                        print(f"Label: {label} is not in label_frequencies.csv")
                else:
                    print(f'The point ({lat}, {lng}) is not in any grid.')
                    
