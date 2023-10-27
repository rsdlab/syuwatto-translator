import csv
import cv2
import glob
import mediapipe as mp
import numpy as np
import os
import re
from rich.progress import track
import shutil
import tensorflow as tf
import time
import warnings
from utils import *
# 関数まとめたやつ
from tools import *

tf.get_logger().setLevel("ERROR")
warnings.simplefilter('ignore')

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# 定数宣言
LANDMARK_LIST = ['WRIST', 'THUMB_CMC', 'THUMB_MCP', 'THUMB_IP', 'THUMB_TIP', 'INDEX_FINGER_MCP', 'INDEX_FINGER_PIP', 'INDEX_FINGER_DIP', 'INDEX_FINGER_TIP', 'MIDDLE_FINGER_MCP', 'MIDDLE_FINGER_PIP', 'MIDDLE_FINGER_DIP', 'MIDDLE_FINGER_TIP', 'RING_FINGER_MCP', 'RING_FINGER_PIP', 'RING_FINGER_DIP', 'RING_FINGER_TIP', 'PINKY_MCP', 'PINKY_PIP', 'PINKY_DIP', 'PINKY_TIP']

DATASET_IMAGE_DIR = '/workspace/dataset/test_translate'
RESULT_DIR = '/workspace/result/test_translate'
TEMPLATE_DIR = '/workspace/dataset/template'
RESULT_IMAGE_DIR = f'/workspace/result/test_translate/image'
# SAVE_CSV_DIR = f'{RESULT_DIR}/csv'

TEMPLATE_CSV_PATH = f'{TEMPLATE_DIR}/landmark_template.csv'
TEMPLATE_SHAPE_CSV_PATH = f'{TEMPLATE_DIR}/template_shape.csv'
OUTPUT_CSV_PATH = f'{TEMPLATE_DIR}/output.csv'
# SAVE_CSV_PATH = f'{SAVE_CSV_DIR}/landmark.csv'

# グローバル変数の定義
answer_words = []

def fields_name():
    # CSVのヘッダを準備
    fields = []
    fields.append('file_name')
    for landmark in LANDMARK_LIST:
        fields.append(f'{landmark}_x')
        fields.append(f'{landmark}_y')
        fields.append(f'{landmark}_z')
    return fields

