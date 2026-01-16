# NFO Editor 批量编辑功能 - 实现计划

## 概述

本计划用于实现 NFO Editor 的批量编辑功能，支持按目录批量修改 studio/genre/director 等字段。

### 需求背景
- **数据量**: 100-1000 个文件/次
- **操作方式**: 选中剧集目录，批量修改字段
- **关键需求**: 预览机制、进度反馈、错误隔离

---

## 架构设计

### 整体结构

采用生产者-消费者模式：

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐
│  前端   │ ──▶ │  FastAPI    │ ──▶ │  后台任务池  │
│ (Web)   │     │   (API层)   │     │ ThreadPool   │
└─────────┘     └─────────────┘     └──────────────┘
                      │                      │
                      ▼                      ▼
                ┌─────────────┐     ┌──────────────┐
                │ 任务状态存储 │ ◀── │ 文件 I/O 操作 │
                │ (内存dict)  │     │ (并发读写)   │
                └─────────────┘     └──────────────┘
```

### 核心组件

1. **BatchTask** - 任务数据类，存储任务状态、进度、结果
2. **TaskManager** - 单例任务管理器，管理所有后台任务
3. **BatchProcessor** - 并发处理器，执行实际的文件读写操作
4. **API 端点** - `/api/batch/preview`、`/api/batch/apply`、`/api/batch/status/{id}`

### 技术选型

- 并发: `concurrent.futures.ThreadPoolExecutor`（I/O 密集型，线程足够）
- 任务 ID: `uuid.uuid4()` 生成唯一标识
- 状态存储: 内存字典（单机部署够用，无需 Redis）
- 后台任务: FastAPI `BackgroundTasks`

---

## 数据模型设计

### BatchTask 数据类

```python
@dataclass
class BatchTask:
    task_id: str
    status: TaskStatus  # pending, running, completed, failed
    total_files: int
    processed_files: int
    success_count: int
    failed_count: int
    errors: List[str]
    created_at: datetime
    field: str
    value: str
    mode: str
    directory: str

    @property
    def progress(self) -> float:
        return self.processed_files / self.total_files * 100
```

### TaskStatus 枚举

```python
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

### API 请求/响应模型

```python
class BatchPreviewRequest(BaseModel):
    directory: str              # 目标目录
    field: str                  # 要修改的字段 (studio/genre/director)
    value: str                  # 新值
    mode: str = "overwrite"     # overwrite / append

class BatchApplyRequest(BaseModel):
    task_id: str                # 预览任务ID
    confirmed: bool = True

class BatchPreviewResponse(BaseModel):
    task_id: str
    total_files: int
    sample_files: List[dict]    # 前5个文件预览

class BatchStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    processed: int
    total: int
    success: int
    failed: int
    errors: List[str]
```

### 并发参数

```python
MAX_WORKERS = 10           # 最大并发线程数
BATCH_SIZE = 50            # 每批处理的文件数
```

---

## 核心处理逻辑

### BatchProcessor 类

```python
class BatchProcessor:
    def __init__(self, parser: XmlParser, max_workers: int = 10):
        self.parser = parser
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def preview(self, directory: Path, field: str, value: str) -> List[dict]:
        """扫描目录，返回将被修改的文件列表"""
        nfo_files = self._scan_nfo_files(directory)
        futures = [
            self.executor.submit(self._preview_file, f, field, value)
            for f in nfo_files
        ]
        return [f.result() for f in as_completed(futures) if f.result()]

    def apply(self, task_id: str, files: List[dict], field: str, value: str,
              mode: str) -> BatchResult:
        """执行批量修改，返回结果"""
        task = TaskManager.get(task_id)
        task.status = TaskStatus.RUNNING

        futures = []
        for file_info in files:
            f = self.executor.submit(
                self._apply_file,
                file_info, field, value, mode, task
            )
            futures.append(f)

        # 等待完成并更新进度
        for future in as_completed(futures):
            task.processed_files += 1
            # 处理结果...

        task.status = TaskStatus.COMPLETED
        return task
```

### 处理流程

**预览阶段**:
1. 扫描目录获取所有 `.nfo` 文件
2. 并发读取每个文件，检查字段当前值
3. 返回将被修改的文件列表

