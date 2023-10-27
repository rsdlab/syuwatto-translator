import socket

def send_wav_file_to_server(file_path, server_host, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        with open(file_path, 'rb') as file:
            data = file.read(1024)
            while data:
                client_socket.send(data)
                data = file.read(1024)
        print(f"{file_path} をサーバーに送信しました")

if __name__ == "__main__":
    file_to_send = "./data/sample.wav"  # 送信するWAVファイルのパス
    ip = 'localhost'
    port = 9999

    send_wav_file_to_server(file_to_send, ip, port)
