// 全局变量
let currentVideoData = null;
let currentFilename = null;
let originalUrl = null;
let currentPlatform = null;

// DOM元素
const shareUrlInput = document.getElementById("shareUrl");
const parseBtn = document.getElementById("parseBtn");
const loadingSection = document.getElementById("loading");
const errorAlert = document.getElementById("errorAlert");
const errorMessage = document.getElementById("errorMessage");
const videoInfoSection = document.getElementById("videoInfo");
const downloadBtn = document.getElementById("downloadBtn");
const copyInfoBtn = document.getElementById("copyInfoBtn");
const downloadProgress = document.getElementById("downloadProgress");
const downloadComplete = document.getElementById("downloadComplete");
const downloadLink = document.getElementById("downloadLink");
const cleanupBtn = document.getElementById("cleanupBtn");

// 页面加载完成后初始化
document.addEventListener("DOMContentLoaded", function () {
  initializeEventListeners();
  setupAutoPaste();
});

// 初始化事件监听器
function initializeEventListeners() {
  // 解析按钮点击事件
  parseBtn.addEventListener("click", handleParseClick);

  // 回车键解析
  shareUrlInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      handleParseClick();
    }
  });

  // 下载按钮点击事件
  downloadBtn.addEventListener("click", handleDownloadClick);

  // 复制信息按钮点击事件
  copyInfoBtn.addEventListener("click", handleCopyInfoClick);

  // 清理文件按钮点击事件
  cleanupBtn.addEventListener("click", handleCleanupClick);
}

// 设置自动粘贴功能
function setupAutoPaste() {
  // 监听粘贴事件
  document.addEventListener("paste", function (e) {
    const pastedText = e.clipboardData.getData("text");
    if (
      pastedText &&
      (pastedText.includes("tiktok.com") ||
        pastedText.includes("vm.tiktok.com"))
    ) {
      shareUrlInput.value = pastedText.trim();
      // 自动解析
      setTimeout(() => {
        handleParseClick();
      }, 100);
    }
  });
}

// 处理解析按钮点击
async function handleParseClick() {
  const url = shareUrlInput.value.trim();

  if (!url) {
    showError("请输入 TikTok 分享链接");
    return;
  }

  if (!isValidTikTokUrl(url)) {
    showError("请输入有效的 TikTok 分享链接");
    return;
  }

  // 显示加载状态
  showLoading();
  hideError();
  hideVideoInfo();

  try {
    const response = await fetch("/api/parse", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: url }),
    });

    const result = await response.json();

    if (response.ok) {
      if (result.success) {
        currentVideoData = result;
        originalUrl = url; // 保存原始URL用于下载
        currentPlatform = result.platform || 'unknown'; // 保存平台信息
        displayVideoInfo(result.video_info, result.platform_name);
      } else {
        showError(result.error || "解析失败");
      }
    } else {
      showError(result.error || "服务器错误");
    }
  } catch (error) {
    console.error("解析错误:", error);
    showError("网络错误，请检查网络连接");
  } finally {
    hideLoading();
  }
}

// 处理下载按钮点击
async function handleDownloadClick() {
  if (!currentVideoData) {
    showError("请先解析视频信息");
    return;
  }

  const videoUrl = currentVideoData.video_info.video_url;
  const videoId = currentVideoData.video_id;

  if (!videoUrl) {
    showError("无法获取视频下载链接");
    return;
  }

  // 显示下载进度
  showDownloadProgress();
  hideVideoInfo();

  try {
    const response = await fetch("/api/download", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        video_url: videoUrl,
        video_id: videoId,
        original_url: originalUrl, // 传递原始URL给后端
        platform: currentPlatform, // 传递平台信息
      }),
    });

    const result = await response.json();

    if (response.ok && result.success) {
      currentFilename = result.filename;
      showDownloadComplete(result.download_url);
    } else {
      showError(result.error || "下载失败");
    }
  } catch (error) {
    console.error("下载错误:", error);
    showError("下载失败，请重试");
  } finally {
    hideDownloadProgress();
  }
}

// 处理复制信息按钮点击
function handleCopyInfoClick() {
  if (!currentVideoData) {
    showError("没有可复制的信息");
    return;
  }

  const videoInfo = currentVideoData.video_info;
  const infoText = `视频标题：${videoInfo.title}\n作者：${videoInfo.author}\n点赞：${formatNumber(videoInfo.like_count)}\n评论：${formatNumber(videoInfo.comment_count)}\n分享：${formatNumber(videoInfo.share_count)}\n时长：${formatDuration(videoInfo.duration)}`;

  navigator.clipboard
    .writeText(infoText)
    .then(() => {
      showSuccessMessage("视频信息已复制到剪贴板");
    })
    .catch(() => {
      // 降级方案
      const textArea = document.createElement("textarea");
      textArea.value = infoText;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      showSuccessMessage("视频信息已复制到剪贴板");
    });
}