**执行阶段**:
1. 从预览结果获取文件列表
2. 并发读取 → 修改 → 写回
3. 实时更新进度到任务状态
4. 收集成功/失败信息

---

## API 端点设计

### 1. 预览接口

```
POST /api/batch/preview
```

```python
@app.post("/api/batch/preview")
async def batch_preview(req: BatchPreviewRequest, auth=Depends(check_auth)):
    """
    预览批量修改操作

    返回:
    - task_id: 用于后续执行
    - total_files: 将被修改的文件数
    - sample_files: 前5个文件预览（显示当前值和新值）
    """
    path = Path(req.directory)
    if not path.exists():
        raise HTTPException(404, "目录不存在")

    processor = BatchProcessor(parser)
    files = processor.preview(path, req.field, req.value)

    task = BatchTask(
        task_id=str(uuid4()),
        status=TaskStatus.PENDING,
        total_files=len(files),
        # ...
    )
    TaskManager.add(task)

    return {
        "task_id": task.task_id,
        "total_files": len(files),
        "sample_files": files[:5]
    }
```

### 2. 执行接口

```
POST /api/batch/apply
```

```python
@app.post("/api/batch/apply")
async def batch_apply(req: BatchApplyRequest, background_tasks: BackgroundTasks,
                      auth=Depends(check_auth)):
    """执行批量修改（后台任务）"""
    task = TaskManager.get(req.task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    # 后台执行
    background_tasks.add_task(
        processor.apply,
        req.task_id,
        task.preview_files,
        # ...
    )

    return {"task_id": req.task_id, "status": "running"}
```

### 3. 进度查询

```
GET /api/batch/status/{task_id}
```

```python
@app.get("/api/batch/status/{task_id}")
async def batch_status(task_id: str, auth=Depends(check_auth)):
    """查询任务进度"""
    task = TaskManager.get(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "progress": task.progress,
        "processed": task.processed_files,
        "total": task.total_files,
        "success": task.success_count,
        "failed": task.failed_count,
        "errors": task.errors[-10:]  # 最近10条错误
    }
```

---

## 错误处理与边界情况

### 错误处理策略

```python
def _apply_file(self, file_info: dict, field: str, value: str,
                mode: str, task: BatchTask):
    """单个文件处理，带错误隔离"""
    try:
        # 1. 读取文件
        data = self.parser.parse(file_info["path"])

        # 2. 应用修改
        self._apply_field(data, field, value, mode)

        # 3. 验证
        is_valid, errors = validate_nfo_data(data)
        if not is_valid:
            raise ValueError(f"验证失败: {errors}")

        # 4. 写回
        self.parser.save(data, file_info["path"])

        task.success_count += 1
        return True

    except Exception as e:
        task.failed_count += 1
        task.errors.append(f"{file_info['filename']}: {str(e)}")
        return False
```

### 边界情况处理

| 场景 | 处理方式 |
|------|----------|
| 目录不存在 | 返回 404，不创建任务 |
| 目录无 .nfo 文件 | 返回空列表，提示用户 |
| 文件无权限 | 记录错误，继续处理其他文件 |
| 文件损坏 XML | 记录错误，跳过该文件 |
| 磁盘空间不足 | 中断任务，标记为 failed |
| 并发冲突 | 文件锁或重试机制 |

### 限制与保护

```python
# 防止过度并发
MAX_CONCURRENT_TASKS = 5

# 防止单次操作文件过多
MAX_FILES_PER_BATCH = 2000

# 任务过期清理（30分钟）
TASK_TTL_SECONDS = 1800
```

---

## 文件变更计划

### 新增文件

```
nfo_editor/
├── batch/
│   ├── __init__.py
│   ├── processor.py      # BatchProcessor 核心逻辑
│   ├── task_manager.py   # TaskManager 任务状态管理
│   └── models.py         # BatchTask, TaskStatus 等数据类
```

### 修改文件

```
web/app.py
├── 新增导入: from nfo_editor.batch import ...
├── 新增 API:
│   ├── POST /api/batch/preview
│   ├── POST /api/batch/apply
│   └── GET  /api/batch/status/{task_id}
```

### 新增测试文件

```
tests/
├── test_batch_processor.py
└── test_batch_api.py
```

---

## 实现步骤

