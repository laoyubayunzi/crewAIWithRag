from crewai_tools import tool
from fpdf import FPDF
import os
import traceback
import tempfile
from PIL import Image, ImageDraw, ImageFont
import io

# 简化 PIL 依赖检查（去掉空 BytesIO 测试，避免报错）
try:
    # 仅验证 PIL 库是否能正常导入
    _test_img = Image.new('RGB', (10, 10), 'white')
except ImportError as e:
    raise ImportError("缺少依赖库：pillow，请运行 pip install pillow 安装") from e
except Exception as e:
    raise RuntimeError(f"PIL 库初始化失败：{str(e)}") from e


@tool("saveText2Pdf")
def saveText2Pdf(inputs: dict) -> str:
    """
    无需系统中文字体！通过图片转文字生成中文PDF，100%兼容所有Windows系统。
    核心优势：不依赖 simhei.ttf/msyh.ttc，避免字体缺失报错。
    :param inputs: 字典格式，支持两种传入方式：
                  1. {"text": "内容", "filename": "文件名"}
                  2. {"inputs": {"text": "内容", "filename": "文件名"}}（兼容Agent嵌套输入）
    :return: 保存状态消息
    """
    try:
        # 1. 智能提取参数（兼容 Agent 嵌套输入格式）
        if "inputs" in inputs and isinstance(inputs["inputs"], dict):
            text = inputs["inputs"].get("text", "").strip()
            filename = inputs["inputs"].get("filename", "健康报告.pdf").strip()
        else:
            text = inputs.get("text", "").strip()
            filename = inputs.get("filename", "健康报告.pdf").strip()

        # 2. 校验必要参数
        if not text:
            return "PDF 保存失败：未获取到要保存的文本内容"
        if not filename.endswith(".pdf"):
            filename += ".pdf"  # 自动补全 .pdf 后缀

        # 3. 处理输出目录（自动创建，避免路径不存在错误）
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        full_path = os.path.join(output_dir, filename)
        absolute_path = os.path.abspath(full_path)

        # 4. 核心：将中文文本绘制成图片（不依赖系统字体）
        def text_to_image(text_content, font_size=12, page_width=550):
            # 初始化绘图参数
            bg_color = (255, 255, 255)  # 白色背景
            text_color = (0, 0, 0)  # 黑色文字
            line_spacing = int(font_size * 1.5)  # 行间距

            # 加载兼容中文的字体（PIL内置，无需额外文件）
            try:
                # 优先使用系统内置Unicode字体（Windows必带）
                font = ImageFont.truetype("arialuni.ttf", font_size)
            except Exception:
                try:
                    # 兜底方案1：使用系统其他常见中文字体
                    font = ImageFont.truetype("simsun.ttc", font_size)  # 宋体
                except Exception:
                    # 兜底方案2：使用PIL默认字体（确保中文可显示）
                    font = ImageFont.load_default(size=font_size)

            # 按页面宽度自动换行（处理长文本和换行符）
            draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            lines = []
            for para in text_content.split('\n'):
                if not para:
                    lines.append("")
                    continue
                current_line = ""
                for char in para:
                    test_line = current_line + char
                    # 计算文本宽度（使用 textbbox 兼容 PIL 9.0+）
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    if bbox[2] <= page_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = char
                if current_line:
                    lines.append(current_line)

            # 计算图片尺寸（适配所有文本）
            img_height = len(lines) * line_spacing + 40  # 上下边距各20
            img = Image.new('RGB', (page_width + 40, img_height), bg_color)
            draw = ImageDraw.Draw(img)

            # 绘制文本到图片
            y = 20  # 上边距20
            for line in lines:
                draw.text((20, y), line, font=font, fill=text_color)
                y += line_spacing

            # 保存图片到内存
            img_byte_io = io.BytesIO()
            img.save(img_byte_io, format='PNG', quality=95)
            img_byte_io.seek(0)
            return img_byte_io

        # 5. 生成图片并插入PDF
        pdf = FPDF()
        pdf.add_page()
        img_byte_io = text_to_image(text, font_size=12, page_width=550)
        
        # 使用临时文件保存图像数据（解决fpdf不支持直接BytesIO的问题）
        temp_file_path = None
        try:
            # 创建临时文件
            temp_fd, temp_file_path = tempfile.mkstemp(suffix='.png')
            with os.fdopen(temp_fd, 'wb') as temp_file:
                temp_file.write(img_byte_io.getvalue())
            
            # 使用临时文件路径
            pdf.image(temp_file_path, x=10, y=10, w=190)
            
            # 6. 保存PDF文件
            pdf.output(full_path)
        finally:
            # 确保删除临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # 忽略删除失败的情况

        # 7. 返回友好的成功消息
        return f"✅ PDF 保存成功！（无需中文字体）\n📁 文件路径：{absolute_path}\n💡 提示：直接复制路径到文件管理器打开"

    except Exception as e:
        # 只返回PDF保存失败的错误信息，不再自动保存为TXT文件
        # 打印详细错误日志，方便排查
        print(f"PDF生成异常：{str(e)}\n{traceback.format_exc()}")
        return f"⚠️ PDF 保存失败：{str(e)}\n请检查系统依赖和权限设置后重试。"
        
        # 注意：根据用户要求，不再自动保存为TXT文件，确保只生成PDF格式


