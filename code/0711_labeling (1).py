import pandas as pd
import string
import os
import folium
import geopy.distance
import datetime

#Raw 데이터 경로
Raw_data_path=os.getcwd()+'/data/pedestrian/___ecfd1086a6934ae08b555b3ae880d31e'
labeled_data_path=os.getcwd()+'/data/pedestrian_processed/___ecfd1086a6934ae08b555b3ae880d31e'

# 위치(number)를 문자로 바꿔 그리드를 표기하기 위해 만든 함수
def num_to_letter(num):
    '''
    num         : number that we have to convert
    ex) num=0 -> A
        num=1 -> B
        ...
        num=25-> Z
    '''
    return string.ascii_uppercase[num]

# 경로가 그리드 안에 있는지 확인하는 함수
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

# 해당 위치의 그리드를 설정하는 함수
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

# 대략적인 대한민국의 경계
south_korea_bounds = [32, 124, 39, 132]

# Create a map 
m = folium.Map(location=[(south_korea_bounds[0] + south_korea_bounds[2]) / 2,
                         (south_korea_bounds[1] + south_korea_bounds[3]) / 2],
               zoom_start=7)

# 이동 경로 불러오기
path_points = []
directory = Raw_data_path
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

# 한국에 초기 그리드값 할당하기
grid_queue = []     #최초 그리드
final_grids = []    #세부로 나눠 만든 최종 그리드
initial_lat_step = (south_korea_bounds[2] - south_korea_bounds[0]) / 26 #한국의 위도를 26등분 냄
initial_lon_step = (south_korea_bounds[3] - south_korea_bounds[1]) / 26 #한국의 경도를 26등분 냄
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
    labeled_file = os.listdir(directory)[idx]
    df.to_csv(f'{labeled_data_path}/{labeled_file}.csv', index=False)

# Save or show map
m.save('south_korea_grid_map_with_subdivided_paths.html')