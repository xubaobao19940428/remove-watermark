import os
import time
import uuid
import re
from typing import Optional, Dict, Any

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class TikTokDownloader:
    def __init__(self, download_dir: str = "downloads") -> None:
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        
        # TikTok URL patterns
        self.tiktok_url_patterns = [
            re.compile(r"https?://vm\.tiktok\.com/[\w\-_/]+/?"),
            re.compile(r"https?://www\.tiktok\.com/@[\w\.-]+/video/\d+/?"),
            re.compile(r"https?://m\.tiktok\.com/v/\d+\.html"),
            re.compile(r"https?://www\.tiktok\.com/t/[\w\-_]+/?"),
        ]
        
        # Video ID patterns
        self.id_patterns = [
            re.compile(r"/video/(\d+)"),
            re.compile(r"/v/(\d+)\.html"),
        ]

    def extract_tiktok_url(self, share_text: str) -> Optional[str]:
        """Extract TikTok URL from share text"""
        if not share_text:
            return None
        for pat in self.tiktok_url_patterns:
            m = pat.search(share_text)
            if m:
                return m.group(0)
        # If no pattern matches but contains tiktok.com, return as-is
        if "tiktok.com" in share_text:
            return share_text.strip()
        return None

    def extract_video_id(self, share_text_or_url: str) -> tuple:
        """Extract video ID from URL"""
        url = self.extract_tiktok_url(share_text_or_url) or share_text_or_url
        if not url or not isinstance(url, str):
            return None, None

        # Try to extract ID directly from URL
        for pat in self.id_patterns:
            m = pat.search(url)
            if m:
                return m.group(1), url
        
        # Return URL without ID for yt-dlp to handle
        if "tiktok.com" in url:
            return "pending", url
        
        return None, None

    def get_video_info(self, video_id: str, canonical_url: Optional[str] = None) -> Dict[str, Any]:
        """Get video info using yt-dlp"""
        if not yt_dlp:
            return self._fallback_response(video_id, "yt-dlp 未安装，请运行: pip install yt-dlp")
        
        url = canonical_url or f"https://www.tiktok.com/@_/video/{video_id}"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }
        
        try:
            print(f"使用 yt-dlp 提取视频信息: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return self._fallback_response(video_id, "无法获取视频信息")
                
                # Extract video URL (prefer no watermark)
                video_url = ""
                formats = info.get('formats', [])
                
                # Find best MP4 format without watermark
                for fmt in reversed(formats):
                    if fmt.get('ext') == 'mp4' and fmt.get('url'):
                        # Prefer formats without watermark in URL
                        if 'wm' not in fmt.get('url', '').lower():
                            video_url = fmt['url']
                            break
                        elif not video_url:
                            video_url = fmt['url']
                
                # Fallback to direct url
                if not video_url:
                    video_url = info.get('url', '')
                
                return {
                    "title": info.get('title', info.get('description', f'TikTok 视频 {video_id}')),
                    "author": info.get('uploader', info.get('creator', '未知作者')),
                    "video_url": video_url,
                    "cover_url": info.get('thumbnail', ''),
                    "duration": info.get('duration', 0),
                    "like_count": info.get('like_count', 0),
                    "comment_count": info.get('comment_count', 0),
                    "share_count": info.get('repost_count', 0),
                }
                
        except Exception as e:
            print(f"yt-dlp 提取失败: {e}")
            return self._fallback_response(video_id, str(e))
    
    def _fallback_response(self, video_id: str, error: str = "") -> Dict[str, Any]:
        """Fallback response when extraction fails"""
        return {
            "title": f"TikTok 视频 {video_id}",
            "author": "未知作者",
            "video_url": "",
            "cover_url": "",
            "duration": 0,
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0,
            "error": error,
        }

    def download_video(self, video_url: str, filename: Optional[str] = None) -> Optional[str]:
        """Download video from URL"""
        if not video_url:
            return None
            
        if not filename:
            filename = f"tiktok_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp4"
        
        # Check if filename is already a full path (from app.py)
        if os.path.dirname(filename):
            # It's already a full path, use it directly
            filepath = filename
        else:
            # Just a filename, prepend download_dir
            filepath = os.path.join(self.download_dir, filename)
        
        # Ensure .mp4 extension
        if not filepath.endswith('.mp4'):
            filepath = filepath + '.mp4'
        
        # Use yt-dlp to download if available
        if yt_dlp:
            ydl_opts = {
                'quiet': False,
                'no_warnings': False,
                'outtmpl': filepath.replace('.mp4', '') + '.%(ext)s',
                'format': 'best[ext=mp4]/best',
                # Add headers to mimic browser
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': 'https://www.tiktok.com/',
                },
                # Retry settings
                'retries': 3,
                'fragment_retries': 3,
                # Skip unavailable fragments
                'skip_unavailable_fragments': True,
            }
            
            try:
                print(f"使用 yt-dlp 下载视频: {video_url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                
                # Find the downloaded file using glob pattern
                import glob
                base_path = filepath.replace('.mp4', '')
                pattern = base_path + '.*'
                found_files = glob.glob(pattern)
                print(f"搜索下载文件: {pattern}, 找到: {found_files}")
                
                for found_file in found_files:
                    if os.path.exists(found_file) and os.path.getsize(found_file) > 0:
                        print(f"下载成功: {found_file}, 大小: {os.path.getsize(found_file)} bytes")
                        return os.path.basename(found_file)
                        
            except Exception as e:
                print(f"yt-dlp 下载失败: {e}")
        
        # Fallback to requests with proper headers
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.tiktok.com/',
            }
            print(f"尝试 requests 下载: {video_url[:100]}...")
            with requests.get(video_url, stream=True, timeout=30, headers=headers) as r:
                if r.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        print(f"requests 下载成功: {filepath}")
                        return os.path.basename(filepath)
        except Exception as e:
            print(f"requests 下载失败: {e}")
        
        return None

    def process_share_url(self, share_text_or_url: str) -> Dict[str, Any]:
        """Process TikTok share URL"""
        video_id, canonical_url = self.extract_video_id(share_text_or_url)
        
        if not video_id:
            return {
                "success": False,
                "error": "无法识别 TikTok 链接。请使用完整的 TikTok 视频链接。"
            }
        
        # Use canonical URL for yt-dlp
        video_info = self.get_video_info(video_id, canonical_url)
        
        return {
            "success": True,
            "video_id": video_id if video_id != "pending" else "extracted",
            "video_info": video_info,
            "has_download_url": bool(video_info.get("video_url")),
        }
