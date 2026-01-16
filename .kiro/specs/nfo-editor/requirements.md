# Requirements Document

## Introduction

一个可视化的 NFO 文件编辑器，用于读取、编辑和预览本地 NFO 文件。NFO 文件是基于 XML 格式的媒体信息文件，常用于 Kodi、Jellyfin 等媒体中心软件。该编辑器提供友好的图形界面，让用户可以方便地查看和修改 NFO 文件中的各种标签信息。

## Glossary

- **NFO_File**: 基于 XML 格式的媒体信息文件，包含电影、电视剧等媒体的元数据
- **Editor**: NFO 文件编辑器应用程序
- **Tag**: NFO 文件中的 XML 标签元素，如 title、year、plot 等
- **Preview_Panel**: 显示 NFO 文件内容预览的界面区域
- **File_Browser**: 用于浏览和选择本地 NFO 文件的组件
- **Batch_Editor**: 批量编辑多个 NFO 文件的功能模块
- **Template**: 预定义的 NFO 字段值集合，用于批量填充缺失信息

## Requirements

### Requirement 1: 文件操作

**User Story:** As a user, I want to open and save NFO files, so that I can edit local media information files.

#### Acceptance Criteria

1. WHEN a user clicks the open button or uses keyboard shortcut, THE Editor SHALL display a file browser dialog filtered to show NFO files
2. WHEN a user selects a valid NFO file, THE Editor SHALL parse the XML content and display all tags in the editing interface
3. WHEN a user attempts to open an invalid or corrupted NFO file, THE Editor SHALL display a clear error message and maintain the current state
4. WHEN a user clicks the save button, THE Editor SHALL write the modified content back to the original file preserving XML formatting
5. WHEN a user clicks save as, THE Editor SHALL allow saving to a new file location
6. THE Editor SHALL support drag and drop of NFO files into the application window

### Requirement 2: 标签编辑

**User Story:** As a user, I want to view and edit NFO tags, so that I can modify media metadata easily.

#### Acceptance Criteria

1. THE Editor SHALL display all NFO tags in a structured, readable format
2. WHEN a user modifies a tag value, THE Editor SHALL update the internal data model immediately
3. THE Editor SHALL support editing common NFO tags including: title, originaltitle, year, plot, runtime, genre, director, actor, studio, rating
4. WHEN editing actor tags, THE Editor SHALL support multiple actors with name, role, and thumb fields
5. WHEN editing genre tags, THE Editor SHALL support multiple genres
6. THE Editor SHALL validate tag values and display warnings for invalid data formats
7. WHEN a user adds a new tag, THE Editor SHALL insert it into the appropriate position in the XML structure

### Requirement 3: 预览功能

**User Story:** As a user, I want to preview the NFO content, so that I can see how the metadata will appear.

#### Acceptance Criteria

1. THE Preview_Panel SHALL display a formatted view of the NFO content
2. WHEN the user modifies any tag, THE Preview_Panel SHALL update in real-time to reflect changes
3. THE Preview_Panel SHALL display poster and fanart images if the paths are specified in the NFO file and images exist locally
4. THE Preview_Panel SHALL format the plot text with proper line breaks and spacing
5. WHEN image paths are invalid or images don't exist, THE Preview_Panel SHALL display a placeholder image

### Requirement 4: 用户界面

**User Story:** As a user, I want a clean and intuitive interface, so that I can efficiently edit NFO files.

#### Acceptance Criteria

1. THE Editor SHALL provide a split-view layout with editing panel on one side and preview on the other
2. THE Editor SHALL support keyboard shortcuts for common operations (Ctrl+O open, Ctrl+S save, Ctrl+Z undo)
3. THE Editor SHALL indicate unsaved changes with a visual marker in the title bar
4. WHEN the user attempts to close with unsaved changes, THE Editor SHALL prompt for confirmation
5. THE Editor SHALL remember the last opened directory for file operations
6. THE Editor SHALL support both light and dark themes

### Requirement 5: NFO 格式支持

**User Story:** As a user, I want support for different NFO formats, so that I can edit files from various media sources.

#### Acceptance Criteria

1. THE Editor SHALL support movie NFO format (movie.nfo structure)
2. THE Editor SHALL support TV show NFO format (tvshow.nfo structure)
3. THE Editor SHALL support episode NFO format (episode.nfo structure)
4. WHEN opening an NFO file, THE Editor SHALL auto-detect the NFO type and adjust the editing interface accordingly
5. THE Editor SHALL preserve unknown tags and attributes when saving, ensuring no data loss


### Requirement 6: 批量编辑

**User Story:** As a user, I want to batch edit multiple NFO files, so that I can efficiently update common fields across many files at once.

#### Acceptance Criteria

1. THE Batch_Editor SHALL allow selecting multiple NFO files from a directory or via multi-select dialog
2. WHEN multiple files are selected, THE Batch_Editor SHALL display a list of selected files with their current field values
3. THE Batch_Editor SHALL provide a field selector to choose which fields to modify (studio, genre, director, etc.)
4. WHEN a user specifies a new value for a field, THE Batch_Editor SHALL apply the change to all selected files
5. THE Batch_Editor SHALL support two modification modes: "overwrite" (replace existing value) and "append" (add to existing values for multi-value fields like genre)
6. WHEN applying batch changes, THE Batch_Editor SHALL display a preview of changes before committing
7. THE Batch_Editor SHALL provide a progress indicator during batch operations
8. IF any file fails to update during batch operation, THE Batch_Editor SHALL continue with remaining files and report errors at completion

### Requirement 7: 模板功能

**User Story:** As a user, I want to use templates to fill in missing NFO information, so that I can quickly populate empty fields with predefined values.

#### Acceptance Criteria

1. THE Editor SHALL allow creating and saving templates with predefined field values
2. THE Template SHALL support all common NFO fields (studio, genre, director, rating, etc.)
3. WHEN applying a template, THE Editor SHALL only fill in fields that are currently empty in the target NFO file
4. THE Editor SHALL provide an option to force-apply template values even to non-empty fields
5. THE Template SHALL be saveable to and loadable from JSON files for sharing and backup
6. THE Batch_Editor SHALL support applying templates to multiple selected files
7. WHEN applying a template to multiple files, THE Batch_Editor SHALL respect the "fill empty only" or "overwrite" mode setting
8. THE Editor SHALL provide a template management interface to create, edit, delete, and organize templates
