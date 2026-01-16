# Design Document: Web Search Feature

## Overview

为 NFO 编辑器网页端添加搜索功能，包括前端搜索界面和后端搜索 API。搜索支持按文件名和 NFO 内容进行匹配，结果可直接点击打开编辑。

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Search Bar  │→ │ Search API  │→ │ Results Display │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │              /api/search endpoint                │    │
│  │  ┌──────────────┐  ┌──────────────────────────┐ │    │
│  │  │ File Scanner │  │ Content Parser (XmlParser)│ │    │
│  │  └──────────────┘  └──────────────────────────┘ │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Backend API

#### SearchRequest Model
```python
class SearchRequest(BaseModel):
    query: str           # 搜索关键词
    path: str = ""       # 搜索起始目录，默认为用户主目录
    max_depth: int = 5   # 最大递归深度
    max_results: int = 50  # 最大结果数
```

#### SearchResult Model
```python
class SearchResultItem(BaseModel):
    path: str            # 文件完整路径
    filename: str        # 文件名
    match_type: str      # 匹配类型: "filename" | "title" | "actor" | "plot"
    match_field: str     # 匹配的具体字段值
    title: str = ""      # NFO 标题（如果有）
```

#### /api/search Endpoint
- Method: POST
- Input: SearchRequest
- Output: `{"results": List[SearchResultItem], "truncated": bool}`
- 搜索逻辑：
  1. 递归扫描目录查找 .nfo 文件
  2. 先匹配文件名
  3. 再解析 NFO 内容匹配 title、originaltitle、actors、plot
  4. 返回去重后的结果

### Frontend Components

#### Search Bar
- 位置：文件浏览面板顶部，路径栏下方
- 元素：
  - 搜索输入框 (input)
  - 搜索按钮 (button)
  - 清除按钮 (button, 仅在有搜索结果时显示)

#### Search Results Display
- 替换文件列表显示搜索结果
- 每个结果显示：
  - 文件名
  - 匹配类型标签
  - 完整路径（较小字体）
- 点击结果：加载文件并导航到所在目录

## Data Models

### SearchResultItem (Frontend)
```javascript
{
    path: string,        // 完整路径
    filename: string,    // 文件名
    match_type: string,  // 匹配类型
    match_field: string, // 匹配字段值
    title: string        // NFO 标题
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: 文件名匹配正确性
*For any* search query string Q and NFO filename F, if F.lower() contains Q.lower(), then the search results SHALL include this file with match_type="filename".

**Validates: Requirements 2.1**

### Property 2: 内容匹配正确性
*For any* search query string Q and NFO file with content fields (title, originaltitle, actors, plot), if any field value V satisfies V.lower() contains Q.lower(), then the search results SHALL include this file with the appropriate match_type indicating which field matched.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 3: 搜索结果去重
*For any* search query, each unique file path SHALL appear at most once in the search results, even if the file matches multiple criteria (filename and content).

**Validates: Requirements 2.3**

### Property 4: 搜索深度限制
*For any* search operation starting at directory D with max_depth=N, the search SHALL only include files from directories at depth 0 to N relative to D. Files at depth > N SHALL NOT appear in results.

**Validates: Requirements 6.1**

### Property 5: 结果数量限制
*For any* search operation with max_results=M, the returned results list length SHALL be <= M.

**Validates: Requirements 6.2**

### Property 6: 截断标志正确性
*For any* search operation, if the total number of matching files exceeds max_results, the response SHALL have truncated=true. If total matches <= max_results, truncated SHALL be false.

**Validates: Requirements 6.3**

## Error Handling

| Error Scenario | Handling |
|----------------|----------|
| 搜索目录不存在 | 返回 404 错误，提示"目录不存在" |
| 无权限访问目录 | 跳过该目录，继续搜索其他目录 |
| NFO 文件解析失败 | 跳过该文件，仅匹配文件名 |
| 搜索关键词为空 | 返回空结果列表 |
| 搜索超时 | 返回已找到的结果，标记 truncated=true |

## Testing Strategy

### Unit Tests
- 测试搜索 API 的基本功能
- 测试文件名匹配逻辑
- 测试内容匹配逻辑
- 测试边界条件（空查询、无结果等）

### Property-Based Tests
- 使用 Hypothesis 库进行属性测试
- 生成随机搜索查询和 NFO 数据
- 验证匹配正确性和结果限制

### Integration Tests
- 测试前后端搜索流程
- 测试搜索结果点击交互
