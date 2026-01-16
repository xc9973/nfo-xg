# 批量操作 UX 设计计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 NFO 编辑器添加批量操作功能，支持多选文件、批量 TMDB 数据获取、进度追踪和错误处理。

**架构:** 在文件浏览器添加多选模式，新增批量操作面板，实现任务队列和进度管理系统。

**技术栈:** 原生 JavaScript、CSS、Fetch API、批量后端接口（需配合后端实现）

---

## 当前问题分析

1. **无法批量操作** - 只能逐个处理 NFO 文件
2. **缺少批量 TMDB** - 需要逐个手动搜索获取数据
3. **无进度显示** - 批量操作时不知道进度
4. **错误难以追踪** - 哪些文件成功/失败不清晰
5. **无任务队列** - 无法管理多个批量任务

---

## Task 1: 添加多选模式界面

**Files:**
- Modify: `web/templates/index.html` (文件浏览器区域)
- Modify: `web/static/style.css** (多选样式)

**Step 1: 在文件浏览器头部添加批量操作按钮**

在 `<h3>📁 文件浏览</h3>` 后添加：

```html
<div class="file-browser-header">
    <h3>📁 文件浏览</h3>
    <div class="batch-controls" style="display:none">
        <button class="btn btn-secondary btn-small" onclick="toggleBatchMode()">✓ 多选</button>
    </div>
</div>
```

**Step 2: 添加批量操作面板**

在文件浏览器底部添加：

```html
<div id="batchPanel" class="batch-panel" style="display:none">
    <div class="batch-header">
        <span class="batch-count">已选择 <strong id="selectedCount">0</strong> 个文件</span>
        <button class="btn-icon-small" onclick="exitBatchMode()">×</button>
    </div>
    <div class="batch-actions">
        <button class="btn btn-primary" onclick="batchTMDBFetch()" style="flex:1">
            <span class="btn-icon">🎬</span> 批量获取 TMDB
        </button>
        <button class="btn btn-secondary" onclick="batchSave()" style="flex:1">
            <span class="btn-icon">💾</span> 批量保存
        </button>
    </div>
</div>
```

**Step 3: 修改文件列表项添加复选框**

修改 `renderFileList` 函数：

```javascript
function renderFileList(data) {
    const list = document.getElementById('fileList');
    let html = '';

    if (data.parent) {
        html += `<div class="file-item dir" onclick="loadDir('${data.parent}')">📁 ..</div>`;
    }

    for (const item of data.items) {
        if (item.is_dir) {
            html += `<div class="file-item dir" onclick="loadDir('${item.path}')">📁 ${item.name}</div>`;
        } else if (item.is_nfo) {
            const checkboxId = `select-${item.path.replace(/[^a-zA-Z0-9]/g, '-')}`;
            html += `
                <div class="file-item nfo ${batchMode ? 'selectable' : ''}" data-path="${item.path}">
                    ${batchMode ? `<input type="checkbox" id="${checkboxId}" class="file-checkbox" onchange="toggleFileSelection('${item.path}')">` : ''}
                    <label for="${checkboxId}" class="file-item-content" onclick="${batchMode ? '' : `loadNfo('${item.path}')`}">
                        📄 ${esc(item.name)}
                    </label>
                </div>
            `;
        }
    }

    list.innerHTML = html;
}
```

**Step 4: 添加多选样式**

```css
/* 批量操作 */
.file-browser-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background: #0f3460;
}

.btn-small {
    padding: 6px 12px;
    font-size: 12px;
}

.batch-panel {
    background: #0f3460;
    border-top: 1px solid #1a4a7a;
    padding: 15px;
}

.batch-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    font-size: 13px;
}

.batch-count strong {
    color: #e94560;
    font-size: 16px;
}

.batch-actions {
    display: flex;
    gap: 10px;
}

.batch-actions .btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
}

/* 多选模式 */
.file-item.selectable {
    padding-left: 35px;
    position: relative;
}

.file-checkbox {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    width: 18px;
    height: 18px;
    cursor: pointer;
}

.file-item-content {
    cursor: pointer;
    flex: 1;
}

.file-item.selected {
    background: rgba(233, 69, 96, 0.2);
}

.batch-mode .file-item:not(.selectable) {
    opacity: 0.5;
    pointer-events: none;
}
```

**Step 5: 实现多选逻辑**

```javascript
// 批量操作状态
let batchMode = false;
let selectedFiles = new Set();

