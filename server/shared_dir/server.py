import socket
import threading
import os 
import time
import glob
# 追加分
import random
from img2text import img2text
from gtts import gTTS
import speech_recognition as sr
from pykakasi import kakasi

IP = '192.168.10.5'
PORT = 8080
MODE_BUFFER_SIZE = 1
BUFFER_SIZE = 1024
CHUNK_SIZE = 128
FORMAT = 'utf-8'

img_count = 0
audio_count = 0
mode = '0'
state = '0'

checkpoint_receive_img = False
checkpoint_send_text = False
checkpoint_send_audio = False
checkpoint_receive_audio = False
checkpoint_send_problem = False
checkpoint_make_problem = False
checkpoint_translate = False

# 練習用モードのクラス
class Practice_Mode():
    def __init__(self):
        # 初期化
        self.moji = [   "あ","い","う","え","お", \
                        "か","き","く","け","こ", \
                        "さ","し","す","せ","そ", \
                        "た","ち","つ","て","と", \
                        "な","に","ぬ","ね","の", \
                        "は","ひ","ふ","へ","ほ", \
                        "ま","み","む","め","も", \
                        "や","ゆ","よ", \
                        "ら","り","る","れ","ろ", \
                        "わ","を","ん"
                    ]
        self.num = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

        return True

    # 重複無し乱数の生成
    def rand_ints_nodup(self, min:int = 0, max: int = 0, length: int = 3):
        idx = []
        while len(idx) < length:
            n = random.randint(min, max)
            if not n in idx:
                idx.append(n)
        return idx
    
    # 問題を生成する関数
    def problem_generate(self, mode:str = 'moji', length:int = 3):
        problem_list = []
        if mode == 'moji':
            target_list = self.moji
        elif mode == 'num':
            target_list = self.num
        else:
            return False
        idx_list = self.rand_ints_nodup(min = 0, max=len(target_list)-1, length=length)

        for idx in idx_list:
            problem_list.append(target_list[idx])

        return ''.join(problem_list)

class AudioRicognition():
    def __init__(self):
        # 初期化
        self.recognizer = sr.Recognizer()
        self.file_path = '/workspace/server/receive/audio/･･･.mp3'
        self.kakasi = kakasi()
        self.kakasi.setMode('J', 'H') # J(Kanji) to H(Hiragana)
        self.kakasi.setMode('H', 'H') # H(Hiragana) to None(noconversion)
        self.kakasi.setMode('K', 'H') # K(Katakana) to a(Hiragana)
        self.kakasi_converter = self.kakasi.getConverter()
        return True
    
    # 音声-->ひらがなテキスト
    def recognition(self):
        # WAVファイルから音声を認識
        with sr.AudioFile(self.file_path) as source:
            print('1')
            audio_data = self.recognizer.record(source)
            try:
                # Googleの音声認識APIを使用して音声をテキストに変換
                text = self.recognizer.recognize_google(audio_data, language="ja-JP")
                print("音声認識結果: ", text)
                hiragana_text = self.kakasi_converter.do(text)
                print("Hiragana text:", hiragana_text)

            except sr.UnknownValueError:
                print("音声を認識できませんでした。")
            except sr.RequestError as e:
                print(f"音声認識サービスエラー; {e}")

        return hiragana_text
        
def delete_jpg_files(directory_path):
    # 指定されたディレクトリ内のjpgファイルのリストを取得
    jpg_files = glob.glob(os.path.join(directory_path, '*.jpg'))
    
    # jpgファイルが1枚以上ある場合、すべてのjpgファイルを削除
    if len(jpg_files) > 0:
        for jpg_file in jpg_files:
            os.remove(jpg_file)
        print(f'{len(jpg_files)}枚のjpgファイルを削除しました。')
    else:
        print('jpgファイルは見つかりませんでした。')

def check_mode(client_socket):
    global mode
    
    data = client_socket.recv(MODE_BUFFER_SIZE)
    
    if not data:
        return
    
    mode = f'{data.decode(FORMAT)}'
    print(f'mode : {mode}')
    
    if mode in ['1', '2', '3', '4']:
        client_socket.send('OK\n'.encode(FORMAT))
    else:
        client_socket.send('NG\n'.encode(FORMAT))


