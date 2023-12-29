import socket
import threading
import os 
import time
import glob
from pydub import AudioSegment

# 追加分
import random
from img2text import img2text
from gtts import gTTS
import speech_recognition as sr
from pykakasi import kakasi

import warnings

import numpy as np
import wave
from scipy.interpolate import interp1d

warnings.filterwarnings("ignore", category=DeprecationWarning)

IP = 'localhost'
PORT = 8080
MODE_BUFFER_SIZE = 1
BUFFER_SIZE = 1024
CHUNK_SIZE = 256
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

DEBUG = False

def interpolate_waveform(waveform, factor=1.5):
    # 線形補間関数を作成
    x = np.arange(len(waveform))
    f = interp1d(x, waveform, kind='linear', fill_value="extrapolate")
    
    # 新しい波形の長さ
    new_length = int(factor * len(waveform))
    
    # 新しいx軸を生成
    new_x = np.linspace(0, len(waveform) - 1, new_length)
    
    # 補完された波形を計算
    interpolated_waveform = f(new_x)
    
    return interpolated_waveform

def mp3_to_waveform(file_path):
    audio = AudioSegment.from_file(file_path, format="mp3")
    waveform = np.array(audio.get_array_of_samples())
    
    return waveform, audio.frame_rate

def waveform_to_mp3(waveform, frame_rate, output_path):
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono audio
        wav_file.setsampwidth(2)  # 16-bit sample width
        wav_file.setframerate(frame_rate)
        wav_file.writeframes(waveform.astype(np.int16).tobytes())
    
    # Convert WAV to MP3
    audio = AudioSegment.from_wav(output_path)
    audio.export(output_path.replace(".wav", ".mp3"), format="mp3")

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
        
        # return True

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
        self.kakasi = kakasi()
        self.kakasi.setMode('J', 'H') # J(Kanji) to H(Hiragana)
        self.kakasi.setMode('H', 'H') # H(Hiragana) to None(noconversion)
        self.kakasi.setMode('K', 'H') # K(Katakana) to a(Hiragana)
        self.kakasi_converter = self.kakasi.getConverter()
        # return True
    
    # 音声-->ひらがなテキスト
    def recognition(self, file_path):
        # WAVファイルから音声を認識
        with sr.AudioFile(file_path) as source:
        # with sr.AudioFile(self.file_path) as source:
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


# サーバー起動時に 'directory_path' で指定したディレクトリにある 'extension' で指定した拡張子のファイルをすべて削除する関数
def delete_files(directory_path, extension):
    files = glob.glob(os.path.join(directory_path, f'*.{extension}'))
    
    if len(files) > 0:
        for file in files:
            os.remove(file)
        print(f'{len(files)}つの{extension}ファイルを削除しました。')
    else:
        print(f'{extension}ファイルは見つかりませんでした。')


# SPRESENSE側がなんの処理をするのかを確認する関数
def check_mode(client_socket):
    global mode
    
    data = client_socket.recv(MODE_BUFFER_SIZE)
    
    if not data:
        return
    
    mode = f'{data.decode(FORMAT)}'
    print(f'mode : {mode}')
    
    # 1:指文字翻訳, 2:音声翻訳, 3:練習, 4:写真撮影
    if mode in ['1', '2', '3', '4']:
        # 1~4であれば 'OK' を送信して次のステップへ
        client_socket.send('OK\n'.encode(FORMAT))
    else:
        # 上記以外のモードは実装されてないので次に進めないように 'NG' を送信
        client_socket.send('NG\n'.encode(FORMAT))
        mode = '0'


# SPRESENSEがデータを受信できる状況かどうかを確認する関数
def check_state(client_socket):
    global state
    check_data = client_socket.recv(MODE_BUFFER_SIZE)
    
    if not check_data:
        return
    
    state = f'{check_data.decode(FORMAT)}'
    print(f'state : {state}')
    
    # 5: 受取準備OK
    if state == '5':
        #  5は準備ができているとみなして 'OK' を送って次のステップへ
        client_socket.send('OK\n'.encode(FORMAT))
    
    else:
        # 5以外は準備ができてないとみなして 'NG' を送って再度データを受信する
        client_socket.send('NG\n'.encode(FORMAT))
        state = '0'


# SPRESENSEかテキストを受け取る関数（現状は使用してない）
def receive_text(client_socket):
    try:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            
            if not data:
                continue
            
            if b'\r\n\r\n\r\n' in data: # 終了フラグが来たら終了する
                break
            
            receive_text = f'{data.decode(FORMAT)}'
            
            print(f'receive_text : {receive_text}')
            
            # クライアントにレスポンスを送信
            client_socket.send('OK\n'.encode(FORMAT))
    
    except:
        client_socket.send('NG\n'.encode(FORMAT))
    
    finally:
        return receive_text


