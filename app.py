import gradio as gr
import logging
from core.engine import WgetEngine
from core.zipper import ZipEngine
from utils.parser import LogParser
from utils.file_manager import FileManager

# --- 配置部分 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("App")

# 初始化全局资源管理器
global_fm = FileManager()
global_fm.initialize()
global_fm.cleanup_old_files(max_age_minutes=60)

# --- 核心逻辑 ---
def process_download(url: str):
    """
    核心处理函数：保持原逻辑不变
    """
    if not url.startswith("http"):
        yield "❌ Error: Please enter a valid URL (http/https).", 0, 0, None, "Invalid URL"
        return

    fm = FileManager()
    engine = WgetEngine(fm)
    zipper = ZipEngine(fm)
    parser = LogParser()

    full_log = ""
    yield "🚀 Initializing download engine...\n", 0, 0, None, "Starting..."

    try:
        # 阶段 1: 下载
        downloaded_folder = None
        for raw_line, folder_path in engine.download(url):
            clean_line, stats = parser.process_line(raw_line)
            if clean_line:
                full_log += clean_line
            if folder_path:
                downloaded_folder = folder_path
            
            yield (full_log, stats['files'], stats['errors'], None, "⬇️ Downloading...")

        # 阶段 2: 压缩
        if downloaded_folder:
            full_log += "\n📦 Compressing files... This may take a moment.\n"
            yield full_log, stats['files'], stats['errors'], None, "📦 Compressing..."
            
            try:
                zip_path = zipper.compress(downloaded_folder)
                full_log += f"\n✅ Compression Complete! File ready: {zip_path}\n"
                fm.clear_temp_folder(downloaded_folder)
                yield (full_log, stats['files'], stats['errors'], zip_path, "✅ Done!")
            except Exception as z_err:
                full_log += f"\n❌ Compression Error: {str(z_err)}\n"
                yield full_log, stats['files'], stats['errors'], None, "❌ Error"
        else:
            full_log += "\n❌ Download failed or directory empty.\n"
            yield full_log, stats['files'], stats['errors'], None, "❌ Failed"

    except Exception as e:
        full_log += f"\n❌ Critical Application Error: {str(e)}\n"
        yield full_log, 0, 0, None, "❌ Error"
    finally:
        engine.stop()

# --- 前端设计 (UI/UX) ---

# 1. 自定义 CSS
# 优化终端显示：增加行高、使用等宽字体、圆角、阴影
custom_css = """
/* 强制隐藏默认 Footer */
footer {display: none !important;}

/* 终端样式优化 */
#log_box textarea {
    font-family: 'JetBrains Mono', 'Consolas', monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important; /* 增加行间距提高可读性 */
    background-color: #1e1e1e !important;
    color: #4ade80 !important; /* 更柔和的绿色 */
    border: 1px solid #374151 !important;
    border-radius: 8px !important;
    padding: 15px !important;
    box-shadow: inset 0 2px 4px 0 rgb(0 0 0 / 0.25);
}

/* 状态卡片样式 */
.stat-card {
    border: 1px solid #e5e7eb;
    background: white;
    border-radius: 8px;
    padding: 10px;
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

/* 下载按钮区域增强 */
.download-area {
    background-color: #f0fdf4;
    border: 1px dashed #22c55e;
    border-radius: 8px;
}
"""

# 2. 自动滚动 JS
# 每当 log_box 内容变化时触发，强制滚动到底部
scroll_js = """
() => {
    const el = document.querySelector('#log_box textarea');
    if (el) {
        el.scrollTop = el.scrollHeight;
    }
}
"""

# 3. 创建自定义主题
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="indigo",
    text_size="lg",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui"], # 主字体
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"], # 代码字体
).set(
    body_background_fill="white",
    block_background_fill="white",
    block_border_width="1px",
    input_background_fill="#f9fafb",
)

with gr.Blocks(title="Website Downloader Pro", css=custom_css, theme=theme) as app:
    
    # 标题区
    with gr.Row():
        gr.Markdown(
            """
            # 🌐 Website Downloader
            ### Python Edition
            Enter a URL to recursively download the website assets and receive a ZIP archive.
            """
        )

    # 输入与控制区
    with gr.Group():
        with gr.Row():
            with gr.Column(scale=4):
                url_input = gr.Textbox(
                    label="Target Website URL", 
                    placeholder="https://example.com",
                    max_lines=1,
                    show_label=True
                )
            with gr.Column(scale=1):
                start_btn = gr.Button("🚀 Start Download", variant="primary", scale=1, size='lg')
                stop_btn = gr.Button("🛑 Stop", variant="stop", scale=1, size='lg')

    # 状态仪表盘 (使用 Group 增加视觉聚合感)
    with gr.Row(elem_classes="stat-row"):
        with gr.Column(scale=1, elem_classes="stat-card"):
            status_label = gr.Label(value="Ready", label="Current Status", show_label=True)
        with gr.Column(scale=1, elem_classes="stat-card"):
            file_count = gr.Number(value=0, label="Files Downloaded", show_label=True)
        with gr.Column(scale=1, elem_classes="stat-card"):
            error_count = gr.Number(value=0, label="Errors (404/Fail)", show_label=True)

    # 日志与下载区
    with gr.Row():
        with gr.Column(scale=3):
            # 将 autoscroll 设为 False，完全交由 JS 控制，防止冲突
            log_box = gr.TextArea(
                label="Terminal Log (Real-time)", 
                elem_id="log_box", 
                lines=18, 
                max_lines=18,
                interactive=False,
                autoscroll=False 
            )
        with gr.Column(scale=1):
            with gr.Group(elem_classes="download-area"):
                gr.Markdown("### 📥 Output")
                download_file = gr.File(label="Download ZIP", interactive=False, file_count="single")

    # --- 事件绑定 ---

    # 1. 启动下载
    download_event = start_btn.click(
        fn=process_download,
        inputs=[url_input],
        outputs=[log_box, file_count, error_count, download_file, status_label],
        concurrency_limit=2
    )

    # 2. 停止下载
    stop_btn.click(fn=None, cancels=[download_event])

    # 3. **关键修改**: 监听日志框的变化，触发 JS 滚动到底部
    log_box.change(fn=None, js=scroll_js)

    gr.Markdown("---")
    gr.Markdown("*Note: This tool respects `robots.txt` effectively but uses `wget` user-agent. Please use responsibly.*")

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, auth=("newmeng2", "uestc"))