# netlify/functions/server.py
from flask import Flask, request
import sys
import os
# 把根目录加入Python路径（让服务器能找到app.py）
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app import app  # 导入你的Flask应用

# Netlify Functions要求的入口函数
def handler(event, context):
    from flask import request, make_response
    from werkzeug.test import create_environ
    from werkzeug.wrappers import Request

    # 转换Netlify的event为Flask能识别的请求
    environ = create_environ(
        path=event['path'],
        base_url="https://endearing-belekoy-ee02c7.netlify.app/",  # 先随便写，后面可以改
        query_string=event['queryStringParameters'],
        method=event['httpMethod'],
        headers=event['headers'],
        data=event['body'] if event['body'] else b''
    )
    request = Request(environ)
    
    # 让Flask处理请求
    with app.test_request_context(
        path=event['path'],
        method=event['httpMethod'],
        data=event['body'],
        headers=event['headers']
    ):
        try:
            response = app.full_dispatch_request()
        except Exception as e:
            response = app.make_response(str(e))
    
    # 转换Flask响应为Netlify能识别的格式
    return {
        'statusCode': response.status_code,
        'headers': dict(response.headers),
        'body': response.get_data(as_text=True)
    }