function toggleBatchMode() {
    batchMode = !batchMode;
    const controls = document.querySelector('.batch-controls');
    const panel = document.getElementById('batchPanel');
    const container = document.querySelector('.container');

    if (batchMode) {
        controls.querySelector('button').textContent = '✕ 取消';
        panel.style.display = 'block';
        container.classList.add('batch-mode');
        selectedFiles.clear();
        updateSelectedCount();
    } else {
        exitBatchMode();
    }

    // 重新渲染文件列表
    const currentPath = document.getElementById('currentPath').textContent;
    loadDir(currentPath === '~' ? '' : currentPath);
}

function exitBatchMode() {
    batchMode = false;
    selectedFiles.clear();

    const controls = document.querySelector('.batch-controls');
    const panel = document.getElementById('batchPanel');
    const container = document.querySelector('.container');

    controls.querySelector('button').textContent = '✓ 多选';
    panel.style.display = 'none';
    container.classList.remove('batch-mode');

    const currentPath = document.getElementById('currentPath').textContent;
    loadDir(currentPath === '~' ? '' : currentPath);
}

function toggleFileSelection(path) {
    if (selectedFiles.has(path)) {
        selectedFiles.delete(path);
    } else {
        selectedFiles.add(path);
    }

    // 更新视觉状态
    const item = document.querySelector(`.file-item[data-path="${path}"]`);
    if (item) {
        item.classList.toggle('selected', selectedFiles.has(path));
    }

    updateSelectedCount();
}

function updateSelectedCount() {
    document.getElementById('selectedCount').textContent = selectedFiles.size;
}

// 初始化：显示批量控制按钮
document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('.batch-controls').style.display = 'block';
});
```

**Step 6: 测试多选功能**

1. 点击"多选"按钮
2. 勾选多个 NFO 文件
3. 预期：显示已选择数量，批量面板出现

**Step 7: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add file multi-select mode with batch panel"
```

---

## Task 2: 实现批量 TMDB 获取功能

**Files:**
- Modify: `web/templates/index.html` (批量操作函数)
- Requires: Backend batch API (需配合后端实现)

**Step 1: 创建批量获取状态管理**

```javascript
// 批量 TMDB 获取状态
let batchTMDBState = {
    active: false,
    total: 0,
    completed: 0,
    failed: 0,
    results: []
};
```

**Step 2: 实现批量获取函数**

```javascript
async function batchTMDBFetch() {
    if (selectedFiles.size === 0) {
        showToast('请先选择文件', 'warning');
        return;
    }

    // 确认操作
    if (!confirm(`确定要批量获取 ${selectedFiles.size} 个文件的 TMDB 数据？`)) {
        return;
    }

    // 初始化状态
    batchTMDBState = {
        active: true,
        total: selectedFiles.size,
        completed: 0,
        failed: 0,
        results: []
    };

    // 显示进度面板
    showBatchProgress();

    // 逐个处理
    const files = Array.from(selectedFiles);
    for (const filePath of files) {
        try {
            // 加载文件
            const loadRes = await fetch('/api/load', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: filePath})
            });
            const loadData = await loadRes.json();

            if (!loadRes.ok) throw new Error(loadLoad.detail);

            const currentTitle = loadData.data.title;
            if (!currentTitle) {
                throw new Error('没有标题');
            }

            // 搜索 TMDB
            updateBatchProgress(`搜索: ${currentTitle}`);
            const searchRes = await fetch(`/api/tmdb/search?q=${encodeURIComponent(currentTitle)}`);
            const searchData = await searchRes.json();

            if (!searchRes.ok) {
                throw new Error(searchData.detail || '搜索失败');
            }

            if (!searchData.results || searchData.results.length === 0) {
                throw new Error('未找到结果');
            }

            // 选择第一个结果
            const firstResult = searchData.results[0];
            const endpoint = firstResult.media_type === 'movie'
                ? `/api/tmdb/movie/${firstResult.id}`
                : `/api/tmdb/tv/${firstResult.id}`;

            // 获取详情
            updateBatchProgress(`获取详情: ${currentTitle}`);
            const detailRes = await fetch(endpoint);
            const detailData = await detailRes.json();

            if (!detailRes.ok) {
                throw new Error(detailData.detail || '获取详情失败');
            }

            // 保存文件
            updateBatchProgress(`保存: ${currentTitle}`);
            const saveRes = await fetch('/api/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    path: filePath,
                    data: detailData
                })
            });

            if (!saveRes.ok) {
                throw new Error('保存失败');
            }

            // 记录成功
            batchTMDBState.completed++;
            batchTMDBState.results.push({
                file: filePath,
                success: true,
                title: currentTitle
            });

        } catch (e) {
            // 记录失败
            batchTMDBState.failed++;
            batchTMDBState.results.push({
                file: filePath,
                success: false,
                error: e.message
            });
        }

        updateBatchProgress();
    }

    // 完成
    batchTMDBState.active = false;
    showBatchComplete();

    // 退出多选模式
    exitBatchMode();
}
```

