# UI 状态指示器和加载状态优化计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 NFO 编辑器添加完整的状态指示系统，包括保存状态、加载状态、修改状态和错误提示，提升用户体验和操作反馈。

**架构:** 在现有前端基础上添加状态管理系统，通过 CSS 类和 JavaScript 状态变量实现 UI 状态切换。

**技术栈:** 原生 JavaScript (ES6+)、CSS 状态类、Toast 通知系统

---

## 当前问题分析

1. **保存无反馈** - 点击保存后按钮没有状态变化，用户不知道是否保存成功
2. **无修改提示** - 修改表单后没有"未保存"提示，可能丢失数据
3. **加载不明显** - 文件加载时缺少明显加载指示
4. **错误提示单一** - 只有 Toast 提示，缺少内联错误显示
5. **无操作历史** - 无法查看之前的操作记录

---

## Task 1: 添加保存状态指示器

**Files:**
- Modify: `web/templates/index.html:179` (保存按钮)
- Modify: `web/static/style.css` (添加状态样式)

**Step 1: 修改保存按钮添加状态支持**

更新保存按钮 HTML，添加加载和成功状态：

```html
<button class="btn btn-primary" id="saveBtn" onclick="saveNfo()">
    <span class="btn-text">💾 保存</span>
    <span class="btn-loading" style="display:none"><span class="spinner"></span> 保存中...</span>
    <span class="btn-success" style="display:none">✓ 已保存</span>
</button>
```

**Step 2: 添加按钮状态 CSS 样式**

在 `style.css` 的 `.btn` 部分后添加：

```css
/* 按钮状态 */
.btn-text, .btn-loading, .btn-success {
    display: inline-flex;
    align-items: center;
    gap: 5px;
}

.btn.loading {
    opacity: 0.7;
    pointer-events: none;
}

.btn.loading .btn-text { display: none; }
.btn.loading .btn-loading { display: inline-flex !important; }

.btn.success {
    background: #27ae60 !important;
}

.btn.success .btn-text { display: none; }
.btn.success .btn-success { display: inline-flex !important; }
.btn.success .btn-loading { display: none; }
```

**Step 3: 修改 saveNfo 函数添加状态管理**

```javascript
async function saveNfo() {
    const saveBtn = document.getElementById('saveBtn');

    try {
        // 设置加载状态
        saveBtn.classList.add('loading');

        const data = collectData();
        const res = await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path: currentFile, data})
        });
        const result = await res.json();

        if (!res.ok) throw new Error(result.detail);

        // 设置成功状态
        saveBtn.classList.remove('loading');
        saveBtn.classList.add('success');
        showToast('保存成功!', 'success');

        // 清除修改标记
        setModified(false);

        // 2秒后恢复按钮状态
        setTimeout(() => {
            saveBtn.classList.remove('success');
        }, 2000);

    } catch (e) {
        saveBtn.classList.remove('loading');
        showToast(e.message, 'error');
    }
}
```

**Step 4: 测试保存状态**

运行应用，修改内容后点击保存，预期：
- 按钮显示"保存中..."和加载动画
- 保存成功后按钮变绿显示"✓ 已保存"
- 2秒后恢复原始状态

**Step 5: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add save button status indicator with loading and success states"
```

---

## Task 2: 添加表单修改状态跟踪

**Files:**
- Modify: `web/templates/index.html` (添加修改标记)
- Modify: `web/static/style.css` (修改标记样式)

**Step 1: 在编辑器标题添加修改指示器**

修改 `<h2>NFO 编辑器</h2>` 为：

```html
<h2>
    NFO 编辑器
    <span id="modifiedBadge" class="modified-badge" style="display:none">● 未保存</span>
</h2>
```

**Step 2: 添加修改标记 CSS 样式**

```css
/* 修改状态标记 */
.modified-badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    background: #e94560;
    color: white;
    margin-left: 10px;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}
```

**Step 3: 添加修改状态管理**

在 `nfoData` 声明后添加：

```javascript
let isModified = false;

function setModified(value) {
    isModified = value;
    const badge = document.getElementById('modifiedBadge');
    if (badge) {
        badge.style.display = value ? 'inline-block' : 'none';
    }
}

