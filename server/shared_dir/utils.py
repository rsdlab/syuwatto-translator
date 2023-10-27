import socket
import cv2
import struct
import numpy as np
from gtts import gTTS

def img_server(conn):
    """
    socket通信で送られ続ける画像を1枚1枚numpy型に変換してlist化する関数
    input:
        -conn   :   socket通信のconnection
    return:
        -img_list   :   画像のリスト
    """
    img_list = []
    # end flagまでのloop
    while True:
        # 画像サイズを受信
        data = conn.recv(4)
        # end flagが来たら抜け
        if data == 'fin':
            break

        size = struct.unpack('!I', data)[0]
        data = b''
        # 1枚あたりのloop
        while len(data) < size:
            packet = conn.recv(size - len(data))
            # 画像データが最後まで行ったら
            if not packet:
                break
            data += packet
        # 受信したデータをデコード
        frame_data = np.frombuffer(data, dtype=np.uint8)
        # データを画像に変換
        frame = cv2.imdecode(frame_data, 1)
        img_list.append(frame)
    return img_list

def send_wav_file_to_server(file_path, connection):
    """
    音声データを読み込んで送信する関数
    input:
        -file_path   :  音声データ(.mp3)までのpath
        -connection  :  socket通信のconnection
    return:
        nothing
    """
    with open(file_path, 'rb') as file:
        data = file.read(1024)
        while data:
            connection.send(data)
            data = file.read(1024)
    print(f"{file_path} をサーバーに送信しました")
    return True

def text2speech(text, language="ja"):
    """
    テキストをスピーチ化する関数
    参照:https://gtts.readthedocs.io/en/latest/
    """
    t2s = gTTS(text, lang=language)
    return t2s


import cv2
import copy
import csv
import math
import numpy as np
from numpy import linalg as LA
import os
import re

# 距離にかける倍率
RATE1 = 10.0
RATE2 = 5.0
RATE3 = 2.0

# 角度の閾値
THRESHOLD_ANGLE_0 = 0
THRESHOLD_ANGLE_15 = 15
THRESHOLD_ANGLE_20 = 20
THRESHOLD_ANGLE_30 = 30
THRESHOLD_ANGLE_50 = 50
THRESHOLD_ANGLE_60 = 60
THRESHOLD_ANGLE_70 = 70
THRESHOLD_ANGLE_80 = 80
THRESHOLD_ANGLE_90 = 90
THRESHOLD_ANGLE_120 = 120

def read_template_shape(csv_path):
    # テンプレートの関節座標を取得する関数
    
    hand_direction_list = []
    thump_shape_list = []
    index_shape_list = []
    middle_shape_list = []
    ring_shape_list = []
    pinky_shape_list = []
    threshold_distance_list = []
    
    with open(csv_path) as f:
        reader = csv.reader(f)
        header = next(reader)
        
        for row in reader:
            hand_direction_list.append(row[1])
            thump_shape_list.append(row[2])
            index_shape_list.append(row[3])
            middle_shape_list.append(row[4])
            ring_shape_list.append(row[5])
            pinky_shape_list.append(row[6])
            threshold_distance_list.append(row[7])
        
    return hand_direction_list, thump_shape_list, index_shape_list, middle_shape_list, ring_shape_list, pinky_shape_list, threshold_distance_list