**Step 3: 创建进度面板**

在 `</body>` 前添加：

```html
<!-- 批量操作进度模态框 -->
<div id="batchProgressModal" class="modal">
    <div class="modal-content batch-progress-content">
        <div class="modal-header">
            <h3>📦 批量操作进度</h3>
        </div>
        <div class="modal-body">
            <div class="batch-progress-summary">
                <div class="progress-stat">
                    <span class="stat-value" id="progressTotal">0</span>
                    <span class="stat-label">总数</span>
                </div>
                <div class="progress-stat">
                    <span class="stat-value success" id="progressCompleted">0</span>
                    <span class="stat-label">完成</span>
                </div>
                <div class="progress-stat">
                    <span class="stat-value error" id="progressFailed">0</span>
                    <span class="stat-label">失败</span>
                </div>
            </div>
            <div class="batch-progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="batch-current-file" id="currentFile"></div>
        </div>
    </div>
</div>
```

**Step 4: 添加进度面板样式**

```css
/* 批量进度 */
.batch-progress-content {
    max-width: 500px;
}

.batch-progress-summary {
    display: flex;
    justify-content: space-around;
    margin-bottom: 20px;
}

.progress-stat {
    text-align: center;
}

.stat-value {
    display: block;
    font-size: 32px;
    font-weight: bold;
    color: #eee;
}

.stat-value.success { color: #27ae60; }
.stat-value.error { color: #e74c3c; }

.stat-label {
    font-size: 12px;
    color: #aaa;
    text-transform: uppercase;
}

.batch-progress-bar {
    height: 8px;
    background: #0f3460;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 15px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #e94560, #ff6b6b);
    width: 0%;
    transition: width 0.3s ease;
}

.batch-current-file {
    text-align: center;
    color: #aaa;
    font-size: 13px;
    min-height: 20px;
}
```

**Step 5: 实现进度更新函数**

```javascript
function showBatchProgress() {
    document.getElementById('batchProgressModal').classList.add('active');
    updateBatchProgress();
}

function updateBatchProgress(message) {
    const total = batchTMDBState.total;
    const completed = batchTMDBState.completed;
    const failed = batchTMDBState.failed;
    const processed = completed + failed;
    const percent = (processed / total) * 100;

    // 更新统计
    document.getElementById('progressTotal').textContent = total;
    document.getElementById('progressCompleted').textContent = completed;
    document.getElementById('progressFailed').textContent = failed;

    // 更新进度条
    document.getElementById('progressFill').style.width = percent + '%';

    // 更新当前文件消息
    if (message) {
        document.getElementById('currentFile').textContent = message;
    }
}

function showBatchComplete() {
    const {total, completed, failed} = batchTMDBState;

    // 显示完成消息
    setTimeout(() => {
        document.getElementById('batchProgressModal').classList.remove('active');

        if (failed === 0) {
            showToast(`全部完成！成功 ${completed} 个文件`, 'success');
        } else {
            showToast(`完成 ${completed} 个，失败 ${failed} 个`, 'warning');
            // 可以添加显示详细结果的逻辑
        }
    }, 1000);
}
```

**Step 6: 测试批量获取**

1. 选择多个 NFO 文件
2. 点击"批量获取 TMDB"
3. 预期：显示进度面板，逐个处理

