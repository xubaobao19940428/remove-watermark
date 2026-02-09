# TikTok 视频去水印工具

一个功能强大的 TikTok 视频去水印工具，支持解析分享链接、获取无水印视频、提取视频信息等功能。

## ✨ 功能特性

- 🔗 **智能解析** - 支持各种 TikTok 分享链接格式
- 🎬 **无水印下载** - 获取高质量无水印视频
- 📊 **信息提取** - 获取视频标题、作者、统计数据等
- 🎨 **现代界面** - 美观的响应式Web界面
- ⚡ **快速处理** - 高效的视频解析和下载
- 📱 **移动适配** - 完美支持手机和桌面设备

## 🚀 快速开始

### 环境要求

- Python 3.7+
- pip

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd remove-watermark
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
python app.py
```

4. **访问应用**
打开浏览器访问 `http://localhost:4000`

## 📖 使用说明

### 基本使用

1. **复制 TikTok 视频链接**
   - 在 TikTok 网页版或APP中复制视频链接
   - 推荐使用完整链接格式：`https://www.tiktok.com/@username/video/1234567890`
   - 注意：短链接 `vm.tiktok.com` 可能因反爬虫机制无法正常解析

2. **粘贴并解析**
   - 将链接粘贴到输入框
   - 点击"解析"按钮或按回车键

3. **查看视频信息**
   - 系统会显示视频封面、标题、作者等信息
   - 查看点赞、评论、分享等统计数据

4. **下载无水印视频**
   - 点击"下载无水印视频"按钮
   - 等待下载完成后点击"立即下载"

### 高级功能

- **自动粘贴** - 直接粘贴 TikTok 链接会自动填充并解析
- **复制信息** - 一键复制视频详细信息到剪贴板
- **文件清理** - 下载完成后可清理服务器上的临时文件

## 🛠️ 技术架构

### 后端技术
- **Flask** - Web框架
- **requests** - HTTP请求库
- **BeautifulSoup** - HTML解析
- **正则表达式** - URL解析

### 前端技术
- **Bootstrap 5** - UI框架
- **Font Awesome** - 图标库
- **原生JavaScript** - 交互逻辑
- **CSS3** - 样式和动画

### 核心模块

#### `tiktok_downloader.py`
- `TikTokDownloader` 类 - 核心下载器
- `extract_video_id()` - 提取视频ID
- `get_video_info()` - 获取视频信息
- `download_video()` - 下载视频文件

#### `app.py`
- Flask Web应用
- RESTful API接口
- 文件下载服务

## 🔧 配置说明

### 环境变量
```bash
# 可选：设置Flask环境
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### 自定义配置
可以在 `app.py` 中修改以下配置：

```python
# 下载目录
DOWNLOAD_DIR = 'downloads'

# 最大文件大小限制
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 服务器配置
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 📁 项目结构

```
remove-watermark/
├── app.py                 # Flask应用主文件
├── douyin_downloader.py  # 抖音下载器核心模块
├── requirements.txt      # Python依赖
├── README.md            # 项目说明
├── templates/           # HTML模板
│   └── index.html      # 主页面
├── static/             # 静态资源
│   ├── css/
│   │   └── style.css   # 样式文件
│   └── js/
│       └── app.js      # JavaScript逻辑
└── downloads/          # 下载文件目录（自动创建）
```

## 🔍 API接口

### 解析链接
```http
POST /api/parse
Content-Type: application/json

{
    "url": "TikTok 分享链接"
}
```

### 下载视频
```http
POST /api/download
Content-Type: application/json

{
    "video_url": "视频URL",
    "video_id": "视频ID"
}
```

### 清理文件
```http
POST /api/cleanup
Content-Type: application/json

{
    "filename": "文件名"
}
```

## 🛡️ 注意事项

1. **合法使用** - 请遵守相关法律法规，仅用于个人学习和研究
2. **版权尊重** - 尊重原创作者的版权，不要用于商业用途
3. **网络环境** - 确保网络连接稳定，避免下载中断
4. **存储空间** - 注意服务器存储空间，及时清理下载文件

## 🐛 常见问题

### Q: 解析失败怎么办？
A: 检查链接是否有效，确保网络连接正常，尝试刷新页面重试。

### Q: 下载速度慢？
A: 这取决于网络环境和视频大小，请耐心等待。

### Q: 支持哪些链接格式？
A: 主要支持完整的 TikTok 视频链接格式（如：https://www.tiktok.com/@username/video/1234567890）。短链接可能因 TikTok 的反爬虫机制无法正常解析。

### Q: 为什么无法获取视频下载链接？
A: TikTok 的反爬虫机制比抖音更严格，会返回压缩/加密数据而不是标准HTML。工具可以成功提取视频ID，但获取视频信息需要更复杂的浏览器环境模拟。建议使用浏览器开发者工具手动获取视频链接。

### Q: 如何批量下载？
A: 目前支持单个视频下载，批量功能正在开发中。

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 加入讨论群

---

**免责声明**: 本工具仅供学习和研究使用，使用者需自行承担使用风险，开发者不承担任何法律责任。