def add_shape_bias(i, num, hand_direction, finger_shape_list, distance, points_list, hand_direction_list, thump_shape_list, index_shape_list, middle_shape_list, ring_shape_list, pinky_shape_list, hand_side, last_num):
    # 指の形に応じて結果の値を変化させる関数
    
    pattern =  re.compile(r'\,')
    
    # 手の向きが違う場合は誤差をRATE1（倍）する
    hand_direction_template = pattern.split(hand_direction_list[i])
    if hand_direction not in hand_direction_template:
        distance *= RATE1
    
    # 親指の形が違う場合は誤差をRATE1（倍）する
    distance, finger_shape_flag = check_finger_shape(thump_shape_list, finger_shape_list, i, 0, distance, RATE1)
    
    # 人差し指の形が違う場合は誤差をRATE2（倍）する
    distance, finger_shape_flag = check_finger_shape(index_shape_list, finger_shape_list, i, 1, distance, RATE2)
    
    # 中指の形が違う場合は誤差をRATE2（倍）する
    distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
    
    # 薬指の形が違う場合は誤差をRATE2（倍）する
    distance, finger_shape_flag = check_finger_shape(ring_shape_list, finger_shape_list, i, 3, distance, RATE2)
    
    # 小指の形が違う場合は誤差をRATE2（倍）する
    distance, finger_shape_flag = check_finger_shape(pinky_shape_list, finger_shape_list, i, 4, distance, RATE2)
    
    front_or_back = check_front_or_back(points_list, hand_side, hand_direction)
    
    # 個別対応編
    if num == 0: # あ
        pass
    
    if num == 1: # い
        if (do_intersect([points_list[3][0], points_list[3][1]], [points_list[4][0], points_list[4][1]], [points_list[6][0], points_list[6][1]], [points_list[7][0], points_list[7][1]])) or do_intersect([points_list[3][0], points_list[3][1]], [points_list[4][0], points_list[4][1]], [points_list[7][0], points_list[7][1]], [points_list[8][0], points_list[8][1]]):
            distance *= RATE2
    
    if num == 2: # う
        pass
    
    if num == 3: # え
        pass
    
    if num == 4: # お
        # if hand_direction not in hand_direction_template:
        #     distance *= RATE1
        
        for j in range(4):
            if not (finger_shape_list[j + 1] == 'close' or finger_shape_list[j + 1] == 'side-open'):
                distance *= RATE2
            
            if do_intersect([points_list[(4 * j) + 5][0], points_list[(4 * j) + 5][1]], [points_list[(4 * j) + 8][0], points_list[(4 * j) + 8][1]], [points_list[1][0], points_list[1][1]], [points_list[4][0], points_list[4][1]]):
                distance *= RATE2
    
    if num == 5: # か
        # 人差し指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(index_shape_list, finger_shape_list, i, 1, distance, RATE2)
    
    if num == 6: # き
        # 人差し指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(index_shape_list, finger_shape_list, i, 1, distance, RATE2)
        
        if finger_shape_flag == False:
            distance /= RATE3
        
        # 小指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(pinky_shape_list, finger_shape_list, i, 4, distance, RATE2)
        
        if finger_shape_flag == False:
            distance /= RATE3
    
    if num == 7: # く
        pass
    
    if num == 8: # け
        degree = math.degrees(math.atan2((points_list[4][1] - points_list[3][1]), (points_list[4][0] - points_list[3][0])))
        if abs(degree) <= THRESHOLD_ANGLE_120:
            distance *= RATE2
    
    if num == 9: # こ
        for j in range(4):
            if not (finger_shape_list[j + 1] == 'open' or finger_shape_list[j + 1] == 'side-open'):
                distance *= RATE2
            
            if not do_intersect([points_list[(4 * j) + 5][0], points_list[(4 * j) + 5][1]], [points_list[(4 * j) + 8][0], points_list[(4 * j) + 8][1]], [points_list[1][0], points_list[1][1]], [points_list[4][0], points_list[4][1]]):
                distance *= RATE2
    
    if num == 10: # さ
        pass
    
    if num == 11: # し
        pass
    
    if num == 12: # す
        for j in range(2):
            degree = math.degrees(math.atan2((points_list[(4 * j) + 8][1] - points_list[(4 * j) + 5][1]), (points_list[(4 * j) + 8][0] - points_list[(4 * j) + 5][0])))
            if ((degree >= 105) or (degree <= 75)):
                distance *= RATE2
        # 中指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
        
        if finger_shape_flag == False:
            distance /= RATE3
    
    if num == 13: # せ
        pass
    
    if num == 14: # そ
        degree = math.degrees(math.atan2((points_list[4][1] - points_list[1][1]), (points_list[4][0] - points_list[1][0])))
        degree2 = math.degrees(math.atan2((points_list[8][1] - points_list[5][1]), (points_list[8][0] - points_list[5][0])))
        
        if degree <= THRESHOLD_ANGLE_50:
            distance *= RATE2
        
        else:
            distance /= RATE3
        if points_list[4][0] >= points_list[8][0]:
            distance *= RATE2
        
        else:
            distance /= RATE3
        
        # 中指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
        
        if finger_shape_flag == False:
            distance /= RATE3
        
        if abs(degree2) <= THRESHOLD_ANGLE_15:
            distance *= RATE2
    
    if num == 15: # た
        pass
    
    if num == 16: # ち
        # 人差し指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(index_shape_list, finger_shape_list, i, 1, distance, RATE2)
        
        # 中指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
        
        for j in range(3):
            degree = math.degrees(math.atan2((points_list[(4 * (j + 1)) + 4][1] - points_list[(4 * (j + 1)) + 1][1]), (points_list[(4 * (j + 1)) + 4][0] - points_list[(4 * (j + 1)) + 1][0])))
            if degree >= THRESHOLD_ANGLE_70 or degree <= -(THRESHOLD_ANGLE_60):
                distance *= RATE2
        
        # degree = math.degrees(math.atan2((points_list[4][1] - points_list[3][1]), (points_list[4][0] - points_list[3][0])))
        # if degree <= -(THRESHOLD_ANGLE_90):
        #     distance *= RATE2
    
    if num == 17: # つ
        # 人差し指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(index_shape_list, finger_shape_list, i, 1, distance, RATE2)
        
        # 中指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
        
        for j in range(2):
            degree = math.degrees(math.atan2((points_list[(4 * (j + 1)) + 4][1] - points_list[(4 * (j + 1)) + 1][1]), (points_list[(4 * (j + 1)) + 4][0] - points_list[(4 * (j + 1)) + 1][0])))
            if degree >= THRESHOLD_ANGLE_70 or degree <= -(THRESHOLD_ANGLE_60):
                distance *= RATE2
        
        degree2 = math.degrees(math.atan2((points_list[16][1] - points_list[13][1]), (points_list[16][0] - points_list[13][0])))
        if abs(degree2) <= THRESHOLD_ANGLE_70:
            distance *= RATE2
    
    if num == 18: # て
        for j in range(5):
            degree = math.degrees(math.atan2((points_list[(4 * j) + 4][1] - points_list[(4 * j) + 1][1]), (points_list[(4 * j) + 4][0] - points_list[(4 * j) + 1][0])))
            if abs(degree) <= THRESHOLD_ANGLE_70:
                distance *= RATE2
        
        if do_intersect([points_list[2][0], points_list[2][1]], [points_list[4][0], points_list[4][1]], [points_list[5][0], points_list[5][1]], [points_list[8][0], points_list[8][1]]):
            distance *= RATE2
        
        if do_intersect([points_list[18][0], points_list[18][1]], [points_list[20][0], points_list[20][1]], [points_list[13][0], points_list[13][1]], [points_list[16][0], points_list[16][1]]):
            distance *= RATE2
    
    if num == 19: # と
        if front_or_back != 'back':
            distance *= RATE1
    
    if num == 20: # な
        for j in range(2):
            degree = math.degrees(math.atan2((points_list[(4 * j) + 8][1] - points_list[(4 * j) + 5][1]), (points_list[(4 * j) + 8][0] - points_list[(4 * j) + 5][0])))
            if ((degree >= 105) or (degree <= 75)):
                distance *= RATE2
        if front_or_back != 'back':
            distance *= RATE1
        
        # 中指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
        
        if finger_shape_flag == False:
            distance /= RATE3
    
    if num == 21: # に
        for j in range(2):
            degree = math.degrees(math.atan2((points_list[(4 * j) + 8][1] - points_list[(4 * j) + 5][1]), (points_list[(4 * j) + 8][0] - points_list[(4 * j) + 5][0])))
            if ((degree >= 30) or (degree <= -30)):
                distance *= RATE2
        
        degree = math.degrees(math.atan2((points_list[8][1] - points_list[5][1]), (points_list[8][0] - points_list[5][0])))
        if degree >= THRESHOLD_ANGLE_0:
            distance *= RATE2
    
    if num == 22: # ぬ
        if finger_shape_list[2] != 'close':
            distance *= RATE2
        
        if finger_shape_list[2] == 'close':
            distance /= RATE3
    
    if num == 23: # ね
        pass
    
    if num == 24: # の
        pass
    
    if num == 25: # は
        for j in range(5):
            degree = math.degrees(math.atan2((points_list[(4 * j) + 4][1] - points_list[(4 * j) + 1][1]), (points_list[(4 * j) + 4][0] - points_list[(4 * j) + 1][0])))
            
            if ((j == 1 or j == 2) and ((degree >= 120) and (degree <= 180))):
                distance /= RATE2
            
            if ((j == 1 or j == 2) and (points_list[(4 * j) + 4][0] >= points_list[(4 * j) + 1][0])):
                distance *= RATE2
            
            if ((j == 3 or j == 4) and (points_list[(4 * j) + 4][0] <= points_list[(4 * j) + 1][0])):
                distance *= RATE2
    
    if num == 27: # ふ
        degree = math.degrees(math.atan2((points_list[4][1] - points_list[1][1]), (points_list[4][0] - points_list[1][0])))
        if degree >= THRESHOLD_ANGLE_50:
            distance *= RATE2
        
        if points_list[4][0] <= points_list[8][0]:
            distance *= RATE2
    
    if num == 28: # へ
        pass
    
    if num == 29: # ほ
        if front_or_back != 'back':
            distance *= RATE1
    
    if num == 30: # ま
        if front_or_back != 'back':
            distance *= RATE1
    
    if num == 31: # み
        pass
    
    if num == 32: # む
        degree = math.degrees(math.atan2((points_list[4][1] - points_list[1][1]), (points_list[4][0] - points_list[1][0])))
        if degree >= -(THRESHOLD_ANGLE_50):
            distance *= RATE2
    
    if num == 33: # め
        # 中指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
        
        if finger_shape_flag == False:
            distance /= RATE3
    
    if num == 34: # も
        if front_or_back != 'back':
            distance *= RATE1
        
        degree = math.degrees(math.atan2((points_list[4][1] - points_list[1][1]), (points_list[4][0] - points_list[1][0])))
        if degree >= -(THRESHOLD_ANGLE_50):
            distance *= RATE2
        
        degree2 = math.degrees(math.atan2((points_list[8][1] - points_list[5][1]), (points_list[8][0] - points_list[5][0])))
        if degree2 >= -(THRESHOLD_ANGLE_50):
            distance *= RATE2
    
    if num == 35: # や
        pass
    
    if num == 36: # ゆ
        if front_or_back != 'back':
            distance *= RATE1
        
        if not do_intersect([points_list[2][0], points_list[2][1]], [points_list[4][0], points_list[4][1]], [points_list[5][0], points_list[5][1]], [points_list[8][0], points_list[8][1]]):
            distance *= RATE2
        
        if not do_intersect([points_list[18][0], points_list[18][1]], [points_list[20][0], points_list[20][1]], [points_list[13][0], points_list[13][1]], [points_list[16][0], points_list[16][1]]):
            distance *= RATE2
    
    if num == 37: # よ
        pass
    
    if num == 38: # ら
        theta = calc_angle_vector2vector(np.array([points_list[8][0] - points_list[7][0], points_list[8][1] - points_list[7][1]]), np.array([points_list[12][0] - points_list[11][0], points_list[12][1] - points_list[11][1]]))
        if theta <= THRESHOLD_ANGLE_15:
            distance *= RATE2
        
        if points_list[8][1] <= points_list[12][1]:
            distance *= RATE2
        
        if points_list[8][0] <= points_list[12][0]:
            distance /= RATE3
        
        if do_intersect([points_list[7][0], points_list[7][1]], [points_list[8][0], points_list[8][1]], [points_list[11][0], points_list[11][1]], [points_list[12][0], points_list[12][1]]):
            distance /= RATE3
    
    if num == 40: # る
        if hand_direction != 'upward':
            distance *= RATE1
        
        if front_or_back != 'front':
            distance *= RATE1
        
        # 中指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
        
        pattern =  re.compile(r'\,')
        middle_shape = pattern.split(middle_shape_list[i])
        if finger_shape_list[2] in middle_shape:
            distance /= RATE3
        
        degree = math.degrees(math.atan2((points_list[12][1] - points_list[11][1]), (points_list[12][0] - points_list[11][0])))
        if degree >= -(THRESHOLD_ANGLE_80):
            distance *= RATE2
        
        degree2 = math.degrees(math.atan2((points_list[12][1] - points_list[9][1]), (points_list[12][0] - points_list[9][0])))
        if degree2 >= THRESHOLD_ANGLE_0:
            distance *= RATE2
    
    if num == 41: # れ
        degree = math.degrees(math.atan2((points_list[12][1] - points_list[9][1]), (points_list[12][0] - points_list[9][0])))
        if degree <= THRESHOLD_ANGLE_0:
            distance *= RATE2
    
    if num == 42: # ろ
        # 人差し指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(index_shape_list, finger_shape_list, i, 1, distance, RATE2)
        
        if finger_shape_flag == False:
            distance /= RATE3
        
        # 中指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
        
        if finger_shape_flag == False:
            distance /= RATE3
    
    if num == 43: # わ
        if finger_shape_list[4] == 'open':
            distance *= RATE2
        pass
    
    if num == 324: # の_2
        if (points_list[0][0] <= points_list[17][0]):
            distance /= RATE3
    
        # 中指の形が違う場合は誤差をRATE2（倍）する
        distance, finger_shape_flag = check_finger_shape(middle_shape_list, finger_shape_list, i, 2, distance, RATE2)
    
    if num == 334: # も_2
        degree = math.degrees(math.atan2((points_list[4][1] - points_list[1][1]), (points_list[4][0] - points_list[1][0])))
        degree2 = math.degrees(math.atan2((points_list[8][1] - points_list[5][1]), (points_list[8][0] - points_list[5][0])))
        
        if degree2 - degree <= 0:
            distance /= RATE2
        
        if last_num == 34:
            distance /= RATE1
            distance /= RATE1
        
        if front_or_back != 'back':
            distance *= RATE1
    
    if num == 339: # り_2
        degree = math.degrees(math.atan2((points_list[12][1] - points_list[9][1]), (points_list[12][0] - points_list[9][0])))
        
        if degree <= THRESHOLD_ANGLE_15:
            distance *= RATE2
        
        else:
            distance /= RATE3
    
    return distance