def img2text(img_list):
    start_time = time.perf_counter()
    template_num_list = []
    template_idx_list = []
    template_points_list = []
    
    output_flag = False
    last_answer_index = None
    last_output_index = None
    last_coordinate_list = []
    
    # 結果の保存ディレクトリの初期化
    if os.path.exists(RESULT_IMAGE_DIR):
        shutil.rmtree(RESULT_IMAGE_DIR)
    
    # 出力する文字と識別結果の数字の対応を確認するlistの読み込み
    with open(OUTPUT_CSV_PATH, 'r') as f:
        check_output_list = []
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            check_output_list.append([row[0], row[1], row[2]])
    
    # テンプレートの関節座標の読み込み
    with open(TEMPLATE_CSV_PATH, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            points = []
            for j in range(21):
                x = row[(3 * j) + 1]
                y = row[(3 * j) + 2]
                z = row[(3 * j) + 3]
                points.append([x, y, z])
                np_points = np.array(points)
                np_points_T = np_points.T
            template_points_list.append(np_points_T.tolist())
    
    # 対象画像の一覧を取得
    # targetPattern = f'{DATASET_IMAGE_DIR}/*.jpg'
    # file_list = sorted(glob.glob(targetPattern))
    
    # テンプレート画像の一覧を取得
    targetPattern_template = f'{TEMPLATE_DIR}/*.jpg'
    template_img_list = sorted(glob.glob(targetPattern_template))
    
    # 判定する文字の一覧を取得
    pattern =  re.compile(r'\/')
    pattern2 = re.compile(r'\.')
    pattern3 = re.compile(r'\_')
    for template_img in template_img_list:
        file_name = pattern.split(template_img)[4]
        file_name2 = pattern2.split(file_name)[0]
        file_index = int(pattern3.split(file_name2)[0])
        file_number = int(pattern3.split(file_name2)[1])
        template_idx_list.append(file_index)
        template_num_list.append(file_number)
    
    with mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5) as hands:
        for idx, img in enumerate(track(img_list)):
            points_list = []
            coordinate_list = []
            distance_list = []
            
            if last_answer_index is not None:
                last_num = template_num_list[last_answer_index]
            else:
                last_num = None
            
            # 画像を読み取り、利き手が正しく出力されるようにy軸を中心に反転
            image = cv2.flip(img, 1)
            
            # 処理する前にBGR画像をRGBに変換
            results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            if not results.multi_hand_landmarks:
                if (output_flag == True) and (last_answer_index not in [42, 43, 44]):
                    answer_words.append(check_output_list[last_output_index][1])
                # 前回値をリセット
                output_flag = False
                last_answer_index = None
                last_output_index = None
                last_coordinate_list = []
                output_path = f'{RESULT_IMAGE_DIR}/annotated_image_{idx}.jpg'
                output(RESULT_IMAGE_DIR, image, None, output_path)
                # print('検出不可')
                continue
            
            hand_side = results.multi_handedness[0].classification[0].label
            
            # 右手で入力された場合は反転させる
            if hand_side == 'Right':
                image = cv2.flip(image, 1)
                results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                if not results.multi_hand_landmarks:
                    if (output_flag == True) and (last_answer_index not in [42, 43, 44]):
                        answer_words.append(check_output_list[last_output_index][1])
                    # 前回値をリセット
                    output_flag = False
                    last_answer_index = None
                    last_output_index = None
                    last_coordinate_list = []
                    # print('検出不可2')
                    continue
                hand_side = results.multi_handedness[0].classification[0].label
            
            # ランドマークの座標情報
            landmarks = results.multi_hand_landmarks[0]
            
            # 画像サイズを取得
            image_height, image_width, _ = image.shape
            
            for i, landmark in enumerate(landmarks.landmark):
                if i == 0:
                    standard_x = landmark.x
                    standard_y = landmark.y
                    standard_z = landmark.z
                land_points = [landmark.x - standard_x, landmark.y - standard_y, landmark.z - standard_z]
                coordinate = [landmark.x * image_width, landmark.y * image_height]
                points_list.append(land_points)
                coordinate_list.append(coordinate)
            
            # 手の向きや指の形を判定
            hand_direction = judge_of_hand_direction(points_list)
            finger_shape_list = judge_of_finger_shape(hand_direction, points_list, hand_side)
            
            # 手の向きや指の形のテンプレートを読み込み
            hand_direction_list, thump_shape_list, index_shape_list, middle_shape_list, ring_shape_list, pinky_shape_list, threshold_distance_list= read_template_shape(TEMPLATE_SHAPE_CSV_PATH)
            
            # 距離の計算
            for i, num in enumerate(template_num_list):
                total_distance = 0
                for j in range(len(points_list)):
                    a = np.array([float(points_list[j][0]), float(points_list[j][1])])
                    b = np.array([float(template_points_list[i][0][j]), float(template_points_list[i][1][j])])
                    
                    distance = np.linalg.norm(b - a)
                    
                    # 各関節の誤差を加算する
                    total_distance += distance
                    
                # 手の向きや指の形に応じて値の処理を行う
                total_distance = add_shape_bias(i, num, hand_direction, finger_shape_list, total_distance, points_list, hand_direction_list, thump_shape_list, index_shape_list, middle_shape_list, ring_shape_list, pinky_shape_list, hand_side, last_num)
                
                distance_list.append(total_distance)
            
            answer_index = distance_list.index(min(distance_list))
            answer_number= template_num_list[answer_index]
            
            for index, out in enumerate(check_output_list):
                if f'{answer_number}' in out:
                    output_index = index
            
            # 確認用
            # 出力用に画像をコピー
            annotated_image = image.copy()
            
            for hand_landmarks in results.multi_hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    annotated_image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                    mp.solutions.drawing_styles.get_default_hand_connections_style()
                    )
            
            # 出力用の画像を反転して元の向きに戻す
            annotated_image_fliped = cv2.flip(annotated_image, 1)
            
            cv2.arrowedLine(annotated_image_fliped, (70, 10), (30, 10), (0, 0, 255), thickness=3)
            cv2.arrowedLine(annotated_image_fliped, (70, 10), (70, 50), (255, 0, 0), thickness=3)
            cv2.putText(annotated_image_fliped, text = 'x', org = (10, 15), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7, color=(0, 0, 255), thickness=2, lineType=cv2.LINE_4)
            cv2.putText(annotated_image_fliped, text = 'y', org = (65, 70), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7, color=(255, 0, 0), thickness=2, lineType=cv2.LINE_4)
            
            text_list = [[f'hand : {hand_side}', (image_width * (1 / 10)), (image_height * (15 / 20))], [f'{hand_direction} {finger_shape_list}', (image_width * (1 / 10)), (image_height * (16 / 20))], [f'answer : {template_num_list[answer_index]} "{check_output_list[output_index][2]}"', (image_width * (1 / 10)), (image_height * (17 / 20))], [f'pred : {distance_list[distance_list.index(min(distance_list))]}', (image_width * (1 / 10)), (image_height * (18 / 20))]]
            output_path = f'{RESULT_IMAGE_DIR}/annotated_image_{idx}.jpg'
            output(RESULT_IMAGE_DIR, annotated_image_fliped, text_list, output_path)
            
            # 計算結果が閾値以下の時
            if float(distance_list[answer_index]) <= float(threshold_distance_list[answer_index]):
                # 前回文字が決定できなかった場合
                if (last_answer_index in [2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 24, 25, 26, 27, 28, 33]):
                    # 2フレーム文字の可能性がある場合
                    # 「う」or「り」
                    if last_answer_index == 2:
                        # 今回が「り」の2フレーム目の場合は「り」で確定
                        if answer_index == 44:
                            answer_words.append(check_output_list[output_index][1])
                            output_flag = False
                            last_answer_index = answer_index
                            last_output_index = output_index
                            last_coordinate_list = coordinate_list
                            continue
                        
                        # 今回が「り」の2フレーム目ではない場合は前回の「う」が確定
                        elif last_answer_index != 2:
                            answer_words.append(check_output_list[last_output_index][1])
                    
                    # 「の」or「ひ」
                    if last_answer_index == 24:
                        # 今回が「の」の2フレーム目の場合は「の」で確定
                        if answer_index == 42:
                            answer_words.append(check_output_list[output_index][1])
                            output_flag = False
                            last_answer_index = answer_index
                            last_output_index = output_index
                            last_coordinate_list = coordinate_list
                            continue
                        
                        # 今回が「の」の2フレーム目ではなく、今回が「の」「ひ」の1フレーム目ではない場合は前回の「ひ」が確定
                        elif answer_index not in [24, 42]:
                            last_answer_number= 26
                            for index, out in enumerate(check_output_list):
                                if f'{last_answer_number}' in out:
                                    output_index = index
                            answer_words.append(check_output_list[last_output_index][1])
                            output_flag = True
                            if (idx == (len(img) - 1)) and (answer_index not in [42, 43, 44]):
                                answer_words.append(check_output_list[output_index][1])
                            continue
                    
                    # 「も」
                    if last_answer_index == 33:
                        # 今回が「も」の2フレーム目の場合は「も」で確定
                        if answer_index == 43:
                            answer_words.append(check_output_list[output_index][1])
                            output_flag = False
                            last_answer_index = answer_index
                            last_output_index = output_index
                            last_coordinate_list = coordinate_list
                            continue
                    
                    # 濁点・半濁点の可能性がある場合
                    if last_answer_index in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 24, 25, 26, 27, 28]:
                        # 前回値と今回値が同じ場合（それ以外は濁点・半濁点はつかない）
                        if last_answer_index == answer_index:
                            if answer_index in [24, 25, 26, 27, 28]:
                                # if max(np.array(coordinate_list).T[1]) <= (min(np.array(last_coordinate_list).T[1])):
                                if max(np.array(coordinate_list).T[1]) <= (min(np.array(last_coordinate_list).T[1])) + (((min(np.array(last_coordinate_list).T[1])) + (max(np.array(last_coordinate_list).T[1]))) / 8):
                                    new_answer_number = answer_number + 200
                                    
                                    for index, out in enumerate(check_output_list):
                                        if f'{new_answer_number}' in out:
                                            new_output_index = index
                                    
                                    answer_words.append(check_output_list[new_output_index][1])
                                    output_flag = False
                                    last_answer_index = answer_index
                                    last_output_index = output_index
                                    last_coordinate_list = coordinate_list
                                    continue
                            
                            # if max(np.array(coordinate_list).T[0]) <= (min(np.array(last_coordinate_list).T[0])):
                            if max(np.array(coordinate_list).T[0]) <= (min(np.array(last_coordinate_list).T[0]) + (((min(np.array(last_coordinate_list).T[0])) + (max(np.array(last_coordinate_list).T[0]))) / 8)):
                                new_answer_number = answer_number + 100
                                
                                for index, out in enumerate(check_output_list):
                                    if f'{new_answer_number}' in out:
                                        new_output_index = index
                                
                                answer_words.append(check_output_list[new_output_index][1])
                                output_flag = False
                                last_answer_index = answer_index
                                last_output_index = output_index
                                last_coordinate_list = coordinate_list
                                continue
                        
                        # 前回の文字が確定
                        else:
                            if (output_flag == True) and (last_answer_index not in [42, 43, 44]):
                                answer_words.append(check_output_list[last_output_index][1])
                            output_flag = False
                
                if (last_answer_index == answer_index):
                    # 今回値を前回値として保存
                    if (output_flag == True) and (last_answer_index not in [42, 43, 44]):
                        answer_words.append(check_output_list[last_output_index][1])
                    output_flag = False
                    last_answer_index = answer_index
                    last_output_index = output_index
                    last_coordinate_list = coordinate_list
                    continue
                
                # 今回で文字を決定できない場合
                if (answer_index in [2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 24, 25, 26, 27, 28, 33]):
                    if (output_flag == True) and (last_answer_index not in [42, 43, 44]):
                        answer_words.append(check_output_list[last_output_index][1])
                    output_flag = True
                    last_answer_index = answer_index
                    last_output_index = output_index
                    last_coordinate_list = coordinate_list
                    if (idx == (len(img) - 1)) and (answer_index not in [42, 43, 44]):
                        answer_words.append(check_output_list[output_index][1])
                    continue
                
                # 今回で文字が決定できる場合：今回の文字を出力する（連続で同じ文字が出るのを防ぐため今回値を前回値として保存）
                if (answer_index not in [42, 43, 44]):
                    answer_words.append(check_output_list[output_index][1])
                output_flag = False
                last_answer_index = answer_index
                last_output_index = output_index
                last_coordinate_list = coordinate_list
                continue
            
            # 計算結果が閾値より大きい時
            else:
                if (output_flag == True) and (last_answer_index not in [42, 43, 44]):
                    answer_words.append(check_output_list[last_output_index][1])
                # 前回値をリセット
                output_flag = False
                last_answer_index = None
                last_output_index = None
                last_coordinate_list = []
    
    end_time = time.perf_counter()
    # 結果の出力
    print(answer_words)
    print(f'time : {(end_time - start_time):.03f}s')
    result = "".join(answer_words)
    return result

if __name__ == "__main__":
    main()