import socket
import ssl
import threading

# 加载自签名 CA 证书
context = ssl.create_default_context()
context.load_cert_chain(certfile="/Users/icepan/data/py-code/http-proxy/ssl/mycert.pem",
                        keyfile="/Users/icepan/data/py-code/http-proxy/ssl/private_key.pem")
context.check_hostname = False  # 忽略校验域名
context.verify_mode = ssl.CERT_NONE  # 忽略校验客户端CA


# ssl拦截之后下面内容都可见
def forward(source_socket, target_socket):
    while True:
        content = source_socket.recv(1024)
        if not content:
            break
        target_socket.sendall(content)


def handle_client(client_socket: socket.socket) -> None:
    request = client_socket.recv(1024)
    if not request:
        client_socket.close()
        print('request is None')
        return
    content = request.decode()
    lines = content.split('\r\n')

    first_line = lines[0]
    method, url, _ = first_line.split()
    if method.upper() == 'CONNECT':
        host, port = url.split(':')
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((host, int(port)))
        client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        print('HTTPS connection established')

        ssl_client_socket = context.wrap_socket(client_socket, server_side=True)
        ssl_server_socket = ssl.wrap_socket(server_socket)

        t1 = threading.Thread(target=forward, args=(ssl_server_socket, ssl_client_socket))
        t2 = threading.Thread(target=forward, args=(ssl_client_socket, ssl_server_socket))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        client_socket.close()
        server_socket.close()
        print('connection finished')
        return

    host_header = [line for line in lines if line.startswith("Host:")]
    if not host_header:
        print('no host header')
        client_socket.close()
        return

    port = 80
    host = host_header[0].strip().split(':')[1].strip()
    if ':' in host:
        host, port = host.split(':')
        port = int(port)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((host, port))
    server_socket.sendall(request)  # 转发请求
    while True:
        response = server_socket.recv(4096)
        if not response:
            break
        client_socket.sendall(response)
    server_socket.close()
    client_socket.close()


def main():
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_socket.bind(('0.0.0.0', 8080))
    proxy_socket.listen(128)
    print('listening on port 8080')

    while True:
        client_socket, addr = proxy_socket.accept()
        print('received connection from', addr)
        threading.Thread(target=handle_client, args=(client_socket,)).start()


if __name__ == '__main__':
    main()