def check_finger_shape(template_shape_list, finger_shape_list, i, number, distance, rate):
    # 指の形によって値を変化させる関数
    
    pattern =  re.compile(r'\,')
    finger_shape = pattern.split(template_shape_list[i])
    if (finger_shape_list[number] not in finger_shape) and ('undecided' not in finger_shape):
        distance *= rate
        flag = True
    
    else:
        flag = False
    
    return distance, flag

def judge_of_hand_direction(points_list):
    # 手の向きの判定を行う関数
    
    # 上向き
    if (points_list[0][1] > points_list[5][1]) and  (points_list[0][1] > points_list[9][1]) and (points_list[0][1] > points_list[13][1]) and  (points_list[0][1] > points_list[17][1]):
        # 縦向き
        theta = calc_angle_vector2vector(np.array([points_list[5][0] - points_list[0][0], points_list[5][1] - points_list[0][1]]), np.array([points_list[17][0] - points_list[0][0], points_list[17][1] - points_list[0][1]]))
        if theta <= THRESHOLD_ANGLE_20:
            return 'portrait'
        else:
            return 'upward'
    
    # 下向き
    if (points_list[0][1] < points_list[5][1]) and  (points_list[0][1] < points_list[9][1]) and (points_list[0][1] < points_list[13][1]) and  (points_list[0][1] < points_list[17][1]):
        return 'downward'
    
    # 横向き
    elif (points_list[0][1] > points_list[5][1] and points_list[0][1] <  points_list[17][1]) or (points_list[0][1] < points_list[5][1] and points_list[0][1] >  points_list[17][1]):
        return 'landscape'
    
    # 不定
    else:
        return 'undecided'

