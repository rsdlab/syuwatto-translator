#!/usr/bin/env python

import socket
import cv2
import numpy as np
import struct
"""
https://zenn.dev/pinto0309/scraps/101f111b7f4deb
"""
ip = 'localhost'
port = 9876

# 画像ファイルのパス
img_path = './data/debug.JPG'

# ソケットを作成
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
print('Connected to the server')

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
frame = cv2.imread(img_path)

try:
    while True:
        print('Enter "quit" to exit or press Enter to send the image')
        message = input()
        if message == "quit":
            s.send(message.encode('utf-8'))
            break

        # 画像を読み込んでバイト列に変換
        result, frame_data = cv2.imencode('.jpg', frame, encode_param)
        # フレームのサイズを送信
        size = len(frame_data)
        s.send(struct.pack('!I', size))
        # フレームデータを送信
        s.sendall(frame_data)

        # サーバーからの応答を受信
        response = s.recv(1024).decode('utf-8')
        print(response)

finally:
    s.close()

print('Connection closed')
