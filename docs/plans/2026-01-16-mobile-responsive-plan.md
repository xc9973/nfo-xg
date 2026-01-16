# 移动端响应式设计改进计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 优化 NFO 编辑器在移动设备上的显示和交互体验，确保在手机和平板上都能流畅使用。

**架构:** 基于现有响应式 CSS，添加移动端专用布局、触摸优化和自适应组件。

**技术栈:** CSS Media Queries、Flexbox/Grid、Viewport Meta、Touch Events

---

## 当前问题分析

1. **文件浏览器占用过多空间** - 移动端 300px 太宽
2. **表单输入框太小** - 触摸目标不够大
3. **模态框不适配小屏** - TMDB 搜索模态框在手机上显示不佳
4. **没有移动端导航** - 缺少汉堡菜单或标签切换
5. **键盘弹出遮挡输入** - 没有处理虚拟键盘问题

---

## Task 1: 优化文件浏览器移动端布局

**Files:**
- Modify: `web/static/style.css` (响应式部分)

**Step 1: 添加移动端断点**

在现有的 `@media (max-width: 768px)` 前添加新断点：

```css
/* 平板端 */
@media (max-width: 1024px) {
    .container {
        grid-template-columns: 250px 1fr;
    }

    .file-browser {
        font-size: 13px;
    }
}

/* 移动端 */
@media (max-width: 768px) {
    /* ... 现有样式 ... */
}

/* 小屏手机 */
@media (max-width: 480px) {
    /* 新增小屏优化 */
}
```

**Step 2: 优化移动端文件浏览器**

```css
@media (max-width: 768px) {
    .container {
        grid-template-columns: 1fr;
        grid-template-rows: auto 1fr;
    }

    .file-browser {
        max-height: 35vh;
        border-right: none;
        border-bottom: 1px solid #0f3460;
    }

    .file-browser h3 {
        font-size: 13px;
        padding: 10px;
    }

    .path-bar {
        font-size: 11px;
        padding: 8px;
    }

    .file-item {
        padding: 12px 10px;
        font-size: 14px; /* 增大触摸目标 */
    }

    .template-section {
        display: none; /* 移动端隐藏模板，使用独立面板 */
    }
}
```

**Step 3: 添加移动端模板按钮**

在 `index.html` 的搜索区域后添加：

```html
<!-- 在 search-section 后添加 -->
<div class="mobile-actions" style="display:none">
    <button class="btn btn-secondary" onclick="showMobileTemplates()" style="flex:1">📋 模板</button>
</div>
```

**Step 4: 添加移动端操作按钮样式**

```css
@media (max-width: 768px) {
    .mobile-actions {
        display: flex;
        gap: 10px;
        padding: 10px;
        border-top: 1px solid #0f3460;
    }
}
```

**Step 5: 测试移动端文件浏览器**

使用浏览器开发者工具切换到移动视图，预期：
- 文件浏览器在顶部，高度 35vh
- 模板区域隐藏
- 触摸目标足够大

**Step 6: 提交**

```bash
git add web/static/style.css
git commit -m "style: optimize file browser layout for mobile devices"
```

---

## Task 2: 增大触摸目标尺寸

**Files:**
- Modify: `web/static/style.css` (移动端样式)

**Step 1: 优化按钮触摸区域**

```css
@media (max-width: 768px) {
    .btn {
        padding: 12px 18px;
        font-size: 14px;
        min-height: 44px; /* iOS 推荐最小触摸目标 */
    }

    .btn-icon {
        min-width: 44px;
        min-height: 44px;
        padding: 12px;
    }

    .search-btn, .clear-btn {
        min-width: 44px;
        padding: 12px;
    }
}

@media (max-width: 480px) {
    .btn {
        width: 100%;
        margin-bottom: 10px;
    }

    .actions {
        flex-direction: column;
    }
}
```

**Step 2: 优化输入框触摸区域**

```css
@media (max-width: 768px) {
    input, select, textarea {
        padding: 12px 14px;
        font-size: 16px; /* 防止 iOS 自动缩放 */
        min-height: 44px;
    }

    textarea {
        min-height: 120px;
    }
}
```

**Step 3: 优化列表项触摸区域**

```css
@media (max-width: 768px) {
    .list-item {
        padding: 8px 12px;
        font-size: 14px;
        min-height: 40px;
    }

    .actor-item {
        grid-template-columns: 1fr;
        gap: 8px;
        padding: 12px;
    }

    .actor-item input {
        min-height: 44px;
    }
}
```

