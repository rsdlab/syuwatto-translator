import socket
import os
import numpy as np
import cv2
import struct
"""
https://zenn.dev/pinto0309/scraps/101f111b7f4deb
"""
ip = 'localhost'
port = 9876
save_dir = './data/received_img.jpg'

# ソケットを作成
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ip, port))
s.listen(1)

print('Server is listening on {}:{}'.format(ip, port))

try:
    while True:
        conn, addr = s.accept()
        print('Connected by', addr)

        try:
            while True:
                # 画像サイズを受信
                data = conn.recv(4)
                if not data:
                    break

                size = struct.unpack('!I', data)[0]
                data = b''
                while len(data) < size:
                    packet = conn.recv(size - len(data))
                    if not packet:
                        break
                    data += packet
                # 受信したデータをデコード
                frame_data = np.frombuffer(data, dtype=np.uint8)
                # データを画像に変換
                frame = cv2.imdecode(frame_data, 1)
                cv2.imwrite(save_dir, frame)
                print('Image saved as:', save_dir)

                # クライアントへ応答を送信
                conn.send('Image received successfully'.encode('utf-8'))

        finally:
            conn.close()

except KeyboardInterrupt:
    pass

finally:
    s.close()
    print('Server is shutting down')
