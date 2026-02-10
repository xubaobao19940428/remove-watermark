"""
通用视频下载器 - 支持多平台
使用 yt-dlp 实现，支持 Instagram、YouTube、Twitter/X、Facebook 等 1000+ 平台
抖音使用 curl_cffi 模拟浏览器访问移动端页面
"""
import os
import time
import uuid
import re
import json
from typing import Optional, Dict, Any, Tuple
from urllib.parse import unquote

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    from curl_cffi import requests as cffi_requests
    _has_curl_cffi = True
except ImportError:
    _has_curl_cffi = False
    import requests


class UniversalDownloader:
    """通用视频下载器，支持多平台"""
    
    # 支持的平台及其 URL 匹配模式
    PLATFORMS = {
        'tiktok': {
            'name': 'TikTok',
            'patterns': [
                r'tiktok\.com',
                r'vm\.tiktok\.com',
            ],
            'icon': '🎵',
        },
        'douyin': {
            'name': '抖音',
            'patterns': [
                r'douyin\.com',
                r'v\.douyin\.com',
                r'iesdouyin\.com',
            ],
            'icon': '🎶',
        },
        'instagram': {
            'name': 'Instagram',
            'patterns': [
                r'instagram\.com',
                r'instagr\.am',
            ],
            'icon': '📸',
        },
        'youtube': {
            'name': 'YouTube',
            'patterns': [
                r'youtube\.com',
                r'youtu\.be',
            ],
            'icon': '🎬',
        },
        'twitter': {
            'name': 'Twitter/X',
            'patterns': [
                r'twitter\.com',
                r'x\.com',
            ],
            'icon': '🐦',
        },
        'facebook': {
            'name': 'Facebook',
            'patterns': [
                r'facebook\.com',
                r'fb\.watch',
                r'fb\.com',
            ],
            'icon': '📘',
        },
        'bilibili': {
            'name': 'B站',
            'patterns': [
                r'bilibili\.com',
                r'b23\.tv',
            ],
            'icon': '📺',
        },
        'weibo': {
            'name': '微博',
            'patterns': [
                r'weibo\.com',
                r'weibo\.cn',
            ],
            'icon': '🔴',
        },
    }
    
    def __init__(self, download_dir: str = "downloads") -> None:
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
    
    def detect_platform(self, url: str) -> Tuple[str, str]:
        """
        检测 URL 对应的平台
        返回: (platform_key, platform_name)
        """
        if not url:
            return 'unknown', '未知平台'
        
        url_lower = url.lower()
        for platform_key, platform_info in self.PLATFORMS.items():
            for pattern in platform_info['patterns']:
                if re.search(pattern, url_lower):
                    return platform_key, platform_info['name']
        
        return 'other', '其他平台'
    
    def get_supported_platforms(self) -> list:
        """获取所有支持的平台列表"""
        return [
            {
                'key': key,
                'name': info['name'],
                'icon': info['icon'],
            }
            for key, info in self.PLATFORMS.items()
        ]
    
    def extract_url_from_text(self, text: str) -> str:
        """
        从分享文本中提取视频 URL
        支持抖音、TikTok、Instagram 等平台的分享文本格式
        """
        if not text:
            return ""
        
        # 通用 URL 正则表达式
        url_patterns = [
            # 抖音短链接
            r'https?://v\.douyin\.com/[A-Za-z0-9]+/?',
            # 抖音完整链接
            r'https?://www\.douyin\.com/video/\d+',
            # TikTok 短链接
            r'https?://vm\.tiktok\.com/[A-Za-z0-9]+/?',
            r'https?://www\.tiktok\.com/t/[A-Za-z0-9]+/?',
            # TikTok 完整链接
            r'https?://www\.tiktok\.com/@[^/]+/video/\d+',
            # Instagram
            r'https?://(?:www\.)?instagram\.com/(?:p|reel)/[A-Za-z0-9_-]+/?',
            # YouTube
            r'https?://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]+',
            r'https?://youtu\.be/[A-Za-z0-9_-]+',
            r'https?://(?:www\.)?youtube\.com/shorts/[A-Za-z0-9_-]+',
            # Twitter/X
            r'https?://(?:www\.)?(?:twitter|x)\.com/[^/]+/status/\d+',
            # Facebook
            r'https?://(?:www\.)?facebook\.com/.+/videos/\d+',
            r'https?://fb\.watch/[A-Za-z0-9]+/?',
            # Bilibili
            r'https?://(?:www\.)?bilibili\.com/video/[A-Za-z0-9]+',
            r'https?://b23\.tv/[A-Za-z0-9]+',
            # 微博
            r'https?://(?:www\.)?weibo\.com/tv/show/\d+',
            r'https?://(?:m\.)?weibo\.cn/[^\s]+',
            # 通用 HTTPS 链接（作为后备）
            r'https?://[^\s<>"]+',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, text)
            if match:
                url = match.group(0)
                # 清理 URL 末尾可能的标点符号
                url = url.rstrip('.,;:!?\'\"')
                print(f"从文本中提取到 URL: {url}")
                return url
        
        # 如果没有匹配到任何 URL 模式，返回原始文本（可能本身就是 URL）
        return text.strip()
    
    def _resolve_douyin_url(self, url: str) -> str:
        """解析抖音短链接，获取视频ID"""
        try:
            if _has_curl_cffi:
                session = cffi_requests.Session(impersonate='chrome120')
                resp = session.get(url, allow_redirects=True)
            else:
                resp = requests.get(url, allow_redirects=True, headers={
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'
                })
            final_url = str(resp.url)
            match = re.search(r'/video/(\d+)', final_url)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"[抖音] 解析短链接失败: {e}")
        return None
    
    def _get_douyin_video_info(self, url: str) -> Dict[str, Any]:
        """
        通过移动端页面获取抖音视频信息
        使用 curl_cffi 模拟浏览器访问 m.douyin.com
        """
        # 提取视频ID
        video_id = None
        match = re.search(r'/video/(\d+)', url)
        if match:
            video_id = match.group(1)
        else:
            video_id = self._resolve_douyin_url(url)
        
        if not video_id:
            return self._error_response("无法提取抖音视频ID")
        
        print(f"[抖音] 视频ID: {video_id}")
        
        try:
            # 访问移动端页面
            if _has_curl_cffi:
                session = cffi_requests.Session(impersonate='chrome120')
            else:
                session = None
                
            mobile_url = f'https://m.douyin.com/share/video/{video_id}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }
            
            if session:
                mobile_resp = session.get(mobile_url, headers=headers)
            else:
                mobile_resp = requests.get(mobile_url, headers=headers)
            
            html = mobile_resp.text
            print(f"[抖音] 获取移动端页面: {len(html)} 字节")
            
            # 从 script 标签中提取视频数据
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
            
            for script in scripts:
                if 'play_addr' not in script:
                    continue
                
                # 提取各字段
                title = ''
                author = ''
                video_url = ''
                cover_url = ''
                duration = 0
                like_count = 0
                comment_count = 0
                share_count = 0
                
                # 标题
                desc_match = re.search(r'"desc"\s*:\s*"((?:[^"\\]|\\.)*)"', script)
                if desc_match:
                    title = self._decode_unicode_text(desc_match.group(1))
                
                # 作者
                nick_match = re.search(r'"nickname"\s*:\s*"((?:[^"\\]|\\.)*)"', script)
                if nick_match:
                    author = self._decode_unicode_text(nick_match.group(1))
                
                # 视频播放地址
                play_match = re.search(r'"play_addr"\s*:\s*\{[^}]*"url_list"\s*:\s*\["((?:[^"\\]|\\.)*)"', script)
                if play_match:
                    video_url = play_match.group(1).replace('\\u002F', '/').replace('playwm', 'play')
                
                # 封面图
                cover_match = re.search(r'"cover"\s*:\s*\{[^}]*"url_list"\s*:\s*\["((?:[^"\\]|\\.)*)"', script)
                if cover_match:
                    cover_url = cover_match.group(1).replace('\\u002F', '/')
                
                # 时长
                dur_match = re.search(r'"duration"\s*:\s*(\d+)', script)
                if dur_match:
                    duration = int(dur_match.group(1))
                    # 抖音duration是毫秒，转为秒
                    if duration > 1000:
                        duration = duration // 1000
                
                # 统计数据
                like_match = re.search(r'"digg_count"\s*:\s*(\d+)', script)
                if like_match:
                    like_count = int(like_match.group(1))
                
                comment_match = re.search(r'"comment_count"\s*:\s*(\d+)', script)
                if comment_match:
                    comment_count = int(comment_match.group(1))
                
                share_match = re.search(r'"share_count"\s*:\s*(\d+)', script)
                if share_match:
                    share_count = int(share_match.group(1))
                
                if title or video_url:
                    print(f"[抖音] 成功解析: {title[:50]}")
                    print(f"[抖音] 作者: {author}")
                    print(f"[抖音] 视频URL: {'已获取' if video_url else '无'}")
                    
                    return {
                        "success": True,
                        "platform": "douyin",
                        "platform_name": "抖音",
                        "video_id": video_id,
                        "title": title or f"抖音视频 {video_id}",
                        "author": author or "未知作者",
                        "video_url": video_url,
                        "cover_url": cover_url,
                        "duration": duration,
                        "like_count": like_count,
                        "comment_count": comment_count,
                        "view_count": share_count,
                    }
            
            return self._error_response("无法从页面提取视频数据")
            
        except Exception as e:
            print(f"[抖音] 解析错误: {e}")
            return self._error_response(f"抖音解析错误: {str(e)}")
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        获取视频信息
        """
        if not yt_dlp:
            return self._error_response("yt-dlp 未安装，请运行: pip install yt-dlp")
        
        if not url:
            return self._error_response("请提供视频链接")
        
        platform_key, platform_name = self.detect_platform(url)
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            },
        }
        
        # 抖音需要 cookies 认证
        if platform_key == 'douyin':
            ydl_opts['cookiesfrombrowser'] = ('chrome',)
        
        try:
            print(f"[{platform_name}] 正在解析: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return self._error_response("无法获取视频信息")
                
                # 提取视频 URL
                video_url = self._extract_best_video_url(info)
                
                return {
                    "success": True,
                    "platform": platform_key,
                    "platform_name": platform_name,
                    "video_id": info.get('id', str(int(time.time()))),
                    "title": info.get('title', info.get('description', '未知标题'))[:200],
                    "author": info.get('uploader', info.get('channel', info.get('creator', '未知作者'))),
                    "video_url": video_url,
                    "cover_url": info.get('thumbnail', ''),
                    "duration": info.get('duration', 0),
                    "like_count": info.get('like_count', 0),
                    "view_count": info.get('view_count', 0),
                    "comment_count": info.get('comment_count', 0),
                }
                
        except Exception as e:
            error_msg = str(e)
            print(f"[{platform_name}] 解析失败: {error_msg}")
            
            # 提供更友好的错误信息
            if 'login' in error_msg.lower() or 'private' in error_msg.lower():
                return self._error_response(f"该视频可能是私密内容或需要登录才能查看")
            elif 'not found' in error_msg.lower() or '404' in error_msg:
                return self._error_response(f"视频不存在或已被删除")
            else:
                return self._error_response(f"解析失败: {error_msg[:100]}")
    
    def _extract_best_video_url(self, info: Dict) -> str:
        """从 yt-dlp 信息中提取最佳视频 URL"""
        # 优先使用 url 字段
        if info.get('url'):
            return info['url']
        
        # 从 formats 中选择最佳
        formats = info.get('formats', [])
        if not formats:
            return ''
        
        # 优先选择 mp4 格式，无水印
        for fmt in reversed(formats):
            if fmt.get('ext') == 'mp4' and fmt.get('url'):
                url = fmt['url']
                # 跳过带水印的
                if 'wm' not in url.lower():
                    return url
        
        # 回退到任意 mp4
        for fmt in reversed(formats):
            if fmt.get('ext') == 'mp4' and fmt.get('url'):
                return fmt['url']
        
        # 回退到任意格式
        for fmt in reversed(formats):
            if fmt.get('url'):
                return fmt['url']
        
        return ''
    
    @staticmethod
    def _decode_unicode_text(text: str) -> str:
        """正确解码包含 \\uXXXX 的文本"""
        try:
            # 替换 \uXXXX 为实际字符
            def replace_unicode(match):
                return chr(int(match.group(1), 16))
            return re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, text)
        except Exception:
            return text
    
    def download_video(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        下载视频
        支持传入分享文本，会自动提取 URL
        """
        if not url:
            return None
        
        # 从分享文本中提取 URL
        extracted_url = self.extract_url_from_text(url)
        if not extracted_url:
            print("无法从文本中提取 URL")
            return None
        url = extracted_url
        
        if not yt_dlp:
            print("yt-dlp 未安装")
            return None
        
        platform_key, platform_name = self.detect_platform(url)
        
        # 生成文件名
        if not filename:
            timestamp = int(time.time())
            filename = f"{platform_key}_{timestamp}_{uuid.uuid4().hex[:8]}.mp4"
        
        # 处理路径
        if os.path.dirname(filename):
            filepath = filename
        else:
            filepath = os.path.join(self.download_dir, filename)
        
        if not filepath.endswith('.mp4'):
            filepath = filepath + '.mp4'
        
        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'outtmpl': filepath.replace('.mp4', '') + '.%(ext)s',
            'format': 'best[ext=mp4]/best',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': url,
            },
            'retries': 3,
            'fragment_retries': 3,
        }
        
        # 抖音使用直接下载视频 URL
        if platform_key == 'douyin':
            # 先解析获取直接视频URL，用 requests 直接下载
            douyin_info = self._get_douyin_video_info(url)
            if douyin_info.get('success') and douyin_info.get('video_url'):
                try:
                    video_direct_url = douyin_info['video_url']
                    print(f"[抖音] 使用无水印URL下载: {video_direct_url[:80]}...")
                    
                    # 先获取重定向后的真实下载地址
                    if _has_curl_cffi:
                        session = cffi_requests.Session(impersonate='chrome120')
                        # 先请求获取重定向地址
                        head_resp = session.get(video_direct_url, allow_redirects=True, timeout=30)
                        real_url = str(head_resp.url)
                        content_length = len(head_resp.content)
                        
                        if content_length > 0:
                            # 直接写入已获取的内容
                            print(f"[抖音] 文件大小: {content_length / 1024 / 1024:.1f} MB")
                            with open(filepath, 'wb') as f:
                                f.write(head_resp.content)
                        else:
                            print(f"[抖音] 使用重定向地址下载: {real_url[:80]}...")
                            resp = session.get(real_url, timeout=300)
                            with open(filepath, 'wb') as f:
                                f.write(resp.content)
                    else:
                        import requests as std_requests
                        resp = std_requests.get(video_direct_url, 
                            allow_redirects=True, 
                            timeout=300,
                            headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'},
                            stream=True
                        )
                        with open(filepath, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=65536):
                                if chunk:
                                    f.write(chunk)
                    
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        file_size = os.path.getsize(filepath) / 1024 / 1024
                        print(f"[抖音] 下载成功: {filepath} ({file_size:.1f} MB)")
                        return os.path.basename(filepath)
                    else:
                        print(f"[抖音] 下载文件为空")
                        return None
                except Exception as e:
                    print(f"[抖音] 直接下载失败: {e}")
                    return None
            else:
                print(f"[抖音] 无法获取视频URL")
                return None
        
        try:
            print(f"[{platform_name}] 正在下载: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 查找下载的文件
            import glob
            base_path = filepath.replace('.mp4', '')
            found_files = glob.glob(base_path + '.*')
            
            for found_file in found_files:
                if os.path.exists(found_file) and os.path.getsize(found_file) > 0:
                    print(f"[{platform_name}] 下载成功: {found_file}")
                    return os.path.basename(found_file)
            
            print(f"[{platform_name}] 未找到下载文件")
            return None
            
        except Exception as e:
            print(f"[{platform_name}] 下载失败: {e}")
            return None
    
    def _error_response(self, error: str) -> Dict[str, Any]:
        """生成错误响应"""
        return {
            "success": False,
            "error": error,
        }
    
    def process_url(self, url: str) -> Dict[str, Any]:
        """
        处理 URL - 主入口方法
        支持直接传入分享文本，会自动提取 URL
        """
        if not url:
            return self._error_response("请提供视频链接")
        
        # 从分享文本中提取 URL
        extracted_url = self.extract_url_from_text(url)
        
        if not extracted_url:
            return self._error_response("无法从文本中提取视频链接")
        
        platform_key, platform_name = self.detect_platform(extracted_url)
        
        if platform_key == 'unknown':
            return self._error_response("无法识别该链接，请检查是否为支持的平台")
        
        # 抖音使用移动端页面解析（绕过 yt-dlp cookies 问题）
        if platform_key == 'douyin':
            print(f"[{platform_name}] 使用移动端页面解析")
            info = self._get_douyin_video_info(extracted_url)
            
            if info.get('success'):
                return {
                    "success": True,
                    "platform": platform_key,
                    "platform_name": platform_name,
                    "video_id": info.get('video_id', 'unknown'),
                    "video_info": {
                        "title": info.get('title', '未知标题'),
                        "author": info.get('author', '未知作者'),
                        "video_url": info.get('video_url', ''),
                        "cover_url": info.get('cover_url', ''),
                        "duration": info.get('duration', 0),
                        "like_count": info.get('like_count', 0),
                        "view_count": info.get('view_count', 0),
                        "comment_count": info.get('comment_count', 0),
                    },
                    "has_download_url": bool(info.get('video_url')),
                }
            else:
                return self._error_response(info.get('error', '抖音解析失败'))
        
        # 其他平台使用 yt-dlp
        info = self.get_video_info(extracted_url)
        
        if not info.get('success'):
            return info
        
        return {
            "success": True,
            "platform": platform_key,
            "platform_name": platform_name,
            "video_id": info.get('video_id', 'unknown'),
            "video_info": {
                "title": info.get('title', '未知标题'),
                "author": info.get('author', '未知作者'),
                "video_url": info.get('video_url', ''),
                "cover_url": info.get('cover_url', ''),
                "duration": info.get('duration', 0),
                "like_count": info.get('like_count', 0),
                "view_count": info.get('view_count', 0),
                "comment_count": info.get('comment_count', 0),
            },
            "has_download_url": bool(info.get('video_url')),
        }


# 单例实例
universal_downloader = UniversalDownloader()