function checkModified() {
    if (isModified) {
        return confirm('有未保存的更改，确定要继续吗？');
    }
    return true;
}
```

**Step 4: 在表单输入时设置修改状态**

修改 `renderEditor` 函数，在所有 input 元素上添加 onchange：

```javascript
// 为所有输入框添加修改追踪
document.querySelectorAll('#editorContent input, #editorContent textarea, #editorContent select').forEach(el => {
    el.addEventListener('input', () => setModified(true));
    el.addEventListener('change', () => setModified(true));
});
```

**Step 5: 在加载文件时清除修改状态**

修改 `loadNfo` 函数：

```javascript
async function loadNfo(path) {
    // 检查未保存更改
    if (!checkModified()) return;

    try {
        // ... 现有代码 ...
        setModified(false); // 加载新文件后清除修改标记
    } catch (e) {
        showToast(e.message, 'error');
    }
}
```

**Step 6: 在切换目录时检查修改状态**

修改 `loadDir` 函数：

```javascript
async function loadDir(path = '') {
    if (!checkModified()) return;
    // ... 现有代码 ...
}
```

**Step 7: 测试修改状态**

1. 打开 NFO 文件
2. 修改任意字段
3. 预期：标题旁显示"● 未保存"标记
4. 保存后标记消失

**Step 8: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add unsaved changes indicator with confirmation"
```

---

## Task 3: 优化文件加载状态

**Files:**
- Modify: `web/templates/index.html` (编辑器区域)
- Modify: `web/static/style.css` (加载状态样式)

**Step 1: 修改编辑器内容区域添加加载状态**

更新 `<div id="editorContent">`：

```html
<div id="editorContent">
    <p style="color:#666">← 从左侧选择一个 .nfo 文件开始编辑</p>
</div>

<!-- 添加加载状态覆盖层 -->
<div id="editorLoading" class="editor-loading" style="display:none">
    <div class="loading-spinner">
        <span class="spinner large"></span>
        <p>加载中...</p>
    </div>
</div>
```

**Step 2: 添加编辑器加载样式**

```css
/* 编辑器加载状态 */
.editor-loading {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(26, 26, 46, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
}

.loading-spinner {
    text-align: center;
    color: #aaa;
}

.spinner.large {
    width: 40px;
    height: 40px;
    border-width: 3px;
}
```

**Step 3: 修改 loadNfo 函数显示加载状态**

```javascript
async function loadNfo(path) {
    if (!checkModified()) return;

    const loading = document.getElementById('editorLoading');
    const content = document.getElementById('editorContent');

    try {
        // 显示加载状态
        loading.style.display = 'flex';

        const res = await fetch('/api/load', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path})
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail);

        currentFile = path;
        nfoData = data.data;
        renderEditor();
        setModified(false);
        showToast('加载成功', 'success');

    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        loading.style.display = 'none';
    }
}
```

**Step 4: 调整编辑器区域相对定位**

```css
.editor {
    padding: 20px;
    overflow-y: auto;
    position: relative; /* 添加这行 */
}
```

**Step 5: 测试加载状态**

点击 NFO 文件，预期：
- 显示加载覆盖层
- 加载完成后覆盖层消失

**Step 6: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add loading overlay for file operations"
```

---

## Task 4: 增强 Toast 通知系统

**Files:**
- Modify: `web/templates/index.html` (Toast 函数)
- Modify: `web/static/style.css` (Toast 样式)

**Step 1: 创建 Toast 容器**

在 `</body>` 前添加：

```html
<div id="toastContainer" class="toast-container"></div>
```

**Step 2: 添加 Toast 容器样式**

```css
/* Toast 容器 */
.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 3000;
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 350px;
}

.toast {
    padding: 15px 20px;
    border-radius: 6px;
    color: white;
    font-size: 14px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    animation: slideIn 0.3s ease, fadeOut 0.3s ease 2.7s;
    display: flex;
    align-items: center;
    gap: 10px;
    max-width: 100%;
}

