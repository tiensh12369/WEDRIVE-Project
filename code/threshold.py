from scipy.stats import iqr
from sklearn.cluster import KMeans
from collections import defaultdict

def Mean_Standard_Deviation(frequencies):

    data = frequencies
    mean_value = np.mean(data)
    std_dev = np.std(data)
    k = 2

    threshold = mean_value + k * std_dev

    return threshold

def Median_Interquartile_Range(frequencies):

    data = frequencies
    median_value = np.median(data)
    iqr_value = iqr(data)
    k = 2

    threshold = median_value + k * iqr_value

    return threshold

def Percentiles(frequencies):

    data = frequencies
    threshold = np.percentile(data, 95)

    return threshold

def KMeans_threshold(frequencies):

    data = np.array(frequencies).reshape(-1, 1)
    kmeans = KMeans(n_clusters=2, n_init=10)  # You may need to adjust the number of clusters
    kmeans.fit(data)
    threshold = np.max(kmeans.cluster_centers_)

    return threshold