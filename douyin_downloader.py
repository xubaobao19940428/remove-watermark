import re
import json
import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import time
import random
import hashlib
import base64

class DouyinDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        
        # 设置一些基本的cookies
        self.session.cookies.update({
            'msToken': 'abc123',
            'ttwid': 'def456',
            'odin_tt': 'ghi789',
            'passport_csrf_token': 'jkl012',
        })
    
    def extract_video_id(self, share_url):
        """从分享链接中提取视频ID"""
        try:
            # 首先从完整分享文本中提取抖音链接
            douyin_patterns = [
                r'https://v\.douyin\.com/[a-zA-Z0-9_-]+/?',
                r'https://www\.douyin\.com/video/\d+',
                r'https://www\.iesdouyin\.com/share/video/\d+',
                r'https://www\.douyin\.com/share/video/\d+'
            ]
            
            extracted_url = None
            for pattern in douyin_patterns:
                match = re.search(pattern, share_url)
                if match:
                    extracted_url = match.group(0)
                    break
            
            if not extracted_url:
                print("未找到抖音链接")
                return None
            
            # 处理短链接
            if 'v.douyin.com' in extracted_url:
                try:
                    response = self.session.get(extracted_url, allow_redirects=True, timeout=10)
                    extracted_url = response.url
                except Exception as e:
                    print(f"处理短链接时出错: {e}")
                    # 如果短链接处理失败，尝试直接提取ID
                    pass
            
            # 提取视频ID
            id_patterns = [
                r'/video/(\d+)',
                r'item_ids=(\d+)',
                r'aweme_id=(\d+)',
                r'/(\d+)\?',
                r'/share/video/(\d+)'
            ]
            
            for pattern in id_patterns:
                match = re.search(pattern, extracted_url)
                if match:
                    video_id = match.group(1)
                    print(f"成功提取视频ID: {video_id}")
                    return video_id
            
            print(f"无法从链接中提取视频ID: {extracted_url}")
            return None
            
        except Exception as e:
            print(f"提取视频ID时出错: {e}")
            return None
    
    def encrypt_params(self, data):
        """简化的参数加密方法"""
        try:
            # 将数据转换为JSON字符串
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            
            # 使用简单的base64编码
            encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            
            # 生成一个简单的哈希值
            hash_value = hashlib.md5(json_str.encode('utf-8')).hexdigest()
            
            # 组合结果
            result = f"{encoded}_{hash_value[:8]}"
            
            return result
        except Exception as e:
            print(f"加密参数时出错: {e}")
            return ""
    
    def extract_short_url(self, share_text):
        """从分享文本中提取短链接"""
        try:
            # 匹配抖音短链接
            short_pattern = r'https://v\.douyin\.com/[a-zA-Z0-9_-]+/?'
            match = re.search(short_pattern, share_text)
            if match:
                return match.group(0)
            return None
        except Exception as e:
            print(f"提取短链接时出错: {e}")
            return None
    
    def get_video_info(self, video_id, short_url=None):
        """获取视频信息"""
        try:
            # 方法1: 尝试使用移动端API，模拟真实设备
            mobile_headers = {
                'User-Agent': 'com.ss.android.ugc.aweme/494 (Linux; U; Android 10; zh_CN; Pixel 4; Build/QQ3A.200805.001; Cronet/TTNetVersion:5f9540e5 2020-05-25 QuicVersion:47946d2a 2020-05-25)',
                'Accept': 'application/json',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'X-SS-REQ-TICKET': str(int(time.time() * 1000)),
                'sdk-version': '2',
                'passport-sdk-version': '5.12.1',
            }
            
            # 尝试移动端API
            mobile_api_url = f"https://api.amemv.com/aweme/v1/aweme/detail/?aweme_id={video_id}&aid=1128&version_name=23.5.0&device_platform=android&os_version=10&device_type=Pixel%204&language=zh&cpu_abi=arm64-v8a&resolution=1080*1920&openudid=1234567890abcdef&update_version_code=23509999&channel=googleplay&device_platform=android&iid=1234567890&app_name=aweme&version_code=235&device_id=1234567890&os_api=29&carrier_region=CN&sys_region=CN&region=CN&app_type=normal&ac2=wifi&uoo=0&op_region=CN&timezone_name=Asia/Shanghai&dpi=420&carrier_region_v2=460&build_number=235&timezone_offset=28800&locale=zh&ac=wifi&uoo=0&channel=googleplay&device_type=Pixel%204&language=zh&cpu_abi=arm64-v8a&resolution=1080*1920&openudid=1234567890abcdef&update_version_code=23509999&channel=googleplay&device_platform=android&iid=1234567890&app_name=aweme&version_code=235&device_id=1234567890&os_api=29&carrier_region=CN&sys_region=CN&region=CN&app_type=normal&ac2=wifi&uoo=0&op_region=CN&timezone_name=Asia/Shanghai&dpi=420&carrier_region_v2=460&build_number=235&timezone_offset=28800&locale=zh&ac=wifi&uoo=0&channel=googleplay"
            
            try:
                print(f"尝试移动端API绕过: {mobile_api_url}")
                response = self.session.get(mobile_api_url, headers=mobile_headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    print(f"移动端API响应: {data}")
                    
                    if data.get('aweme_detail'):
                        video_data = data['aweme_detail']
                        video_info = {
                            'title': video_data.get('desc', f'抖音视频 {video_id}'),
                            'author': video_data.get('author', {}).get('nickname', '未知作者'),
                            'video_url': video_data.get('video', {}).get('play_addr', {}).get('url_list', [None])[0],
                            'cover_url': video_data.get('video', {}).get('cover', {}).get('url_list', [None])[0],
                            'duration': video_data.get('video', {}).get('duration', 0),
                            'like_count': video_data.get('statistics', {}).get('digg_count', 0),
                            'comment_count': video_data.get('statistics', {}).get('comment_count', 0),
                            'share_count': video_data.get('statistics', {}).get('share_count', 0)
                        }
                        
                        if video_info['video_url']:
                            print(f"成功获取视频URL: {video_info['video_url']}")
                            return video_info
            except Exception as e:
                print(f"移动端API绕过失败: {e}")
            
            # 方法2: 尝试使用Web端API，模拟浏览器行为
            web_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.douyin.com/',
                'Origin': 'https://www.douyin.com',
                'X-Requested-With': 'XMLHttpRequest',
                'Cookie': 'msToken=abc123; ttwid=def456; odin_tt=ghi789'
            }
            
            web_api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?device_platform=webapp&aid=6383&channel=channel_pc_web&aweme_id={video_id}&update_version_code=170400&pc_client_type=1&pc_libra_divert=Mac&support_h265=1&support_dash=1&cpu_core_num=8&version_code=190500&version_name=19.5.0&cookie_enabled=true&screen_width=1470&screen_height=956&browser_language=en&browser_platform=MacIntel&browser_name=Chrome&browser_version=139.0.0.0&browser_online=true&engine_name=Blink&engine_version=139.0.0.0&os_name=Mac+OS&os_version=10.15.7&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=250&webid=7548409579304371721&uifid=f718f562fcd874811d9c30568517194c189689a7c74491d0ed9c7c2e831358f100a6396322b30e6a3e206216b11da655eff7a5f1692631c9d646b7316bace8c81390da7663b7a90b15c86a653e792ac06890cb4b4c9625f3edcd79ddee229011aeab2af1c3353a89cdd74655aca34ce9d5854c8cb32fca016481180c102b08cda5a04eeb87dc0ef1495c116e30111529c08ec28f94981af67159d2205a061826&verifyFp=verify_mfdurrv5_mVWY2Mld_H4O8_4WeY_8AOd_ulsbshIa2z1z&fp=verify_mfdurrv5_mVWY2Mld_H4O8_4WeY_8AOd_ulsbshIa2z1z&msToken=zFsyrJ6m7a3XoH6PFyI4H_ssE0GUog8PHqcdY7hk4UzFMxKOdnB8uCzsswbKlFsZ-7Gf5LTcMlmexbnyptsZZ1xLPmxv7Cr_QxgVZQFQfqsT_eNNNhBTAOyxO51XwjUJuoXjNSLKfTF-2Gxo99cPkwJdlDXSzKA7Ch3d1DFJFHSnvl_BXPI5iks%3D&a_bogus=Q74nDeUJDq8neVMtYcj69HBUxSx%2FrPSydlTKSFqP7NuGcXzbvbP7DrGRJou94NRXnWBziq37VxMMbdxcsUXzZKrkzmpDuiwf6U25VysogZHma-khINDmeJbxzJ-t0AsTscdHEcw11UlE2ocVpqODlZKy7%2Ft75%2FY%2FTqe5pV4ZSxK15AfqpZ1Eun7DO7wqCD%3D%3D&verifyFp=verify_mfdurrv5_mVWY2Mld_H4O8_4WeY_8AOd_ulsbshIa2z1z&fp=verify_mfdurrv5_mVWY2Mld_H4O8_4WeY_8AOd_ulsbshIa2z1z"
            
            try:
                print(f"尝试Web端API绕过: {web_api_url}")
                response = self.session.get(web_api_url, headers=web_headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    print(f"Web端API响应: {data}")
                    
                    if data.get('aweme_detail'):
                        video_data = data['aweme_detail']
                        video_info = {
                            'title': video_data.get('desc', f'抖音视频 {video_id}'),
                            'author': video_data.get('author', {}).get('nickname', '未知作者'),
                            'video_url': video_data.get('video', {}).get('play_addr', {}).get('url_list', [None])[0],
                            'cover_url': video_data.get('video', {}).get('cover', {}).get('url_list', [None])[0],
                            'duration': video_data.get('video', {}).get('duration', 0),
                            'like_count': video_data.get('statistics', {}).get('digg_count', 0),
                            'comment_count': video_data.get('statistics', {}).get('comment_count', 0),
                            'share_count': video_data.get('statistics', {}).get('share_count', 0)
                        }
                        
                        if video_info['video_url']:
                            print(f"成功获取视频URL: {video_info['video_url']}")
                            return video_info
            except Exception as e:
                print(f"Web端API绕过失败: {e}")
            
            # 方法3: 尝试从网页中提取SSR数据
            try:
                print(f"尝试从网页提取SSR数据: https://www.douyin.com/video/{video_id}")
                web_url = f"https://www.douyin.com/video/{video_id}"
                
                # 先访问主页获取cookies
                self.session.get("https://www.douyin.com/", headers=web_headers, timeout=10)
                
                response = self.session.get(web_url, headers=web_headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 查找包含视频数据的script标签
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string and 'window._SSR_HYDRATED_DATA' in script.string:
                            try:
                                # 提取JSON数据
                                json_str = script.string.split('window._SSR_HYDRATED_DATA = ')[1].split(';</script>')[0]
                                json_data = json.loads(json_str)
                                print(f"SSR数据: {json_data}")
                                
                                # 解析SSR数据
                                if json_data.get('app') and json_data['app'].get('initialState'):
                                    video_data = json_data['app']['initialState'].get('aweme', {}).get('detail', {})
                                    if video_data:
                                        video_info = {
                                            'title': video_data.get('desc', f'抖音视频 {video_id}'),
                                            'author': video_data.get('author', {}).get('nickname', '未知作者'),
                                            'video_url': video_data.get('video', {}).get('playAddr', ''),
                                            'cover_url': video_data.get('video', {}).get('cover', ''),
                                            'duration': video_data.get('video', {}).get('duration', 0),
                                            'like_count': video_data.get('statistics', {}).get('diggCount', 0),
                                            'comment_count': video_data.get('statistics', {}).get('commentCount', 0),
                                            'share_count': video_data.get('statistics', {}).get('shareCount', 0)
                                        }
                                        
                                        if video_info['video_url']:
                                            print(f"成功从SSR获取视频URL: {video_info['video_url']}")
                                            return video_info
                            except Exception as e:
                                print(f"SSR数据解析失败: {e}")
                                continue
                    
                    print("未找到SSR数据")
                    
            except Exception as e:
                print(f"网页SSR提取失败: {e}")
            
            # 如果所有绕过方法都失败，返回基本信息
            print("所有绕过方法都失败，返回基本信息")
            
            return {
                'title': f'抖音视频 {video_id}',
                'author': '未知作者',
                'video_url': '',
                'cover_url': '',
                'duration': 0,
                'like_count': 0,
                'comment_count': 0,
                'share_count': 0
            }
            
        except Exception as e:
            print(f"获取视频信息时出错: {e}")
            return {
                'title': f'抖音视频 {video_id}',
                'author': '未知作者',
                'video_url': '',
                'cover_url': '',
                'duration': 0,
                'like_count': 0,
                'comment_count': 0,
                'share_count': 0
            }
    
    def download_video(self, video_url, filename=None):
        """下载视频文件"""
        try:
            if not filename:
                filename = f"douyin_video_{int(time.time())}.mp4"
            
            response = self.session.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return filename
            
        except Exception as e:
            print(f"下载视频时出错: {e}")
            return None
    
    def process_share_url(self, share_url):
        """处理分享链接的完整流程"""
        try:
            # 1. 提取视频ID
            video_id = self.extract_video_id(share_url)
            if not video_id:
                return {'error': '无法提取视频ID'}
            
            # 2. 提取短链接
            short_url = self.extract_short_url(share_url)
            if short_url:
                print(f"提取到短链接: {short_url}")
            
            # 3. 获取视频信息
            video_info = self.get_video_info(video_id, short_url)
            if not video_info:
                return {'error': '无法获取视频信息'}
            
            # 4. 检查是否有视频URL（可选）
            if not video_info['video_url']:
                print("警告: 无法获取视频下载链接，但可以显示基本信息")
                # 不返回错误，而是继续显示基本信息
            
            return {
                'success': True,
                'video_id': video_id,
                'video_info': video_info,
                'has_download_url': bool(video_info['video_url'])
            }
            
        except Exception as e:
            return {'error': f'处理过程中出错: {str(e)}'}

# 使用示例
if __name__ == "__main__":
    downloader = DouyinDownloader()
    
    # 测试链接
    test_url = "https://v.douyin.com/xxxxx/"  # 替换为实际的抖音分享链接
    
    result = downloader.process_share_url(test_url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