### 第一步：数据模型定义 (30分钟)

**文件**: `nfo_editor/batch/models.py`

1. 创建 `TaskStatus` 枚举类
2. 创建 `BatchTask` 数据类
3. 创建 API 请求/响应模型：
   - `BatchPreviewRequest`
   - `BatchApplyRequest`
   - `BatchPreviewResponse`
   - `BatchStatusResponse`

### 第二步：任务管理器 (30分钟)

**文件**: `nfo_editor/batch/task_manager.py`

1. 创建 `TaskManager` 单例类
2. 实现任务增删查改方法：
   - `add(task)`: 添加任务
   - `get(task_id)`: 获取任务
   - `delete(task_id)`: 删除任务
   - `list_all()`: 列出所有任务
3. 实现任务过期清理机制

### 第三步：核心处理逻辑 (1小时)

**文件**: `nfo_editor/batch/processor.py`

1. 创建 `BatchProcessor` 类
2. 实现预览方法 `preview()`
3. 实现执行方法 `apply()`
4. 实现辅助方法：
   - `_scan_nfo_files()`: 扫描 NFO 文件
   - `_preview_file()`: 预览单个文件
   - `_apply_file()`: 应用修改到单个文件
   - `_apply_field()`: 应用字段修改逻辑

### 第四步：API 端点 (30分钟)

**文件**: `web/app.py`

1. 导入批量处理模块
2. 添加预览接口 `POST /api/batch/preview`
3. 添加执行接口 `POST /api/batch/apply`
4. 添加进度查询接口 `GET /api/batch/status/{task_id}`

### 第五步：测试用例 (1小时)

**文件**: `tests/test_batch_processor.py`

1. 空目录测试
2. 单文件修改测试
3. overwrite 模式测试
4. append 模式测试
5. 错误隔离测试
6. 并发性能测试

**文件**: `tests/test_batch_api.py`

1. 预览接口测试
2. 执行接口测试
3. 进度查询测试
4. 完整流程集成测试

---

## 验证命令

### 单元测试

```bash
pytest tests/test_batch_processor.py -v
```

### 集成测试

```bash
pytest tests/test_batch_api.py -v
```

### 启动服务

```bash
uvicorn web.app:app --reload
```

### 手动测试 API

```bash
# 预览
curl -X POST http://localhost:1111/api/batch/preview \
  -H "Content-Type: application/json" \
  -d '{"directory": "/path/to/nfos", "field": "studio", "value": "Netflix"}'

# 执行
curl -X POST http://localhost:1111/api/batch/apply \
  -H "Content-Type: application/json" \
  -d '{"task_id": "xxx", "confirmed": true}'

# 查询状态
curl http://localhost:1111/api/batch/status/xxx
```

---

## 风险与回退

### 潜在风险

1. **并发冲突**: 多个任务同时修改同一文件
   - 缓解: 文件锁机制
2. **内存占用**: 大批量任务时内存增长
   - 缓解: 限制单次任务最大文件数
3. **磁盘空间**: 写入失败导致数据不一致
   - 缓解: 先写入临时文件，成功后替换原文件

### 回退方案

1. 保留原始文件备份（可选）
2. 任务失败时回滚已修改的文件
3. 提供撤销功能（记录修改历史）

---

## 附录

### 字段映射表

| 字段名 | 类型 | NFO 路径 | 支持模式 |
|--------|------|----------|----------|
| studio | 单值 | `//studio` | overwrite |
| genre | 多值 | `//genre` | overwrite, append |
| director | 多值 | `//director` | overwrite, append |

### 时间估算

| 任务 | 预计时间 |
|------|----------|
| 数据模型定义 | 30分钟 |
| 任务管理器 | 30分钟 |
| 核心处理逻辑 | 1小时 |
| API 端点 | 30分钟 |
| 测试用例 | 1小时 |
| **总计** | **3.5小时** |

### 依赖项

当前项目已包含所有必需依赖：
- `lxml>=4.9.0` - XML 解析
- `fastapi>=0.104.0` - Web 框架
- `uvicorn>=0.24.0` - ASGI 服务器
- `pytest>=7.4.0` - 测试框架
- `hypothesis>=6.82.0` - 属性测试

---

*文档版本: 1.0*
*创建日期: 2026-01-15*
