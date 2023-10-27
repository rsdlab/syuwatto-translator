import socket

def save_received_wav_file(client_socket, output_file_path):
    with open(output_file_path, 'wb') as file:
        data = client_socket.recv(1024)
        while data:
            file.write(data)
            data = client_socket.recv(1024)
        print(f"ファイルを受信して保存しました: {output_file_path}")

if __name__ == "__main__":
    ip = 'localhost'
    port = 9999
    output_file_path = "./data/received.wav"  # 受信したWAVファイルの保存先

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((ip, port))
        server_socket.listen()

        print(f"クライアントからの接続待ち中 ({ip}:{port})...")
        client_socket, client_address = server_socket.accept()

        save_received_wav_file(client_socket, output_file_path)
