# TMDB 前端实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 TMDB 搜索模态框 UI 和表单自动填充功能，允许用户从 TMDB API 搜索并自动填充 NFO 数据。

**架构:** 前端原生 JavaScript 实现搜索模态框，通过已实现的 FastAPI 端点与 TMDB 通信，获取数据后自动填充现有表单字段。

**技术栈:** 原生 JavaScript (ES6+)、CSS Grid/Flexbox、Fetch API、FastAPI 后端（已实现）

---

## Task 1: 添加 TMDB 搜索按钮到表单

**Files:**
- Modify: `web/templates/index.html:115-117`

**Step 1: 在标题字段添加搜索按钮**

找到标题字段的 form-group，在输入框后添加搜索按钮：

```html
<div class="form-group">
    <label>标题</label>
    <div class="input-with-action">
        <input type="text" id="title" value="${esc(d.title)}">
        <button class="btn btn-primary btn-icon" onclick="openTMDBSearch()" title="从 TMDB 搜索">🔍</button>
    </div>
</div>
```

**Step 2: 在 CSS 中添加 input-with-action 样式**

**File:** `web/static/style.css`

在 form-group 相关样式后添加（约第 89 行后）：

```css
/* Input with action button */
.input-with-action {
    display: flex;
    gap: 5px;
}

.input-with-action input {
    flex: 1;
}

.btn-icon {
    padding: 10px;
    min-width: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
}
```

**Step 3: 添加 openTMDBSearch 空函数占位**

**File:** `web/templates/index.html`

在 script 区域添加（约第 300 行后，搜索功能前）：

```javascript
// ========== TMDB 搜索功能 ==========

function openTMDBSearch() {
    // 待实现
}
```

**Step 4: 测试按钮显示**

运行: `python web/app.py`
访问: `http://localhost:8000`
预期: 标题字段旁边显示搜索按钮

**Step 5: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add TMDB search button to title field"
```

---

## Task 2: 创建 TMDB 搜索模态框 HTML 结构

**Files:**
- Modify: `web/templates/index.html:534` (body 结束标签前)

**Step 1: 在 body 结束前添加模态框 HTML**

```html
<!-- TMDB 搜索模态框 -->
<div id="tmdbModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>🎬 搜索 TMDB</h3>
            <button class="modal-close" onclick="closeTMDBModal()">×</button>
        </div>
        <div class="modal-body">
            <div class="tmdb-search-bar">
                <input type="text" id="tmdbSearchInput" placeholder="输入电影或剧集名称..."
                    onkeypress="if(event.key==='Enter')searchTMDB()">
                <button class="btn btn-primary" onclick="searchTMDB()">搜索</button>
            </div>
            <div id="tmdbLoading" class="tmdb-loading" style="display:none">
                <span class="spinner"></span> 搜索中...
            </div>
            <div id="tmdbError" class="tmdb-error" style="display:none"></div>
            <div id="tmdbResults" class="tmdb-results"></div>
        </div>
    </div>
</div>
```

**Step 2: 添加模态框 CSS 样式**

**File:** `web/static/style.css`

在文件末尾添加：

```css
/* Modal */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    z-index: 2000;
    align-items: center;
    justify-content: center;
}

.modal.active {
    display: flex;
}

.modal-content {
    background: #16213e;
    border-radius: 8px;
    width: 90%;
    max-width: 800px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    border-bottom: 1px solid #0f3460;
}

.modal-header h3 {
    margin: 0;
    color: #e94560;
    font-size: 18px;
}

.modal-close {
    background: none;
    border: none;
    color: #aaa;
    font-size: 28px;
    cursor: pointer;
    padding: 0;
    line-height: 1;
}

.modal-close:hover {
    color: #e94560;
}

.modal-body {
    padding: 20px;
    overflow-y: auto;
}
```

**Step 3: 测试模态框结构**

修改 `openTMDBSearch` 函数测试显示：

```javascript
function openTMDBSearch() {
    document.getElementById('tmdbModal').classList.add('active');
}
```

运行: `python web/app.py`
点击搜索按钮，预期: 显示模态框

**Step 4: 实现关闭模态框函数**

在 `openTMDBSearch` 后添加：

```javascript
function closeTMDBModal() {
    document.getElementById('tmdbModal').classList.remove('active');
}
```

**Step 5: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add TMDB search modal HTML and base styles"
```

---

## Task 3: 添加 TMDB 搜索栏样式

**Files:**
- Modify: `web/static/style.css` (末尾)

**Step 1: 添加 TMDB 搜索相关样式**

