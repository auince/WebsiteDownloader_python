import re
from typing import Tuple, Optional

class LogParser:
    """
    日志解析器
    负责解析 wget 的原始 stderr 输出，提取关键指标（文件计数、状态）
    并生成适合人类阅读的日志格式。
    """

    def __init__(self):
        self.downloaded_count = 0
        self.error_count = 0
        
        # 预编译正则提高性能
        # 匹配成功保存：... ‘filename’ saved [size/size]
        self.saved_pattern = re.compile(r"‘.+’ saved \[\d+/\d+\]")
        # 匹配 200 OK (另一种成功标志)
        self.ok_pattern = re.compile(r"\s200 OK$")
        # 匹配常见错误
        self.error_pattern = re.compile(r"(ERROR \d+|failed:|Not Found)", re.IGNORECASE)

    def process_line(self, line: str) -> Tuple[str, dict]:
        """
        处理一行原始日志
        
        Args:
            line: wget 输出的一行原始文本
            
        Returns:
            Tuple[str, dict]: 
                - clean_log: 清理后适合展示的日志行（如果是无关紧要的空行则为空字符串）
                - stats: 当前的统计数据字典 {'files': int, 'errors': int}
        """
        line = line.strip()
        if not line:
            return "", self._get_stats()

        # 1. 检测文件下载成功
        # wget 输出通常包含 "saved [bytes/bytes]" 表示写入磁盘完成
        if self.saved_pattern.search(line):
            self.downloaded_count += 1
            # 可以给这行日志加个高亮标记（在 Gradio Markdown 中显示）
            clean_log = f"✅ FILE SAVED: {self._extract_filename(line)}"
        
        # 2. 检测错误
        elif self.error_pattern.search(line):
            self.error_count += 1
            clean_log = f"❌ ERROR: {line}"
            
        # 3. 过滤/格式化其他常见状态
        elif line.startswith("Resolving "):
            clean_log = f"🔄 {line}"
        elif line.startswith("Connecting to "):
            clean_log = f"🔗 {line}"
        elif "200 OK" in line:
            # 200 OK 有时出现在 saved 之前，作为进度提示
            clean_log = f"⬇️  Response: 200 OK" 
        elif line.startswith("Saving to:"):
            # 简化显示，去掉冗长的路径
            filename = self._extract_filename(line)
            clean_log = f"💾 Saving: {filename}..."
        else:
            # 其他日志保持原样，或者选择忽略以减少刷屏
            # 这里我们选择保留，但缩进一下区分
            clean_log = f"   {line}"

        return f"{clean_log}\n", self._get_stats()

    def _extract_filename(self, line: str) -> str:
        """从日志行中尝试提取文件名，仅用于展示"""
        try:
            # 尝试查找引号中的内容 ‘path/to/file’
            start = line.find("‘")
            end = line.find("’")
            if start != -1 and end != -1:
                full_path = line[start+1:end]
                # 只返回文件名，不显示长路径
                return full_path.split('/')[-1]
            return "file"
        except:
            return "file"

    def _get_stats(self) -> dict:
        return {
            "files": self.downloaded_count,
            "errors": self.error_count
        }

    def reset(self):
        """重置统计数据"""
        self.downloaded_count = 0
        self.error_count = 0