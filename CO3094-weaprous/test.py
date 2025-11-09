# main.py
import socket
from daemon.httpadapter import HttpAdapter

def main():
    HOST = '127.0.0.1'
    PORT = 8080
    routes = {}  # có thể thêm RESTful route nếu cần

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[Server] Running on http://{HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            print(f"[Server] Connected by {addr}")

            adapter = HttpAdapter(HOST, PORT, conn, addr, routes)
            adapter.handle_client(conn, addr, routes)

if __name__ == "__main__":
    main()