# SPRESENSEにテキストを送信する関数
def send_text(client_socket, send_text_data, kind):
    global state
    global checkpoint_send_text
    global checkpoint_send_problem
    
    data = client_socket.recv(BUFFER_SIZE)
    
    if not data:
        return
    
    # SPPRESENSEが受信しようとしているデータの形式)の確認
    receive_text_data = f'{data.decode(FORMAT)}'
    
    print(f'received text : {receive_text_data}') # SPRESENSEが受信したい形式
    print(f'send data : {send_text_data}') # 送信しようとしているテキスト
    
    # SPRESENSE側がtextデータを要求している場合のみテキストを送信
    if receive_text_data == 'request_text':
        client_socket.send(f'{send_text_data}\n'.encode(FORMAT))
        
        print(f'sent text data!')
        
        state = 0 # 受信できる状態かどうかを再度確認するためにフラグを取り消す
        
        if kind == 'result':
            checkpoint_send_text = True
        
        elif kind == 'problem':
            checkpoint_send_problem = True
    
    else:
        client_socket.send('NG\n'.encode(FORMAT))


# SPRESENSEからmp3ファイルを受信する関数
def receive_audio(client_socket):
    global audio_count
    global checkpoint_receive_audio
    
    audio_filename = f"/workspace/server/receive/audio/{audio_count:04d}.mp3"
    
    data = client_socket.recv(BUFFER_SIZE)
    
    if b'\r\n\r\n\r\n' in data: # 終了フラグが来たら終了する
        checkpoint_receive_audio = True
        audio_count += 1
        print('Received audio! ')
        return
    
    if not data:
        return
    
    # 画像データをファイルに保存
    with open(audio_filename, "ab") as audio_file:
        audio_file.write(data)
    
    return


# SPRESENSEにmp3ファイルを送信する関数
def send_audio(client_socket, send_audio_filename):
    global state
    global checkpoint_send_audio
    
    data = client_socket.recv(BUFFER_SIZE)
    
    if not data:
        return
    
    # SPPRESENSEが受信しようとしているデータの形式)の確認
    receive_mp3_data = f'{data.decode(FORMAT)}'
    
    print(f'received text : {receive_mp3_data}') # SPRESENSEが受信したい形式
    
    # SPRESENSE側がmp3データを要求している場合のみテキストを送信
    if receive_mp3_data == 'request_mp3':
        with open(send_audio_filename, "rb") as mp3_file:
                file_size = os.path.getsize(send_audio_filename)
                print(f"Sending {send_audio_filename} ({file_size} bytes) to client")
                
                while True:
                    data_audio = mp3_file.read(CHUNK_SIZE)
                    if not data_audio:
                        client_socket.send(b'\r\n\r\n\r\n') # 終了フラグを送信
                        print('Sent mp3!')
                        state = 0
                        checkpoint_send_audio = True
                        break
                    
                    client_socket.send(data_audio)
                    time.sleep(0.1)


# SPRESENSEから画像を受信する関数
def receive_img(client_socket):
    global state
    
    global checkpoint_receive_img
    
    global img_count
    data = client_socket.recv(BUFFER_SIZE)
    if not data:
        return # クライアントが接続を閉じた場合
    
    if b'\r\n\r\n\r\n' in data: # 終了フラグが来たら終了する
        state = 0
        img_count += 1
        checkpoint_receive_img = True
        print('Received img! ')
        
        return
    
    if b'\r\n\r\n' in data: # 1つのファイルが送信終了したフラグ
        img_count += 1
        return # 新しい接続を待ちます
    
    if DEBUG == False:
        # 画像データをバイナリ形式で受信し、連番で保存する
        if img_count != 0:
            image_filename = f"/workspace/server/receive/img/{img_count:04d}.jpg"
            
            # 画像データをファイルに保存
            with open(image_filename, "ab") as image_file:
                image_file.write(data)
    
    return


