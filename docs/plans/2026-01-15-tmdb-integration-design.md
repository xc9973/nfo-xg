# TMDB 在线数据抓取功能 - 设计文档

## 1. 概述

### 1.1 功能描述

为 NFO 编辑器添加在线数据抓取功能，允许用户通过 TMDB (The Movie Database) API 搜索并获取电影/电视剧的元数据，自动填充到 NFO 文件中。

### 1.2 目标

- 减少手动输入工作量，提高编辑效率
- 确保元数据的准确性和完整性
- 提供友好的搜索和选择体验

### 1.3 约束

- 需要有效的 TMDB API Key（用户自行申请）
- 遵守 TMDB API 使用条款和限流规则
- 保持离线优先：在线抓取是可选功能，不影响核心编辑流程

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端 UI   │ ──▶ │  FastAPI    │ ──▶ │  TMDB API   │
│ (搜索界面)  │     │  (后端代理)  │     │  (数据源)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                     ┌─────────────┐
                     │  NFO 文件   │
                     │  (数据填充)  │
                     └─────────────┘
```

### 2.2 组件划分

| 组件 | 职责 | 技术选型 |
|------|------|----------|
| `TMDBClient` | TMDB API 客户端，处理所有 API 调用 | `requests` + `tenacity` |
| `tmdb_api.py` | FastAPI 路由，代理前端请求 | FastAPI |
| `search.html` | 搜索结果展示 UI | 原生 JS + CSS |
| `config.py` | API Key 配置管理 | 环境变量 |

### 2.3 数据流

1. 用户输入搜索关键词 → 前端发送请求到 `/api/tmdb/search`
2. 后端调用 TMDB 搜索 API → 返回结果列表
3. 前端展示搜索结果（标题、年份、海报）
4. 用户选择结果 → 前端发送请求到 `/api/tmdb/get/{id}`
5. 后端获取详细信息 → 映射到 NFO 格式 → 返回
6. 前端自动填充表单字段

---

## 3. TMDB API 客户端设计

### 3.1 核心 API 方法

```python
class TMDBClient:
    """TMDB API 客户端"""

    BASE_URL = "https://api.themoviedb.org/3"

    def search_multi(self, query: str, page: int = 1) -> List[Dict]:
        """搜索电影和电视剧
        Returns: [
            {
                "id": 123,
                "media_type": "movie",  # or "tv"
                "title": "电影名称",
                "original_title": "原标题",
                "year": "2024",
                "poster_path": "/abc.jpg",
                "overview": "简介"
            }, ...
        ]
        """

    def get_movie_details(self, tmdb_id: int) -> Dict:
        """获取电影详细信息
        Returns: 完整的电影数据，映射到 NfoData 格式
        """

    def get_tv_details(self, tmdb_id: int) -> Dict:
        """获取电视剧详细信息
        Returns: 完整的电视剧数据，映射到 NfoData 格式
        """

    def get_tv_episode_details(self, tmdb_id: int,
                                season: int, episode: int) -> Dict:
        """获取单集详细信息
        """
```

### 3.2 数据映射规则

| NFO 字段 | TMDB 字段 | 转换规则 |
|----------|-----------|----------|
| `title` | `title` / `name` | 直接映射 |
| `originaltitle` | `original_title` / `original_name` | 直接映射 |
| `year` | `release_date` / `first_air_date` | 提取年份部分 |
| `plot` | `overview` | 直接映射 |
| `runtime` | `runtime` | 转为字符串 |
| `rating` | `vote_average` | 转为字符串，保留1位小数 |
| `genres` | `genres[]` | 提取 `name` 字段 |
| `directors` | `credits.crew[]` (job=Director) | 提取 `name` 字段 |
| `actors` | `credits.cast[]` | 映射 `name`, `character`, `profile_path` |
| `studio` | `production_companies[0].name` | 取第一个制片公司 |
| `poster` | `poster_path` | 拼接完整 URL |
| `fanart` | `backdrop_path` | 拼接完整 URL |
| `aired` | `air_date` | 直接映射 |

### 3.3 错误处理与重试

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def _request(self, endpoint: str, params: Dict) -> Dict:
    """带重试的 API 请求"""
```

**错误类型处理：**