def judge_of_finger_shape(hand_direction, points_list, hand_side):
    # 指の形の判定を行う関数
    
    finger_shape_list = []
    finger_angle_list = [None, None]
    
    front_or_back = check_front_or_back(points_list, hand_side, hand_direction)
    
    for i in range(5):
        for j in range(2):
            finger_angle_list[j] = calc_angle_vector2vector(np.array([points_list[(4 * i) + j + 2][0] - points_list[(4 * i) + j + 1][0], points_list[(4 * i) + j + 2][1] - points_list[(4 * i) + j + 1][1]]), np.array([points_list[(4 * i) + j + 3][0] - points_list[(4 * i) + j + 2][0], points_list[(4 * i) + j + 3][1] - points_list[(4 * i) + j + 2][1]]))
        
        # 親指の判定
        if i == 0:
            if hand_direction == 'upward':
                if (points_list[1][0] > points_list[2][0] > points_list[3][0] > points_list[4][0]) or (points_list[1][0] < points_list[2][0] < points_list[3][0] < points_list[4][0]):
                    finger_shape_list.append('open')
                
                elif ((points_list[2][0] < points_list[3][0]) or (points_list[2][0] < points_list[4][0])) or ((points_list[2][0] > points_list[3][0]) or (points_list[2][0] > points_list[4][0])):
                    finger_shape_list.append('close')
                
                else:
                    finger_shape_list.append('undecided')
            
            elif hand_direction == 'downward':
                if (points_list[1][0] < points_list[2][0] < points_list[3][0] < points_list[4][0]):
                    finger_shape_list.append('open')
                
                elif ((points_list[2][0] < points_list[3][0]) or (points_list[2][0] < points_list[4][0])) or ((points_list[2][0] > points_list[3][0]) or (points_list[2][0] > points_list[4][0])):
                    finger_shape_list.append('close')
                
                else:
                    finger_shape_list.append('undecided')
            
            elif hand_direction == 'landscape':
                if (points_list[1][1] > points_list[2][1] > points_list[3][1] > points_list[4][1]):
                    finger_shape_list.append('open')
                
                elif ((points_list[2][1] < points_list[3][1]) or (points_list[2][1] < points_list[4][1])) or ((points_list[2][1] > points_list[3][1]) or (points_list[2][1] > points_list[4][1])):
                    finger_shape_list.append('close')
                
                else:
                    finger_shape_list.append('undecided')
            
            else:
                finger_shape_list.append('undecided')
        
        # 親指以外の判定
        else:
            width = (points_list[0][1] - points_list[(4 * i) + 1][1]) * (1 / 5)
            if ((points_list[(4 * i) + 1][1] + width) >= points_list[(4 * i) + 4][1]) and ((points_list[(4 * i) + 3][1]) <= points_list[(4 * i) + 4][1]):
                check = True
            else:
                check = False
            
            if hand_direction == 'upward':
                degree = math.degrees(math.atan2((points_list[(4 * i) + 4][1] - points_list[(4 * i) + 1][1]), (points_list[(4 * i) + 4][0] - points_list[(4 * i) + 1][0])))
                
                if (points_list[(4 * i) + 1][1] > points_list[(4 * i) + 2][1] > points_list[(4 * i) + 3][1] > points_list[(4 * i) + 4][1]):
                    finger_shape_list.append('open')
                                
                elif ((points_list[(4 * i) + 2][1] > points_list[(4 * i) + 3][1]) and (points_list[(4 * i) + 4][1] > points_list[(4 * i) + 3][1])):
                    finger_shape_list.append('half-open')
                
                elif (front_or_back == 'front') and (check == True):
                    finger_shape_list.append('half-close')
                
                elif ((points_list[(4 * i) + 1][0] < points_list[(4 * i) + 2][0] < points_list[(4 * i) + 3][0] < points_list[(4 * i) + 4][0]) and abs(degree) <= THRESHOLD_ANGLE_30):
                    finger_shape_list.append('side-open')
                
                elif (points_list[(4 * i) + 2][1] < points_list[(4 * i) + 3][1]) or (points_list[(4 * i) + 2][1] < points_list[(4 * i) + 4][1]):
                    finger_shape_list.append('close')
                
                else:
                    finger_shape_list.append('undecided')
            
            elif hand_direction == 'downward':
                if points_list[(4 * i) + 1][1] < points_list[(4 * i) + 2][1] < points_list[(4 * i) + 3][1] < points_list[(4 * i) + 4][1]:
                    finger_shape_list.append('open')
                
                elif (points_list[(4 * i) + 2][1] > points_list[(4 * i) + 3][1]) or (points_list[(4 * i) + 2][1] > points_list[(4 * i) + 4][1]):
                    finger_shape_list.append('close')
                
                else:
                    finger_shape_list.append('undecided')
            
            elif hand_direction == 'landscape':
                if ((points_list[(4 * i) + 1][0] > points_list[(4 * i) + 2][0] > points_list[(4 * i) + 3][0] > points_list[(4 * i) + 4][0]) or (points_list[(4 * i) + 1][0] < points_list[(4 * i) + 2][0] < points_list[(4 * i) + 3][0] < points_list[(4 * i) + 4][0])):
                    finger_shape_list.append('open')
                
                elif ((points_list[(4 * i) + 2][0] < points_list[(4 * i) + 3][0]) or (points_list[(4 * i) + 2][0] < points_list[(4 * i) + 4][0])) or ((points_list[(4 * i) + 2][0] > points_list[(4 * i) + 3][0]) or (points_list[(4 * i) + 2][0] > points_list[(4 * i) + 4][0])):
                    finger_shape_list.append('close')
                
                else:
                    finger_shape_list.append('undecided')
            
            elif hand_direction == 'portrait':
                degree = math.degrees(math.atan2((points_list[(4 * i) + 2][1] - points_list[(4 * i) + 1][1]), (points_list[(4 * i) + 2][0] - points_list[(4 * i) + 1][0])))                
                degree2 = math.degrees(math.atan2((points_list[(4 * i) + 4][1] - points_list[(4 * i) + 1][1]), (points_list[(4 * i) + 4][0] - points_list[(4 * i) + 1][0])))
                
                if ((points_list[(4 * i) + 1][1] > points_list[(4 * i) + 2][1] > points_list[(4 * i) + 3][1] > points_list[(4 * i) + 4][1]) or \
                    (points_list[(4 * i) + 1][0] < points_list[(4 * i) + 2][0] < points_list[(4 * i) + 3][0] < points_list[(4 * i) + 4][0])) and (max(finger_angle_list) <= THRESHOLD_ANGLE_15):
                    finger_shape_list.append('open')
                
                elif ((points_list[(4 * i) + 2][1] > points_list[(4 * i) + 3][1]) and (points_list[(4 * i) + 4][1] > points_list[(4 * i) + 3][1]) and abs(degree) >= THRESHOLD_ANGLE_60):
                    finger_shape_list.append('half-open')
                
                elif ((front_or_back == 'front') and abs(degree) >= THRESHOLD_ANGLE_60) and (check == True):
                    finger_shape_list.append('half-close')
                
                elif ((points_list[(4 * i) + 1][0] < points_list[(4 * i) + 2][0] < points_list[(4 * i) + 3][0] < points_list[(4 * i) + 4][0]) and (abs(degree2) <= THRESHOLD_ANGLE_30)):
                    finger_shape_list.append('side-open')
                
                elif (points_list[(4 * i) + 2][1] < points_list[(4 * i) + 3][1]) or (points_list[(4 * i) + 2][1] < points_list[(4 * i) + 4][1]):
                    finger_shape_list.append('close')
                
                else:
                    finger_shape_list.append('undecided')
            
            else:
                finger_shape_list.append('undecided')
            
    return finger_shape_list