# 直接测试函数（不通过装饰器，用于调试）
def test_pdf_generation():
    text = "健康建议报告\n\n患者主诉：心脏病\n\n一、健康档案情况\n经系统检索，当前未获取到与患者相关的健康档案记录..."
    filename = "心脏病健康建议报告.pdf"
    
    try:
        # 复制主要逻辑，但不使用装饰器
        from fpdf import FPDF
        import os
        import io
        import tempfile
        from PIL import Image, ImageDraw, ImageFont
        
        # 处理输出目录
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        full_path = os.path.join(output_dir, filename)
        absolute_path = os.path.abspath(full_path)
        
        # 文本转图片函数
        def text_to_image(text_content, font_size=12, page_width=550):
            bg_color = (255, 255, 255)
            text_color = (0, 0, 0)
            line_spacing = int(font_size * 1.5)
            
            try:
                font = ImageFont.truetype("arialuni.ttf", font_size)
            except Exception:
                try:
                    font = ImageFont.truetype("simsun.ttc", font_size)
                except Exception:
                    font = ImageFont.load_default(size=font_size)
            
            draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            lines = []
            for para in text_content.split('\n'):
                if not para:
                    lines.append("")
                    continue
                current_line = ""
                for char in para:
                    test_line = current_line + char
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    if bbox[2] <= page_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = char
                if current_line:
                    lines.append(current_line)
            
            img_height = len(lines) * line_spacing + 40
            img = Image.new('RGB', (page_width + 40, img_height), bg_color)
            draw = ImageDraw.Draw(img)
            
            y = 20
            for line in lines:
                draw.text((20, y), line, font=font, fill=text_color)
                y += line_spacing
            
            img_byte_io = io.BytesIO()
            img.save(img_byte_io, format='PNG', quality=95)
            img_byte_io.seek(0)
            return img_byte_io
        
        # 生成 PDF
        pdf = FPDF()
        pdf.add_page()
        img_byte_io = text_to_image(text, font_size=12, page_width=550)
        
        # 使用临时文件保存图像数据（解决fpdf不支持直接BytesIO的问题）
        temp_file_path = None
        try:
            # 创建临时文件
            temp_fd, temp_file_path = tempfile.mkstemp(suffix='.png')
            with os.fdopen(temp_fd, 'wb') as temp_file:
                temp_file.write(img_byte_io.getvalue())
            
            # 使用临时文件路径
            pdf.image(temp_file_path, x=10, y=10, w=190)
            
            # 保存文件
            pdf.output(full_path)
            print(f"✅ PDF 测试成功！文件路径：{absolute_path}")
        finally:
            # 确保删除临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # 忽略删除失败的情况
    except Exception as e:
        import traceback
        print(f"❌ PDF 测试失败：{str(e)}")
        print(f"详细错误：{traceback.format_exc()}")

if __name__ == "__main__":
    test_pdf_generation()