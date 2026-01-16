# Implementation Plan: NFO Editor

## Overview

基于 PyQt6 的可视化 NFO 文件编辑器实现计划。采用增量开发方式，先完成核心数据模型和解析器，再构建 GUI 界面。

## Tasks

- [x] 1. 项目初始化和基础结构
  - [x] 1.1 创建项目目录结构和 requirements.txt
    - 创建 nfo_editor/ 目录及子目录 (models, views, controllers, utils, resources)
    - 添加依赖: PyQt6, lxml, Pillow, pytest, hypothesis
    - _Requirements: 项目基础设施_

  - [x] 1.2 创建数据模型 (nfo_model.py, nfo_types.py)
    - 实现 NfoType 枚举 (MOVIE, TVSHOW, EPISODE)
    - 实现 Actor 数据类
    - 实现 NfoData 数据类，包含所有 NFO 字段
    - _Requirements: 2.3, 2.4, 2.5_

  - [x] 1.3 编写数据模型单元测试
    - 测试 NfoData 创建和字段访问
    - 测试 Actor 数据完整性
    - _Requirements: 2.3, 2.4_

- [x] 2. XML 解析器实现
  - [x] 2.1 实现 XML 解析器核心功能 (xml_parser.py)
    - 实现 parse() 方法解析 NFO 文件到 NfoData
    - 实现 save() 方法将 NfoData 保存为 XML
    - 实现 detect_type() 方法自动检测 NFO 类型
    - 实现 format_xml() 方法格式化输出
    - _Requirements: 1.2, 1.4, 5.1, 5.2, 5.3, 5.4_

  - [x] 2.2 实现未知标签保留逻辑
    - 解析时保存未知标签到 extra_tags
    - 保存时还原未知标签到正确位置
    - _Requirements: 5.5_

  - [x] 2.3 实现错误处理和异常类
    - 创建 ParseError, ValidationError, FileError 异常类
    - 处理无效 XML、文件不存在等错误情况
    - _Requirements: 1.3_

  - [x] 2.4 编写属性测试: XML 往返一致性
    - **Property 1: XML 解析保存往返一致性**
    - **Validates: Requirements 1.2, 1.4**

  - [x] 2.5 编写属性测试: 无效 XML 错误处理
    - **Property 2: 无效 XML 错误处理**
    - **Validates: Requirements 1.3**

  - [x] 2.6 编写属性测试: NFO 类型检测
    - **Property 6: NFO 类型自动检测**
    - **Validates: Requirements 5.4**

  - [x] 2.7 编写属性测试: 未知标签保留
    - **Property 7: 未知标签保留**
    - **Validates: Requirements 5.5**

- [x] 3. Checkpoint - 核心解析器验证
  - 确保所有解析器测试通过，如有问题请询问用户

- [x] 4. 数据验证模块
  - [x] 4.1 实现数据验证函数 (validation.py)
    - 验证 year 字段 (1900-2100 范围)
    - 验证 rating 字段 (0-10 范围)
    - 验证 runtime 字段 (正整数)
    - 返回验证结果和错误信息
    - _Requirements: 2.6_

  - [x] 4.2 编写属性测试: 数据验证一致性
    - **Property 5: 数据验证一致性**
    - **Validates: Requirements 2.6**

- [x] 5. 配置管理模块
  - [x] 5.1 实现配置管理 (config.py)
    - 使用 QSettings 存储配置
    - 保存/加载最后打开的目录
    - 保存/加载主题设置
    - _Requirements: 4.5_

  - [x] 5.2 编写属性测试: 配置持久化
    - **Property 8: 配置持久化往返**
    - **Validates: Requirements 4.5**

