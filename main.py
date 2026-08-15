# ← 添加这一行 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minecraft 一键开服脚本 v1.0 (Windows版)
作者: 夕阳再升void
B站: 夕阳再升void (UID: 3546971858012899)
开源协议: MIT

⚠️ 注意: 请勿修改脚本所在路径结构！
💡 如果帮到了你，欢迎去B站给个三连！
"""

import os
import sys
import json
import subprocess
import threading
import time
import shutil
import zipfile
import webbrowser
from datetime import datetime
from pathlib import Path

# ==================== 依赖检查 ====================
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
except ImportError:
    print("错误: tkinter 未安装，请确保Python安装时勾选了tcl/tk")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("错误: requests 未安装，请运行: pip install requests")
    sys.exit(1)

# ==================== 全局常量 ====================
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
AUTHOR = "夕阳再升void"
BILIBILI_UID = "3546971858012899"
BILIBILI_URL = f"https://space.bilibili.com/{BILIBILI_UID}"
CONFIG_FILE = "server_config.json"
SERVER_DIR = "minecraft_server"
JAVA_DIR = "java_runtime"
MIN_MEMORY = 512
MAX_MEMORY = 32768
DEFAULT_MEMORY = 2048

# ==================== 工具函数 ====================
def safe_path(path):
    return str(Path(path).resolve())

def is_port_in_use(port=25565):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except:
            return True

# ==================== 配置管理 ====================
class ConfigManager:
    @staticmethod
    def load():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    @staticmethod
    def save(data):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False

# ==================== Java管理 ====================
class JavaManager:
    @staticmethod
    def get_java_path():
        java_dir = Path(JAVA_DIR)
        if not java_dir.exists():
            return None
        for exe in java_dir.rglob("java.exe"):
            return str(exe)
        for exe in java_dir.rglob("java"):
            return str(exe)
        return None
    
    @staticmethod
    def get_java_version():
        java_path = JavaManager.get_java_path()
        if not java_path:
            return None
        try:
            result = subprocess.run([java_path, "-version"], 
                                   capture_output=True, text=True, timeout=5)
            for line in result.stderr.split('\n'):
                if 'version' in line.lower():
                    return line.strip()
            return "未知版本"
        except:
            return "未知版本"
    
    @staticmethod
    def download_java(callback=None, parent_window=None):
        """下载Java (带进度条)"""
        java_zip = Path("java_temp.zip")
        java_dir = Path(JAVA_DIR)
        
        if JavaManager.get_java_path():
            if callback:
                callback("✅ Java已存在，跳过下载")
            return True
        
        # 多镜像源
        urls = [
            {"url": "https://mirrors.huaweicloud.com/adoptium/17/jdk/x64/windows/OpenJDK17U-jdk_x64_windows_hotspot_17.0.10_7.zip", "name": "华为云"},
            {"url": "https://mirrors.aliyun.com/adoptium/17/jdk/x64/windows/OpenJDK17U-jdk_x64_windows_hotspot_17.0.10_7.zip", "name": "阿里云"},
            {"url": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.10%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.10_7.zip", "name": "GitHub"}
        ]
        
        # 创建进度对话框
        dialog = None
        if parent_window:
            dialog = tk.Toplevel(parent_window)
            dialog.title("正在下载 Java")
            dialog.geometry("450x200")
            dialog.transient(parent_window)
            dialog.grab_set()
            dialog.resizable(False, False)
            ttk.Label(dialog, text="📥 正在下载 Java 运行时环境", font=("", 11)).pack(pady=10)
            source_label = ttk.Label(dialog, text="", font=("", 9))
            source_label.pack(pady=5)
            progress_var = tk.StringVar(value="准备下载...")
            ttk.Label(dialog, textvariable=progress_var, font=("", 9)).pack(pady=5)
            progress_bar = ttk.Progressbar(dialog, mode="determinate", length=350)
            progress_bar.pack(pady=10)
            cancel_flag = [False]
            def cancel_download():
                cancel_flag[0] = True
                dialog.destroy()
            ttk.Button(dialog, text="取消", command=cancel_download).pack(pady=5)
        
        for source in urls:
            if dialog and cancel_flag[0]:
                return False
            
            url = source["url"]
            source_name = source["name"]
            
            try:
                if dialog:
                    source_label.config(text=f"📡 使用 {source_name}")
                    progress_var.set("正在连接服务器...")
                    dialog.update()
                
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                last_percent = 0
                
                with open(java_zip, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if dialog and cancel_flag[0]:
                            java_zip.unlink()
                            return False
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                percent = (downloaded / total_size) * 100
                                if percent - last_percent >= 5:
                                    last_percent = percent
                                    if dialog:
                                        progress_var.set(f"下载进度: {percent:.1f}%")
                                        progress_bar['value'] = percent
                                        dialog.update()
                
                if dialog:
                    progress_var.set("解压中...")
                    dialog.update()
                
                with zipfile.ZipFile(java_zip, 'r') as zip_ref:
                    zip_ref.extractall(java_dir)
                
                extracted = list(java_dir.glob("jdk*"))
                if extracted:
                    src = extracted[0]
                    for item in src.iterdir():
                        dest = java_dir / item.name
                        if dest.exists():
                            if dest.is_dir():
                                shutil.rmtree(dest)
                            else:
                                dest.unlink()
                        shutil.move(str(item), str(dest))
                    shutil.rmtree(src)
                
                java_zip.unlink()
                
                if JavaManager.get_java_path():
                    if dialog:
                        progress_var.set("✅ Java 安装成功!")
                        progress_bar['value'] = 100
                        dialog.update()
                        time.sleep(0.5)
                        dialog.destroy()
                    return True
                else:
                    continue
                    
            except Exception as e:
                if dialog:
                    progress_var.set(f"⚠️ {source_name} 失败，尝试下一个...")
                    dialog.update()
                continue
        
        if dialog:
            dialog.destroy()
            messagebox.showerror("错误", "❌ 所有镜像源均下载失败！\n请手动安装 JDK 17")
        return False

# ==================== 服务端管理 ====================
class ServerManager:
    @staticmethod
    def get_version_info(version):
        try:
            resp = requests.get(VERSION_MANIFEST_URL, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for v in data["versions"]:
                if v["id"] == version:
                    return v
            return None
        except:
            return None
    
    @staticmethod
    def get_versions():
        try:
            resp = requests.get(VERSION_MANIFEST_URL, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            versions = []
            seen = set()
            for v in data["versions"]:
                vid = v["id"]
                if "snapshot" not in vid and vid not in seen:
                    versions.append(vid)
                    seen.add(vid)
            return versions[:60]
        except:
            return ["1.20.4", "1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5"]
    
    @staticmethod
    def download_server(version, callback=None):
        server_jar = Path(SERVER_DIR) / "server.jar"
        if server_jar.exists():
            if callback:
                callback("✅ 服务端已存在，跳过下载")
            return True
        
        try:
            info = ServerManager.get_version_info(version)
            if not info:
                if callback:
                    callback(f"❌ 找不到版本 {version}")
                return False
            
            url = info.get("url")
            if not url:
                if callback:
                    callback(f"❌ 版本 {version} 没有下载链接")
                return False
            
            if callback:
                callback(f"📡 从 Mojang 官方源下载 {version}...")
            
            Path(SERVER_DIR).mkdir(exist_ok=True)
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_percent = 0
            
            with open(server_jar, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            if percent - last_percent >= 10:
                                last_percent = percent
                                if callback:
                                    callback(f"⬇️ 下载进度: {percent:.1f}%")
            
            if callback:
                callback(f"✅ 服务端 {version} 下载完成!")
            return True
            
        except Exception as e:
            if callback:
                callback(f"❌ 服务端下载失败: {str(e)}")
            return False

# ==================== 核心启动器 ====================
class ServerLauncher:
    def __init__(self):
        self.process = None
        self.running = False
        self.log_callback = None
        self.status_callback = None
        self._stop_flag = False
    
    def set_callbacks(self, log_cb, status_cb):
        self.log_callback = log_cb
        self.status_callback = status_cb
    
    def log(self, msg):
        if self.log_callback:
            self.log_callback(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def set_status(self, status):
        if self.status_callback:
            self.status_callback(status)
    
    def launch(self, version, memory, online_mode, frp_enabled):
        java_path = JavaManager.get_java_path()
        if not java_path:
            self.log("❌ 错误: 未找到Java，请先安装")
            return False
        
        server_jar = Path(SERVER_DIR) / "server.jar"
        if not server_jar.exists():
            self.log("❌ 错误: 未找到server.jar，请先下载")
            return False
        
        if is_port_in_use(25565):
            self.log("⚠️ 警告: 端口25565已被占用")
        
        # 生成 eula.txt
        eula_path = Path(SERVER_DIR) / "eula.txt"
        if not eula_path.exists():
            with open(eula_path, 'w', encoding='utf-8') as f:
                f.write("eula=true\n")
        
        # 生成 server.properties
        props_path = Path(SERVER_DIR) / "server.properties"
        if not props_path.exists():
            with open(props_path, 'w', encoding='utf-8') as f:
                f.write(f"online-mode={str(online_mode).lower()}\n")
                f.write("server-port=25565\n")
                f.write("max-players=20\n")
                f.write(f"motd=一键开服v1.0 - 关注B站:{AUTHOR}\n")
        
        # 构建启动命令
        cmd = [
            java_path,
            f"-Xmx{memory}M",
            f"-Xms{min(1024, memory)}M",
            "-XX:+UseG1GC",
            "-jar",
            str(server_jar),
            "nogui"
        ]
        
        self.log(f"🚀 启动命令: java -Xmx{memory}M -jar server.jar nogui")
        self.log(f"🔐 正版验证: {'开启' if online_mode else '关闭'}")
        self.log(f"📺 关注B站: {AUTHOR}")
        
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=SERVER_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            self.running = True
            self._stop_flag = False
            self.set_status("🟢 运行中")
            
            threading.Thread(target=self._read_output, daemon=True).start()
            threading.Thread(target=self._monitor_process, daemon=True).start()
            
            if frp_enabled:
                self.log("🔗 内网穿透已启用 (请自行配置 frp)")
            
            return True
            
        except Exception as e:
            self.log(f"❌ 启动失败: {str(e)}")
            self.set_status("❌ 启动失败")
            return False
    
    def _read_output(self):
        while self.running and self.process and not self._stop_flag:
            try:
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        self.log(line.strip())
                    else:
                        break
                else:
                    break
            except:
                break
        if self.process and self.running:
            self.running = False
            self.set_status("🔴 已停止")
            self.log("⏹️ 服务器已停止")
    
    def _monitor_process(self):
        while self.running and self.process:
            time.sleep(5)
            if self.process and self.process.poll() is not None:
                self.running = False
                self.set_status("💀 已崩溃")
                self.log("💀 服务器进程意外退出！")
                break
    
    def stop(self):
        self._stop_flag = True
        if self.process and self.running:
            self.log("⏹️ 正在停止服务器...")
            try:
                self.process.terminate()
                for _ in range(10):
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.5)
                if self.process.poll() is None:
                    self.process.kill()
                    self.log("⚠️ 强制终止进程")
                self.running = False
                self.set_status("🔴 已停止")
                self.log("✅ 服务器已安全停止")
            except Exception as e:
                self.log(f"停止服务器异常: {e}")

# ==================== GUI界面 ====================
class MinecraftServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Minecraft一键开服v1.0 - {AUTHOR}")
        self.root.geometry("720x650")
        self.root.minsize(600, 500)
        
        self.version_var = tk.StringVar(value="1.20.4")
        self.memory_var = tk.StringVar(value=str(DEFAULT_MEMORY))
        self.online_var = tk.BooleanVar(value=False)
        self.frp_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="⚪ 未启动")
        
        self.launcher = ServerLauncher()
        self.launcher.set_callbacks(self.log_message, self.update_status)
        
        self._build_ui()
        self._load_config()
        self._check_java()
        self._refresh_versions()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _build_ui(self):
        # 头部
        header = ttk.LabelFrame(self.root, text="⭐ v1.0 | 求关注", padding=10)
        header.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(header, text="🎮 Minecraft 一键开服器 v1.0", font=("", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(header, text=f"作者: {AUTHOR} | B站: 夕阳再升void (UID: {BILIBILI_UID})", font=("", 9)).pack(anchor=tk.W)
        ttk.Button(header, text="👉 去B站关注", command=self._open_bilibili).pack(anchor=tk.W, pady=2)
        ttk.Label(header, text="⚠️ 请勿修改脚本所在目录结构！", foreground="red").pack(anchor=tk.W)
        
        # 配置区
        config_frame = ttk.LabelFrame(self.root, text="⚙️ 服务器配置", padding=15)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X, pady=4)
        ttk.Label(row1, text="📦 游戏版本:").pack(side=tk.LEFT)
        self.version_combo = ttk.Combobox(row1, textvariable=self.version_var, width=20, state="readonly")
        self.version_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="🔄 刷新", command=self._refresh_versions).pack(side=tk.LEFT, padx=5)
        
        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, pady=4)
        ttk.Label(row2, text="💾 内存 (MB):").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.memory_var, width=10).pack(side=tk.LEFT, padx=5)
        for m in [1024, 2048, 4096]:
            ttk.Button(row2, text=str(m), width=5, command=lambda v=m: self.memory_var.set(str(v))).pack(side=tk.LEFT, padx=2)
        
        row3 = ttk.Frame(config_frame)
        row3.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(row3, text="🔐 正版验证", variable=self.online_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(row3, text="🔗 内网穿透", variable=self.frp_var).pack(side=tk.LEFT, padx=10)
        
        row4 = ttk.Frame(config_frame)
        row4.pack(fill=tk.X, pady=4)
        ttk.Label(row4, text="📊 状态:").pack(side=tk.LEFT)
        ttk.Label(row4, textvariable=self.status_var, font=("", 11, "bold")).pack(side=tk.LEFT, padx=5)
        self.java_label = ttk.Label(row4, text="", font=("", 8), foreground="gray")
        self.java_label.pack(side=tk.RIGHT)
        
        # 控制按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        self.start_btn = ttk.Button(btn_frame, text="🚀 启动", command=self._start_server, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="⏹️ 停止", command=self._stop_server, width=12, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📁 目录", command=self._open_folder, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⚙️ 配置", command=self._edit_config, width=10).pack(side=tk.LEFT, padx=5)
        
        # 日志区
        log_frame = ttk.LabelFrame(self.root, text="📋 控制台日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
    
    def _open_bilibili(self):
        try:
            webbrowser.open(BILIBILI_URL)
            self.log_message("📺 已打开B站主页，记得关注哦~")
        except:
            self.log_message("❌ 无法打开浏览器")
    
    def _refresh_versions(self):
        self.log_message("🔄 正在获取版本列表...")
        threading.Thread(target=self._do_refresh_versions, daemon=True).start()
    
    def _do_refresh_versions(self):
        versions = ServerManager.get_versions()
        self.root.after(0, lambda: self.version_combo.configure(values=versions))
        self.root.after(0, lambda: self.log_message(f"✅ 已加载 {len(versions)} 个版本"))
        if self.version_var.get() not in versions and versions:
            self.root.after(0, lambda: self.version_var.set(versions[0]))
    
    def _check_java(self):
        java_path = JavaManager.get_java_path()
        if java_path:
            version = JavaManager.get_java_version()
            self.log_message(f"✅ 已找到Java: {version}")
            self.java_label.config(text=f"Java: {version[:30]}...")
            self.update_status("✅ 就绪")
        else:
            self.log_message("⚠️ 未找到Java，点击启动将自动下载")
            self.java_label.config(text="⚠️ Java未安装")
            self.update_status("🔧 需要Java")
    
    def _load_config(self):
        config = ConfigManager.load()
        if config:
            self.version_var.set(config.get("version", "1.20.4"))
            self.memory_var.set(str(config.get("memory", DEFAULT_MEMORY)))
            self.online_var.set(config.get("online_mode", False))
            self.frp_var.set(config.get("frp_enabled", False))
    
    def _save_config(self):
        memory = int(self.memory_var.get()) if self.memory_var.get().isdigit() else DEFAULT_MEMORY
        ConfigManager.save({
            "version": self.version_var.get(),
            "memory": memory,
            "online_mode": self.online_var.get(),
            "frp_enabled": self.frp_var.get()
        })
    
    def log_message(self, msg):
        self.root.after(0, self._do_log, msg)
    
    def _do_log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_status(self, status):
        self.root.after(0, lambda: self.status_var.set(status))
    
    def _start_server(self):
        version = self.version_var.get()
        memory_str = self.memory_var.get().strip()
        if not memory_str.isdigit():
            messagebox.showerror("错误", "内存请输入有效数字!")
            return
        memory = int(memory_str)
        if memory < MIN_MEMORY or memory > MAX_MEMORY:
            messagebox.showerror("错误", f"内存范围: {MIN_MEMORY}-{MAX_MEMORY} MB")
            return
        
        self._save_config()
        
        java_path = JavaManager.get_java_path()
        if not java_path:
            self.log_message("📥 正在下载Java...")
            self.start_btn.config(state=tk.DISABLED)
            def download_done():
                if JavaManager.download_java(self.log_message, self.root):
                    self.log_message("✅ Java安装完成!")
                    self.root.after(0, lambda: self._do_start_server(version, memory))
                else:
                    self.log_message("❌ Java安装失败")
                    self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            threading.Thread(target=download_done, daemon=True).start()
            return
        
        self._do_start_server(version, memory)
    
    def _do_start_server(self, version, memory):
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        online_mode = self.online_var.get()
        frp_enabled = self.frp_var.get()
        
        def launch_thread():
            if not ServerManager.download_server(version, self.log_message):
                self.root.after(0, self._reset_buttons)
                return
            success = self.launcher.launch(version, memory, online_mode, frp_enabled)
            if not success:
                self.root.after(0, self._reset_buttons)
        threading.Thread(target=launch_thread, daemon=True).start()
    
    def _stop_server(self):
        self.stop_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.launcher.stop, daemon=True).start()
        self._reset_buttons()
    
    def _reset_buttons(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def _open_folder(self):
        try:
            Path(SERVER_DIR).mkdir(exist_ok=True)
            os.startfile(safe_path(SERVER_DIR))
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {e}")
    
    def _edit_config(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑 server.properties")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text="📝 编辑配置文件 (保存后重启生效)").pack(pady=5)
        text = scrolledtext.ScrolledText(dialog, height=15, font=("Consolas", 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        prop_path = Path(SERVER_DIR) / "server.properties"
        if prop_path.exists():
            with open(prop_path, 'r', encoding='utf-8') as f:
                text.insert(tk.END, f.read())
        else:
            text.insert(tk.END, "# 服务器配置\n")
        
        def save_config():
            try:
                with open(prop_path, 'w', encoding='utf-8') as f:
                    f.write(text.get(1.0, tk.END))
                messagebox.showinfo("成功", "✅ 配置已保存")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")
        ttk.Button(dialog, text="💾 保存", command=save_config).pack(pady=10)
    
    def _on_close(self):
        if self.launcher.running:
            if messagebox.askyesno("确认", "服务器正在运行，确定退出吗？"):
                self.launcher.stop()
                self.root.destroy()
        else:
            self.root.destroy()

# ==================== 主程序 ====================
def main():
    app = MinecraftServerGUI()
    app.root.mainloop()

if __name__ == "__main__":
    main()
