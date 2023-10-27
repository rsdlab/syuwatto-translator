import socket
import cv2
import struct
import numpy as np
from gtts import gTTS
from utils import *
from img2text import img2text

ip = 'localhost'
port =9876
# socketを作成
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# socketにipアドレスとportを紐づけ
socket.bind((ip, port))
socket.listen()

connection, address = socket.accept()
print('client : {}'.format(address))

try:
    while True:
        mode = connection.recv(1)
        if mode == "0":
            # 練習モード
            pass
        elif mode=="1":
            # 翻訳モード
            # クライアントへ応答を送信
            connection.send('finished preparation'.encode('utf-8'))
            while True:
                modal = connection.recv(1)
                if modal == "0":
                    # 音
                    pass
                elif modal == "1":
                    # 画像
                    img_list =  img_server(conn = connection)
                    # img2text
                    text = img2text(img_list=img_list)
                    # text2audio
                    mp3 = text2speech(text=text)
                    # 一回保存(これが一番楽)
                    mp3.save('./speech.mp3')
                    # 保存されたファイルから音声データを送信
                    send_wav_file_to_server(file_path='./speech.mp3', connection=connection)
                else:
                    print('modal error')
                    break
     

except KeyboardInterrupt:
    pass