# TMDB ID 快速创建功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在主页添加 TMDB ID 快速创建区域，允许用户通过 TMDB ID 直接创建新的 NFO 文件

**架构:** 前端添加独立 UI 区域，复用现有后端 TMDB API，新增状态管理区分新建/编辑模式

**Tech Stack:** HTML/CSS/JavaScript (Vanilla), FastAPI (后端无需修改)

---

## 前置条件

- TMDB API Key 已配置（使用现有 `/api/tmdb/config` 端点）
- 现有 TMDB API 正常工作：
  - `/api/tmdb/id/{tmdb_id}?media_type=auto`
  - `/api/save`

---

### Task 1: 添加 TMDB 快速创建区域 HTML 结构

**Files:**
- Modify: `web/templates/index.html` (在文件选择区域后添加新 HTML)

**Step 1: 定位插入位置**

在 `index.html` 中找到文件选择/上传区域的结束位置，在其后插入新区域。

**Step 2: 添加 TMDB 快速创建区域 HTML**

在文件操作区域（`.file-operations` 或类似容器）后添加：

```html
<!-- TMDB 快速创建区域 -->
<div class="tmdb-quick-create" id="tmdbQuickCreate">
    <div class="tmdb-input-group">
        <input
            type="number"
            id="tmdbIdInput"
            min="1"
            placeholder="输入 TMDB ID"
            class="tmdb-id-input"
        />
        <button
            id="fetchTmdbBtn"
            class="btn btn-primary"
            disabled
        >
            获取数据
        </button>
        <div id="tmdbStatus" class="tmdb-status"></div>
    </div>
</div>
```

**Step 3: 验证 HTML 结构**

在浏览器中打开页面，检查新区域是否正确显示在文件操作区域下方。

**Step 4: Commit**

```bash
git add web/templates/index.html
git commit -m "feat: add TMDB quick create HTML structure"
```

---

### Task 2: 添加 CSS 样式

**Files:**
- Modify: `web/static/style.css`

**Step 1: 添加 TMDB 快速创建区域样式**

在 `style.css` 末尾添加：

```css
/* TMDB 快速创建区域 */
.tmdb-quick-create {
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 16px;
}

.tmdb-input-group {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

.tmdb-id-input {
    flex: 1;
    min-width: 150px;
    padding: 8px 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 14px;
}

.tmdb-id-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.tmdb-status {
    display: flex;
    align-items: center;
    font-size: 13px;
    min-width: 200px;
}

.tmdb-status.loading {
    color: #007bff;
}

.tmdb-status.success {
    color: #28a745;
}

.tmdb-status.error {
    color: #dc3545;
}

/* 加载动画 */
.tmdb-status.loading::before {
    content: "";
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #007bff;
    border-radius: 50%;
    animation: tmdb-spin 1s linear infinite;
    margin-right: 6px;
}

@keyframes tmdb-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 移动端响应式 */
@media (max-width: 768px) {
    .tmdb-input-group {
        flex-direction: column;
        align-items: stretch;
    }

    .tmdb-id-input {
        min-width: unset;
    }

    .tmdb-status {
        min-width: unset;
    }
}
```

**Step 2: 验证样式**

刷新浏览器，检查：
- 输入框、按钮、状态区域布局正确
- 移动端（开发者工具模拟）垂直排列
- 聚焦时显示蓝色边框

**Step 3: Commit**

```bash
git add web/static/style.css
git commit -m "style: add TMDB quick create area styles"
```

---

### Task 3: 添加 JavaScript - 输入验证和按钮状态

**Files:**
- Modify: `web/templates/index.html` (在 `<script>` 标签内)

**Step 1: 获取 DOM 元素引用**

在现有 JavaScript 代码的 DOM 元素获取区域添加：

```javascript
// TMDB 快速创建元素
const tmdbIdInput = document.getElementById('tmdbIdInput');
const fetchTmdbBtn = document.getElementById('fetchTmdbBtn');
const tmdbStatus = document.getElementById('tmdbStatus');
```

**Step 2: 添加输入验证逻辑**

```javascript
// TMDB ID 输入验证
tmdbIdInput.addEventListener('input', function() {
    const value = this.value.trim();
    // 只有当输入为正整数时才启用按钮
    fetchTmdbBtn.disabled = !(value && parseInt(value) > 0);
});
```

**Step 3: 验证功能**

在浏览器中测试：
- 空输入时按钮禁用
- 输入负数或 0 时按钮禁用
- 输入正整数时按钮启用

**Step 4: Commit**

```bash
git add web/templates/index.html
git commit -m "feat: add TMDB ID input validation"
```