```css
/* TMDB Search Bar */
.tmdb-search-bar {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
}

.tmdb-search-bar input {
    flex: 1;
    padding: 12px 15px;
    font-size: 14px;
}

.tmdb-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 30px;
    color: #aaa;
}

.tmdb-error {
    padding: 15px;
    background: rgba(231, 76, 60, 0.2);
    border: 1px solid #e74c3c;
    border-radius: 4px;
    color: #e74c3c;
    margin-bottom: 15px;
}
```

**Step 2: 提交**

```bash
git add web/static/style.css
git commit -m "style: add TMDB search bar styles"
```

---

## Task 4: 实现 TMDB 搜索 JavaScript 函数

**Files:**
- Modify: `web/templates/index.html` (在 TMDB 搜索功能区域)

**Step 1: 实现 searchTMDB 函数**

替换之前的占位函数：

```javascript
async function searchTMDB() {
    const query = document.getElementById('tmdbSearchInput').value.trim();
    if (!query) {
        showToast('请输入搜索关键词', 'error');
        return;
    }

    const loading = document.getElementById('tmdbLoading');
    const errorDiv = document.getElementById('tmdbError');
    const resultsDiv = document.getElementById('tmdbResults');

    // UI 状态
    loading.style.display = 'flex';
    errorDiv.style.display = 'none';
    resultsDiv.innerHTML = '';

    try {
        const res = await fetch(`/api/tmdb/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || '搜索失败');
        }

        renderTMDBResults(data.results);
    } catch (e) {
        errorDiv.textContent = e.message;
        errorDiv.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
}
```

**Step 2: 实现结果渲染函数**

在 `searchTMDB` 后添加：

```javascript
function renderTMDBResults(results) {
    const container = document.getElementById('tmdbResults');

    if (results.length === 0) {
        container.innerHTML = '<div class="tmdb-no-results">未找到匹配结果</div>';
        return;
    }

    let html = '<div class="tmdb-results-grid">';
    for (const item of results) {
        const posterUrl = item.poster_url
            ? item.poster_url
            : 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300"><rect fill="%232a2a4a" width="200" height="300"/><text fill="%23666" x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="24">🎬</text></svg>';
        const year = item.year || '未知';
        const typeLabel = item.media_type === 'movie' ? '电影' : '剧集';

        html += `
            <div class="tmdb-result-card" onclick="selectTMDBResult(${item.id}, '${item.media_type}')">
                <div class="tmdb-poster">
                    <img src="${posterUrl}" alt="${esc(item.title)}" loading="lazy">
                </div>
                <div class="tmdb-info">
                    <span class="tmdb-type">${typeLabel}</span>
                    <div class="tmdb-title">${esc(item.title)}</div>
                    <div class="tmdb-year">${year}</div>
                </div>
            </div>
        `;
    }
    html += '</div>';
    container.innerHTML = html;
}
```

**Step 3: 添加搜索结果容器样式**

**File:** `web/static/style.css` (末尾)

```css
/* TMDB Results */
.tmdb-results {
    margin-top: 15px;
}

.tmdb-no-results {
    padding: 40px;
    text-align: center;
    color: #666;
    font-size: 14px;
}

.tmdb-results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
}

.tmdb-result-card {
    background: #0f3460;
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

.tmdb-result-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 20px rgba(233, 69, 96, 0.3);
}

.tmdb-poster {
    width: 100%;
    aspect-ratio: 2/3;
    overflow: hidden;
    background: #1a1a2e;
}

.tmdb-poster img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.tmdb-info {
    padding: 10px;
}

.tmdb-type {
    display: inline-block;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
    background: #e94560;
    color: white;
    margin-bottom: 5px;
}

