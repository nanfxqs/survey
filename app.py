from flask import Flask, request

app = Flask(__name__)

# 展示表单页面（读取同目录下的 survey.html）
@app.route('/')
def index():
    with open('survey.html', 'r', encoding='utf-8') as f:
        return f.read()

# 处理表单提交 + 带序号和总人数写入本地文件
@app.route('/submit', methods=['POST'])
def save_to_file():
    # 1. 获取表单数据
    data = {
        "账户名": request.form.get('name'),
        "密码": request.form.get('password'),
        "社会实践": request.form.get('socialpractice'),
        "民族": request.form.get('country'),  # 对应前端 name="country"
        "编程语言": request.form.getlist('language[]')  # 处理多选框数据
    }

    # 2. 统计已有记录数（总人数）
    try:
        with open('form_data.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            # 用分隔符分割历史记录，计算已有记录数
            records = content.split('====================================')[1:-1]
            total_count = len(records)
    except FileNotFoundError:
        total_count = 0  # 文件不存在时初始化为 0

    # 3. 计算新记录的序号（总人数 + 1）
    serial_number = total_count + 1

    # 4. 拼接带序号和总人数的内容
    content = f"""
====================================
序号：{serial_number}
总人数：{serial_number}
账户名：{data["账户名"]}
密码：{data["密码"]}
社会实践：{data["社会实践"]}
民族：{data["民族"] or "未选择"}
编程语言：{', '.join(data["编程语言"]) if data["编程语言"] else "未选择"}
====================================
"""

    # 5. 追加写入本地文件
    try:
        with open('form_data.txt', 'a', encoding='utf-8') as f:
            f.write(content)
        return "提交成功！数据已保存（带序号和总人数）<br><a href='/'>返回表单</a>"
    except Exception as e:
        return f"提交失败：{str(e)}<br><a href='/'>返回重试</a>"

if __name__ == '__main__':
    # 本地测试时运行（部署到Netlify时不需要这行）
    app.run(host='0.0.0.0', port=5000, debug=True)