---

### Task 4: 添加 JavaScript - TMDB API 调用

**Files:**
- Modify: `web/templates/index.html` (在 `<script>` 标签内)

**Step 1: 添加状态变量**

在现有状态变量区域添加：

```javascript
// TMDB 创建状态
let isCreatingFromTmdb = false;
```

**Step 2: 添加状态显示函数**

```javascript
// 显示 TMDB 状态消息
function showTmdbStatus(type, message) {
    tmdbStatus.className = `tmdb-status ${type}`;
    tmdbStatus.textContent = message || '';

    // 3秒后清除成功消息
    if (type === 'success') {
        setTimeout(() => {
            if (tmdbStatus.className.includes('success')) {
                tmdbStatus.className = 'tmdb-status';
                tmdbStatus.textContent = '';
            }
        }, 3000);
    }
}
```

**Step 3: 添加 TMDB 数据获取函数**

```javascript
// 从 TMDB ID 获取数据
async function fetchFromTmdb() {
    const tmdbId = parseInt(tmdbIdInput.value.trim());

    if (!tmdbId || tmdbId <= 0) {
        showTmdbStatus('error', '请输入有效的 TMDB ID');
        return;
    }

    // 显示加载状态
    showTmdbStatus('loading', '正在获取数据...');
    fetchTmdbBtn.disabled = true;

    try {
        const response = await fetch(`/api/tmdb/id/${tmdbId}?media_type=auto`);

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('请先配置 TMDB API Key');
            } else if (response.status === 404) {
                throw new Error('未找到该 TMDB ID 对应的内容');
            } else {
                throw new Error(`获取失败: ${response.status}`);
            }
        }

        const data = await response.json();

        // 填充表单数据
        populateForm(data);

        // 设置新建模式状态
        isCreatingFromTmdb = true;
        currentFile = null;
        updateFilePathDisplay('');

        // 清除输入框和状态
        tmdbIdInput.value = '';
        showTmdbStatus('success', '数据获取成功！请编辑后保存');

    } catch (error) {
        showTmdbStatus('error', error.message);
    } finally {
        fetchTmdbBtn.disabled = false;
        // 重新检查输入状态
        tmdbIdInput.dispatchEvent(new Event('input'));
    }
}
```

**Step 4: 绑定按钮点击事件**

```javascript
fetchTmdbBtn.addEventListener('click', fetchFromTmdb);
```

**Step 5: 测试 API 调用**

在浏览器中测试（需要已配置 TMDB API Key）：
- 输入有效的 TMDB ID（如 27205 for Inception）
- 点击「获取数据」
- 验证加载动画显示
- 验证数据成功填充表单
- 测试无效 ID 的错误消息

**Step 6: Commit**

```bash
git add web/templates/index.html
git commit -m "feat: add TMDB API fetch functionality"
```

---

### Task 5: 添加表单数据填充函数

**Files:**
- Modify: `web/templates/index.html` (在 `<script>` 标签内)

**Step 1: 实现 populateForm 函数**

如果不存在此函数，添加；如果存在，扩展它以支持 TMDB 数据格式：

```javascript
// 填充表单数据
function populateForm(data) {
    // 基本字段
    document.getElementById('nfoType').value = data.nfo_type || 'movie';
    document.getElementById('title').value = data.title || '';
    document.getElementById('originalTitle').value = data.originaltitle || '';
    document.getElementById('year').value = data.year || '';
    document.getElementById('plot').value = data.plot || '';
    document.getElementById('runtime').value = data.runtime || '';
    document.getElementById('studio').value = data.studio || '';
    document.getElementById('rating').value = data.rating || '';
    document.getElementById('poster').value = data.poster || '';
    document.getElementById('fanart').value = data.fanart || '';

    // 剧集字段
    document.getElementById('season').value = data.season || '';
    document.getElementById('episode').value = data.episode || '';
    document.getElementById('aired').value = data.aired || '';

    // 类型列表
    const genreContainer = document.getElementById('genreContainer');
    genreContainer.innerHTML = '';
    if (data.genres && data.genres.length > 0) {
        data.genres.forEach(genre => addGenre(genre));
    }

    // 导演列表
    const directorContainer = document.getElementById('directorContainer');
    directorContainer.innerHTML = '';
    if (data.directors && data.directors.length > 0) {
        data.directors.forEach(director => addDirector(director));
    }

    // 演员列表
    const actorContainer = document.getElementById('actorContainer');
    actorContainer.innerHTML = '';
    if (data.actors && data.actors.length > 0) {
        data.actors.forEach(actor => {
            addActor(actor.name, actor.role, actor.thumb, actor.order);
        });
    }

    // Extra tags (如果有)
    if (data.extra_tags) {
        renderExtraTags(data.extra_tags);
    }
}
```