// 处理清理文件按钮点击
async function handleCleanupClick() {
  if (!currentFilename) {
    showError("没有可清理的文件");
    return;
  }

  try {
    const response = await fetch("/api/cleanup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ filename: currentFilename }),
    });

    const result = await response.json();

    if (response.ok && result.success) {
      showSuccessMessage("文件已清理");
      hideDownloadComplete();
      currentFilename = null;
    } else {
      showError(result.error || "清理失败");
    }
  } catch (error) {
    console.error("清理错误:", error);
    showError("清理失败");
  }
}

// 显示视频信息
function displayVideoInfo(videoInfo) {
  // 设置封面图（使用代理解决跨域和防盗链问题）
  const coverImage = document.getElementById("coverImage");
  if (videoInfo.cover_url) {
    // 对于 Instagram 等平台，使用代理加载封面图
    const needsProxy = videoInfo.cover_url.includes('instagram') || 
                       videoInfo.cover_url.includes('cdninstagram') ||
                       videoInfo.cover_url.includes('fbcdn');
    if (needsProxy) {
      coverImage.src = `/api/proxy-image?url=${encodeURIComponent(videoInfo.cover_url)}`;
    } else {
      coverImage.src = videoInfo.cover_url;
    }
    // 添加错误处理，如果加载失败则尝试使用代理
    coverImage.onerror = function() {
      if (!this.src.includes('/api/proxy-image')) {
        this.src = `/api/proxy-image?url=${encodeURIComponent(videoInfo.cover_url)}`;
      } else {
        // 代理也失败，使用占位图
        this.src = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuaXoOazleWKoOi9veWwgemdojwvdGV4dD48L3N2Zz4=";
      }
    };
  } else {
    coverImage.src =
      "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuekuuS+i+WbvueJhzwvdGV4dD48L3N2Zz4=";
  }

  // 设置标题
  document.getElementById("videoTitle").textContent =
    videoInfo.title || "无标题";

  // 设置作者
  const authorSpan = document.querySelector("#videoAuthor span");
  authorSpan.textContent = videoInfo.author || "未知作者";

  // 设置统计数据 (处理新旧字段名兼容)
  document.getElementById("likeCount").textContent = formatNumber(
    videoInfo.like_count || 0,
  );
  document.getElementById("commentCount").textContent = formatNumber(
    videoInfo.comment_count || 0,
  );
  document.getElementById("shareCount").textContent = formatNumber(
    videoInfo.share_count || videoInfo.view_count || 0,
  );
  document.getElementById("duration").textContent = formatDuration(
    videoInfo.duration || 0,
  );

  // 检查是否有可用的下载链接
  const downloadBtn = document.getElementById("downloadBtn");
  const actionButtons = document.querySelector(".action-buttons");

  // 清除之前的提示信息
  const existingNotice = document.getElementById("downloadNotice");
  if (existingNotice) {
    existingNotice.remove();
  }

  if (
    videoInfo.video_url &&
    (videoInfo.video_url.includes("tiktokcdn.com") ||
      videoInfo.video_url.includes("ttwstatic.com") ||
      videoInfo.video_url.includes("tiktokv.com"))
  ) {
    // 有真实的下载链接
    downloadBtn.disabled = false;
    downloadBtn.innerHTML = '<i class="fas fa-download"></i> 下载无水印视频';
    downloadBtn.className = "btn btn-success";

    // 添加成功提示
    const notice = document.createElement("div");
    notice.id = "downloadNotice";
    notice.className = "alert alert-success mt-2";
    notice.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <strong>成功！</strong>已获取到真实的无水印视频下载链接。
            <br><small>${videoInfo.note || ""}</small>
        `;
    actionButtons.appendChild(notice);
  } else if (
    videoInfo.video_url &&
    !videoInfo.video_url.includes("example.com")
  ) {
    // 有其他类型的下载链接
    downloadBtn.disabled = false;
    downloadBtn.innerHTML = '<i class="fas fa-download"></i> 下载视频';
    downloadBtn.className = "btn btn-primary";
  } else {
    // 没有下载链接
    downloadBtn.disabled = true;
    downloadBtn.innerHTML =
      '<i class="fas fa-info-circle"></i> 暂无法自动下载（API限制）';
    downloadBtn.className = "btn btn-secondary";

    // 添加提示信息和替代方案
    const notice = document.createElement("div");
    notice.id = "downloadNotice";
    notice.className = "alert alert-info mt-2";

    let alternativesHtml = "";
    if (videoInfo.alternatives && videoInfo.alternatives.length > 0) {
      alternativesHtml =
        '<div class="mt-3"><strong>替代方案：</strong><div class="row mt-2">';
      videoInfo.alternatives.forEach((alt) => {
        alternativesHtml += `
                        <div class="col-md-4 mb-2">
                            <div class="card">
                                <div class="card-body p-2">
                                    <h6 class="card-title">${alt.name}</h6>
                                    <p class="card-text small">${alt.description}</p>
                                    <a href="${alt.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                        <i class="fas fa-external-link-alt"></i> 访问
                                    </a>
                                </div>
                            </div>
                        </div>
                    `;
      });
      alternativesHtml += "</div></div>";
    }

    notice.innerHTML = `
                <i class="fas fa-info-circle"></i>
                <strong>提示：</strong>由于 TikTok 反爬虫机制较严格，暂时无法自动获取视频下载链接。
                <br><small>${videoInfo.note || "建议使用浏览器开发者工具手动获取视频链接"}</small>
                ${alternativesHtml}
            `;

    actionButtons.appendChild(notice);
  }

  // 显示视频信息区域
  showVideoInfo();
}

// 验证视频URL（支持多平台）
function isValidTikTokUrl(url) {
  const patterns = [
    // TikTok
    /tiktok\.com/,
    /vm\.tiktok\.com/,
    // 抖音
    /douyin\.com/,
    /iesdouyin\.com/,
    // Instagram
    /instagram\.com/,
    /instagr\.am/,
    // YouTube
    /youtube\.com/,
    /youtu\.be/,
    // Twitter/X
    /twitter\.com/,
    /x\.com/,
    // Facebook
    /facebook\.com/,
    /fb\.watch/,
    // Bilibili
    /bilibili\.com/,
    /b23\.tv/,
    // 微博
    /weibo\.com/,
    /weibo\.cn/,
  ];
  return patterns.some((p) => p.test(url));
}

// 格式化数字
function formatNumber(num) {
  if (num === undefined || num === null) {
    return "0";
  }
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + "万";
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num.toString();
}

// 格式化时长
function formatDuration(seconds) {
  if (!seconds) return "0s";

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes > 0) {
    return `${minutes}分${remainingSeconds}秒`;
  }
  return `${remainingSeconds}秒`;
}

// 显示/隐藏函数
function showLoading() {
  loadingSection.style.display = "block";
  parseBtn.disabled = true;
}

function hideLoading() {
  loadingSection.style.display = "none";
  parseBtn.disabled = false;
}

function showError(message) {
  errorMessage.textContent = message;
  errorAlert.style.display = "block";
}

function hideError() {
  errorAlert.style.display = "none";
}

function showVideoInfo() {
  videoInfoSection.style.display = "block";
}

function hideVideoInfo() {
  videoInfoSection.style.display = "none";
}

function showDownloadProgress() {
  downloadProgress.style.display = "block";
}

function hideDownloadProgress() {
  downloadProgress.style.display = "none";
}

function showDownloadComplete(downloadUrl) {
  downloadLink.href = downloadUrl;
  downloadComplete.style.display = "block";
}

function hideDownloadComplete() {
  downloadComplete.style.display = "none";
}

function showSuccessMessage(message) {
  // 创建临时成功消息
  const successAlert = document.createElement("div");
  successAlert.className = "alert alert-success";
  successAlert.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
  successAlert.style.position = "fixed";
  successAlert.style.top = "20px";
  successAlert.style.right = "20px";
  successAlert.style.zIndex = "9999";
  successAlert.style.minWidth = "300px";

  document.body.appendChild(successAlert);

  // 3秒后自动移除
  setTimeout(() => {
    if (successAlert.parentNode) {
      successAlert.parentNode.removeChild(successAlert);
    }
  }, 3000);
}

// 添加一些交互效果
document.addEventListener("DOMContentLoaded", function () {
  // 输入框焦点效果
  shareUrlInput.addEventListener("focus", function () {
    this.parentElement.style.transform = "scale(1.02)";
  });

  shareUrlInput.addEventListener("blur", function () {
    this.parentElement.style.transform = "scale(1)";
  });

  // 按钮悬停效果
  const buttons = document.querySelectorAll(".btn");
  buttons.forEach((button) => {
    button.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-2px)";
    });

    button.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0)";
    });
  });
});
