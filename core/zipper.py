import shutil
import os
import time
from utils.file_manager import FileManager

class ZipEngine:
    """
    压缩引擎 (更新版)
    集成 FileManager 获取输出路径
    """

    def __init__(self, file_manager: FileManager):
        """
        Args:
            file_manager: 初始化的 FileManager 实例
        """
        self.fm = file_manager
        self.paths = self.fm.get_paths()
        self.output_dir = self.paths['zip']

    def compress(self, source_dir: str) -> str:
        """
        将指定目录打包为 ZIP
        """
        if not os.path.exists(source_dir):
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        # 准备文件名
        base_name = os.path.basename(os.path.normpath(source_dir))
        output_base_path = os.path.join(self.output_dir, base_name)
        
        # 简单的防重名策略
        if os.path.exists(output_base_path + ".zip"):
            timestamp = int(time.time())
            output_base_path = f"{output_base_path}_{timestamp}"

        try:
            # 这里的逻辑保持不变，依然使用 shutil
            parent_dir = os.path.dirname(source_dir)
            target_folder_name = os.path.basename(source_dir)

            zip_path = shutil.make_archive(
                base_name=output_base_path,
                format='zip',
                root_dir=parent_dir,
                base_dir=target_folder_name
            )
            
            return zip_path

        except Exception as e:
            raise Exception(f"Compression failed: {str(e)}")