import os
import pandas as pd
import numpy as np

#전처리 결과

#파일 경로
directory_path=os.getcwd()
data_directory_path=os.getcwd()+'/Label/pedestrian/___ecfd1086a6934ae08b555b3ae880d31e'
#테스트 파일 Label/pedestrian/___ecfd1086a6934ae08b555b3ae880d31e/20240710151855832667.csv
CollapseRecurringLabels_directory_path=os.getcwd()+'/Label/pedestrian/p__ecfd1086a6934ae08b555b3ae880d31e'

# 연속되는 중복을 제거한 리스트 제작
def CollapseRecurringLabels(original_list):

    # Initialize the result list with the first element of the original list
    result_list = [original_list[0]]  

    for i in range(1, len(original_list)):
        if original_list[i] != original_list[i - 1]:
            result_list.append(original_list[i])

    return result_list

frequency_dict = {}
new_df=pd.DataFrame(columns=['path_F1', 'path'])
i=0
limit=2

Keydict = {}
for file_name in os.listdir(data_directory_path):
    if file_name.endswith('.csv'):
        file_path = os.path.join(data_directory_path, file_name)
        df = pd.read_csv(file_path)

        #읽어온 데이터프레임에서 연속되는 중복 제거
        labels = df['grid_label'].tolist()
        unique_labels = CollapseRecurringLabels(labels)
        df_ = pd.DataFrame(unique_labels, columns=['grid_label'])
        
        label_counts = df_['grid_label'].value_counts().to_dict()
        
        if df_['grid_label'] not in Keydict:
            Keydict[df_['grid_label']] = 0
        else:
            Keydict[df_['grid_label']] += label_counts

        

        
#각각의 레이블을 카운트        
        

        #빈도수 업데이트
        df_['lF']=df_['grid_label'].map(label_counts)

        #N/AN 칼럼 추가
        df_['F1'] = np.where(df_['lF'] >= limit, 'N', 'AN')

        #df_ col(grid_label, lF, F1)
        #csv 파일 생성
        df_.to_csv(f'{CollapseRecurringLabels_directory_path}/{file_name}')
        
#새로운 데이터 프레임 생성 [경로를 리스트로 바꿔 하나의 칼럼에 넣고, N/AN 인지 판단]

path=df_['grid_label'].values.tolist()
F1=df_['F1'].values.tolist()
nor=F1.count('AN')
if nor==0:
    new_row={'path_F1':'N','path':path,}
    new_df.loc[i]=new_row
else:
    new_row={'path_F1':'AN','path':path,}
    new_df.loc[i]=new_row
i+=1

#최종 전처리 csv 파일 생성
new_df.to_csv(f'{directory_path}/preprocessing.csv')