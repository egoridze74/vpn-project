import os
import sys
import socket
import threading
import json
import hashlib

sys.path.insert(0, '/workspaces/project')

from database.db import Database
from common import xor_encrypt, create_tun, start_tunnel


class VPNServer:
    def __init__(self, port=1194, db_path="db.sqlite"):
        self.port = port
        self.db_path = db_path
        self.clients = {}
        self.running = True
        self.tun_fd = None
        self.udp_sock = None
        
    def get_db(self):
        return Database(self.db_path)
    
    def authenticate_user(self, username, password):
        db = self.get_db()
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            user = db.fetchone(
                'SELECT * FROM "Users" WHERE "Username" = ? AND "Password" = ?',
                (username, password_hash)
            )
            return user is not None
        finally:
            db.connection.close()
    
    def handle_auth(self, data, client_addr):
        try:
            decrypted = xor_encrypt(data)
            request = json.loads(decrypted.decode())
            username = request.get('username')
            password = request.get('password')
            
            if not username or not password:
                response = {'status': 'error', 'message': 'Missing credentials'}
                return xor_encrypt(json.dumps(response).encode())
            
            if self.authenticate_user(username, password):
                self.clients[client_addr] = {'username': username}
                print(f"[VPN] User '{username}' authenticated")
                response = {
                    'status': 'authenticated',
                    'tun_ip': '10.0.0.1',
                    'message': 'Connected to VPN'
                }
            else:
                response = {'status': 'error', 'message': 'Invalid credentials'}
            
            return xor_encrypt(json.dumps(response).encode())
        except Exception as e:
            response = {'status': 'error', 'message': str(e)}
            return xor_encrypt(json.dumps(response).encode())
    
    def start(self):
        print(f"[VPN] Starting server on port {self.port}")
        
        self.tun_fd = create_tun("tun_server")
        if self.tun_fd:
            import subprocess
            subprocess.run(["ip", "addr", "add", "10.0.0.1/24", "dev", "tun_server"], capture_output=True)
            print("[VPN] TUN interface created")
        
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(("0.0.0.0", self.port))
        
        while self.running:
            try:
                data, client_addr = self.udp_sock.recvfrom(4096)
                
                if client_addr not in self.clients:
                    response = self.handle_auth(data, client_addr)
                    self.udp_sock.sendto(response, client_addr)
                elif self.tun_fd:
                    start_tunnel(self.tun_fd, self.udp_sock, client_addr)
                    print(f"[VPN] Tunnel established with {client_addr}")
                    break
            except Exception as e:
                print(f"[VPN] Error: {e}")
        
        try:
            while self.running:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        self.running = False
        if self.tun_fd:
            os.close(self.tun_fd)
        if self.udp_sock:
            self.udp_sock.close()


if __name__ == "__main__":
    server = VPNServer(port=1194)
    server.start()