| 错误 | HTTP 状态 | 处理方式 |
|------|-----------|----------|
| 无效 API Key | 401 | 返回配置错误提示 |
| 请求限流 | 429 | 自动重试，指数退避 |
| 未找到结果 | 404 | 返回空列表 |
| 网络错误 | - | 重试3次 |
| 超时 | - | 10秒超时，重试 |

---

## 4. API 端点设计

### 4.1 搜索接口

```
GET /api/tmdb/search?q={query}&page={page}
```

**响应格式：**
```json
{
    "results": [
        {
            "id": 123,
            "media_type": "movie",
            "title": "Inception",
            "year": "2010",
            "poster_url": "https://image.tmdb.org/t/p/w200/abc.jpg",
            "overview": "A thief who steals corporate secrets..."
        }
    ],
    "total_pages": 5,
    "total_results": 42
}
```

### 4.2 获取详情接口

```
GET /api/tmdb/movie/{tmdb_id}
GET /api/tmdb/tv/{tmdb_id}
GET /api/tmdb/tv/{tmdb_id}/season/{season}/episode/{episode}
```

**响应格式（直接对应 NFO 数据结构）：**
```json
{
    "nfo_type": "movie",
    "title": "Inception",
    "originaltitle": "Inception",
    "year": "2010",
    "plot": "A thief who steals corporate secrets...",
    "runtime": "148",
    "rating": "8.4",
    "genres": ["Action", "Science Fiction", "Adventure"],
    "directors": ["Christopher Nolan"],
    "actors": [
        {"name": "Leonardo DiCaprio", "role": "Cobb", "thumb": "", "order": 0},
        {"name": "Joseph Gordon-Levitt", "role": "Arthur", "thumb": "", "order": 1}
    ],
    "studio": "Warner Bros. Pictures",
    "poster": "https://image.tmdb.org/t/p/original/abc.jpg",
    "fanart": "https://image.tmdb.org/t/p/original/def.jpg"
}
```

### 4.3 配置管理接口

```
POST /api/tmdb/config
{
    "api_key": "your_api_key_here"
}
```

API Key 存储在服务器配置文件中，不返回给前端。

---

## 5. 前端 UI 设计

### 5.1 搜索界面布局

```
┌─────────────────────────────────────────────────────────┐
│  NFO 编辑器                                    [🔍 搜索]  │
├─────────────┬───────────────────────────────────────────┤
│             │  编辑表单区域                              │
│  文件浏览   │  ┌─────────────────────────────────────┐  │
│             │  │ 标题: [Inception        ] [搜索...] │  │
│  📋 模板    │  │ 原标题: [Inception      ]           │  │
│             │  │ 年份: [2010             ]           │  │
│  + 新建模板 │  │ ...                                │  │
│             │  └─────────────────────────────────────┘  │
└─────────────┴───────────────────────────────────────────┘
                    │ 点击搜索按钮后
                    ▼
┌─────────────────────────────────────────────────────────┐
│  搜索 TMDB                                    [× 关闭]   │
├─────────────────────────────────────────────────────────┤
│  搜索: [Inception                     ] [搜索]           │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│  │ 海报    │ │ 海报    │ │ 海报    │                   │
│  │ 缩略图  │ │ 缩略图  │ │ 缩略图  │                   │
│  └─────────┘ └─────────┘ └─────────┘                   │
│  Inception   Interstellar  The Dark Knight              │
│  2010        2014          2012                         │
│  [选择]      [选择]        [选择]                        │
└─────────────────────────────────────────────────────────┘
```

### 5.2 交互流程

1. 用户点击标题字段旁的"搜索"按钮
2. 弹出搜索模态框，自动填入当前标题作为搜索词
3. 用户修改搜索词，点击"搜索"
4. 显示加载状态，展示搜索结果
5. 用户点击某个结果的"选择"按钮
6. 模态框关闭，所有表单字段自动填充
7. 显示提示"已从 TMDB 获取数据"

### 5.3 JavaScript 实现

```javascript
async function searchTMDB() {
    const query = document.getElementById('title').value || prompt('请输入搜索关键词:');
    if (!query) return;

    const modal = showSearchModal();
    modal.setLoading(true);

    try {
        const res = await fetch(`/api/tmdb/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        modal.showResults(data.results);
    } catch (e) {
        modal.showError(e.message);
    }
}