**Step 7: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: implement batch TMDB fetch with progress tracking"
```

---

## Task 3: 实现批量保存功能

**Files:**
- Modify: `web/templates/index.html` (批量保存函数)

**Step 1: 实现批量保存函数**

```javascript
async function batchSave() {
    if (selectedFiles.size === 0) {
        showToast('请先选择文件', 'warning');
        return;
    }

    // 这里可以实现批量保存特定内容
    // 例如：批量更新某个字段值
    const field = prompt('要批量更新哪个字段？\n(例: studio, year, rating)');

    if (!field) return;

    const value = prompt(`输入 ${field} 的新值:`);
    if (value === null) return;

    // 确认操作
    if (!confirm(`确定要将 ${selectedFiles.size} 个文件的 ${field} 更新为 "${value}"？`)) {
        return;
    }

    // 初始化状态
    batchTMDBState = {
        active: true,
        total: selectedFiles.size,
        completed: 0,
        failed: 0,
        results: []
    };

    showBatchProgress();

    // 逐个处理
    const files = Array.from(selectedFiles);
    for (const filePath of files) {
        try {
            // 加载文件
            updateBatchProgress(`加载: ${filePath.split('/').pop()}`);
            const loadRes = await fetch('/api/load', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: filePath})
            });
            const loadData = await loadRes.json();

            if (!loadRes.ok) throw new Error(loadData.detail);

            // 更新字段
            loadData.data[field] = value;

            // 保存文件
            updateBatchProgress(`保存: ${filePath.split('/').pop()}`);
            const saveRes = await fetch('/api/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    path: filePath,
                    data: loadData.data
                })
            });

            if (!saveRes.ok) throw new Error('保存失败');

            batchTMDBState.completed++;

        } catch (e) {
            batchTMDBState.failed++;
            batchTMDBState.results.push({
                file: filePath,
                success: false,
                error: e.message
            });
        }

        updateBatchProgress();
    }

    batchTMDBState.active = false;
    showBatchComplete();
    exitBatchMode();
}
```

**Step 2: 测试批量保存**

1. 选择多个文件
2. 点击"批量保存"
3. 输入字段名和值
4. 预期：批量更新完成

**Step 3: 提交**

```bash
git add web/templates/index.html
git commit -m "feat: add batch save with field update"
```

---

## Task 4: 添加批量操作历史记录

**Files:**
- Modify: `web/templates/index.html** (历史面板扩展)
- Modify: `web/static/style.css` (历史样式)

**Step 1: 扩展历史面板支持批量操作**

修改历史面板 HTML：

```html
<div id="historyPanel" class="history-panel" style="display:none">
    <div class="history-header">
        <h4>操作历史</h4>
        <button class="btn-icon-small" onclick="toggleHistory()">×</button>
    </div>
    <div class="history-tabs">
        <button class="history-tab active" onclick="showHistoryTab('single')">单个操作</button>
        <button class="history-tab" onclick="showHistoryTab('batch')">批量操作</button>
    </div>
    <div id="historyList" class="history-list"></div>
    <div id="batchHistoryList" class="history-list" style="display:none"></div>
</div>
```

**Step 2: 添加批量历史样式**

```css
/* 历史标签页 */
.history-tabs {
    display: flex;
    border-bottom: 1px solid #0f3460;
}

.history-tab {
    flex: 1;
    background: none;
    border: none;
    padding: 10px;
    color: #aaa;
    font-size: 12px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
}

.history-tab.active {
    color: #e94560;
    border-bottom-color: #e94560;
}

.history-tab:hover {
    color: #eee;
}
```

**Step 3: 实现批量历史记录**

```javascript
let batchHistory = [];

function addBatchHistory(action, successCount, failCount) {
    const timestamp = new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit'});
    batchHistory.unshift({
        action,
        successCount,
        failCount,
        timestamp
    });

    if (batchHistory.length > 20) {
        batchHistory = batchHistory.slice(0, 20);
    }

    renderBatchHistory();
}

function renderBatchHistory() {
    const list = document.getElementById('batchHistoryList');

    if (batchHistory.length === 0) {
        list.innerHTML = '<div style="color:#666;font-size:12px;padding:10px;text-align:center">暂无批量操作</div>';
        return;
    }

    list.innerHTML = batchHistory.map(item => `
        <div class="history-item batch">
            <div>
                <strong>${item.action}</strong>
                <span class="batch-result-success">✓ ${item.successCount}</span>
                ${item.failCount > 0 ? `<span class="batch-result-fail">✕ ${item.failCount}</span>` : ''}
            </div>
            <span class="history-time">${item.timestamp}</span>
        </div>
    `).join('');
}

function showHistoryTab(tab) {
    const tabs = document.querySelectorAll('.history-tab');
    tabs.forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');

    document.getElementById('historyList').style.display = tab === 'single' ? 'block' : 'none';
    document.getElementById('batchHistoryList').style.display = tab === 'batch' ? 'block' : 'none';
}

// 在批量操作完成时记录
// 在 showBatchComplete 中添加
addBatchHistory(
    `批量 TMDB 获取`,
    batchTMDBState.completed,
    batchTMDBState.failed
);
```

**Step 4: 测试批量历史**

