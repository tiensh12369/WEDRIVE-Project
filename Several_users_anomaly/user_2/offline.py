import os
import string
import datetime

import folium
import pandas as pd
import geopy.distance

# Paths of all the datasets
train_dataset_path = os.getcwd()+'\\Train'
test_dataset_path = os.getcwd()+'\\Test'
labeled_data_path = os.getcwd()+'\\Label'

# Define a function to convert numbers into corresponding letter labels
def num_to_letter(num):
    '''
    num         : number that we have to convert
    '''
    return string.ascii_uppercase[num]

# Define a function to check whether the path passes through the grid
def is_path_in_grid(south, west, north, east, path_points):
    '''
    south       : minimum latitude
    west        : minimum longitude
    north       : maximum latitude
    east        : maximum longitude
    path_points : coordinate points
    '''
    for lat, lng in path_points:
        if south <= lat <= north and west <= lng <= east:
            return True
    return False

# Create a function to get the grid label of the coordinate point
def get_grid_label(lat, lng, final_grids):
    '''
    lat         : latitude
    lng         : longitude
    final_grids : all cells and their minimum/maximum latitude/longitude
    '''
    for south, west, north, east, grid_label in final_grids:
        if south <= lat <= north and west <= lng <= east:
            return grid_label
    return None

# Approximate border coordinates of South Korea
south_korea_bounds = [32, 124, 39, 132]
 
# Create a map 
m = folium.Map(location=[(south_korea_bounds[0] + south_korea_bounds[2]) / 2,
                         (south_korea_bounds[1] + south_korea_bounds[3]) / 2],
               zoom_start=7)

# Read waypoint
path_points = []
directory = train_dataset_path
path_dataframes = []

for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        data = pd.read_csv(file_path, encoding='utf-8')
        path_dataframes.append(data)
        points = data[['lat', 'lng']].values.tolist()
        path_points.extend(points)
 
        # draw a line on the map
        folium.PolyLine(points, color='red', weight=2.5, opacity=1).add_to(m)

# Initialize grid queue
grid_queue = []
final_grids = []  # Used to store the final small grid
initial_lat_step = (south_korea_bounds[2] - south_korea_bounds[0]) / 26
initial_lon_step = (south_korea_bounds[3] - south_korea_bounds[1]) / 26
#initial_lat_step *= 0.94
#initial_lon_step *= 0.94
 
for i in range(26):
    for j in range(26):
        south = south_korea_bounds[0] + i * initial_lat_step
        north = south_korea_bounds[0] + (i + 1) * initial_lat_step
        west = south_korea_bounds[1] + j * initial_lon_step
        east = south_korea_bounds[1] + (j + 1) * initial_lon_step
        grid_queue.append((south, west, north, east, num_to_letter(i) + num_to_letter(j)))

# Process grid queue
min_size_km = 1  # Minimum grid size (km)
subdivisions = ['A', 'B', 'C', 'D']  # Split label
while grid_queue:
    south, west, north, east, grid_label = grid_queue.pop(0)
    grid_size_km = min(geopy.distance.distance((south, west), (south, east)).km,
                       geopy.distance.distance((south, west), (north, west)).km)
 
    if grid_size_km > min_size_km and is_path_in_grid(south, west, north, east, path_points):
        mid_lat = (south + north) / 2
        mid_lon = (west + east) / 2
        grid_queue.append((south, west, mid_lat, mid_lon, grid_label + 'C'))
        grid_queue.append((mid_lat, west, north, mid_lon, grid_label + 'A'))
        grid_queue.append((south, mid_lon, mid_lat, east, grid_label + 'D'))
        grid_queue.append((mid_lat, mid_lon, north, east, grid_label + 'B'))
    else:
        final_grids.append((south, west, north, east, grid_label))
        folium.Rectangle(
            bounds=[[south, west], [north, east]],
            color='#0000FF',
            fill=True,
            fill_opacity=0.1
        ).add_to(m)
        # Add a green label to the center of the grid
        folium.Marker(
            location=[(south + north) / 2, (west + east) / 2],
            icon=folium.DivIcon(html=f'<div style="font-size: 8pt; color: yellow;">{grid_label}</div>')
        ).add_to(m)

grid_data = {
    'Grid Name': [label for _, _, _, _, label in final_grids],
    'Min Latitude, Min Longitude': [(south, west) for south, west, _, _, _ in final_grids],
    'Max Latitude, Max Longitude': [(north, east) for _, _, north, east, _ in final_grids]
}
grid_df = pd.DataFrame(grid_data)

# Save the grid information to a CSV file
grid_df.to_csv('grid_information_with_paths.csv', index=False)

# Assign final grid labels to waypoints
for data in path_dataframes:
    data['grid_label'] = data.apply(lambda row: get_grid_label(row['lat'], row['lng'], final_grids), axis=1)

# checking if the directory demo_folder exist or not. 
if not os.path.exists(labeled_data_path):  
    os.makedirs(labeled_data_path)

# Save the updated DataFrame to a new CSV file
for idx, df in enumerate(path_dataframes):
    labeled_file = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    df.to_csv(f'Label/{labeled_file}.csv', index=False)

# Save or show map
m.save('south_korea_grid_map_with_subdivided_paths.html')