def output(output_dir, output_image, text_list, output_path):
    # 取得した関節と諸情報を画像に投影する関数（翻訳には不要）
    
    os.makedirs(output_dir, exist_ok=True)
    output_image_text = copy.copy(output_image)
    
    if text_list is not None:
        for i in range(len(text_list)):
            cv2.putText(output_image_text, text = text_list[i][0], org = (int(text_list[i][1]), int(text_list[i][2])), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7, color=(0, 0, 255), thickness=2, lineType=cv2.LINE_4)
    
    cv2.imwrite(output_path, output_image_text)

def calc_angle_vector2vector(vector1, vector2):
    # ２つのベクトル間の角度を求める関数
    
    cos_theta = sum(vector1 * vector2) / np.sqrt(sum(vector1**2)) / np.sqrt(sum(vector2**2))
    rad = np.arccos(cos_theta)
    degree = rad * 180 / np.pi
    return degree

def check_front_or_back(points_list, hand_side, hand_direction):
    # 手の表裏を判定する関数
    
    if hand_direction == 'upward' or hand_direction == 'portrait':
        if hand_side == 'Left':
            if points_list[5][0] > points_list[17][0]:
                return 'front'
            
            else:
                return 'back'
        
        elif hand_side == 'Right':
            if points_list[5][0] < points_list[17][0]:
                return 'front'
            
            else:
                return 'back'
        
        else:
            return 'undecided'
    
    elif hand_direction == 'downward':
        if hand_side == 'Left':
            if points_list[5][0] < points_list[17][0]:
                return 'front'
            
            else:
                return 'back'
        
        elif hand_side == 'Right':
            if points_list[5][0] > points_list[17][0]:
                return 'front'
            
            else:
                return 'back'
        
        else:
            return 'undecided'
    
    else:
        return 'undecided'

