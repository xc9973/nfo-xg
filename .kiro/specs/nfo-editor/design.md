# Design Document: NFO Editor

## Overview

NFO Editor 是一个基于 Python 的桌面应用程序，使用 PyQt6 作为 GUI 框架。应用采用 MVC 架构模式，将数据模型、视图和控制逻辑分离，便于维护和扩展。

### 技术栈选择

- **GUI 框架**: PyQt6 - 成熟稳定，跨平台支持好，控件丰富
- **XML 解析**: lxml - 性能优秀，支持 XPath，保留格式
- **图片处理**: Pillow - 用于图片预览和缩放
- **配置存储**: QSettings - Qt 原生配置管理

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Main Window                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Menu Bar      │  │   Tool Bar      │  │  Status Bar │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │                      │  │                              │ │
│  │   Editor Panel       │  │     Preview Panel            │ │
│  │   (Tag Editing)      │  │     (Formatted View)         │ │
│  │                      │  │                              │ │
│  └──────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 模块结构

```
nfo_editor/
├── main.py                 # 应用入口
├── models/
│   ├── __init__.py
│   ├── nfo_model.py        # NFO 数据模型
│   ├── nfo_types.py        # NFO 类型定义
│   └── template.py         # 模板数据模型
├── views/
│   ├── __init__.py
│   ├── main_window.py      # 主窗口
│   ├── editor_panel.py     # 编辑面板
│   ├── preview_panel.py    # 预览面板
│   ├── batch_editor.py     # 批量编辑窗口
│   ├── template_manager.py # 模板管理窗口
│   └── widgets/
│       ├── __init__.py
│       ├── tag_editor.py   # 标签编辑器组件
│       └── actor_editor.py # 演员编辑器组件
├── controllers/
│   ├── __init__.py
│   ├── file_controller.py  # 文件操作控制器
│   └── batch_controller.py # 批量操作控制器
├── utils/
│   ├── __init__.py
│   ├── xml_parser.py       # XML 解析工具
│   ├── config.py           # 配置管理
│   └── template_io.py      # 模板文件读写
└── resources/
    ├── icons/              # 图标资源
    ├── styles/             # 样式表
    └── templates/          # 默认模板
```

## Components and Interfaces

### 1. NFO 数据模型 (NfoModel)

```python
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class NfoType(Enum):
    MOVIE = "movie"
    TVSHOW = "tvshow"
    EPISODE = "episodedetails"

@dataclass
class Actor:
    name: str
    role: str = ""
    thumb: str = ""
    order: int = 0

@dataclass
class NfoData:
    nfo_type: NfoType
    title: str = ""
    originaltitle: str = ""
    year: str = ""
    plot: str = ""
    runtime: str = ""
    genres: List[str] = field(default_factory=list)
    directors: List[str] = field(default_factory=list)
    actors: List[Actor] = field(default_factory=list)
    studio: str = ""
    rating: str = ""
    poster: str = ""
    fanart: str = ""
    # TV Show specific
    season: str = ""
    episode: str = ""
    aired: str = ""
    # 保留未知标签
    extra_tags: dict = field(default_factory=dict)
```

### 2. XML 解析器接口 (XmlParser)

```python
class XmlParser:
    def parse(self, file_path: str) -> NfoData:
        """解析 NFO 文件，返回 NfoData 对象"""
        pass
    
    def save(self, data: NfoData, file_path: str) -> None:
        """将 NfoData 保存为 NFO 文件"""
        pass
    
    def detect_type(self, file_path: str) -> NfoType:
        """检测 NFO 文件类型"""
        pass
    
    def format_xml(self, data: NfoData) -> str:
        """将 NfoData 格式化为 XML 字符串（用于预览）"""
        pass
```

### 3. 主窗口接口 (MainWindow)

```python
class MainWindow(QMainWindow):
    # 信号
    file_opened = Signal(str)      # 文件打开信号
    file_saved = Signal(str)       # 文件保存信号
    data_changed = Signal()        # 数据变更信号
    
    def __init__(self):
        self.current_file: Optional[str] = None
        self.nfo_data: Optional[NfoData] = None
        self.is_modified: bool = False
    
    def open_file(self, file_path: str = None) -> None:
        """打开 NFO 文件"""
        pass
    
    def save_file(self) -> None:
        """保存当前文件"""
        pass
    
    def save_file_as(self) -> None:
        """另存为"""
        pass
    
    def update_title(self) -> None:
        """更新窗口标题（显示修改状态）"""
        pass
```

### 4. 编辑面板接口 (EditorPanel)

```python
class EditorPanel(QWidget):
    data_changed = Signal()  # 数据变更信号
    
    def load_data(self, data: NfoData) -> None:
        """加载 NFO 数据到编辑界面"""
        pass
    
    def get_data(self) -> NfoData:
        """获取编辑后的数据"""
        pass
    
    def set_nfo_type(self, nfo_type: NfoType) -> None:
        """根据 NFO 类型调整界面"""
        pass
```