- [-] 6. GUI 主窗口实现
  - [x] 6.1 创建主窗口框架 (main_window.py)
    - 创建 QMainWindow 子类
    - 设置菜单栏 (文件、编辑、视图、帮助)
    - 设置工具栏 (打开、保存、另存为)
    - 设置状态栏
    - _Requirements: 4.1, 4.2_

  - [x] 6.2 实现文件操作功能
    - 实现打开文件对话框 (过滤 .nfo 文件)
    - 实现保存和另存为功能
    - 实现拖拽文件支持
    - 实现关闭时未保存提示
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 4.4_

  - [x] 6.3 实现快捷键绑定
    - Ctrl+O 打开, Ctrl+S 保存, Ctrl+Shift+S 另存为
    - Ctrl+Z 撤销, Ctrl+Y 重做
    - _Requirements: 4.2_

  - [x] 6.4 实现窗口标题更新
    - 显示当前文件名
    - 未保存时显示 * 标记
    - _Requirements: 4.3_

- [-] 7. 编辑面板实现
  - [x] 7.1 创建编辑面板框架 (editor_panel.py)
    - 使用 QScrollArea 包装
    - 使用 QFormLayout 布局标签编辑器
    - _Requirements: 2.1_

  - [x] 7.2 实现基础标签编辑器
    - 实现 title, originaltitle, year, plot, runtime, studio, rating 编辑
    - 使用 QLineEdit 和 QTextEdit
    - 连接信号实现实时更新
    - _Requirements: 2.2, 2.3_

  - [x] 7.3 实现多值标签编辑器 (genre, director)
    - 创建可添加/删除的列表编辑器
    - 支持拖拽排序
    - _Requirements: 2.5_

  - [x] 7.4 实现演员编辑器 (actor_editor.py)
    - 创建演员列表视图
    - 支持添加/删除/编辑演员
    - 每个演员包含 name, role, thumb, order 字段
    - _Requirements: 2.4_

  - [x] 7.5 编写属性测试: 多演员数据完整性
    - **Property 3: 多演员数据完整性**
    - **Validates: Requirements 2.4**

  - [x] 7.6 编写属性测试: 多类型标签处理
    - **Property 4: 多类型标签处理**
    - **Validates: Requirements 2.5**

  - [x] 7.7 实现 NFO 类型切换
    - 根据 NFO 类型显示/隐藏相关字段
    - 电视剧显示 season, episode, aired 字段
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 8. Checkpoint - 编辑功能验证
  - 确保所有编辑面板测试通过，如有问题请询问用户

- [-] 9. 预览面板实现
  - [x] 9.1 创建预览面板框架 (preview_panel.py)
    - 使用 QScrollArea 包装
    - 创建格式化显示区域
    - _Requirements: 3.1_

  - [x] 9.2 实现内容预览
    - 格式化显示所有标签信息
    - 实时响应编辑变化
    - _Requirements: 3.1, 3.2_

  - [x] 9.3 实现图片预览
    - 加载并显示 poster 和 fanart 图片
    - 图片不存在时显示占位图
    - 支持图片缩放
    - _Requirements: 3.3, 3.5_

  - [x] 9.4 实现 plot 文本格式化
    - 处理换行和空格
    - 保持可读性
    - _Requirements: 3.4_

- [-] 10. 主题支持
  - [x] 10.1 实现主题切换
    - 创建 light 和 dark 主题样式表
    - 添加视图菜单切换选项
    - 保存主题偏好到配置
    - _Requirements: 4.6_

- [-] 11. 应用入口和集成
  - [x] 11.1 创建应用入口 (main.py)
    - 初始化 QApplication
    - 加载配置
    - 创建并显示主窗口
    - 处理命令行参数 (可选打开文件)
    - _Requirements: 全部集成_

  - [x] 11.2 组件集成和信号连接
    - 连接 EditorPanel 和 PreviewPanel
    - 连接文件操作和数据模型
    - 确保数据流正确
    - _Requirements: 全部集成_

- [x] 12. Final Checkpoint - 完整功能验证
  - 确保所有测试通过
  - 手动测试完整工作流程
  - 如有问题请询问用户

