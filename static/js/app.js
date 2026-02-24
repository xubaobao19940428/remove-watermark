// 核心状态管理
const state = {
    videoData: null,
    filename: null,
    originalUrl: null,
    platform: null
};

// DOM 元素引用
const elements = {
    shareUrlInput: document.getElementById("shareUrl"),
    parseBtn: document.getElementById("parseBtn"),
    loadingSection: document.getElementById("loading"),
    errorAlert: document.getElementById("errorAlert"),
    errorMessage: document.getElementById("errorMessage"),
    videoInfoSection: document.getElementById("videoInfo"),
    downloadBtn: document.getElementById("downloadBtn"),
    copyInfoBtn: document.getElementById("copyInfoBtn"),
    downloadProgress: document.getElementById("downloadProgress"),
    downloadComplete: document.getElementById("downloadComplete"),
    downloadLink: document.getElementById("downloadLink"),
    cleanupBtn: document.getElementById("cleanupBtn"),
    coverImage: document.getElementById("coverImage")
};

// 初始化
document.addEventListener("DOMContentLoaded", () => {
    initEvents();
    initAnimations();
});

function initEvents() {
    elements.parseBtn.addEventListener("click", handleParse);
    
    elements.shareUrlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") handleParse();
    });

    elements.downloadBtn.addEventListener("click", handleDownload);
    elements.copyInfoBtn.addEventListener("click", handleCopyInfo);
    elements.cleanupBtn.addEventListener("click", handleCleanup);

    // 智能剪贴板监听
    window.addEventListener('focus', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (isValidUrl(text) && text !== state.originalUrl) {
                elements.shareUrlInput.value = text;
            }
        } catch (e) {}
    });
}

function initAnimations() {
    // 按钮交互
    const btns = document.querySelectorAll('.btn');
    btns.forEach(btn => {
        btn.addEventListener('mousedown', () => btn.style.transform = 'scale(0.95)');
        btn.addEventListener('mouseup', () => btn.style.transform = 'scale(1)');
    });
}

async function handleParse() {
    const url = elements.shareUrlInput.value.trim();
    if (!url) return notify('warning', '请输入解析链接');
    if (!isValidUrl(url)) return notify('error', '链接格式无效');

    toggleUI('loading', true);
    toggleUI('error', false);
    toggleUI('video', false);

    try {
        const res = await fetch("/api/parse", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            state.videoData = data;
            state.originalUrl = url;
            state.platform = data.platform;
            renderVideoInfo(data.video_info);
        } else {
            notify('error', data.error || "解析引擎繁忙，请稍后再试");
        }
    } catch (e) {
        notify('error', "云端连接失败，请检查网络");
    } finally {
        toggleUI('loading', false);
    }
}

async function handleDownload() {
    if (!state.videoData) return;

    toggleUI('progress', true);
    toggleUI('video', false);

    try {
        const res = await fetch("/api/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                video_url: state.videoData.video_info.video_url,
                video_id: state.videoData.video_id,
                original_url: state.originalUrl,
                platform: state.platform
            })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            state.filename = data.filename;
            elements.downloadLink.href = data.download_url;
            toggleUI('complete', true);
        } else {
            notify('error', data.error || "下载任务失败");
            toggleUI('video', true);
        }
    } catch (e) {
        notify('error', "下载引擎异常");
        toggleUI('video', true);
    } finally {
        toggleUI('progress', false);
    }
}

function renderVideoInfo(info) {
    // 封面代理逻辑
    const needsProxy = /instagram|cdninstagram|fbcdn/.test(info.cover_url);
    elements.coverImage.src = needsProxy 
        ? `/api/proxy-image?url=${encodeURIComponent(info.cover_url)}`
        : (info.cover_url || '');

    elements.coverImage.onerror = () => {
        elements.coverImage.src = 'https://placehold.co/600x400/1e1b4b/white?text=Preview+Unavailable';
    };

    document.getElementById("videoTitle").textContent = info.title || "无标题视频";
    document.getElementById("videoAuthor").textContent = info.author || "佚名";
    document.getElementById("likeCount").textContent = formatNum(info.like_count);
    document.getElementById("commentCount").textContent = formatNum(info.comment_count);
    document.getElementById("shareCount").textContent = formatNum(info.share_count || info.view_count);
    document.getElementById("duration").textContent = formatTime(info.duration);

    toggleUI('video', true);
    window.scrollTo({ top: elements.videoInfoSection.offsetTop - 50, behavior: 'smooth' });
}

function handleCopyInfo() {
    const info = state.videoData.video_info;
    const text = `【${info.title}】\n作者：${info.author}\n链接：${state.originalUrl}`;
    navigator.clipboard.writeText(text).then(() => notify('success', '文案已成功存入剪贴板'));
}

async function handleCleanup() {
    if (!state.filename) return;
    try {
        await fetch("/api/cleanup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: state.filename })
        });
        state.filename = null;
        toggleUI('complete', false);
        notify('success', '缓存已清理');
    } catch (e) {}
}

// 辅助工具
function toggleUI(key, show) {
    const map = {
        loading: elements.loadingSection,
        error: elements.errorAlert,
        video: elements.videoInfoSection,
        progress: elements.downloadProgress,
        complete: elements.downloadComplete
    };
    if (map[key]) map[key].style.display = show ? "block" : "none";
}

function notify(type, msg) {
    if (type === 'error') {
        elements.errorMessage.textContent = msg;
        toggleUI('error', true);
    } else {
        const toast = document.createElement('div');
        toast.className = `glass-panel fixed-top m-3 p-3 text-center border-${type}`;
        toast.style.zIndex = 9999;
        toast.style.maxWidth = '400px';
        toast.style.left = '50%';
        toast.style.transform = 'translateX(-50%)';
        toast.innerHTML = `<i class="fas fa-check-circle me-2"></i>${msg}`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}

function isValidUrl(url) {
    return /tiktok|douyin|instagram|youtube|twitter|x\.com|facebook|bilibili|weibo/.test(url.toLowerCase());
}

function formatNum(n) {
    if (!n) return '0';
    return n >= 10000 ? (n/10000).toFixed(1) + 'w' : n.toLocaleString();
}

function formatTime(s) {
    if (!s) return '0s';
    const m = Math.floor(s / 60);
    return m > 0 ? `${m}m ${s%60}s` : `${s}s`;
}

