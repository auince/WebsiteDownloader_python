import subprocess
import os
import signal
from typing import Generator, Tuple, Optional
from urllib.parse import urlparse
from utils.file_manager import FileManager

class WgetEngine:
    """
    核心下载引擎 (更新版)
    集成 FileManager 进行路径管理和清理
    """
    
    def __init__(self, file_manager: FileManager):
        """
        Args:
            file_manager: 初始化的 FileManager 实例
        """
        self.fm = file_manager
        self.paths = self.fm.get_paths()
        self.base_dir = self.paths['temp']
        
        self.process: Optional[subprocess.Popen] = None
        self.current_website_dir: Optional[str] = None

    def _get_domain_from_url(self, url: str) -> str:
        """从 URL 解析域名"""
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        return domain.split(':')[0]

    def download(self, url: str) -> Generator[Tuple[str, Optional[str]], None, None]:
        """
        执行 wget 下载
        Yields: (log_line, completed_folder_path)
        """
        
        # 1. 确定目标路径
        domain = self._get_domain_from_url(url)
        self.current_website_dir = os.path.join(self.base_dir, domain)

        # 2. 清理旧数据 (使用 FileManager 的安全清理)
        if os.path.exists(self.current_website_dir):
            yield f"[Engine] Cleaning old directory: {domain}...\n", None
            self.fm.clear_temp_folder(self.current_website_dir)

        # 3. 构建 wget 命令
        cmd = [
            "wget",
            "-m", "-k", "-E", "-p", "-np",
            "--no-if-modified-since",
            "-P", self.base_dir,  # 使用 FileManager 提供的统一临时目录
            url
        ]

        yield f"[Engine] Starting download for: {domain}\n", None
        yield f"[Engine] Command: {' '.join(cmd)}\n", None

        try:
            # 4. 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )

            # 5. 实时流式输出
            while True:
                line = self.process.stderr.readline()
                if line:
                    yield line, None
                
                if self.process.poll() is not None:
                    remaining = self.process.stderr.read()
                    if remaining:
                        yield remaining, None
                    break

            # 6. 处理结果
            return_code = self.process.poll()
            
            if return_code == 0 and os.path.exists(self.current_website_dir):
                yield f"\n[Engine] Download completed successfully.\n", self.current_website_dir
            else:
                yield f"\n[Engine] Error: Process exited with code {return_code}.\n", None
                self.cleanup_partial_files()

        except Exception as e:
            yield f"\n[Engine] Critical Exception: {str(e)}\n", None
            self.cleanup_partial_files()
        finally:
            self.process = None

    def stop(self):
        """强制停止并清理"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self.process = None
                self.cleanup_partial_files()

    def cleanup_partial_files(self):
        """调用 FileManager 进行安全清理"""
        if self.current_website_dir:
            self.fm.clear_temp_folder(self.current_website_dir)