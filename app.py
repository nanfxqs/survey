from flask import Flask, request, render_template_string
import os
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

app = Flask(__name__)

# 获取当前文件所在目录的绝对路径（解决文件路径问题的核心）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 初始化Firebase（从环境变量读取配置）
try:
    # 从Netlify环境变量加载Firebase配置
    firebase_config = {
        "type": os.environ.get("FIREBASE_TYPE"),
        "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
        "private_key_id": os.environ.get("FIREBASE_PR_KEY_ID"),
        "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace('\\n', '\n') if os.environ.get("FIREBASE_PRIVATE_KEY") else None,
        "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL")
    }
    
    # 初始化Firebase应用
    cred = credentials.Certificate(firebase_config)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    submissions_ref = db.collection('survey_submissions')  # 存储提交数据的集合
except Exception as e:
    app.logger.error(f"Firebase初始化失败: {str(e)}")
    db = None  # 标记数据库初始化失败

# 表单HTML模板（内嵌方式避免文件读取问题）
FORM_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>调查问卷</title>
    <style>
        body { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; box-sizing: border-box; margin-bottom: 10px; }
        .radio-group { display: flex; gap: 15px; margin-bottom: 10px; }
        .checkbox-group { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 10px; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background: #45a049; }
        .error { color: red; margin: 10px 0; }
        .success { color: green; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>调查问卷</h1>
    {% if message %}
        <div class="{{ message_type }}">{{ message }}</div>
    {% endif %}
    <form action="/submit" method="POST">
        <div class="form-group">
            <label>账户名：</label>
            <input type="text" name="name" required placeholder="请输入账户名">
        </div>
        <div class="form-group">
            <label>密码：</label>
            <input type="password" name="password" required placeholder="请输入密码">
        </div>
        <div class="form-group">
            <label>社会实践经历：</label>
            <select name="socialpractice" required>
                <option value="">请选择</option>
                <option value="有">有</option>
                <option value="无">无</option>
            </select>
        </div>
        <div class="form-group">
            <label>民族：</label>
            <input type="text" name="country" required placeholder="请输入民族">
        </div>
        <div class="form-group">
            <label>熟悉的编程语言（可多选）：</label>
            <div class="checkbox-group">
                <label><input type="checkbox" name="language" value="Python"> Python</label>
                <label><input type="checkbox" name="language" value="Java"> Java</label>
                <label><input type="checkbox" name="language" value="JavaScript"> JavaScript</label>
                <label><input type="checkbox" name="language" value="C++"> C++</label>
            </div>
        </div>
        <button type="submit">提交</button>
    </form>
</body>
</html>
"""

# 首页展示表单
@app.route('/')
def index():
    try:
        # 使用内嵌模板避免文件读取问题，彻底解决FileNotFoundError
        return render_template_string(FORM_HTML)
    except Exception as e:
        return f"页面加载失败: {str(e)}", 500

# 处理表单提交
@app.route('/submit', methods=['POST'])
def submit():
    # 检查数据库是否初始化成功
    if not db:
        return render_template_string(
            FORM_HTML, 
            message="服务异常，请稍后再试", 
            message_type="error"
        )

    # 1. 获取并验证表单数据
    required_fields = ['name', 'password', 'socialpractice', 'country']
    for field in required_fields:
        if not request.form.get(field):
            return render_template_string(
                FORM_HTML, 
                message=f"错误：{field} 为必填项", 
                message_type="error"
            )

    # 2. 处理密码（哈希加密）
    password = request.form.get('password').encode('utf-8')
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())  # 加密存储

    # 3. 整理提交数据
    submission_data = {
        "name": request.form.get('name'),
        "password_hash": hashed_password.decode('utf-8'),  # 存储加密后的密码
        "socialpractice": request.form.get('socialpractice'),
        "country": request.form.get('country'),
        "languages": request.form.getlist('language'),  # 获取多选框数据
        "submitted_at": datetime.utcnow()  # 提交时间（UTC时间）
    }

    try:
        # 4. 存入Firebase数据库
        submissions_ref.add(submission_data)
        
        # 5. 计算总提交数（实时统计）
        total_count = submissions_ref.count().get()[0][0]
        
        return render_template_string(
            FORM_HTML, 
            message=f"提交成功！当前总提交人数：{total_count}", 
            message_type="success"
        )
    except Exception as e:
        app.logger.error(f"提交失败: {str(e)}")
        return render_template_string(
            FORM_HTML, 
            message=f"提交失败：{str(e)}", 
            message_type="error"
        )

if __name__ == '__main__':
    # 本地测试用（生产环境由Netlify Functions托管）
    app.run(host='0.0.0.0', port=5000, debug=True)
    