### 5. 预览面板接口 (PreviewPanel)

```python
class PreviewPanel(QWidget):
    def update_preview(self, data: NfoData) -> None:
        """更新预览内容"""
        pass
    
    def load_image(self, image_path: str, image_type: str) -> None:
        """加载并显示图片"""
        pass
    
    def set_placeholder(self, image_type: str) -> None:
        """显示占位图片"""
        pass
```

### 6. 模板数据模型 (Template)

```python
@dataclass
class NfoTemplate:
    """NFO 模板数据模型"""
    name: str                              # 模板名称
    description: str = ""                  # 模板描述
    studio: Optional[str] = None           # 制片公司
    genres: Optional[List[str]] = None     # 类型列表
    directors: Optional[List[str]] = None  # 导演列表
    rating: Optional[str] = None           # 评分
    # 其他可模板化的字段...
    
    def to_dict(self) -> dict:
        """转换为字典（用于 JSON 序列化）"""
        pass
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NfoTemplate':
        """从字典创建模板"""
        pass
```

### 7. 批量编辑器接口 (BatchEditor)

```python
class BatchEditor(QDialog):
    """批量编辑对话框"""
    
    def __init__(self, parent=None):
        self.selected_files: List[str] = []
        self.nfo_data_list: List[Tuple[str, NfoData]] = []
    
    def add_files(self, file_paths: List[str]) -> None:
        """添加要批量编辑的文件"""
        pass
    
    def add_directory(self, dir_path: str, recursive: bool = False) -> None:
        """从目录添加 NFO 文件"""
        pass
    
    def set_field_value(self, field: str, value: Any, mode: str = "overwrite") -> None:
        """设置字段值
        
        Args:
            field: 字段名
            value: 新值
            mode: "overwrite" 覆盖 | "append" 追加（仅多值字段）
        """
        pass
    
    def apply_template(self, template: NfoTemplate, fill_empty_only: bool = True) -> None:
        """应用模板到所有选中文件
        
        Args:
            template: 要应用的模板
            fill_empty_only: True 只填充空字段，False 覆盖所有字段
        """
        pass
    
    def preview_changes(self) -> List[dict]:
        """预览将要进行的更改"""
        pass
    
    def apply_changes(self) -> BatchResult:
        """应用更改到所有文件"""
        pass


@dataclass
class BatchResult:
    """批量操作结果"""
    total: int                    # 总文件数
    success: int                  # 成功数
    failed: int                   # 失败数
    errors: List[Tuple[str, str]] # (文件路径, 错误信息)
```

### 8. 模板管理器接口 (TemplateManager)

```python
class TemplateManager(QDialog):
    """模板管理对话框"""
    
    def __init__(self, parent=None):
        self.templates: List[NfoTemplate] = []
    
    def load_templates(self) -> None:
        """加载所有保存的模板"""
        pass
    
    def save_template(self, template: NfoTemplate) -> None:
        """保存模板"""
        pass
    
    def delete_template(self, name: str) -> None:
        """删除模板"""
        pass
    
    def export_template(self, template: NfoTemplate, file_path: str) -> None:
        """导出模板到 JSON 文件"""
        pass
    
    def import_template(self, file_path: str) -> NfoTemplate:
        """从 JSON 文件导入模板"""
        pass
    
    def create_from_nfo(self, nfo_data: NfoData) -> NfoTemplate:
        """从现有 NFO 数据创建模板"""
        pass
```

## Data Models

### NFO XML 结构示例

**Movie NFO:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>电影标题</title>
    <originaltitle>Original Title</originaltitle>
    <year>2024</year>
    <plot>剧情简介...</plot>
    <runtime>120</runtime>
    <genre>动作</genre>
    <genre>科幻</genre>
    <director>导演名</director>
    <studio>制片公司</studio>
    <rating>8.5</rating>
    <actor>
        <name>演员名</name>
        <role>角色名</role>
        <thumb>actor_thumb.jpg</thumb>
        <order>0</order>
    </actor>
    <poster>poster.jpg</poster>
    <fanart>fanart.jpg</fanart>
</movie>
```

### 数据流

```
┌─────────────┐     parse      ┌─────────────┐
│  NFO File   │ ─────────────> │  NfoData    │
│   (XML)     │                │  (Model)    │
└─────────────┘                └─────────────┘
                                     │
                                     │ bind
                                     ▼
                               ┌─────────────┐
                               │ EditorPanel │
                               │   (View)    │
                               └─────────────┘
                                     │
                                     │ update
                                     ▼
                               ┌─────────────┐
                               │PreviewPanel │
                               │   (View)    │
                               └─────────────┘
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: XML 解析保存往返一致性 (Round-Trip)

*For any* 有效的 NfoData 对象，将其序列化为 XML 然后再解析回来，应该得到等价的 NfoData 对象。

