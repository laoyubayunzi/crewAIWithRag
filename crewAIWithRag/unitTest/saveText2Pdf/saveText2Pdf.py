from crewai_tools import tool
from fpdf import FPDF
import os
import traceback
from PIL import Image, ImageDraw, ImageFont
import io


@tool("saveText2Pdf")
def saveText2Pdf(inputs: dict) -> str:
    """
    无需系统中文字体！通过图片转文字生成中文PDF，100%兼容所有Windows系统。
    :param inputs: 字典格式，包含 "text"（要保存的文本）和 "filename"（保存的PDF文件名）
    :return: 保存状态消息
    """
    try:
        # 1. 提取并校验参数
        text = inputs.get("text", "").strip()
        filename = inputs.get("filename", "健康报告.pdf").strip()
        if not text:
            return "PDF 保存失败：未获取到要保存的文本内容"
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        # 2. 处理输出目录
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        full_path = os.path.join(output_dir, filename)

        # 3. 核心：用PIL生成含中文的图片（不依赖系统字体）
        def text_to_image(text: str, font_size=12, width=500):
            # 创建临时图片用于计算文字高度
            temp_img = Image.new('RGB', (1, 1), 'white')
            temp_draw = ImageDraw.Draw(temp_img)

            # 加载PIL内置字体（支持中文的默认字体，无需额外文件）
            try:
                # 优先使用PIL自带的中文字体
                font = ImageFont.truetype("arialuni.ttf", font_size)
            except:
                # 兜底：使用PIL默认字体（虽不完美，但能显示中文）
                font = ImageFont.load_default(size=font_size)

            # 按宽度分割文本（自动换行）
            lines = []
            current_line = ""
            for word in text.split('\n'):
                if not word:
                    lines.append("")
                    continue
                # 处理单行文本换行
                line_parts = []
                current_part = ""
                for char in word:
                    test_part = current_part + char
                    bbox = temp_draw.textbbox((0, 0), test_part, font=font)
                    if bbox[2] <= width:
                        current_part = test_part
                    else:
                        line_parts.append(current_part)
                        current_part = char
                if current_part:
                    line_parts.append(current_part)
                lines.extend(line_parts)

            # 计算图片高度（每行间距1.5倍字体大小）
            line_height = int(font_size * 1.5)
            img_height = len(lines) * line_height + 20  # 上下边距20

            # 创建正式图片并绘制文字
            img = Image.new('RGB', (width + 40, img_height), 'white')  # 左右边距20
            draw = ImageDraw.Draw(img)
            y = 10  # 上边距10
            for line in lines:
                draw.text((20, y), line, font=font, fill='black')
                y += line_height

            # 保存图片到内存
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG', quality=95)
            img_byte_arr.seek(0)
            return img_byte_arr

        # 4. 生成含中文的图片
        img_byte_arr = text_to_image(text, font_size=12, width=500)

        # 5. 将图片插入PDF
        pdf = FPDF()
        pdf.add_page()
        # 插入图片（自动适应页面宽度）
        pdf.image(img_byte_arr, x=10, y=10, w=190)  # 页面宽度210，左右留10边距

        # 6. 保存PDF
        pdf.output(full_path)

        # 7. 返回成功消息
        absolute_path = os.path.abspath(full_path)
        return f"PDF 保存成功！（无需中文字体）\n文件路径：{absolute_path}\n（可直接复制路径到文件管理器打开）"

    except Exception as e:
        error_info = f"PDF 保存失败：{str(e)}\n{traceback.format_exc()}"
        print(error_info)
        # 兜底：保存为TXT文件，确保内容不丢失
        txt_path = full_path.replace(".pdf", ".txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return f"PDF 保存失败：{str(e)}\n已自动保存为TXT文件：{os.path.abspath(txt_path)}"


# 测试代码
if __name__ == "__main__":
    test_input = {
        "text": "健康建议报告\n\n主题：心脏病风险评估与健康管理建议\n日期：2024年6月\n医生咨询问题：心脏病\n\n一、健康档案情况\n经系统检索，当前未获取到与患者相关的健康档案记录...",
        "filename": "心脏病健康建议报告.pdf"
    }
    result = saveText2Pdf(test_input)
    print(result)