执行批量操作后查看历史面板。

**Step 5: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add batch operation history with separate tab"
```

---

## Task 5: 添加错误详情查看

**Files:**
- Modify: `web/templates/index.html` (错误详情模态框)

**Step 1: 创建错误详情模态框**

```html
<div id="batchErrorModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>❌ 批量操作错误详情</h3>
            <button class="modal-close" onclick="closeBatchErrorModal()">×</button>
        </div>
        <div class="modal-body">
            <div id="batchErrorList" class="batch-error-list"></div>
        </div>
    </div>
</div>
```

**Step 2: 添加错误列表样式**

```css
.batch-error-list {
    max-height: 400px;
    overflow-y: auto;
}

.batch-error-item {
    padding: 12px;
    margin-bottom: 10px;
    background: rgba(231, 76, 60, 0.1);
    border: 1px solid #e74c3c;
    border-radius: 4px;
}

.batch-error-file {
    font-weight: 500;
    color: #eee;
    margin-bottom: 5px;
    word-break: break-all;
}

.batch-error-reason {
    font-size: 12px;
    color: #e74c3c;
}
```

**Step 3: 实现错误显示逻辑**

```javascript
function showBatchErrors() {
    const failedResults = batchTMDBState.results.filter(r => !r.success);

    if (failedResults.length === 0) {
        showToast('没有失败的文件', 'info');
        return;
    }

    const list = document.getElementById('batchErrorList');
    list.innerHTML = failedResults.map(item => `
        <div class="batch-error-item">
            <div class="batch-error-file">📄 ${item.file.split('/').pop()}</div>
            <div class="batch-error-reason">${item.error}</div>
        </div>
    `).join('');

    document.getElementById('batchErrorModal').classList.add('active');
}

function closeBatchErrorModal() {
    document.getElementById('batchErrorModal').classList.remove('active');
}

// 修改完成提示，添加查看错误按钮
function showBatchComplete() {
    const {total, completed, failed} = batchTMDBState;

    setTimeout(() => {
        document.getElementById('batchProgressModal').classList.remove('active');

        if (failed === 0) {
            showToast(`全部完成！成功 ${completed} 个文件`, 'success');
        } else {
            // 使用自定义对话框或添加查看错误按钮
            if (confirm(`完成 ${completed} 个，失败 ${failed} 个\n\n点击"确定"查看错误详情`)) {
                showBatchErrors();
            }
        }
    }, 1000);
}
```

**Step 4: 测试错误详情**

制造一些失败情况（如没有标题的文件），查看错误详情。

**Step 5: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add batch operation error details modal"
```

---

## 验证步骤总结

**本地验证：**

```bash
# 1. 启动应用
cd /Volumes/1disk/项目/nfo-xg
python web/app.py

# 2. 准备测试数据
# - 创建多个 NFO 文件
# - 部分文件有标题，部分没有
# - 部分文件标题可以匹配到 TMDB
```

**功能测试清单：**

1. **多选模式**
   - [ ] 点击"多选"进入选择模式
   - [ ] 文件列表显示复选框
   - [ ] 勾选文件更新计数
   - [ ] 退出多选恢复正常

2. **批量 TMDB**
   - [ ] 选择多个文件
   - [ ] 点击批量获取
   - [ ] 显示进度面板
   - [ ] 实时更新进度
   - [ ] 完成后显示结果

3. **批量保存**
   - [ ] 选择多个文件
   - [ ] 输入字段名和值
   - [ ] 批量更新完成

4. **进度追踪**
   - [ ] 显示总数/完成/失败
   - [ ] 进度条正确更新
   - [ ] 显示当前处理文件

5. **错误处理**
   - [ ] 失败文件正确记录
   - [ ] 可查看错误详情
   - [ ] 错误信息清晰

**预期结果：**
- 多选界面清晰易用
- 批量操作稳定可靠
- 进度反馈实时准确
- 错误处理完善

---

## 风险与回退

**潜在问题：**
1. **并发限制** - 后端 API 可能有速率限制
2. **内存占用** - 大量文件处理可能占用内存
3. **网络超时** - 长时间操作可能超时
4. **部分失败** - 需要明确处理策略

**回退方案：**
```bash
git reset --hard HEAD~5  # 回滚所有批量操作功能
```

**后续优化：**
- 添加并发控制（限制同时处理的数量）
- 实现断点续传
- 添加批量操作日志导出
- 支持自定义批量规则

---

*计划版本: 1.0*
*创建日期: 2026-01-16*
