# TMDB ID 快速创建功能设计文档

**目标**: 允许用户在主页通过 TMDB ID 快速创建新的 NFO 文件，无需预先存在 NFO 文件

**创建时间**: 2026-01-17

---

## 概述

当前 NFO-XG 编辑器主要用于编辑现有的 NFO 文件。本功能为用户提供一个新的入口：当用户只有 TMDB ID 而没有 NFO 文件时，可以通过 TMDB ID 直接获取数据并创建新的 NFO 文件。

---

## 功能规格

### 入口位置
主页添加独立「TMDB 快速创建」区域，位于文件路径选择区域和编辑表单之间。

### 用户工作流程

```
1. 用户在输入框中输入 TMDB ID（纯数字）
   ↓
2. 点击「获取数据」按钮
   ↓
3. 系统调用 /api/tmdb/id/{tmdb_id} 接口获取数据
   ↓
4. 获取成功后，数据自动填充到编辑表单
   ↓
5. 用户可在表单中修改数据
   ↓
6. 用户点击「保存」
   ↓
7. 弹出文件保存对话框，用户选择保存位置
   ↓
8. 保存 NFO 文件
```

---

## UI 设计

### TMDB 快速创建区域布局

| 组件 | 说明 |
|------|------|
| 输入框 | `input type="number"`，只能输入数字，placeholder="输入 TMDB ID" |
| 按钮 | 「获取数据」按钮，空输入时禁用 |
| 状态提示 | 右侧显示加载动画/成功/错误消息 |

**布局方式**：单行水平布局，使用 Flexbox
**响应式**：移动端自动垂直排列
**样式**：与现有「上传文件」区域保持一致

### 前端状态管理

| 状态 | 类型 | 说明 |
|------|------|------|
| `isCreatingFromTmdb` | boolean | 区分「编辑现有文件」和「从 TMDB 新建」 |
| `tmdbLoading` | boolean | TMDB 数据加载状态 |
| `tmdbError` | string\|null | 错误消息 |
| `currentFile` | string\|null | 当前打开的文件路径，新建时为 null |

**状态转换**：
- 获取 TMDB 数据成功：`isCreatingFromTmdb = true`, `currentFile = null`
- 用户手动打开文件：`isCreatingFromTmdb = false`

---

## API 设计

### 现有 API（无需修改）

```
GET /api/tmdb/id/{tmdb_id}?media_type=auto
```

**响应示例**：
```json
{
  "nfo_type": "movie",
  "title": "盗梦空间",
  "originaltitle": "Inception",
  "year": "2010",
  "plot": "...",
  "rating": "8.8",
  "genres": ["动作", "科幻"],
  "runtime": "148",
  "poster": "...",
  "detected_type": "movie"
}
```

```
POST /api/save
```

**请求**：
```json
{
  "path": "/Movies/Inception.nfo",
  "data": { /* NFO 数据 */ }
}
```

---

## 错误处理

| 错误场景 | 前端处理 |
|----------|----------|
| TMDB ID 不存在 (404) | 显示「未找到该 TMDB ID 对应的内容」 |
| API Key 未配置 (401) | 显示「请先配置 TMDB API Key」 |
| 网络超时 | 显示「连接 TMDB 超时，请检查网络或稍后重试」 |
| 用户取消保存对话框 | 不执行保存，保持编辑状态 |
| 保存权限错误 (500) | 显示「保存失败：无权限写入该位置」 |

### 输入验证

- TMDB ID 限制为正整数（`value > 0`）
- 空输入时禁用「获取数据」按钮

---

## 文件变更清单

### 前端

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `web/templates/index.html` | 修改 | 添加 TMDB 快速创建区域 HTML |
| `web/static/style.css` | 修改 | 添加新区域样式 |
| `web/templates/index.html` (JS) | 修改 | 添加 TMDB ID 获取逻辑、状态管理 |

### 后端

无需修改，复用现有 API。

---

## 实现要点

1. **TMDB ID 输入框**：使用 `<input type="number" min="1">`
2. **保存对话框**：使用 `showSaveFilePicker()` API，回退到传统方式
3. **状态标志**：`isCreatingFromTmdb` 用于区分新建/编辑模式
4. **数据填充**：TMDB API 返回数据结构可直接填充表单
5. **样式一致性**：参考现有上传文件区域的 CSS

---

## 测试要点

| 测试场景 | 验证内容 |
|----------|----------|
| 输入有效 TMDB ID | 数据成功加载并填充表单 |
| 输入无效 TMDB ID | 显示正确错误消息 |
| 空输入 | 「获取数据」按钮禁用 |
| 保存新建文件 | 弹出保存对话框，文件成功创建 |
| 取消保存对话框 | 不执行保存操作 |
| 手动打开已有文件 | `isCreatingFromTmdb` 状态正确重置 |

---

## 未来扩展（YAGNI - 暂不实现）

- 保存 TMDB ID 创建历史记录
- 批量 TMDB ID 创建
- 自动命名建议（基于标题）
