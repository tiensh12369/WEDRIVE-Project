import pandas as pd
import os
import ast

labeled_data_path = os.getcwd()+'\\Label'
test_dataset_path = os.getcwd()+'\\Test'

geo_trace_pts = {} #전체 중복 경로 횟수

def jaro_similarity(list1, list2):
    # 두 리스트의 길이를 구함
    len_list1 = len(list1)
    len_list2 = len(list2)

    # 두 리스트 중에서 더 긴 길이를 기준으로 함
    max_len = max(len_list1, len_list2)

    # 일치하는 값의 개수를 세기 위한 변수 초기화
    match_count = 0

    # 일치하는 값의 인덱스를 저장하기 위한 리스트 초기화
    matches_list1 = [False] * len_list1
    matches_list2 = [False] * len_list2

    # 첫 번째 단계: 일치하는 값 세기
    for i in range(len_list1):
        start = max(0, i - int(max_len / 2))
        end = min(i + int(max_len / 2) + 1, len_list2)

        for j in range(start, end):
            if not matches_list2[j] and list1[i] == list2[j]:
                matches_list1[i] = True
                matches_list2[j] = True
                match_count += 1
                break

    # 일치하는 값이 하나도 없으면 0 반환
    if match_count == 0:
        return 0.0

    # 두 번째 단계: 일치하는 값의 순서에 따라 가중치 적용
    transpositions = 0
    k = 0
    for i in range(len_list1):
        if matches_list1[i]:
            while not matches_list2[k]:
                k += 1

            if list1[i] != list2[k]:
                transpositions += 1

            k += 1

    # 유사도 계산
    jaro_similarity = ((match_count / len_list1 + match_count / len_list2 + (match_count - transpositions / 2) / match_count)/ 3.0)

    return jaro_similarity

def com_cell(label):
    
    if label in cell:
        print('정상 경로')
        return True
    else:
        print('비정상 경로')
        return False

# Create a function to get the grid label of the coordinate point
def find_label_for_point(lat, lng, grid_info):
    for index, row in grid_info.iterrows():
        # Convert string representations to tuples
        min_lat, min_lng = ast.literal_eval(row['Min Latitude, Min Longitude'])
        max_lat, max_lng = ast.literal_eval(row['Max Latitude, Max Longitude'])

        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
            return row['Grid Name']

    return None

# 디렉토리 내의 모든 CSV 파일 가져오기
csv_files = [f for f in os.listdir(labeled_data_path) if f.endswith('.csv')]

# 각 CSV 파일을 다른 데이터프레임에 저장하기 위한 딕셔너리 생성
dfs = {}

# 각 CSV 파일을 읽어서 데이터프레임에 저장
for file in csv_files:
    # CSV 파일의 경로
    file_path = os.path.join(labeled_data_path, file)
    
    # 파일명을 key로 사용하여 데이터프레임 생성
    df_key = os.path.splitext(file)[0]  # 파일명에서 확장자 제거
    dfs[df_key] = pd.read_csv(file_path)['grid_label']
     
    gridDataLabel = 0 # grid lable 중복 제거 변수
    geo_trace = [] #geo trace 리스트
    
    for grid_label in dfs[df_key]:
        if gridDataLabel != grid_label:
            gridDataLabel = grid_label
            geo_trace.append(grid_label)

    if geo_trace == []:
        geo_trace.append(grid_label)

    tuple_geo = tuple(geo_trace)
    geo_trace_pts[tuple_geo] = geo_trace_pts.get(tuple_geo, 0) + 1
    sorted_geo_trace_pts = dict(sorted(geo_trace_pts.items(), key=lambda x: x[1], reverse=True))
    
# 유사도 비교
cell_list = []
pair_list = []
pair_dict = {}
flatten_list = []
flatten_dict = {}

for key1, value1 in sorted_geo_trace_pts.items():
    list1 = list(key1)
    for key2, value2 in sorted_geo_trace_pts.items():
        if key1 == key2:
            continue
        list2 = list(key2)
        if jaro_similarity(list1, list2)>0.80:
            jaro_sim = jaro_similarity(list1, list2)
            cell_list.extend(list2)

cell = set(cell_list)

grid_info_file = 'grid_information_with_paths.csv'
grid_info = pd.read_csv(grid_info_file)
listpath = []
current_label = 'A'

for filename in os.listdir(test_dataset_path):
    if filename.endswith('.csv'):
        csv_file_path = os.path.join(test_dataset_path, filename)
        df = pd.read_csv(csv_file_path)
        previous_label = ""
        
        for index, row in df.iterrows():
            lat = row['lat']
            lng = row['lng']
            
            label = find_label_for_point(lat, lng, grid_info)
            
            if current_label != label:
                current_label = label
                print("사용자 현재 위치", label)
                com_cell(label)
                listpath.append(label)