def interpolate_3d_point(points_list, num):
    # ２点間を点群で埋める関数（翻訳には不要）
    
    result_points_list = []
    
    for points in points_list:
        for t in range(num):
            t = t / (num - 1)
            x1, y1, z1 = points[0]
            x2, y2, z2 = points[1]
            
            xt = x1 + t * (x2 - x1)
            yt = y1 + t * (y2 - y1)
            zt = z1 + t * (z2 - z1)
            result_points_list.append([xt, yt, zt])
    
    return result_points_list

def make_ply(points, path):
    # 取得した関節をplyファイルに保存する関数（翻訳には不要）
    
    rgb_list = [[0, 0, 0], [0, 0, 255], [0, 255, 0], [255, 0, 0], [255, 255, 255], [0, 255, 255]]
    file = open(path, mode='w')
    file.write(f'ply\n\
    format ascii 1.0\n\
    comment Kinect v1 generated\n\
    element vertex {int(len(points))}\n\
    property double x\n\
    property double y\n\
    property double z\n\
    property uchar red\n\
    property uchar green\n\
    property uchar blue\n\
    end_header\n\n\n\n\n')
    
    for i in range(len(points)):
        file.write(f'{points[i][0]} {points[i][1]} {points[i][2]} {0} {0} {0}')
    file.close()

def do_intersect(p1, q1, p2, q2):
    # ２つの線分が交差しているかどうかを判定する関数
    
    def orientation(p, q, r):
        val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        return 0 if val == 0 else 1 if val > 0 else 2
    
    def on_segment(p, q, r):
        return q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1])
    
    o1, o2, o3, o4 = orientation(p1, q1, p2), orientation(p1, q1, q2), orientation(p2, q2, p1), orientation(p2, q2, q1)
    
    if o1 != o2 and o3 != o4:
        return True
    
    if 0 in (o1, o2) and on_segment(p1, p2, q1):
        return True
    
    if 0 in (o2, o3) and on_segment(p1, q2, q1):
        return True
    
    if 0 in (o3, o4) and on_segment(p2, p1, q2):
        return True
    
    if 0 in (o4, o1) and on_segment(p2, q1, q2):
        return True
    
    return False