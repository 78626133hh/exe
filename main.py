import socket
import subprocess
import re
import platform

def get_ipv4_address():
    """获取本机IPv4地址"""
    try:
        # 方法1: 通过连接外部DNS获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # 方法2: 获取所有网络接口的IP
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except Exception:
            return None

def get_all_ipv4():
    """获取所有网卡的IPv4地址"""
    ips = []
    try:
        hostname = socket.gethostname()
        # 获取所有IP地址
        for addr in socket.getaddrinfo(hostname, None):
            ip = addr[4][0]
            if ':' not in ip and not ip.startswith('127.'):
                if ip not in ips:
                    ips.append(ip)
    except Exception:
        pass
    
    # 如果上面方法没获取到，尝试备用方法
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            pass
    
    return ips

def get_public_ip():
    """尝试获取公网IP（通过外部服务）"""
    try:
        import urllib.request
        import json
        
        # 使用多个服务获取公网IP
        services = [
            'https://api.ipify.org?format=json',
            'https://httpbin.org/ip',
            'https://ipinfo.io/json'
        ]
        
        for url in services:
            try:
                with urllib.request.urlopen(url, timeout=3) as response:
                    data = json.loads(response.read().decode())
                    if 'ip' in data:
                        return data['ip']
                    elif 'origin' in data:
                        return data['origin']
            except:
                continue
        return None
    except ImportError:
        # 如果urllib不可用，使用socket方式
        try:
            import urllib2
            import json
            response = urllib2.urlopen('https://api.ipify.org?format=json', timeout=3)
            data = json.loads(response.read().decode())
            return data['ip']
        except:
            return None
    except Exception:
        return None

def get_network_interfaces():
    """获取网络接口信息（适用于多系统）"""
    interfaces = {}
    system = platform.system()
    
    if system == 'Windows':
        try:
            output = subprocess.check_output(['ipconfig'], encoding='gbk', errors='ignore')
            # 解析Windows的ipconfig输出
            current_interface = None
            for line in output.split('\n'):
                if '适配器' in line or 'adapter' in line.lower():
                    current_interface = line.strip()
                    interfaces[current_interface] = []
                elif 'IPv4 地址' in line or 'IPv4 Address' in line:
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match and current_interface:
                        interfaces[current_interface].append(ip_match.group(1))
        except Exception as e:
            print(f"获取Windows网络接口失败: {e}")
    
    elif system in ['Linux', 'Darwin']:  # Darwin = macOS
        try:
            if system == 'Darwin':
                cmd = ['ifconfig']
            else:
                cmd = ['ip', 'addr']
            
            output = subprocess.check_output(cmd, encoding='utf-8', errors='ignore')
            # 简单的正则匹配IP地址
            ips = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
            for ip in ips:
                if not ip.startswith('127.'):
                    if 'interfaces' not in interfaces:
                        interfaces['interfaces'] = []
                    interfaces['interfaces'].append(ip)
        except Exception as e:
            print(f"获取Unix网络接口失败: {e}")
    
    return interfaces

def main():
    """主函数 - 显示网络信息"""
    print("=" * 60)
    print(" 网络信息获取工具 - 内网穿透助手")
    print("=" * 60)
    
    # 1. 获取主要IPv4地址
    main_ip = get_ipv4_address()
    if main_ip:
        print(f"\n📌 本机主要IPv4地址: {main_ip}")
    
    # 2. 获取所有IPv4地址
    all_ips = get_all_ipv4()
    if all_ips:
        print(f"\n📋 所有IPv4地址:")
        for i, ip in enumerate(all_ips, 1):
            print(f"   {i}. {ip}")
    
    # 3. 获取网络接口详情
    interfaces = get_network_interfaces()
    if interfaces:
        print(f"\n🔌 网络接口详情:")
        for interface, ips in interfaces.items():
            if ips:
                print(f"   {interface}: {', '.join(ips)}")
    
    # 4. 获取公网IP
    print(f"\n🌐 正在获取公网IP...")
    public_ip = get_public_ip()
    if public_ip:
        print(f"   公网IP: {public_ip}")
        print(f"   ⚠️  注意: 如果此IP与内网IP不同，说明你在NAT后面")
    else:
        print("   ⚠️  无法获取公网IP（可能网络连接问题）")
    
    # 5. 内网穿透建议
    print("\n" + "=" * 60)
    print(" 💡 内网穿透建议")
    print("=" * 60)
    
    if main_ip:
        print(f"\n1. 你的内网IP: {main_ip}")
        print(f"   → 可使用 frp、ngrok、ZeroTier 等工具进行内网穿透")
        print(f"   → 如需远程访问，请将 {main_ip} 告诉朋友")
    
    if public_ip and public_ip != main_ip:
        print(f"\n2. 公网IP: {public_ip} (与内网不同)")
        print(f"   → 你位于NAT网络，需要使用内网穿透服务")
        print(f"   → 推荐: frp、nps、Ngrok、Tailscale")
    elif public_ip and public_ip == main_ip:
        print(f"\n2. 公网IP: {public_ip} (与内网相同)")
        print(f"   → 你有公网IP，可直接开放端口访问")
    else:
        print(f"\n2. ⚠️ 无法确定公网IP情况")
        print(f"   → 建议使用内网穿透工具：frp、ngrok、ZeroTier")
    
    # 6. 常用端口推荐
    print(f"\n3. 常用内网穿透端口:")
    print("   • Web服务: 80, 443, 8080")
    print("   • SSH: 22 (Linux/macOS)")
    print("   • RDP: 3389 (Windows远程桌面)")
    print("   • VNC: 5900")
    print("   • 数据库: 3306 (MySQL), 5432 (PostgreSQL)")
    
    print("\n" + "=" * 60)
    print("📖 提示: 如需安装 frp，可访问: https://github.com/fatedier/frp")
    print("=" * 60)

if __name__ == "__main__":
    main()