- [-] 13. 模板功能实现
  - [x] 13.1 创建模板数据模型 (template.py)
    - 实现 NfoTemplate 数据类
    - 支持所有可模板化的 NFO 字段
    - 实现 to_dict() 和 from_dict() 方法
    - _Requirements: 7.1, 7.2_

  - [x] 13.2 实现模板文件读写 (template_io.py)
    - 实现 save_template() 保存模板到 JSON
    - 实现 load_template() 从 JSON 加载模板
    - 实现 list_templates() 列出所有模板
    - _Requirements: 7.5_

  - [x] 13.3 编写属性测试: 模板序列化往返
    - **Property 9: 模板序列化往返一致性**
    - **Validates: Requirements 7.5**

  - [x] 13.4 实现模板应用逻辑
    - 实现 apply_template() 应用模板到 NfoData
    - 支持 "fill empty only" 模式（只填充空字段）
    - 支持 "overwrite" 模式（覆盖所有字段）
    - _Requirements: 7.3, 7.4_

  - [x] 13.5 编写属性测试: 模板填充空字段
    - **Property 10: 模板填充空字段不覆盖已有值**
    - **Validates: Requirements 7.3**

  - [x] 13.6 实现模板管理界面 (template_manager.py)
    - 创建模板列表视图
    - 支持创建、编辑、删除模板
    - 支持导入/导出模板文件
    - _Requirements: 7.8_

- [-] 14. 批量编辑功能实现
  - [x] 14.1 实现批量操作控制器 (batch_controller.py)
    - 实现文件批量加载
    - 实现批量字段修改（覆盖/追加模式）
    - 实现批量保存
    - _Requirements: 6.1, 6.4, 6.5_

  - [x] 14.2 编写属性测试: 批量追加模式
    - **Property 12: 批量追加模式保留原有值**
    - **Validates: Requirements 6.5**

  - [x] 14.3 实现批量编辑界面 (batch_editor.py)
    - 创建文件选择列表
    - 创建字段选择器
    - 创建值编辑器（支持覆盖/追加模式）
    - 显示进度条
    - _Requirements: 6.2, 6.3, 6.7_

  - [x] 14.4 实现变更预览功能
    - 显示将要修改的文件和字段
    - 显示修改前后的值对比
    - _Requirements: 6.6_

  - [x] 14.5 实现批量应用模板
    - 支持选择模板应用到多个文件
    - 支持 "fill empty only" 和 "overwrite" 模式
    - _Requirements: 7.6, 7.7_

  - [x] 14.6 实现错误处理和报告
    - 单个文件失败不影响其他文件
    - 完成后显示成功/失败统计
    - 显示失败文件列表和错误原因
    - _Requirements: 6.8_

  - [x] 14.7 编写属性测试: 批量操作原子性
    - **Property 11: 批量操作原子性**
    - **Validates: Requirements 6.8**

- [x] 15. Checkpoint - 批量功能验证
  - 确保所有批量编辑和模板测试通过
  - 如有问题请询问用户

- [x] 16. 主窗口集成批量功能
  - [x] 16.1 添加批量编辑菜单项
    - 在文件菜单添加"批量编辑..."选项
    - 添加快捷键 Ctrl+B
    - _Requirements: 6.1_

  - [x] 16.2 添加模板管理菜单项
    - 在编辑菜单添加"模板管理..."选项
    - 添加"应用模板"子菜单
    - _Requirements: 7.8_

- [x] 17. Final Checkpoint - 完整功能验证（含批量功能）
  - 确保所有测试通过
  - 手动测试批量编辑工作流程
  - 手动测试模板功能工作流程
  - 如有问题请询问用户

## Notes

- 所有任务都是必做的，包括测试任务
- 每个任务都引用了具体的需求条款以便追溯
- Checkpoint 任务用于阶段性验证
- 属性测试验证核心正确性属性
- 单元测试验证具体示例和边界情况
- 任务 13-16 为新增的批量编辑和模板功能
