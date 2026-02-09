from flask import Flask, render_template, request, jsonify, send_file, Response
from universal_downloader import UniversalDownloader
import os
import time
import json
import re
import requests

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 创建下载目录
DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# 创建通用下载器实例
downloader = UniversalDownloader(DOWNLOAD_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/platforms')
def get_platforms():
    """获取支持的平台列表"""
    return jsonify({
        'platforms': downloader.get_supported_platforms()
    })

@app.route('/api/parse', methods=['POST'])
def parse_url():
    """解析视频分享链接（支持多平台）"""
    try:
        data = request.get_json()
        share_url = data.get('url', '').strip()
        
        if not share_url:
            return jsonify({'error': '请提供视频分享链接'}), 400
        
        # 检测平台
        platform_key, platform_name = downloader.detect_platform(share_url)
        print(f"检测到 {platform_name} 链接")
        
        # 处理链接
        result = downloader.process_url(share_url)
        
        if not result.get('success'):
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    """下载视频文件（支持多平台）"""
    try:
        data = request.get_json()
        video_id = data.get('video_id', '')
        original_url = data.get('original_url', '')  # 原始链接
        platform = data.get('platform', 'unknown')
        
        if not video_id or not original_url:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 生成文件名
        timestamp = int(time.time())
        filename = f"{platform}_{video_id}_{timestamp}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        # 使用原始 URL 下载（避免 CDN 403 问题）
        downloaded_file = downloader.download_video(original_url, filepath)
        
        if not downloaded_file:
            return jsonify({'error': '下载失败，请稍后重试'}), 500
        
        return jsonify({
            'success': True,
            'filename': downloaded_file,
            'filepath': os.path.join(DOWNLOAD_DIR, downloaded_file),
            'download_url': f'/download/{downloaded_file}'
        })
        
    except Exception as e:
        return jsonify({'error': f'下载错误: {str(e)}'}), 500

@app.route('/download/<filename>')
def serve_file(filename):
    """提供文件下载服务"""
    try:
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'文件服务错误: {str(e)}'}), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_files():
    """清理下载的文件"""
    try:
        data = request.get_json()
        filename = data.get('filename', '')
        
        if filename:
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return jsonify({'success': True, 'message': '文件已删除'})
        
        return jsonify({'error': '文件不存在'}), 404
        
    except Exception as e:
        return jsonify({'error': f'清理错误: {str(e)}'}), 500

@app.route('/api/proxy-image')
def proxy_image():
    """代理外部图片（解决 Instagram 等平台封面图无法直接访问的问题）"""
    try:
        image_url = request.args.get('url', '')
        if not image_url:
            return jsonify({'error': '缺少图片URL'}), 400
        
        # 请求外部图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/*,*/*;q=0.8',
            'Referer': 'https://www.instagram.com/',
        }
        
        resp = requests.get(image_url, headers=headers, timeout=10, stream=True)
        
        if resp.status_code == 200:
            content_type = resp.headers.get('Content-Type', 'image/jpeg')
            return Response(resp.content, mimetype=content_type)
        else:
            return jsonify({'error': '无法获取图片'}), resp.status_code
            
    except Exception as e:
        print(f"代理图片错误: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000)
