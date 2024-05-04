import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score

# Assuming result_df and result_df_test are your dataframes
# Convert 'F1' column to binary (0 and 1) based on your mapping
result_df['F1'] = result_df['F1'].replace({'N': 0, 'AN': 1})

# Compute accuracy
accuracy = accuracy_score(result_df['F1'], result_df_test['label'])

# Compute confusion matrix
conf_matrix = confusion_matrix(result_df['F1'], result_df_test['label'])

# Compute recall
recall = recall_score(result_df['F1'], result_df_test['label'])

# Compute precision
precision = precision_score(result_df['F1'], result_df_test['label'])

print("Accuracy:", accuracy)
print("Confusion Matrix:")
print(conf_matrix)
print("Recall:", recall)
print("Precision:", precision)