.toast.success { background: #27ae60; }
.toast.error { background: #e74c3c; }
.toast.warning { background: #f39c12; }
.toast.info { background: #3498db; }

@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}

.toast.removing {
    animation: slideOut 0.3s ease forwards;
}

@keyframes slideOut {
    to { transform: translateX(100%); opacity: 0; }
}
```

**Step 3: 重写 showToast 函数**

```javascript
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');

    // 创建 Toast 元素
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // 添加图标
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${esc(message)}</span>
    `;

    container.appendChild(toast);

    // 自动移除
    setTimeout(() => {
        toast.classList.add('removing');
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, duration);

    // 允许点击关闭
    toast.addEventListener('click', () => {
        toast.classList.add('removing');
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    });
}
```

**Step 4: 测试增强的 Toast**

在浏览器控制台测试：
```javascript
showToast('成功消息', 'success');
showToast('错误消息', 'error');
showToast('警告消息', 'warning');
showToast('信息消息', 'info');
```

**Step 5: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: enhance toast notification system with icons and animations"
```

---

## Task 5: 添加操作历史记录

**Files:**
- Modify: `web/templates/index.html` (添加历史面板)
- Modify: `web/static/style.css` (历史面板样式)

**Step 1: 在编辑器区域添加历史按钮**

在编辑器标题旁边添加：

```html
<h2>
    NFO 编辑器
    <span id="modifiedBadge" class="modified-badge" style="display:none">● 未保存</span>
    <button class="btn-icon-small" onclick="toggleHistory()" title="操作历史" id="historyBtn" style="display:none">📜</button>
</h2>
```

**Step 2: 添加历史面板 HTML**

在 `</div class="editor">` 前添加：

```html
<div id="historyPanel" class="history-panel" style="display:none">
    <div class="history-header">
        <h4>操作历史</h4>
        <button class="btn-icon-small" onclick="toggleHistory()">×</button>
    </div>
    <div id="historyList" class="history-list"></div>
</div>
```

**Step 3: 添加历史面板样式**

```css
/* 历史面板 */
.btn-icon-small {
    background: none;
    border: none;
    font-size: 16px;
    cursor: pointer;
    padding: 5px;
    margin-left: 10px;
    opacity: 0.6;
}

.btn-icon-small:hover {
    opacity: 1;
}

.history-panel {
    background: #16213e;
    border: 1px solid #0f3460;
    border-radius: 6px;
    margin-bottom: 20px;
    max-height: 200px;
    display: flex;
    flex-direction: column;
}

.history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    border-bottom: 1px solid #0f3460;
}

.history-header h4 {
    margin: 0;
    font-size: 13px;
    color: #aaa;
}

.history-list {
    overflow-y: auto;
    padding: 10px;
}

.history-item {
    padding: 8px 10px;
    font-size: 12px;
    border-radius: 4px;
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.history-item.save {
    background: rgba(39, 174, 96, 0.2);
    color: #27ae60;
}

.history-item.load {
    background: rgba(52, 152, 219, 0.2);
    color: #3498db;
}

.history-item.apply {
    background: rgba(233, 69, 96, 0.2);
    color: #e94560;
}

.history-time {
    color: #666;
    font-size: 11px;
}
```

**Step 4: 添加历史记录功能**

```javascript
let actionHistory = [];

function addHistory(action, type) {
    const timestamp = new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit', second:'2-digit'});
    actionHistory.unshift({action, type, timestamp});

    // 最多保留 20 条
    if (actionHistory.length > 20) {
        actionHistory = actionHistory.slice(0, 20);
    }

    renderHistory();
}

function renderHistory() {
    const list = document.getElementById('historyList');
    const btn = document.getElementById('historyBtn');

    if (actionHistory.length === 0) {
        btn.style.display = 'none';
        return;
    }

    btn.style.display = 'inline-block';

    list.innerHTML = actionHistory.map(item => `
        <div class="history-item ${item.type}">
            <span>${item.action}</span>
            <span class="history-time">${item.timestamp}</span>
        </div>
    `).join('');
}

function toggleHistory() {
    const panel = document.getElementById('historyPanel');
    panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
}
```

**Step 5: 在关键操作中记录历史**

修改相关函数添加历史记录：

```javascript
// 在 saveNfo 成功后
addHistory(`保存: ${currentFile}`, 'save');

// 在 loadNfo 成功后
addHistory(`加载: ${path.split('/').pop()}`, 'load');

// 在 applyTMDBData 后
addHistory('从 TMDB 获取数据', 'apply');
```

**Step 6: 测试历史记录**

1. 执行各种操作
2. 点击历史按钮
3. 预期：显示操作历史列表

**Step 7: 提交**

```bash
git add web/templates/index.html web/static/style.css
git commit -m "feat: add operation history panel with action tracking"
```

---

## 验证步骤总结

**本地验证：**

```bash
# 1. 启动应用
cd /Volumes/1disk/项目/nfo-xg
python web/app.py

# 2. 测试清单
```

**功能测试清单：**

1. **保存状态**
   - [ ] 点击保存显示加载状态
   - [ ] 保存成功显示绿色成功状态
   - [ ] 2秒后恢复原始状态

2. **修改状态**
   - [ ] 修改字段后显示"未保存"标记
   - [ ] 保存后标记消失
   - [ ] 切换文件时提示未保存

3. **加载状态**
   - [ ] 加载文件显示覆盖层
   - [ ] 加载完成后覆盖层消失

4. **Toast 通知**
   - [ ] 成功消息显示绿色带 ✓ 图标
   - [ ] 错误消息显示红色带 ✕ 图标
   - [ ] 可点击关闭
   - [ ] 多个 Toast 堆叠显示

5. **操作历史**
   - [ ] 操作后历史按钮出现
   - [ ] 点击显示历史面板
   - [ ] 显示操作类型和时间

**预期结果：**
- 所有操作都有清晰的状态反馈
- 用户始终知道系统当前状态
- 未保存更改不会丢失

---

## 风险与回退

**潜在问题：**
1. **状态同步** - 多个状态变量可能不同步
2. **性能影响** - 频繁 DOM 更新可能影响性能
3. **样式冲突** - 新样式可能与现有样式冲突

**回退方案：**
```bash
git reset --hard HEAD~5  # 回滚所有状态指示器更改
```

---

*计划版本: 1.0*
*创建日期: 2026-01-16*