**Step 2: 验证数据填充**

测试 TMDB 数据获取后，检查所有字段是否正确填充到表单。

**Step 3: Commit**

```bash
git add web/templates/index.html
git commit -m "feat: add form population from TMDB data"
```

---

### Task 6: 修改保存逻辑支持新建模式

**Files:**
- Modify: `web/templates/index.html` (在 `<script>` 标签内)

**Step 1: 修改现有保存函数**

找到现有的保存函数（可能是 `saveNfo()` 或类似名称），修改其逻辑：

```javascript
// 保存 NFO 文件
async function saveNfo() {
    // 收集表单数据
    const nfoData = collectFormData();

    // 检查是否为新建模式
    if (isCreatingFromTmdb && !currentFile) {
        // 弹出保存文件对话框
        try {
            const handle = await showSaveFilePicker({
                suggestedName: `${nfoData.title || 'movie'}.nfo`,
                types: [{
                    description: 'NFO Files',
                    accept: {'text/xml': ['.nfo']}
                }]
            });

            const file = await handle.createWritable();
            currentFile = handle.name;
            isCreatingFromTmdb = false;

        } catch (err) {
            if (err.name === 'AbortError') {
                // 用户取消，不保存
                return;
            }
            // 如果不支持 File System Access API，使用传统方式
            const path = prompt('请输入保存路径:', `/Movies/${nfoData.title || 'movie'}.nfo`);
            if (!path) return;
            currentFile = path;
            isCreatingFromTmdb = false;
        }
    }

    // 执行保存
    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                path: currentFile,
                data: nfoData
            })
        });

        const result = await response.json();

        if (result.success) {
            showMessage('success', '保存成功');
            addRecentFile(currentFile);
        } else {
            showMessage('error', result.message || '保存失败');
        }
    } catch (error) {
        showMessage('error', '保存失败: ' + error.message);
    }
}
```

**Step 2: 添加 showSaveFilePicker 的 polyfill**

在文件顶部或工具函数区域添加：

```javascript
// 检查浏览器是否支持 File System Access API
const supportsFileSystemAccess = 'showSaveFilePicker' in window;

// 保存文件对话框
async function showSaveFileDialog(defaultName) {
    if (supportsFileSystemAccess) {
        try {
            return await window.showSaveFilePicker({
                suggestedName: defaultName,
                types: [{
                    description: 'NFO Files',
                    accept: {'text/xml': ['.nfo']}
                }]
            });
        } catch (err) {
            if (err.name === 'AbortError') return null;
            throw err;
        }
    } else {
        // 回退到 prompt 方式
        const path = prompt('请输入保存路径:', `/Movies/${defaultName}`);
        return path ? { name: path, isFallback: true } : null;
    }
}
```

**Step 3: 更新保存函数使用新对话框**

将保存函数中的对话框调用替换为：

```javascript
const handle = await showSaveFileDialog(`${nfoData.title || 'movie'}.nfo`);
if (!handle) return; // 用户取消

if (handle.isFallback) {
    currentFile = handle.name;
} else {
    // File System Access API: 需要写入文件
    const writable = await handle.createWritable();
    // 等待获取响应后再写入...
}
```

**注意**: 完整的 File System Access API 集成需要修改后端返回文件内容，这里简化为只获取路径。

**简化版本**（推荐）：

```javascript
// 保存 NFO 文件
async function saveNfo() {
    const nfoData = collectFormData();

    // 新建模式：询问保存路径
    if (isCreatingFromTmdb && !currentFile) {
        const defaultName = `${nfoData.title || 'movie'}.nfo`;
        const path = prompt('请输入保存路径:', `/Movies/${defaultName}`);
        if (!path) return;
        currentFile = path;
        isCreatingFromTmdb = false;
    }

    // 执行保存（复用现有逻辑）
    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                path: currentFile,
                data: nfoData
            })
        });

        const result = await response.json();

        if (result.success) {
            showMessage('success', '保存成功');
            addRecentFile(currentFile);
        } else {
            showMessage('error', result.message || '保存失败');
        }
    } catch (error) {
        showMessage('error', '保存失败: ' + error.message);
    }
}
```

**Step 4: 测试保存流程**

1. 从 TMDB ID 获取数据
2. 点击保存
3. 输入保存路径
4. 验证文件创建成功

**Step 5: Commit**

