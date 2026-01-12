# Function
# GUI to covert `Copy as cURL (bash)` from `Chrome DevTools` into python code.
# 
import tkinter as tk
from tkinter import scrolledtext
import re
import json
import shlex


class CurlToPythonConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("cURL to Python 转换工具 (增强版)")
        self.root.geometry("1200x700")
        
        # 创建主框架
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建顶部框架（用于左右两个文本框）
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 配置列权重
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_rowconfigure(1, weight=1)
        
        # 左侧标签和文本框
        left_label = tk.Label(
            top_frame, 
            text="输入 cURL 命令 (Copy as cURL bash):", 
            font=("Arial", 10, "bold")
        )
        left_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=(0, 5))
        
        self.left_text = scrolledtext.ScrolledText(
            top_frame, 
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.left_text.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        # 右侧标签和文本框
        right_label = tk.Label(
            top_frame, 
            text="转换后的 Python 代码:", 
            font=("Arial", 10, "bold")
        )
        right_label.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=(0, 5))
        
        self.right_text = scrolledtext.ScrolledText(
            top_frame, 
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#f5f5f5"
        )
        self.right_text.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        
        # 底部按钮
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        convert_button = tk.Button(
            button_frame,
            text="转化",
            command=self.convert_curl_to_python,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=40,
            pady=10,
            cursor="hand2"
        )
        convert_button.pack()
        
        # 添加示例
        self.add_example()
    
    def add_example(self):
        """添加示例cURL命令"""
        example = """curl 'https://httpbin.org/post' \\
  -H 'accept: application/json' \\
  -H 'content-type: application/json' \\
  -H 'cookie: session_id=abc123; user_token=xyz789' \\
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)' \\
  --data-raw '{"username":"test","password":"123456"}'"""
        self.left_text.insert("1.0", example)
    
    def parse_cookies(self, cookie_string):
        """解析Cookie字符串"""
        cookies = {}
        if not cookie_string:
            return cookies
        
        cookie_parts = cookie_string.split(';')
        for part in cookie_parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        return cookies
    
    def parse_curl_command(self, curl_cmd):
        """解析cURL命令"""
        result = {
            'url': '',
            'method': 'GET',
            'headers': {},
            'cookies': {},
            'data': None,
            'json_data': None
        }
        
        # 清理命令
        curl_cmd = curl_cmd.replace('\\\n', ' ').replace('\\\r\n', ' ')
        curl_cmd = re.sub(r'\s+', ' ', curl_cmd).strip()
        
        if curl_cmd.startswith('curl '):
            curl_cmd = curl_cmd[5:].strip()
        
        # 分割参数
        try:
            parts = shlex.split(curl_cmd)
        except:
            parts = self.simple_split(curl_cmd)
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            # URL
            if not part.startswith('-') and not result['url']:
                result['url'] = part.strip("'\"")
                i += 1
                continue
            
            # 请求方法
            if part in ['-X', '--request']:
                if i + 1 < len(parts):
                    result['method'] = parts[i + 1].upper()
                    i += 2
                    continue
            
            # Headers
            if part in ['-H', '--header']:
                if i + 1 < len(parts):
                    header = parts[i + 1]
                    if ':' in header:
                        key, value = header.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key == 'cookie':
                            result['cookies'] = self.parse_cookies(value)
                        else:
                            result['headers'][key] = value
                    i += 2
                    continue
            
            # Cookie参数
            if part in ['-b', '--cookie']:
                if i + 1 < len(parts):
                    cookies = self.parse_cookies(parts[i + 1])
                    result['cookies'].update(cookies)
                    i += 2
                    continue
            
            # Data
            if part in ['-d', '--data', '--data-raw', '--data-binary']:
                if i + 1 < len(parts):
                    data = parts[i + 1]
                    try:
                        result['json_data'] = json.loads(data)
                    except:
                        result['data'] = data
                    
                    if result['method'] == 'GET':
                        result['method'] = 'POST'
                    i += 2
                    continue
            
            i += 1
        
        return result
    
    def simple_split(self, cmd):
        """简单分割"""
        parts = []
        current = ''
        in_quote = None
        
        for char in cmd:
            if char in ['"', "'"]:
                if in_quote == char:
                    in_quote = None
                elif in_quote is None:
                    in_quote = char
                else:
                    current += char
            elif char == ' ' and in_quote is None:
                if current:
                    parts.append(current)
                    current = ''
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts
    
    def format_dict(self, d, indent=4):
        """格式化字典"""
        if not d:
            return "{}"
        
        items = []
        for key, value in d.items():
            value_escaped = str(value).replace("'", "\\'")
            items.append(f"{' ' * indent}'{key}': '{value_escaped}'")
        return "{\n" + ",\n".join(items) + "\n}"
    
    def generate_python_code(self, parsed):
        """生成Python代码"""
        lines = []
        
        # 导入
        lines.append("import requests")
        if parsed['json_data']:
            lines.append("import json")
        lines.append("")
        
        # URL
        lines.append(f"url = '{parsed['url']}'")
        lines.append("")
        
        # Headers
        if parsed['headers']:
            lines.append(f"headers = {self.format_dict(parsed['headers'])}")
            lines.append("")
        
        # Cookies
        if parsed['cookies']:
            lines.append("# Cookies")
            lines.append(f"cookies = {self.format_dict(parsed['cookies'])}")
            lines.append("")
        
        # 构建请求
        method = parsed['method'].lower()
        params = ["url"]
        
        if parsed['headers']:
            params.append("headers=headers")
        if parsed['cookies']:
            params.append("cookies=cookies")
        
        if method == 'get':
            lines.append("# 发送 GET 请求")
            lines.append(f"response = requests.get({', '.join(params)})")
        
        elif method == 'post':
            lines.append("# 发送 POST 请求")
            
            if parsed['json_data']:
                json_str = json.dumps(parsed['json_data'], indent=4, ensure_ascii=False)
                lines.append(f"data = {json_str}")
                lines.append("")
                params.append("json=data")
                lines.append(f"response = requests.post({', '.join(params)})")
            
            elif parsed['data']:
                lines.append(f"data = '{parsed['data']}'")
                lines.append("")
                params.append("data=data")
                lines.append(f"response = requests.post({', '.join(params)})")
            else:
                lines.append(f"response = requests.post({', '.join(params)})")
        
        else:
            lines.append(f"# 发送 {method.upper()} 请求")
            lines.append(f"response = requests.{method}({', '.join(params)})")
        
        # 响应处理
        lines.append("")
        lines.append("# 处理响应")
        lines.append("print(f'状态码: {response.status_code}')")
        lines.append("")
        lines.append("# 获取响应内容")
        lines.append("try:")
        lines.append("    # 尝试解析为 JSON")
        lines.append("    result = response.json()")
        if parsed['json_data']:
            lines.append("    print(json.dumps(result, indent=4, ensure_ascii=False))")
        else:
            lines.append("    print(result)")
        lines.append("except:")
        lines.append("    # 如果不是 JSON，打印文本内容")
        lines.append("    print(response.text[:1000])")
        
        return "\n".join(lines)
    
    def convert_curl_to_python(self):
        """转换cURL为Python"""
        curl_cmd = self.left_text.get("1.0", tk.END).strip()
        
        self.right_text.delete("1.0", tk.END)
        
        if not curl_cmd:
            self.right_text.insert("1.0", "错误: 请输入 cURL 命令！")
            return
        
        try:
            parsed = self.parse_curl_command(curl_cmd)
            
            if not parsed['url']:
                self.right_text.insert("1.0", "错误: 无法解析 URL，请检查 cURL 命令格式！")
                return
            
            python_code = self.generate_python_code(parsed)
            self.right_text.insert("1.0", python_code)
        
        except Exception as e:
            self.right_text.insert("1.0", f"转换出错: {str(e)}\n\n请检查 cURL 命令格式。")


def main():
    root = tk.Tk()
    app = CurlToPythonConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