.tmdb-title {
    font-size: 13px;
    font-weight: 500;
    color: #eee;
    margin-bottom: 3px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.tmdb-year {
    font-size: 11px;
    color: #aaa;
}
```

**Step 4: 测试搜索功能**

运行: `python web/app.py`
1. 点击搜索按钮打开模态框
2. 输入关键词搜索
预期: 显示搜索结果卡片网格

**Step 5: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: implement TMDB search and results rendering"
```

---

## Task 5: 实现 TMDB 结果选择和数据获取

**Files:**
- Modify: `web/templates/index.html` (在 TMDB 搜索功能区域)

**Step 1: 实现 selectTMDBResult 函数**

在 `renderTMDBResults` 后添加：

```javascript
async function selectTMDBResult(tmdbId, mediaType) {
    const loading = document.getElementById('tmdbLoading');
    const errorDiv = document.getElementById('tmdbError');

    loading.style.display = 'flex';
    errorDiv.style.display = 'none';

    try {
        let endpoint;
        if (mediaType === 'movie') {
            endpoint = `/api/tmdb/movie/${tmdbId}`;
        } else {
            endpoint = `/api/tmdb/tv/${tmdbId}`;
        }

        const res = await fetch(endpoint);
        const nfoData = await res.json();

        if (!res.ok) {
            throw new Error(nfoData.detail || '获取详情失败');
        }

        // 填充表单
        applyTMDBData(nfoData);

        // 关闭模态框
        closeTMDBModal();
        showToast('已从 TMDB 获取数据', 'success');
    } catch (e) {
        errorDiv.textContent = e.message;
        errorDiv.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
}
```

**Step 2: 实现 applyTMDBData 函数**

在 `selectTMDBResult` 后添加：

```javascript
function applyTMDBData(data) {
    // 更新 nfoData 对象
    nfoData.nfo_type = data.nfo_type || nfoData.nfo_type;
    nfoData.title = data.title || '';
    nfoData.originaltitle = data.originaltitle || '';
    nfoData.year = data.year || '';
    nfoData.plot = data.plot || '';
    nfoData.runtime = data.runtime || '';
    nfoData.rating = data.rating || '';
    nfoData.genres = data.genres || [];
    nfoData.directors = data.directors || [];
    nfoData.actors = data.actors || [];
    nfoData.studio = data.studio || '';
    nfoData.poster = data.poster || '';
    nfoData.fanart = data.fanart || '';
    nfoData.season = data.season || '';
    nfoData.episode = data.episode || '';
    nfoData.aired = data.aired || '';

    // 重新渲染表单
    renderEditor();
}
```

**Step 3: 修改 openTMDBSearch 预填当前标题**

更新 `openTMDBSearch` 函数：

```javascript
function openTMDBSearch() {
    const modal = document.getElementById('tmdbModal');
    const searchInput = document.getElementById('tmdbSearchInput');

    // 预填当前标题作为搜索词
    const currentTitle = document.getElementById('title')?.value || '';
    searchInput.value = currentTitle;

    // 清空之前的结果
    document.getElementById('tmdbResults').innerHTML = '';
    document.getElementById('tmdbError').style.display = 'none';

    modal.classList.add('active');

    // 如果有预填内容，自动搜索
    if (currentTitle) {
        searchTMDB();
    } else {
        searchInput.focus();
    }
}
```

**Step 4: 测试完整流程**

运行: `python web/app.py`
1. 打开或创建 NFO 文件
2. 点击搜索按钮
3. 搜索电影
4. 选择结果
预期: 表单自动填充数据

**Step 5: 提交**

```bash
git add web/templates/index.html
git commit -m "feat: implement TMDB result selection and form auto-fill"
```

---

## Task 6: 添加 ESC 键关闭模态框

**Files:**
- Modify: `web/templates/index.html` (在 script 区域)

**Step 1: 添加键盘事件监听**

在 `loadTemplates()` 调用后添加：

```javascript
// 键盘事件
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeTMDBModal();
    }
});
```

**Step 2: 测试 ESC 键**

按 ESC 键，预期: 模态框关闭

**Step 3: 提交**

```bash
git add web/templates/index.html
git commit -m "feat: add ESC key to close TMDB modal"
```

---

## Task 7: 添加点击模态框背景关闭

**Files:**
- Modify: `web/templates/index.html`

**Step 1: 修改模态框 HTML**

更新模态框 div 添加点击事件：

```html
<div id="tmdbModal" class="modal" onclick="handleModalClick(event)">
```

**Step 2: 实现点击处理函数**

在 `closeTMDBModal` 后添加：

```javascript
function handleModalClick(event) {
    if (event.target.id === 'tmdbModal') {
        closeTMDBModal();
    }
}
```

**Step 3: 测试点击背景关闭**

点击模态框外部区域，预期: 模态框关闭

**Step 4: 提交**

```bash
git add web/templates/index.html
git commit -m "feat: add click outside to close TMDB modal"
```

---

## Task 8: 添加响应式样式优化

**Files:**
- Modify: `web/static/style.css`

**Step 1: 在响应式区域添加模态框样式**

找到 `@media (max-width: 768px)` 部分（约第 222 行），在其中添加：

```css
@media (max-width: 768px) {
    /* ... 现有样式 ... */

    .modal-content {
        width: 95%;
        max-height: 90vh;
    }

    .tmdb-results-grid {
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 10px;
    }

    .tmdb-title {
        font-size: 12px;
    }
}
```

**Step 2: 测试移动端显示**

使用浏览器开发者工具切换到移动视图，预期: 模态框和结果网格适应小屏幕

**Step 3: 提交**

```bash
git add web/static/style.css
git commit -m "style: add responsive styles for TMDB modal"
```

---

## Task 9: 手动测试完整流程

**Files:** 无（测试步骤）

**Step 1: 启动应用**

```bash
cd /Users/duola/Downloads/nfo-xg
python web/app.py
```

**Step 2: 测试清单**

1. **基本功能**
   - [ ] 点击搜索按钮打开模态框
   - [ ] 输入关键词搜索
   - [ ] 查看搜索结果（带海报）
   - [ ] 点击结果选择
   - [ ] 表单自动填充
   - [ ] 显示成功提示

2. **交互功能**
   - [ ] ESC 键关闭模态框
   - [ ] 点击 × 关闭模态框
   - [ ] 点击背景关闭模态框
   - [ ] 预填当前标题作为搜索词
   - [ ] 有内容时自动搜索

3. **边界情况**
   - [ ] 空搜索词提示
   - [ ] 无搜索结果显示
   - [ ] API 错误显示
   - [ ] 无海报时显示占位图
   - [ ] 长标题截断显示

4. **响应式**
   - [ ] 移动端模态框大小
   - [ ] 结果网格自适应

**Step 3: 验证数据映射**

检查以下字段是否正确填充：
- [ ] title / originaltitle
- [ ] year
- [ ] plot
- [ ] runtime
- [ ] rating
- [ ] genres (列表)
- [ ] directors (列表)
- [ ] actors (带 name, role)
- [ ] studio
- [ ] poster / fanart

---

## Task 10: 清理和优化

**Files:**
- Modify: `web/templates/index.html`

**Step 1: 整理 TMDB 功能代码区域**

确保所有 TMDB 相关函数组织清晰：

```javascript
// ========== TMDB 搜索功能 ==========
function openTMDBSearch() { ... }
function closeTMDBModal() { ... }
function handleModalClick(event) { ... }
async function searchTMDB() { ... }
function renderTMDBResults(results) { ... }
async function selectTMDBResult(tmdbId, mediaType) { ... }
function applyTMDBData(data) { ... }
```

**Step 2: 添加代码注释**

在每个主要函数前添加功能说明注释：

```javascript
// 打开 TMDB 搜索模态框，预填当前标题
function openTMDBSearch() { ... }

// 关闭 TMDB 搜索模态框
function closeTMDBModal() { ... }

// 处理模态框点击事件（背景点击关闭）
function handleModalClick(event) { ... }

// 执行 TMDB 搜索请求
async function searchTMDB() { ... }

// 渲染 TMDB 搜索结果卡片
function renderTMDBResults(results) { ... }

// 选择 TMDB 结果并获取详情
async function selectTMDBResult(tmdbId, mediaType) { ... }

// 将 TMDB 数据应用到 NFO 表单
function applyTMDBData(data) { ... }
```

**Step 3: 最终提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "refactor: organize and comment TMDB frontend code"
```

---

## 验证步骤总结

**本地验证：**

```bash
# 1. 启动应用
cd /Users/duola/Downloads/nfo-xg
python web/app.py

# 2. 访问浏览器
open http://localhost:8000

# 3. 测试流程
# - 选择或创建 NFO 文件
# - 点击标题旁的搜索按钮
# - 搜索电影（如 "Inception"）
# - 选择结果
# - 验证表单自动填充

# 4. 检查 API 调用（浏览器控制台 Network 标签）
# /api/tmdb/search?q=Inception
# /api/tmdb/movie/27205  (或类似 ID)
```

**预期结果：**
- 搜索模态框正常显示和关闭
- 搜索结果卡片网格正确渲染
- 选择结果后表单字段全部填充
- Toast 提示"已从 TMDB 获取数据"

---

## 风险与回退

**潜在问题：**
1. **API Key 未配置** - 后端返回 401 错误，前端显示错误提示
2. **网络超时** - 后端重试机制处理，前端显示加载状态
3. **数据字段缺失** - `applyTMDBData` 使用空字符串默认值
4. **海报加载失败** - SVG 占位图显示

**回退方案：**
如遇问题可通过以下回滚：
```bash
git reset --hard HEAD~10  # 回滚所有 TMDB 前端更改
```

---

*计划版本: 1.0*
*创建日期: 2026-01-15*