# SPRESENSEに画像を送信する関数（使用用途がなかったため未実装）
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
    # 4 : 写真撮影モード
    ########################################################
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
                if DEBUG == False:
                    if checkpoint_receive_img == False:
                        if state != '5':
                            check_state(client_socket)
                            continue
                        receive_img(client_socket)
                
                elif DEBUG == True:
                    checkpoint_receive_img = True
                
                if checkpoint_receive_img == True:
                    if checkpoint_translate == False:
                        #---------------------------------------------------------------------------------------------------------------#
                        #  翻訳を実行\
                        # input : 画像（/workspace/server/receive/img/*.jpgに保存されています）
                        # output : テキスト（変数 'send_text_data'にひらがなの文字列で格納してください）
                        #           　音声（/workspace/server/send/audio/speech.mp3に保存してください）
                        #---------------------------------------------------------------------------------------------------------------#
                        img_list = glob.glob('/workspace/server/receive/img/*.jpg')
                        img_list.sort()
                        send_text_data = img2text(img_list = img_list, debug = DEBUG)
                        text2speech = gTTS(send_text_data, lang='ja', slow=True)
                        text2speech.save('/workspace/server/send/audio/speech.mp3')
                        input_file = "/workspace/server/send/audio/speech.mp3"
                        output_file = "/workspace/server/send/audio/speech.mp3"
                        # MP3ファイルを波形データに変換
                        waveform, frame_rate = mp3_to_waveform(input_file)
                        
                        # 波形を2倍に補完
                        interpolated_waveform = interpolate_waveform(waveform, factor=2)
                        
                        # 補完された波形をMP3ファイルに変換して保存
                        waveform_to_mp3(interpolated_waveform, frame_rate, output_file)
                        
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
                        checkpoint_send_text = False
                        checkpoint_send_audio = False
                        checkpoint_translate = False
                        mode = '0'
                        state = '0'
            
            elif mode == '2':# 音声翻訳モード
                ##########################流れ##########################
                # 音声を受信→音声をテキストに翻訳→テキストを送信
                ########################################################
                if checkpoint_receive_audio == False:
                    if state != '5':
                        check_state(client_socket)
                        continue
                    
                    receive_audio(client_socket)
                
                if checkpoint_receive_audio == True:
                    time1 = time.perf_counter()
                    # convert wav to mp3
                    audSeg = AudioSegment.from_mp3(f"/workspace/server/receive/audio/{(audio_count - 1):04d}.mp3")
                    audSeg.export(f"/workspace/server/receive/audio/{(audio_count - 1):04d}.wav", format="wav")
                    
                    if checkpoint_translate == False:
                        #---------------------------------------------------------------------------------------------------------------#
                        #  翻訳を実行\
                        # input : 音声（/workspace/server/receive/audio/･･･.mp3に保存されています）
                        # output : テキスト（変数 'send_text_data'にひらがなの文字列で格納してください）
                        #---------------------------------------------------------------------------------------------------------------#
                        receive_audio_path = f"/workspace/server/receive/audio/{(audio_count - 1):04d}.wav"
                        send_text_data = audio_ricognition.recognition(receive_audio_path)
                        time2 = time.perf_counter()
                        print(time2 - time1)
                        checkpoint_translate = True
                    
                    if checkpoint_send_text == False:
                        send_text(client_socket, send_text_data, 'result')
                        if checkpoint_send_text == False:
                            continue
                        
                        checkpoint_receive_audio = False
                        checkpoint_send_text = False
                        checkpoint_translate = False
                        mode = '0'
                        state = '0'
            
            elif mode == '3': # 練習モード
                ##########################流れ##########################
                # テキストを送信→画像を受信→画像をテキストに翻訳
                # →正誤判定？→結果（正誤or翻訳）のテキストを送信
                ########################################################
                if checkpoint_make_problem == False:
                    #---------------------------------------------------------------------------------------------------------------#
                    #  問題の作成\
                    # input :   mode:str ('num' or 'moji')文字で問題を作成するか、数字で作成するか(default='moji')
                    #           length: int  文字列の長さ(default=3)
                    # output : テキスト（変数 'problem_data'にひらがなの文字列で格納してください）
                    #---------------------------------------------------------------------------------------------------------------#
                    problem_data = practice_random_mode.problem_generate(mode = 'moji')
                    checkpoint_make_problem = True
                
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
                        
                        receive_img(client_socket)
                    
                    if checkpoint_receive_audio == True:
                        if checkpoint_translate == False:
                            #---------------------------------------------------------------------------------------------------------------#
                            #  翻訳を実行\
                            # input : 画像（/workspace/server/receive/img/*.jpgに保存されています）
                            # output : テキスト（変数 'send_text_data'にひらがなの文字列で格納してください）
                            #           　音声（/workspace/server/send/audio/speech.mp3に保存してください）
                            #---------------------------------------------------------------------------------------------------------------#
                            img_list = glob.glob('/workspace/server/receive/img/*.jpg')
                            img_list.sort()
                            send_text_data = img2text(img_list = img_list, debug = DEBUG)
                            text2speech = gTTS(send_text_data, lang='ja')
                            text2speech.save('/workspace/server/send/audio/speech.mp3')
                            
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
                            checkpoint_send_text = False
                            checkpoint_send_audio = False
                            checkpoint_translate = False
                            mode = '0'
                            state = '0'
            
            elif mode == '4': # 写真撮影モード
                ##########################流れ##########################
                # 画像を受信→?
                ########################################################
                if checkpoint_receive_img == False:
                    if state != '5':
                        check_state(client_socket)
                        continue
                    
                    receive_img(client_socket) #画像を受信
                
                if checkpoint_receive_img == True:
                            #---------------------------------------------------------------------------------------------------------------#
                            #  ウェブページ上に画像表示？
                            #---------------------------------------------------------------------------------------------------------------#
                        
                        checkpoint_receive_img = False
                        mode = '0'
                        state = '0'
    
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
    dirs = ['receive/img', 'receive/audio', 'send/img', 'send/audio']
    for dir in dirs:
        os.makedirs(f'/workspace/server/{dir}', exist_ok=True)
    image_directory_path= '/workspace/server/receive/img'
    audio_directory_path= '/workspace/server/receive/audio'
    practice_random_mode = Practice_Mode()
    audio_ricognition = AudioRicognition()
    
    delete_files(image_directory_path, 'jpg')
    delete_files(audio_directory_path, 'mp3')
    delete_files(audio_directory_path, 'wav')
    
    start_server()