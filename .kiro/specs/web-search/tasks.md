# Implementation Plan: Web Search Feature

## Overview

为 NFO 编辑器网页端实现搜索功能，包括后端搜索 API 和前端搜索界面。

## Tasks

- [x] 1. 实现后端搜索 API
  - [x] 1.1 添加搜索请求和响应模型
    - 在 `web/app.py` 中添加 `SearchRequest` 和 `SearchResultItem` Pydantic 模型
    - _Requirements: 2.1, 3.1_

  - [x] 1.2 实现搜索核心逻辑
    - 实现递归目录扫描函数
    - 实现文件名匹配逻辑（大小写不敏感）
    - 实现 NFO 内容匹配逻辑（title, originaltitle, actors, plot）
    - 实现结果去重和数量限制
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 6.1, 6.2_

  - [x] 1.3 添加 /api/search 端点
    - 创建 POST `/api/search` 端点
    - 处理搜索请求并返回结果
    - 处理错误情况（目录不存在、无权限等）
    - _Requirements: 2.3, 2.4, 6.3_

  - [x] 1.4 编写搜索 API 单元测试
    - 测试文件名匹配
    - 测试内容匹配
    - 测试边界条件
    - _Requirements: 2.1, 3.1_

  - [x] 1.5 编写属性测试 - 文件名匹配正确性
    - **Property 1: 文件名匹配正确性**
    - **Validates: Requirements 2.1**

  - [x] 1.6 编写属性测试 - 结果数量限制
    - **Property 5: 结果数量限制**
    - **Validates: Requirements 6.2**

- [x] 2. 实现前端搜索界面
  - [x] 2.1 添加搜索栏 HTML 和样式
    - 在文件浏览面板添加搜索输入框和按钮
    - 添加搜索结果显示区域
    - 添加相关 CSS 样式
    - _Requirements: 1.1, 1.2_

  - [x] 2.2 实现搜索 JavaScript 功能
    - 实现 `search()` 函数调用后端 API
    - 实现 `renderSearchResults()` 显示搜索结果
    - 实现搜索结果点击处理（加载文件、导航目录）
    - 实现清除搜索功能
    - _Requirements: 1.3, 1.4, 4.1, 4.2, 5.1, 5.2, 5.3_

- [x] 3. Checkpoint - 确保所有测试通过
  - 运行所有测试，确保功能正常
  - 如有问题请询问用户

## Notes

- 每个任务都引用了具体的需求条款以便追溯
- 属性测试验证核心正确性属性
- 单元测试覆盖边界条件和错误处理