**Validates: Requirements 1.2, 1.4**

### Property 2: 无效 XML 错误处理

*For any* 无效或格式错误的 XML 字符串，解析器应该抛出明确的异常而不是崩溃，且不会产生部分损坏的数据。

**Validates: Requirements 1.3**

### Property 3: 多演员数据完整性

*For any* 包含多个演员的 NfoData，每个演员的 name、role、thumb、order 字段在解析和保存后都应该保持完整。

**Validates: Requirements 2.4**

### Property 4: 多类型标签处理

*For any* 包含多个 genre 或 director 的 NfoData，所有条目在往返解析后应该保持顺序和内容不变。

**Validates: Requirements 2.5**

### Property 5: 数据验证一致性

*For any* 无效的标签值（如非数字的 year、超出范围的 rating），验证函数应该返回 False 并提供错误信息。

**Validates: Requirements 2.6**

### Property 6: NFO 类型自动检测

*For any* 有效的 NFO 文件，解析器应该正确识别其类型（movie、tvshow、episodedetails）。

**Validates: Requirements 5.4**

### Property 7: 未知标签保留

*For any* 包含未知/自定义标签的 NFO 文件，这些标签在解析和保存后应该完整保留，不丢失任何数据。

**Validates: Requirements 5.5**

### Property 8: 配置持久化往返

*For any* 配置设置（如最后打开的目录），保存后重新加载应该得到相同的值。

**Validates: Requirements 4.5**

### Property 9: 模板序列化往返一致性

*For any* 有效的 NfoTemplate 对象，将其序列化为 JSON 然后再解析回来，应该得到等价的 NfoTemplate 对象。

**Validates: Requirements 7.5**

### Property 10: 模板填充空字段不覆盖已有值

*For any* NfoData 和 NfoTemplate，当使用 "fill empty only" 模式应用模板时，原有非空字段的值应该保持不变。

**Validates: Requirements 7.3**

### Property 11: 批量操作原子性

*For any* 批量编辑操作，如果某个文件更新失败，其他文件的更新应该继续执行，且失败的文件应该保持原始状态。

**Validates: Requirements 6.8**

### Property 12: 批量追加模式保留原有值

*For any* 多值字段（如 genre）的批量追加操作，原有的值应该全部保留，新值应该被添加到列表末尾。

**Validates: Requirements 6.5**

## Error Handling

### 错误类型定义

```python
class NfoEditorError(Exception):
    """NFO 编辑器基础异常"""
    pass

class ParseError(NfoEditorError):
    """XML 解析错误"""
    def __init__(self, message: str, line: int = None, column: int = None):
        self.line = line
        self.column = column
        super().__init__(message)

class ValidationError(NfoEditorError):
    """数据验证错误"""
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"{field}: {message}")

class FileError(NfoEditorError):
    """文件操作错误"""
    pass
```

### 错误处理策略

| 错误场景 | 处理方式 |
|---------|---------|
| 文件不存在 | 显示错误对话框，保持当前状态 |
| XML 解析失败 | 显示详细错误信息（行号、列号），保持当前状态 |
| 编码问题 | 尝试自动检测编码，失败则提示用户选择 |
| 保存失败 | 显示错误信息，提供"另存为"选项 |
| 图片加载失败 | 显示占位图，不影响其他功能 |
| 验证失败 | 高亮显示问题字段，允许继续编辑 |

## Testing Strategy

### 测试框架

- **单元测试**: pytest
- **属性测试**: hypothesis (Python PBT 库)
- **GUI 测试**: pytest-qt

### 测试结构

```
tests/
├── conftest.py              # pytest 配置和 fixtures
├── test_xml_parser.py       # XML 解析器测试
├── test_nfo_model.py        # 数据模型测试
├── test_validation.py       # 验证逻辑测试
├── test_config.py           # 配置管理测试
├── generators.py            # Hypothesis 生成器
└── fixtures/                # 测试用 NFO 文件
    ├── movie.nfo
    ├── tvshow.nfo
    └── episode.nfo
```

### 测试方法

**单元测试**:
- 测试特定示例和边界情况
- 测试错误条件和异常处理
- 测试组件集成点

**属性测试**:
- 使用 Hypothesis 库
- 每个属性测试至少运行 100 次迭代
- 测试标签格式: `# Feature: nfo-editor, Property N: property_text`

### 生成器设计

```python
from hypothesis import strategies as st

# 生成有效的 NfoData
@st.composite
def nfo_data_strategy(draw):
    nfo_type = draw(st.sampled_from(list(NfoType)))
    title = draw(st.text(min_size=1, max_size=200))
    year = draw(st.integers(min_value=1900, max_value=2100).map(str))
    # ... 其他字段
    return NfoData(nfo_type=nfo_type, title=title, year=year, ...)

# 生成无效 XML
@st.composite  
def invalid_xml_strategy(draw):
    # 生成各种无效 XML 情况
    pass
```