def check_state(client_socket):
    global state
    check_data = client_socket.recv(MODE_BUFFER_SIZE)
    
    if not check_data:
        return
    
    state = f'{check_data.decode(FORMAT)}'
    print(f'state : {state}')
    
    if state == '5':
        client_socket.send('OK\n'.encode(FORMAT))
    
    else:
        client_socket.send('NG\n'.encode(FORMAT))


def receive_text(client_socket):
    try:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            
            if not data:
                continue
            
            if b'\r\n\r\n\r\n' in data:
                break
            
            text = f'{data.decode(FORMAT)}'
            
            # クライアントにレスポンスを送信
            client_socket.send('OK\n'.encode(FORMAT))
    
    except:
        client_socket.send('NG\n'.encode(FORMAT))
    
    finally:
        return text


def send_text(client_socket, send_text_data, kind):
    global state
    global checkpoint_send_text
    global checkpoint_send_problem
    
    data = client_socket.recv(BUFFER_SIZE)
    
    if not data:
        return
    
    receive_text_data = f'{data.decode(FORMAT)}'
    print(f'received text : {receive_text_data}')
    print(f'send data : {send_text_data}')
    
    if receive_text_data == 'request_text':
        # クライアントにレスポンスを送信
        client_socket.send(f'{send_text_data}\n'.encode(FORMAT))
        state = 0
        if kind == 'result':
            checkpoint_send_text = True
        
        elif kind == 'problem':
            checkpoint_send_problem = True
    
    else:
        client_socket.send('NG\n'.encode(FORMAT))


def receive_audio(client_socket):
    global audio_count
    
    global checkpoint_receive_audio
    
    data = client_socket.recv(BUFFER_SIZE)
    
    if not data:
        return False
    
    if b'\r\n\r\n\r\n' in data:
        checkpoint_receive_audio = True
        return True
    
    if b'\r\n\r\n' in data:
        audio_count += 1
        return False  # 新しい接続を待ちます
    
    # 音声データをバイナリ形式で受信し、連番で保存する
    audio_filename = f"/workspace/server/receive/audio/{audio_count:04d}.mp3"
    
    # クライアントにレスポンスを送信
    client_socket.send('OK\n'.encode(FORMAT))
    
    # 画像データをファイルに保存
    with open(audio_filename, "ab") as audio_file:
        audio_file.write(data)
    
    return False


def send_audio(client_socket, send_audio_filename):
    global state
    global checkpoint_send_audio
    
    data = client_socket.recv(BUFFER_SIZE)
    
    if not data:
        return
    
    receive_mp3_data = f'{data.decode(FORMAT)}'
    print(f'received text : {receive_mp3_data}')
    
    if receive_mp3_data == 'request_mp3':
        with open(send_audio_filename, "rb") as mp3_file:
                file_size = os.path.getsize(send_audio_filename)
                print(f"Sending {send_audio_filename} ({file_size} bytes) to client")
                
                while True:
                    data_audio = mp3_file.read(CHUNK_SIZE)
                    if not data_audio:
                        client_socket.send(b'\r\n\r\n\r\n')
                        print('Fin!!!')
                        state = 0
                        checkpoint_send_audio = True
                        break
                    
                    client_socket.send(data_audio)
                    time.sleep(0.1)


def receive_img(client_socket):
    global state
    
    global checkpoint_receive_img
    
    global img_count
    data = client_socket.recv(BUFFER_SIZE)
    if not data:
        return False # クライアントが接続を閉じた場合
    
    if b'\r\n\r\n\r\n' in data:
        state = 0
        checkpoint_receive_img = True
        print('Received img! ')
        return True
    
    if b'\r\n\r\n' in data:
        img_count += 1
        return  False# 新しい接続を待ちます
    
    # 画像データをバイナリ形式で受信し、連番で保存する
    image_filename = f"/workspace/server/receive/img/{img_count:04d}.jpg"
    
    # 画像データをファイルに保存
    with open(image_filename, "ab") as image_file:
        image_file.write(data)
    
    return False