```bash
git add web/templates/index.html
git commit -m "feat: add save dialog for new files from TMDB"
```

---

### Task 7: 修复打开文件时重置状态

**Files:**
- Modify: `web/templates/index.html` (在 `<script>` 标签内)

**Step 1: 修改文件打开/加载函数**

找到现有的文件加载函数（可能是 `loadNfo()` 或在文件列表点击处理中），添加状态重置：

```javascript
// 加载 NFO 文件
async function loadNfo(filePath) {
    try {
        const response = await fetch('/api/load', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path: filePath})
        });

        const result = await response.json();

        if (result.success) {
            populateForm(result.data);
            currentFile = filePath;
            // 重置 TMDB 新建状态
            isCreatingFromTmdb = false;
            updateFilePathDisplay(filePath);
            addRecentFile(filePath);
        } else {
            showMessage('error', result.message || '加载失败');
        }
    } catch (error) {
        showMessage('error', '加载失败: ' + error.message);
    }
}
```

**Step 2: 测试状态切换**

1. 从 TMDB ID 获取数据（`isCreatingFromTmdb = true`）
2. 打开已有 NFO 文件
3. 验证 `isCreatingFromTmdb` 被重置为 false
4. 验证保存时不弹出路径对话框

**Step 3: Commit**

```bash
git add web/templates/index.html
git commit -m "fix: reset TMDB create state when opening existing file"
```

---

### Task 8: 添加键盘快捷键支持

**Files:**
- Modify: `web/templates/index.html` (在 `<script>` 标签内)

**Step 1: 添加 Enter 键触发获取**

```javascript
// TMDB ID 输入框按 Enter 键触发获取
tmdbIdInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !fetchTmdbBtn.disabled) {
        fetchFromTmdb();
    }
});
```

**Step 2: 测试快捷键**

在 TMDB ID 输入框中按 Enter 键，验证触发数据获取。

**Step 3: Commit**

```bash
git add web/templates/index.html
git commit -m "feat: add Enter key shortcut for TMDB fetch"
```

---

### Task 9: 手动测试完整流程

**Files:**
- No code changes

**测试清单**：

| 场景 | 步骤 | 预期结果 |
|------|------|----------|
| 有效 TMDB ID | 输入 27205，点击获取 | 数据填充表单，显示成功消息 |
| 无效 TMDB ID | 输入 999999999，点击获取 | 显示错误消息 |
| 空 ID | 输入框为空 | 按钮禁用 |
| 负数 ID | 输入 -1 | 按钮禁用 |
| Enter 键 | 输入 ID 后按 Enter | 触发获取数据 |
| 保存新建 | 获取数据后点击保存 | 弹出路径对话框，文件创建成功 |
| 取消保存 | 获取数据后点击保存，输入框取消 | 不执行保存 |
| 打开已有文件 | 在 TMDB 新建后打开已有文件 | 状态正确重置 |
| 移动端布局 | 使用移动设备或模拟器 | 垂直排列 |

**Step 1: 执行所有测试场景**

记录每个场景的测试结果。

**Step 2: 修复发现的问题**

如有问题，修复并提交。

---

### Task 10: 更新文档

**Files:**
- Create: `docs/user-guide/tmdb-quick-create.md` (可选)

**Step 1: 创建用户指南（可选）**

```markdown
# TMDB 快速创建功能使用指南

## 功能说明

当您没有 NFO 文件但有 TMDB ID 时，可以通过此功能快速创建 NFO 文件。

## 使用步骤

1. 在主页「TMDB 快速创建」区域输入 TMDB ID
2. 点击「获取数据」按钮
3. 数据自动填充到编辑表单
4. 根据需要修改内容
5. 点击「保存」，输入保存路径

## TMDB ID 查找

- 访问 https://www.themoviedb.org/
- 搜索电影或剧集
- URL 中的数字即为 TMDB ID
  - 例如: https://www.themoviedb.org/movie/27205
  - TMDB ID 为 27205
```

**Step 2: Commit**

```bash
git add docs/user-guide/tmdb-quick-create.md
git commit -m "docs: add TMDB quick create user guide"
```

---

## 完成验证

运行所有测试并验证：

```bash
# 启动开发服务器
python web/app.py

# 在浏览器中测试完整流程
```

**最终验收**：
- [ ] TMDB ID 输入和验证正常
- [ ] 数据获取和表单填充正常
- [ ] 保存路径对话框正常
- [ ] 文件创建成功
- [ ] 状态切换正确
- [ ] 样式在各浏览器一致
- [ ] 移动端布局正常