**Step 4: 测试触摸目标**

在移动设备上测试：
- 所有按钮可轻松点击
- 输入框不会触发缩放
- 列表项易于选择

**Step 5: 提交**

```bash
git add web/static/style.css
git commit -m "style: increase touch target sizes for mobile devices"
```

---

## Task 3: 优化模态框移动端体验

**Files:**
- Modify: `web/static/style.css` (模态框响应式)

**Step 1: 优化移动端模态框**

```css
@media (max-width: 768px) {
    .modal {
        padding: 10px;
    }

    .modal-content {
        width: 100%;
        max-width: 100%;
        max-height: 90vh;
        border-radius: 8px 8px 0 0; /* 底部圆角 */
        margin-top: auto; /* 推到底部 */
    }

    .modal-header {
        padding: 12px 15px;
    }

    .modal-header h3 {
        font-size: 16px;
    }

    .modal-body {
        padding: 15px;
    }
}

@media (max-width: 480px) {
    .modal-content {
        max-height: 85vh;
    }

    .modal-header {
        padding: 10px;
    }
}
```

**Step 2: 优化 TMDB 搜索栏**

```css
@media (max-width: 768px) {
    .tmdb-search-bar {
        flex-direction: column;
        gap: 8px;
    }

    .tmdb-search-bar input {
        width: 100%;
    }

    .tmdb-search-bar button {
        width: 100%;
    }
}
```

**Step 3: 优化搜索结果网格**

```css
@media (max-width: 768px) {
    .tmdb-results-grid {
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 10px;
    }

    .tmdb-title {
        font-size: 12px;
    }

    .tmdb-year {
        font-size: 10px;
    }
}

@media (max-width: 480px) {
    .tmdb-results-grid {
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
    }

    .tmdb-poster {
        aspect-ratio: 2/3;
    }

    .tmdb-info {
        padding: 6px;
    }

    .tmdb-type {
        font-size: 9px;
        padding: 1px 4px;
    }

    .tmdb-title {
        font-size: 11px;
    }
}
```

**Step 4: 添加模态框滑动关闭**

在 `index.html` 中添加：

```javascript
// 在模态框相关函数后添加
let touchStartY = 0;
let modalContent = null;

function handleTouchStart(e) {
    touchStartY = e.touches[0].clientY;
}

function handleTouchMove(e) {
    if (!modalContent) return;

    const touchY = e.touches[0].clientY;
    const diff = touchY - touchStartY;

    if (diff > 0) {
        modalContent.style.transform = `translateY(${diff}px)`;
    }
}

function handleTouchEnd(e) {
    if (!modalContent) return;

    const touchY = e.changedTouches[0].clientY;
    const diff = touchY - touchStartY;

    if (diff > 100) {
        closeTMDBModal();
    }

    modalContent.style.transform = '';
}

// 在打开模态框时添加触摸监听
const originalOpenTMDBSearch = openTMDBSearch;
openTMDBSearch = function() {
    originalOpenTMDBSearch();
    modalContent = document.querySelector('.modal-content');

    if (modalContent) {
        modalContent.addEventListener('touchstart', handleTouchStart);
        modalContent.addEventListener('touchmove', handleTouchMove);
        modalContent.addEventListener('touchend', handleTouchEnd);
    }
};

// 在关闭模态框时移除监听
const originalCloseTMDBModal = closeTMDBModal;
closeTMDBModal = function() {
    originalCloseTMDBModal();

    if (modalContent) {
        modalContent.removeEventListener('touchstart', handleTouchStart);
        modalContent.removeEventListener('touchmove', handleTouchMove);
        modalContent.removeEventListener('touchend', handleTouchEnd);
        modalContent = null;
    }
};
```

**Step 5: 测试移动端模态框**

在移动设备上测试：
- 模态框占据大部分屏幕
- 可向下滑动关闭
- 搜索按钮全宽

**Step 6: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: optimize modal for mobile with swipe-to-close"
```

---

## Task 4: 添加移动端导航

**Files:**
- Modify: `web/templates/index.html` (添加导航栏)
- Modify: `web/static/style.css` (导航样式)

**Step 1: 添加移动端底部导航**

在 `</body>` 前添加：

```html
<!-- 移动端底部导航 -->
<nav class="mobile-nav" style="display:none">
    <button class="nav-item active" onclick="showMobilePanel('files')">
        <span class="nav-icon">📁</span>
        <span class="nav-label">文件</span>
    </button>
    <button class="nav-item" onclick="showMobilePanel('editor')">
        <span class="nav-icon">✏️</span>
        <span class="nav-label">编辑</span>
    </button>
    <button class="nav-item" onclick="showMobilePanel('search')">
        <span class="nav-icon">🔍</span>
        <span class="nav-label">搜索</span>
    </button>
