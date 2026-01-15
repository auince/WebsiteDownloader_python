import os
import shutil
import time
import logging
from pathlib import Path
from typing import Union

class FileManager:
    """
    文件系统管理器
    负责初始化目录结构、清理过期文件以及安全路径检查。
    解决了原项目 "Known Issues #2: Storage management" 的问题。
    """

    def __init__(self, base_storage_path: str = "storage"):
        # 使用 pathlib 处理路径更安全
        self.root = Path(base_storage_path)
        self.temp_dir = self.root / "temp_sites"
        self.zip_dir = self.root / "output_zips"
        
        # 初始化日志
        self.logger = logging.getLogger("FileManager")

    def initialize(self):
        """初始化存储目录结构"""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.zip_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Storage initialized at: {self.root.absolute()}")

    def cleanup_old_files(self, max_age_minutes: int = 60):
        """
        清理过期的 ZIP 文件，防止磁盘爆满。
        
        Args:
            max_age_minutes: 文件保留的最长时间（分钟），默认 60 分钟
        """
        if not self.zip_dir.exists():
            return

        current_time = time.time()
        age_seconds = max_age_minutes * 60
        count = 0

        try:
            for file_path in self.zip_dir.glob("*.zip"):
                # 获取文件最后修改时间
                file_age = current_time - file_path.stat().st_mtime
                
                if file_age > age_seconds:
                    try:
                        file_path.unlink()  # 删除文件
                        count += 1
                        self.logger.info(f"Deleted expired file: {file_path.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete {file_path.name}: {e}")
            
            if count > 0:
                print(f"[FileManager] Cleaned up {count} expired ZIP files.")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def clear_temp_folder(self, folder_path: Union[str, Path]):
        """
        强制删除指定的临时文件夹（用于下载完成后清理源码，只保留 ZIP）
        """
        path = Path(folder_path)
        
        # 安全检查：确保要删除的路径在 temp_dir 之内，防止误删系统文件
        # resolve() 获取绝对路径进行比较
        try:
            if self.temp_dir.resolve() in path.resolve().parents:
                if path.exists() and path.is_dir():
                    shutil.rmtree(path)
                    self.logger.info(f"Removed temp folder: {path.name}")
            else:
                self.logger.warning(f"Security Warning: Attempted to delete outside temp dir: {path}")
        except Exception as e:
            self.logger.error(f"Failed to clear temp folder {path}: {e}")

    def get_paths(self):
        """返回路径配置，供其他模块使用"""
        return {
            "root": str(self.root),
            "temp": str(self.temp_dir),
            "zip": str(self.zip_dir)
        }