def send_img(client_socket):
    pass



def handle_client(client_socket, address):
    print(f"Accepted connection from {address}")
    global mode
    global state
    global img_count
    
    global checkpoint_receive_img
    global checkpoint_send_text
    global checkpoint_send_audio
    global checkpoint_receive_audio
    global checkpoint_send_problem
    global checkpoint_make_problem
    global checkpoint_translate
    
    ##########################kind##########################
    # 0 : モード不定
    # 1 : 指文字翻訳モード
    # 2 : 音声翻訳モード
    # 3 : 練習モード
    # 4 : 写真撮影モード（実装時期未定）
    ########################################################
    
    # 仮
    send_text_data = 'かんせい'
    try:
        while True:
            if mode == '0':
                check_mode(client_socket)
                continue
            
            elif mode == '1': # 指文字翻訳モード
                ##########################流れ##########################
                # 画像を受信→画像をテキストに翻訳→テキストを音声に翻訳
                # →テキストと音声を送信
                ########################################################
                if checkpoint_receive_img == False:
                    if state != '5':
                        check_state(client_socket)
                        continue
                    
                    flag_receive_img = receive_img(client_socket)
                
                if flag_receive_img == True:
                    if checkpoint_translate == False:
                        #---------------------------------------------------------------------------------------------------------------#
                        #  翻訳を実行\
                        # input : 画像（/workspace/server/receive/img/*.jpgに保存されています）
                        # output : テキスト（変数 'send_text_data'にひらがなの文字列で格納してください）
                        #           　音声（/workspace/server/send/audio/speech.mp3に保存してください）
                        #---------------------------------------------------------------------------------------------------------------#
                        img_list = glob.glob('/workspace/server/receive/img/*.jpg')
                        img_list.sort()
                        send_text_data = img2text(img_list=img_list)
                        text2speech = gTTS(send_text_data, lang='ja')
                        text2speech.save('/workspace/server/send/audio/speech.mp3')
                        
                        time.sleep(10) # サーバでの処理時間用（適当）
                        checkpoint_translate = True
                    
                    if checkpoint_send_text == False:
                        send_text(client_socket, send_text_data, 'result')
                        if checkpoint_send_text == False:
                            continue
                    
                    if checkpoint_send_audio == False:
                        if state != '5':
                            check_state(client_socket)
                            if state != '5':
                                continue
                        
                        send_audio_filename = f'/workspace/server/send/audio/speech.mp3'
                        send_audio(client_socket, send_audio_filename)
                        if checkpoint_send_audio == False:
                            continue
                        
                        checkpoint_receive_img = False
                        checkpoint_receive_audio = False
                        flag_receive_img = False
                        checkpoint_send_text = False
                        checkpoint_send_audio = False
                        checkpoint_translate = False
                        mode = '0'
                        state = '0'
            
            elif mode == '2':# 音声翻訳モード
                ##########################流れ##########################
                # 音声を受信→音声をテキストに翻訳→テキストを送信
                ########################################################
                if checkpoint_receive_img == False:
                    if state != '5':
                        check_state(client_socket)
                        continue
                
                if checkpoint_receive_audio == False:
                    flag_receive_audio = receive_audio(client_socket)
                
                if flag_receive_audio == True:
                    if checkpoint_translate == False:
                        #---------------------------------------------------------------------------------------------------------------#
                        #  翻訳を実行\
                        # input : 音声（/workspace/server/receive/audio/･･･.mp3に保存されています）
                        # output : テキスト（変数 'send_text_data'にひらがなの文字列で格納してください）
                        #---------------------------------------------------------------------------------------------------------------#
                        
                        send_text_data = audio_ricognition.recognition()
                        time.sleep(10) # サーバでの処理時間用（適当）
                        checkpoint_translate = True
                    
                    if checkpoint_send_text == False:
                        send_text(client_socket, send_text_data, 'result')
                        if checkpoint_send_text == False:
                            continue
                        
                        checkpoint_receive_img = False
                        checkpoint_receive_audio = False
                        flag_receive_audio = False
                        checkpoint_send_text = False
                        checkpoint_send_audio = False
                        checkpoint_translate = False
                        mode = '0'
                        state = '0'
            
            elif mode == '3': # 練習モード
                ##########################流れ##########################
                # テキストを送信→画像を受信→画像をテキストに翻訳
                # →正誤判定？→結果（正誤or翻訳）のテキストを送信
                ########################################################
                
                problem_data = 'ぼんくら'
                
                if checkpoint_make_problem == False:
                    #---------------------------------------------------------------------------------------------------------------#
                    #  問題の作成\
                    # input :   mode:str ('num' or 'moji')文字で問題を作成するか、数字で作成するか(default='moji')
                    #           length: int  文字列の長さ(default=3)
                    # output : テキスト（変数 'problem_data'にひらがなの文字列で格納してください）
                    #---------------------------------------------------------------------------------------------------------------#
                    problem_data = practice_random_mode.problem_generate(mode = 'moji')
                    checkpoint_make_problem = True
                    time.sleep(10) # サーバでの処理時間用（適当）
                
                if checkpoint_send_problem == False:
                    if state != '5':
                        check_state(client_socket)
                        continue
                    
                    send_text(client_socket, problem_data, 'problem')
                
                if checkpoint_send_problem == True:
                    if checkpoint_receive_img == False:
                        if state != '5':
                            check_state(client_socket)
                            continue
                        
                        flag_receive_img = receive_img(client_socket)
                    
                    if flag_receive_img == True:
                        if checkpoint_translate == False:
                            #---------------------------------------------------------------------------------------------------------------#
                            #  翻訳を実行\
                            # input : 画像（/workspace/server/receive/img/*.jpgに保存されています）
                            # output : テキスト（変数 'send_text_data'にひらがなの文字列で格納してください）
                            #           　音声（/workspace/server/send/audio/speech.mp3に保存してください）
                            #---------------------------------------------------------------------------------------------------------------#

                            img_list = glob.glob('/workspace/server/receive/img/*.jpg')
                            img_list.sort()
                            send_text_data = img2text(img_list=img_list)
                            text2speech = gTTS(send_text_data, lang='ja')
                            text2speech.save('/workspace/server/send/audio/speech.mp3')


                            time.sleep(10) # サーバでの処理時間用（適当）
                            checkpoint_translate = True
                        
                        if checkpoint_send_text == False:
                            send_text(client_socket, send_text_data, 'result')
                            if checkpoint_send_text == False:
                                continue
                        
                        if checkpoint_send_audio == False:
                            if state != '5':
                                check_state(client_socket)
                            
                            send_audio_filename = f'/workspace/server/send/audio/speech.mp3'
                            send_audio(client_socket, send_audio_filename)
                            
                            checkpoint_make_problem = False
                            checkpoint_send_problem = False
                            checkpoint_receive_img = False
                            checkpoint_receive_audio = False
                            flag_receive_img = False
                            checkpoint_send_text = False
                            checkpoint_send_audio = False
                            checkpoint_translate = False
                            mode = '0'
                            state = '0'
            
            elif mode == '4': # 写真撮影モード（実装時期未定）
                ##########################流れ##########################
                # 
                ########################################################
                mode = '0'
    
    finally:
        client_socket.close()
        print(f"Connection with {address} closed")


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    
    print(f"Server listening on {IP}:{PORT}")
    
    try:
        while True:
            client_socket, address = server_socket.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
            client_handler.start()
    
    except KeyboardInterrupt:
        print("Exit the program.")
    
    finally:
        print("Server shutting down.")
        server_socket.close()
        print("Server shutdown has been completed.")
        exit()

if __name__ == "__main__":
    image_filename = '/workspace/server/receive/img'
    practice_random_mode = Practice_Mode()
    audio_ricognition = AudioRicognition()

    delete_jpg_files(image_filename)
    
    start_server()