</nav>
```

**Step 2: 添加移动端导航样式**

```css
/* 移动端导航 */
.mobile-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #16213e;
    border-top: 1px solid #0f3460;
    display: flex;
    justify-content: space-around;
    padding: 8px 0;
    z-index: 1000;
    padding-bottom: env(safe-area-inset-bottom);
}

.nav-item {
    background: none;
    border: none;
    color: #666;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    padding: 8px 16px;
    min-width: 60px;
}

.nav-item.active {
    color: #e94560;
}

.nav-icon {
    font-size: 20px;
}

.nav-label {
    font-size: 11px;
}

@media (max-width: 768px) {
    .mobile-nav {
        display: flex !important;
    }

    .container {
        padding-bottom: 60px; /* 为导航栏留空间 */
    }
}
```

**Step 3: 添加面板切换功能**

```javascript
// 移动端面板管理
function showMobilePanel(panel) {
    const fileBrowser = document.querySelector('.file-browser');
    const editor = document.querySelector('.editor');
    const navItems = document.querySelectorAll('.nav-item');

    // 更新导航状态
    navItems.forEach(item => item.classList.remove('active'));
    event.target.closest('.nav-item').classList.add('active');

    // 切换面板
    switch(panel) {
        case 'files':
            fileBrowser.style.display = 'flex';
            editor.style.display = 'none';
            break;
        case 'editor':
            fileBrowser.style.display = 'none';
            editor.style.display = 'block';
            break;
        case 'search':
            document.getElementById('searchInput').focus();
            if (window.innerWidth <= 768) {
                showMobilePanel('files'); // 搜索在文件面板中
            }
            break;
    }
}

// 初始化：移动端默认显示文件面板
if (window.innerWidth <= 768) {
    showMobilePanel('files');
}
```

**Step 4: 在编辑文件时自动切换**

```javascript
// 修改 loadNfo 函数
async function loadNfo(path) {
    // ... 现有代码 ...

    // 移动端：加载后切换到编辑面板
    if (window.innerWidth <= 768) {
        setTimeout(() => showMobilePanel('editor'), 100);
    }
}
```

**Step 5: 测试移动端导航**

在移动设备上测试：
- 底部显示导航栏
- 点击切换面板
- 加载文件后自动切换到编辑

**Step 6: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add mobile bottom navigation with panel switching"
```

---

## Task 5: 优化虚拟键盘处理

**Files:**
- Modify: `web/templates/index.html` (键盘处理)
- Modify: `web/static/style.css** (视口样式)

**Step 1: 添加视口元标签优化**

更新 `<head>` 中的 viewport：

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
```

**Step 2: 添加键盘弹出处理**

```javascript
// 处理虚拟键盘弹出
let originalHeight = window.innerHeight;

window.addEventListener('resize', () => {
    const currentHeight = window.innerHeight;
    const keyboardHeight = originalHeight - currentHeight;

    // 如果键盘弹出（高度减少超过 150px）
    if (keyboardHeight > 150) {
        document.body.classList.add('keyboard-open');

        // 滚动到聚焦元素
        const activeElement = document.activeElement;
        if (activeElement) {
            activeElement.scrollIntoView({behavior: 'smooth', block: 'center'});
        }
    } else {
        document.body.classList.remove('keyboard-open');
    }
});

// 保存原始高度
window.addEventListener('load', () => {
    originalHeight = window.innerHeight;
});
```

**Step 3: 添加键盘打开时的样式**

```css
@media (max-width: 768px) {
    body.keyboard-open .mobile-nav {
        display: none; /* 键盘打开时隐藏导航 */
    }

    body.keyboard-open .container {
        padding-bottom: 0;
    }
}
```

**Step 4: 优化输入框焦点行为**

```css
@media (max-width: 768px) {
    input:focus, select:focus, textarea:focus {
        position: relative;
        z-index: 10;
    }
}
```

**Step 5: 测试虚拟键盘处理**

在移动设备上测试：
- 点击输入框时键盘弹出
- 输入框自动滚动到可见区域
- 键盘打开时底部导航隐藏

