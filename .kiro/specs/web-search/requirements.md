# Requirements Document

## Introduction

为 NFO 编辑器网页端添加搜索功能，允许用户在当前目录及子目录中搜索 NFO 文件，支持按文件名和 NFO 内容（如标题、演员等）进行搜索。

## Glossary

- **Search_System**: 负责处理搜索请求并返回匹配结果的系统组件
- **NFO_File**: 包含媒体元数据的 XML 格式文件，扩展名为 .nfo
- **Search_Query**: 用户输入的搜索关键词
- **Search_Result**: 匹配搜索条件的 NFO 文件列表

## Requirements

### Requirement 1: 搜索界面

**User Story:** 作为用户，我想要一个搜索输入框，以便快速查找 NFO 文件。

#### Acceptance Criteria

1. THE Search_System SHALL display a search input field in the file browser panel
2. WHEN a user types in the search field, THE Search_System SHALL show a search button to trigger the search
3. WHEN a user presses Enter in the search field, THE Search_System SHALL trigger the search operation
4. WHEN a search is in progress, THE Search_System SHALL display a loading indicator

### Requirement 2: 文件名搜索

**User Story:** 作为用户，我想要按文件名搜索 NFO 文件，以便快速定位特定文件。

#### Acceptance Criteria

1. WHEN a user submits a search query, THE Search_System SHALL search for NFO files whose filename contains the query string (case-insensitive)
2. THE Search_System SHALL search recursively in the current directory and all subdirectories
3. WHEN search results are found, THE Search_System SHALL display the matching files with their full paths
4. WHEN no results are found, THE Search_System SHALL display a "no results" message

### Requirement 3: 内容搜索

**User Story:** 作为用户，我想要按 NFO 文件内容搜索，以便通过标题、演员等信息查找文件。

#### Acceptance Criteria

1. WHEN a user submits a search query, THE Search_System SHALL search within NFO file content including title, originaltitle, actors, and plot fields
2. THE Search_System SHALL perform case-insensitive content matching
3. WHEN content matches are found, THE Search_System SHALL indicate which field matched in the results

### Requirement 4: 搜索结果交互

**User Story:** 作为用户，我想要点击搜索结果直接打开对应的 NFO 文件进行编辑。

#### Acceptance Criteria

1. WHEN a user clicks on a search result, THE Search_System SHALL load the selected NFO file into the editor
2. WHEN a user clicks on a search result, THE Search_System SHALL navigate the file browser to the file's parent directory
3. THE Search_System SHALL highlight the currently selected file in the search results

### Requirement 5: 搜索状态管理

**User Story:** 作为用户，我想要能够清除搜索结果并返回正常的文件浏览模式。

#### Acceptance Criteria

1. WHEN search results are displayed, THE Search_System SHALL show a clear/close button
2. WHEN a user clicks the clear button, THE Search_System SHALL hide search results and restore normal file browsing
3. WHEN a user clears the search input and presses Enter, THE Search_System SHALL clear search results

### Requirement 6: 搜索性能

**User Story:** 作为用户，我想要搜索操作快速响应，不会因为文件数量多而卡顿。

#### Acceptance Criteria

1. THE Search_System SHALL limit recursive search depth to prevent excessive scanning
2. THE Search_System SHALL limit the maximum number of results returned
3. IF the search exceeds limits, THEN THE Search_System SHALL inform the user that results may be incomplete