async function selectTMDBResult(id, mediaType) {
    const modal = getSearchModal();
    modal.setLoading(true);

    try {
        const endpoint = mediaType === 'movie' ? 'movie' : 'tv';
        const res = await fetch(`/api/tmdb/${endpoint}/${id}`);
        const nfoData = await res.json();

        // 填充表单
        applyNFOData(nfoData);
        modal.close();
        showToast('已从 TMDB 获取数据', 'success');
    } catch (e) {
        modal.showError(e.message);
    }
}
```

---

## 6. 文件结构

```
nfo_editor/
├── services/
│   ├── __init__.py
│   ├── tmdb_client.py      # TMDB API 客户端
│   └── tmdb_mapper.py       # TMDB → NFO 数据映射
│
web/
├── app.py                   # 添加 TMDB 路由
├── config.py                # 添加 API Key 配置
├── static/
│   ├── style.css            # 添加搜索模态框样式
│   └── tmdb.css             # TMDB 相关样式（可选）
└── templates/
    └── index.html           # 添加搜索 UI

tests/
├── test_tmdb_client.py      # TMDB 客户端测试
├── test_tmdb_mapper.py      # 数据映射测试
└── test_tmdb_api.py         # API 端点测试

config/
├── config.example.yaml      # 添加 TMDB 配置示例
└── tmdb_config.yaml         # TMDB 配置文件（gitignore）
```

---

## 7. 配置管理

### 7.1 环境变量

```bash
# .env
TMDB_API_KEY=your_api_key_here
```

### 7.2 配置文件

```yaml
# config/tmdb_config.yaml
tmdb:
  api_key: "${TMDB_API_KEY}"
  base_url: "https://api.themoviedb.org/3"
  image_base_url: "https://image.tmdb.org/t/p"
  timeout: 10
  max_retries: 3
```

### 7.3 API Key 验证

启动时验证 API Key 有效性：

```python
def validate_tmdb_config() -> bool:
    """验证 TMDB 配置是否有效"""
    client = TMDBClient(api_key=settings.TMDB_API_KEY)
    try:
        # 使用一个简单的请求验证
        client.get_movie_details(550)  # Fight Club, known ID
        return True
    except Exception as e:
        logger.error(f"TMDB API Key 验证失败: {e}")
        return False
```

---

## 8. 实现计划

### 阶段 1: 后端核心 (1-2小时)

1. **TMDB 客户端实现** (`services/tmdb_client.py`)
   - 实现 `TMDBClient` 类
   - 添加搜索、获取详情方法
   - 实现错误处理和重试逻辑

2. **数据映射实现** (`services/tmdb_mapper.py`)
   - 实现 TMDB 数据到 NFO 数据的映射
   - 处理各种边界情况

3. **API 端点** (`web/app.py`)
   - 添加搜索接口
   - 添加获取详情接口
   - 添加配置管理接口

### 阶段 2: 前端界面 (1小时)

1. **搜索模态框 UI**
   - HTML 结构
   - CSS 样式
   - JavaScript 交互逻辑

2. **表单自动填充**
   - 实现 `applyNFOData()` 函数
   - 处理字段映射

### 阶段 3: 测试 (1小时)

1. **单元测试**
   - TMDB 客户端测试
   - 数据映射测试

2. **集成测试**
   - API 端点测试
   - 手动测试完整流程

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| TMDB API 限流 | 搜索请求被拒绝 | 实现请求队列和缓存 |
| API Key 泄露 | 滥用导致配额耗尽 | API Key 仅存储服务端，不暴露给前端 |
| 网络不稳定 | 请求超时失败 | 实现重试机制和友好错误提示 |
| 数据映射不完整 | 填充数据缺失 | 允许用户手动修正 |
| TMDB 服务中断 | 功能不可用 | 优雅降级，保持离线编辑功能 |

---

## 10. 未来扩展

- **多数据源支持**: 整合 IMDB、OMDB 等其他数据源
- **本地缓存**: 缓存搜索结果，减少 API 调用
- **批量匹配**: 根据文件名批量搜索并填充
- **多语言支持**: 支持搜索和获取多语言元数据
- **图片下载**: 下载海报和背景图到本地

---

*文档版本: 1.0*
*创建日期: 2026-01-15*