**Step 6: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: handle virtual keyboard on mobile devices"
```

---

## Task 6: 添加移动端手势支持

**Files:**
- Modify: `web/templates/index.html` (手势处理)

**Step 1: 添加滑动返回功能**

```javascript
// 移动端滑动手势
let touchStartX = 0;
let touchStartY = 0;

document.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
}, {passive: true});

document.addEventListener('touchend', (e) => {
    const touchEndX = e.changedTouches[0].clientX;
    const touchEndY = e.changedTouches[0].clientY;

    const diffX = touchEndX - touchStartX;
    const diffY = touchEndY - touchStartY;

    // 水平滑动超过 100px 且垂直滑动小于 50px
    if (Math.abs(diffX) > 100 && Math.abs(diffY) < 50) {
        if (diffX > 0) {
            // 右滑：返回文件面板
            const editor = document.querySelector('.editor');
            if (editor.style.display !== 'none' && window.innerWidth <= 768) {
                showMobilePanel('files');
            }
        }
    }
}, {passive: true});
```

**Step 2: 添加下拉刷新功能**

```javascript
// 下拉刷新
let pullStartY = 0;
let isPulling = false;
const pullThreshold = 80;

document.querySelector('.file-browser').addEventListener('touchstart', (e) => {
    const fileList = document.getElementById('fileList');
    if (fileList.scrollTop === 0) {
        pullStartY = e.touches[0].clientY;
        isPulling = true;
    }
}, {passive: true});

document.querySelector('.file-browser').addEventListener('touchmove', (e) => {
    if (!isPulling) return;

    const currentY = e.touches[0].clientY;
    const diff = currentY - pullStartY;

    if (diff > 0 && diff < pullThreshold * 2) {
        e.preventDefault();
        // 可以添加视觉反馈
    }
}, {passive: false});

document.querySelector('.file-browser').addEventListener('touchend', (e) => {
    if (!isPulling) return;

    const endY = e.changedTouches[0].clientY;
    const diff = endY - pullStartY;

    if (diff > pullThreshold) {
        // 刷新当前目录
        const currentPath = document.getElementById('currentPath').textContent;
        loadDir(currentPath === '~' ? '' : currentPath);
        showToast('已刷新', 'info');
    }

    isPulling = false;
}, {passive: true});
```

**Step 3: 测试手势功能**

在移动设备上测试：
- 在编辑器向右滑返回文件列表
- 在文件列表顶部下拉刷新

**Step 4: 提交**

```bash
git add web/templates/index.html
git commit -m "feat: add mobile gestures (swipe back, pull to refresh)"
```

---

## 验证步骤总结

**本地验证：**

```bash
# 1. 启动应用
cd /Volumes/1disk/项目/nfo-xg
python web/app.py

# 2. 使用浏览器开发者工具测试
# - Chrome DevTools > Toggle Device Toolbar
# - 测试不同设备尺寸 (iPhone, iPad, Android)
```

**测试设备清单：**

1. **小屏手机** (320px - 375px)
   - [ ] 文件浏览器高度适中
   - [ ] 触摸目标 >= 44px
   - [ ] 底部导航显示
   - [ ] 模态框全屏显示

2. **中大屏手机** (375px - 414px)
   - [ ] 搜索结果 3 列显示
   - [ ] 表单垂直排列
   - [ ] 手势响应灵敏

3. **平板** (768px - 1024px)
   - [ ] 文件浏览器 250px 宽
   - [ ] 双列布局保持
   - [ ] 模态框居中显示

**交互测试清单：**

1. **导航**
   - [ ] 底部导航切换面板
   - [ ] 右滑返回文件列表
   - [ ] 加载文件自动切换

2. **输入**
   - [ ] 键盘弹出不遮挡输入
   - [ ] 输入框不触发缩放
   - [ ] 自动滚动到焦点

3. **手势**
   - [ ] 下拉刷新文件列表
   - [ ] 滑动关闭模态框

**预期结果：**
- 所有触摸目标 >= 44px
- 没有水平滚动
- 虚拟键盘正确处理
- 手势响应流畅

---

## 风险与回退

**潜在问题：**
1. **兼容性** - 部分手势在某些设备不支持
2. **性能** - 频繁 DOM 操作可能影响性能
3. **样式冲突** - 媒体查询可能覆盖桌面样式

**回退方案：**
```bash
git reset --hard HEAD~6  # 回滚所有移动端改进
```

---

*计划版本: 1.0*
*创建日期: 2026-01-16*
