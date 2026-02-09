"""
通用视频下载器 - 支持多平台
使用 yt-dlp 实现，支持 Instagram、YouTube、Twitter/X、Facebook 等 1000+ 平台
"""
import os
import time
import uuid
import re
from typing import Optional, Dict, Any, Tuple

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

# 导入原有的抖音下载器作为后备
try:
    from douyin_downloader import DouyinDownloader
    _douyin_downloader = DouyinDownloader()
except ImportError:
    _douyin_downloader = None


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
    
    def download_video(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        下载视频
        """
        if not url:
            return None
        
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
        
        # 抖音需要 cookies 认证
        if platform_key == 'douyin':
            ydl_opts['cookiesfrombrowser'] = ('chrome',)
        
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
        
        # 抖音使用原有的下载器（绕过 yt-dlp cookies 问题）
        if platform_key == 'douyin' and _douyin_downloader:
            print(f"[{platform_name}] 使用原生抖音下载器")
            result = _douyin_downloader.process_share_url(url)  # 传入原始文本
            
            if result.get('success'):
                video_info = result.get('video_info', {})
                return {
                    "success": True,
                    "platform": platform_key,
                    "platform_name": platform_name,
                    "video_id": result.get('video_id', 'unknown'),
                    "video_info": {
                        "title": video_info.get('title', '未知标题'),
                        "author": video_info.get('author', '未知作者'),
                        "video_url": video_info.get('video_url', ''),
                        "cover_url": video_info.get('cover_url', ''),
                        "duration": video_info.get('duration', 0),
                        "like_count": video_info.get('like_count', 0),
                        "view_count": video_info.get('share_count', 0),
                        "comment_count": video_info.get('comment_count', 0),
                    },
                    "has_download_url": result.get('has_download_url', False),
                }
            else:
                return self._error_response(result.get('error', '抖音解析失败'))
        
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
