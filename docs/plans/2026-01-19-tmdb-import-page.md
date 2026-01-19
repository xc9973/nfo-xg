# TMDB 专用导入页实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 新建专用 TMDB 导入页面，采用分步式流程（选类型→输ID→选季集→确认），替代现有的混合搜索逻辑。

**Architecture:** 前端分步表单 + 后端 API 验证 + Flask Session 存储中间状态。复用现有 `tmdb_client` 和 `tmdb_to_nfo` 映射器。

**Tech Stack:** Flask, Jinja2, Vanilla JS, TMDB API (tmdb_search 包)

---

## Task 1: 创建导入页面路由

**Files:**
- Modify: `web/app.py` (after line 100, in main routes section)

**Step 1: 添加导入页面路由**

在 `web/app.py` 的 `@app.route("/login")` 之前添加：

```python
@app.route("/import", methods=["GET"])
def import_page():
    """TMDB 导入页面."""
    if not check_auth():
        return redirect(url_for("login"))
    return render_template("import.html")
```

**Step 2: 启动开发服务器验证路由**

Run: `cd /Volumes/1disk/项目/nfo-xg && python -m flask --app web.app run --debug`
Expected: 服务器启动，访问 `/import` 会报错模板不存在（下一步创建）

**Step 3: Commit**

```bash
git add web/app.py
git commit -m "feat: add import page route"
```

---

## Task 2: 创建导入页面模板（静态HTML）

**Files:**
- Create: `web/templates/import.html`

**Step 1: 创建基础模板**

创建 `web/templates/import.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TMDB 导入 - NFO 编辑器</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/import.css') }}">
</head>
<body>
    <div class="import-container">
        <div class="import-card">
            <h1>TMDB 导入</h1>

            <!-- 进度条 -->
            <div class="progress-bar">
                <div class="step active" data-step="1">1.选择类型</div>
                <div class="step" data-step="2">2.输入ID</div>
                <div class="step" data-step="3">3.选季集</div>
                <div class="step" data-step="4">4.确认</div>
            </div>

            <!-- 步骤 1: 选择类型 -->
            <div class="step-content active" id="step1">
                <h2>选择媒体类型</h2>
                <div class="type-buttons">
                    <button class="type-btn" data-type="movie">
                        <span class="icon">🎬</span>
                        <span class="label">电影</span>
                    </button>
                    <button class="type-btn" data-type="tv">
                        <span class="icon">📺</span>
                        <span class="label">电视剧</span>
                    </button>
                </div>
            </div>

            <!-- 步骤 2: 输入 TMDB ID -->
            <div class="step-content" id="step2">
                <h2>输入 TMDB ID</h2>
                <div class="input-group">
                    <input type="number" id="tmdbIdInput" placeholder="例如: 12345" min="1">
                    <button id="validateBtn">验证</button>
                </div>
                <div id="validateResult"></div>
                <button id="step2Back" class="btn-secondary">返回</button>
            </div>

            <!-- 步骤 3: 选择季集（仅电视剧） -->
            <div class="step-content" id="step3">
                <h2>选择季集</h2>
                <div class="season-options">
                    <label>
                        <input type="radio" name="importType" value="season" checked>
                        导入整季信息
                    </label>
                    <label>
                        <input type="radio" name="importType" value="episode">
                        导入单集
                    </label>
                </div>
                <div id="seasonList" class="season-list"></div>
                <div id="episodeInputs" class="episode-inputs" style="display:none;">
                    <label>季数: <input type="number" id="seasonNum" min="1"></label>
                    <label>集数: <input type="number" id="episodeNum" min="1"></label>
                </div>
                <button id="step3Next" class="btn-primary">下一步</button>
                <button id="step3Back" class="btn-secondary">返回</button>
            </div>

            <!-- 步骤 4: 确认导入 -->
            <div class="step-content" id="step4">
                <h2>确认导入</h2>
                <div id="importSummary"></div>
                <button id="confirmImport" class="btn-primary">确认导入</button>
                <button id="step4Back" class="btn-secondary">返回</button>
            </div>
        </div>
    </div>

    <script src="{{ url_for('static', filename='js/import.js') }}"></script>
</body>
</html>
```

**Step 2: 启动服务器验证页面渲染**

Run: `python -m flask --app web.app run --debug`
访问: `http://localhost:5000/import`
Expected: 显示分步表单，但样式缺失（下一步添加 CSS）

**Step 3: Commit**

```bash
git add web/templates/import.html
git commit -m "feat: add import page template"
```

---

## Task 3: 添加导入页面样式

**Files:**
- Create: `web/static/css/import.css`

**Step 1: 创建 CSS 文件**

创建 `web/static/css/import.css`：

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.import-container {
    width: 100%;
    max-width: 600px;
}

.import-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.import-card h1 {
    text-align: center;
    margin-bottom: 24px;
    color: #1a1a2e;
}

.progress-bar {
    display: flex;
    justify-content: space-between;
    margin-bottom: 32px;
    position: relative;
}

.progress-bar::before {
    content: '';
    position: absolute;
    top: 16px;
    left: 0;
    right: 0;
    height: 2px;
    background: #e0e0e0;
    z-index: 0;
}

.step {
    position: relative;
    z-index: 1;
    padding: 8px 16px;
    background: #f0f0f0;
    border-radius: 20px;
    font-size: 12px;
    color: #666;
    transition: all 0.3s;
}

.step.active {
    background: #4f46e5;
    color: white;
}

.step.completed {
    background: #10b981;
    color: white;
}

.step-content {
    display: none;
}

.step-content.active {
    display: block;
}

.step-content h2 {
    margin-bottom: 20px;
    color: #1a1a2e;
}

.type-buttons {
    display: flex;
    gap: 16px;
}

.type-btn {
    flex: 1;
    padding: 32px;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    background: white;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
}

.type-btn:hover {
    border-color: #4f46e5;
    background: #f8f8ff;
}

.type-btn .icon {
    font-size: 48px;
}

.type-btn .label {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a2e;
}

.input-group {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
}

.input-group input {
    flex: 1;
    padding: 12px 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
}

.input-group button {
    padding: 12px 24px;
    background: #4f46e5;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
}

.btn-primary, .btn-secondary {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    margin-right: 12px;
}

.btn-primary {
    background: #4f46e5;
    color: white;
}

.btn-secondary {
    background: #e0e0e0;
    color: #1a1a2e;
}

.season-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
    margin: 20px 0;
}

.season-item {
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
}

.season-item:hover, .season-item.selected {
    border-color: #4f46e5;
    background: #f8f8ff;
}

.preview-card {
    display: flex;
    gap: 16px;
    padding: 16px;
    background: #f8f8ff;
    border-radius: 12px;
    margin-top: 16px;
}

.preview-card img {
    width: 80px;
    height: 120px;
    object-fit: cover;
    border-radius: 8px;
}

.preview-info h3 {
    margin-bottom: 8px;
    color: #1a1a2e;
}

.preview-info p {
    color: #666;
    margin: 4px 0;
}

.error {
    color: #ef4444;
    padding: 12px;
    background: #fef2f2;
    border-radius: 8px;
    margin-top: 16px;
}

.loading {
    text-align: center;
    color: #666;
    padding: 20px;
}
```

**Step 2: 刷新浏览器验证样式**

访问: `http://localhost:5000/import`
Expected: 页面有完整样式，显示步骤1的类型选择按钮

**Step 3: Commit**

```bash
git add web/static/css/import.css
git commit -m "feat: add import page styles"
```

---

## Task 4: 添加 API 端点 - 验证 TMDB ID

**Files:**
- Modify: `web/app.py` (after line 551, in TMDB Search API section)

**Step 1: 添加验证 API**

在 `web/app.py` 的 `tmdb_search` 函数后添加：

```python
@app.route("/api/tmdb/validate", methods=["POST"])
def tmdb_validate():
    """验证 TMDB ID 并返回预览信息."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.get_json()
        tmdb_id = data.get("tmdb_id")
        media_type = data.get("media_type")  # "movie" or "tv"

        if not tmdb_id or not media_type:
            return jsonify({"error": "缺少参数"}), 400

        if not isinstance(tmdb_id, int) or tmdb_id <= 0:
            return jsonify({"error": "无效的 TMDB ID"}), 400

        # 获取详情用于预览
        if media_type == "movie":
            details = tmdb_client.get_movie_details(tmdb_id)
            title = details.get("title", "")
            year = details.get("release_date", "")[:4]
            poster_path = details.get("poster_path")
        else:  # tv
            details = tmdb_client.get_tv_details(tmdb_id)
            title = details.get("name", "")
            year = details.get("first_air_date", "")[:4]
            poster_path = details.get("poster_path")

        poster = tmdb_client.get_image_url(poster_path, "w200")

        return jsonify({
            "valid": True,
            "title": title,
            "year": year,
            "poster": poster,
            "tmdb_id": tmdb_id,
            "media_type": media_type
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"TMDB validate failed: {e}")
        return jsonify({"error": "验证失败"}), 500
```

**Step 2: 测试 API（手动验证）**

使用 curl 或 Postman 测试：

```bash
curl -X POST http://localhost:5000/api/tmdb/validate \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"tmdb_id": 299534, "media_type": "movie"}'
```

Expected: 返回 `{"valid": true, "title": "Avengers: Endgame", ...}`

**Step 3: Commit**

```bash
git add web/app.py
git commit -m "feat: add TMDB ID validation API"
```

---

## Task 5: 添加 API 端点 - 获取季列表

**Files:**
- Modify: `web/app.py` (after existing get_tv_details function)

**Step 1: 修改现有 get_tv_details 返回更多信息**

现有函数（约 614 行）已经返回季列表，但我们需要确保它包含完整信息。验证现有实现已满足需求：

```python
@app.route("/api/tmdb/tv/<int:tmdb_id>", methods=["GET"])
def get_tv_details(tmdb_id: int):
    """Get TV show details with seasons list."""
    # 现有实现已返回 seasons，无需修改
```

**Step 2: 验证现有 API 可用**

```bash
curl http://localhost:5000/api/tmdb/tv/1668 -H "Cookie: session=..."
```

Expected: 返回包含 `seasons` 数组的 JSON

**Step 3: 无需 commit（现有代码已满足需求）**

---

## Task 6: 添加 API 端点 - 最终导入

**Files:**
- Modify: `web/app.py` (after batch_import_episodes function)

**Step 1: 添加最终导入 API**

在 `web/app.py` 的 `batch_import_episodes` 函数后添加：

```python
@app.route("/api/tmdb/import/final", methods=["POST"])
def tmdb_import_final():
    """最终导入：存储到 session 并跳转到编辑页."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.get_json()
        tmdb_id = data.get("tmdb_id")
        media_type = data.get("media_type")  # "movie", "tv", "episode"
        season = data.get("season")
        episode = data.get("episode")

        if not tmdb_id or not media_type:
            return jsonify({"error": "缺少参数"}), 400

        # 获取 NFO 数据
        if media_type == "movie":
            details = tmdb_client.get_movie_details(tmdb_id)
            nfo_data = tmdb_to_nfo(details, "movie")
        elif media_type == "tv":
            details = tmdb_client.get_tv_details(tmdb_id)
            nfo_data = tmdb_to_nfo(details, "tv")
        elif media_type == "episode":
            if not season or not episode:
                return jsonify({"error": "缺少季数或集数"}), 400
            details = tmdb_client.get_tv_episode_details(tmdb_id, season, episode)
            from tmdb_search.models import TMDBEpisodeData
            mapper = TMDBMapper(tmdb_client)
            episode_data = mapper.map_episode(details)
            nfo_data = NfoData(
                nfo_type=NfoType.EPISODE,
                title=episode_data.title,
                originaltitle=episode_data.original_title,
                year=episode_data.year,
                plot=episode_data.plot,
                runtime=episode_data.runtime,
                genres=episode_data.genres,
                directors=episode_data.directors,
                actors=[Actor(**a.__dict__) for a in episode_data.actors],
                studio=episode_data.studio,
                rating=episode_data.rating,
                poster=episode_data.poster,
                fanart=episode_data.fanart,
                season=episode_data.season,
                episode=episode_data.episode,
                aired=episode_data.aired,
            )
        else:
            return jsonify({"error": "无效的媒体类型"}), 400

        # 存储到 session，生成新文件 ID
        session_files = session.get("files", {})
        file_id = str(uuid.uuid4())

        # 确定文件名
        if media_type == "movie":
            filename = secure_filename(f"{nfo_data.title or 'movie'}.nfo")
        elif media_type == "tv":
            filename = secure_filename("tvshow.nfo")
        else:  # episode
            filename = secure_filename(f"{nfo_data.title or 'episode'}.S{nfo_data.season}E{nfo_data.episode}.nfo")

        session_files[file_id] = {
            "name": filename,
            "original_data": nfo_data,
            "edited_data": None,
            "modified_fields": [],
            "upload_time": datetime.now().isoformat(),
        }
        session["files"] = session_files

        return jsonify({
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "redirect": f"/edit?file_id={file_id}"
        })

    except Exception as e:
        logger.error(f"Final import failed: {e}")
        return jsonify({"error": str(e)}), 500
```

**Step 2: 测试导入 API**

```bash
curl -X POST http://localhost:5000/api/tmdb/import/final \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"tmdb_id": 299534, "media_type": "movie"}'
```

Expected: 返回 `{"success": true, "file_id": "...", "redirect": "/edit?file_id=..."}`

**Step 3: Commit**

```bash
git add web/app.py
git commit -m "feat: add final import API"
```

---

## Task 7: 实现前端交互逻辑

**Files:**
- Create: `web/static/js/import.js`

**Step 1: 创建 JS 文件**

创建 `web/static/js/import.js`：

```javascript
// 状态管理
const state = {
    step: 1,
    mediaType: null,
    tmdbId: null,
    previewData: null,
    seasons: [],
    selectedSeason: null,
    importType: 'season',  // 'season' or 'episode'
    seasonNum: null,
    episodeNum: null
};

// 工具函数
function $(selector) { return document.querySelector(selector); }
function $$(selector) { return document.querySelectorAll(selector); }

// 更新步骤显示
function updateStep() {
    $$('.step').forEach((el, i) => {
        el.classList.remove('active', 'completed');
        if (i + 1 < state.step) el.classList.add('completed');
        if (i + 1 === state.step) el.classList.add('active');
    });

    $$('.step-content').forEach(el => el.classList.remove('active'));
    $(`#step${state.step}`).classList.add('active');
}

// 步骤 1: 类型选择
$$('.type-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        state.mediaType = btn.dataset.type;
        state.step = 2;
        updateStep();

        // 如果是电影，跳过季集步骤
        if (state.mediaType === 'movie') {
            $$('.step').forEach(el => {
                if (el.dataset.step === '3') el.style.display = 'none';
            });
        } else {
            $$('.step').forEach(el => {
                if (el.dataset.step === '3') el.style.display = 'block';
            });
        }
    });
});

// 步骤 2: 验证 TMDB ID
$('#validateBtn').addEventListener('click', validateTmdbId);
$('#tmdbIdInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') validateTmdbId();
});

async function validateTmdbId() {
    const tmdbId = parseInt($('#tmdbIdInput').value);
    if (!tmdbId || tmdbId <= 0) {
        showError('请输入有效的 TMDB ID');
        return;
    }

    $('#validateResult').innerHTML = '<div class="loading">验证中...</div>';

    try {
        const response = await fetch('/api/tmdb/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tmdb_id: tmdbId, media_type: state.mediaType })
        });

        const data = await response.json();

        if (data.valid) {
            state.tmdbId = tmdbId;
            state.previewData = data;

            $('#validateResult').innerHTML = `
                <div class="preview-card">
                    <img src="${data.poster}" alt="海报" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 80 120%22><rect fill=%22%23ccc%22 width=%2280%22 height=%22120%22/></svg>'">
                    <div class="preview-info">
                        <h3>${data.title}</h3>
                        <p>年份: ${data.year}</p>
                        <p>TMDB ID: ${data.tmdb_id}</p>
                    </div>
                </div>
            `;

            // 如果是电视剧，加载季列表
            if (state.mediaType === 'tv') {
                await loadSeasons();
            }
        } else {
            showError(data.error || '验证失败');
        }
    } catch (error) {
        showError('网络错误，请重试');
    }
}

async function loadSeasons() {
    try {
        const response = await fetch(`/api/tmdb/tv/${state.tmdbId}`);
        const data = await response.json();
        state.seasons = data.seasons;

        $('#seasonList').innerHTML = data.seasons.map(s => `
            <div class="season-item" data-season="${s.season_number}">
                <strong>第 ${s.season_number} 季</strong><br>
                <small>${s.episode_count} 集</small>
            </div>
        `).join('');

        // 季选择事件
        $$('.season-item').forEach(item => {
            item.addEventListener('click', () => {
                $$('.season-item').forEach(el => el.classList.remove('selected'));
                item.classList.add('selected');
                state.selectedSeason = parseInt(item.dataset.season);
            });
        });
    } catch (error) {
        showError('加载季列表失败');
    }
}

function showError(message) {
    $('#validateResult').innerHTML = `<div class="error">${message}</div>`;
}

// 步骤 2 返回按钮
$('#step2Back').addEventListener('click', () => {
    state.step = 1;
    state.mediaType = null;
    state.tmdbId = null;
    state.previewData = null;
    $('#tmdbIdInput').value = '';
    $('#validateResult').innerHTML = '';
    updateStep();
});

// 步骤 3: 季集选择
$$('input[name="importType"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        state.importType = e.target.value;
        if (state.importType === 'season') {
            $('#seasonList').style.display = 'grid';
            $('#episodeInputs').style.display = 'none';
        } else {
            $('#seasonList').style.display = 'none';
            $('#episodeInputs').style.display = 'block';
        }
    });
});

$('#step3Next').addEventListener('click', () => {
    if (state.importType === 'season') {
        if (!state.selectedSeason) {
            alert('请选择季度');
            return;
        }
    } else {
        state.seasonNum = parseInt($('#seasonNum').value);
        state.episodeNum = parseInt($('#episodeNum').value);
        if (!state.seasonNum || !state.episodeNum) {
            alert('请输入季数和集数');
            return;
        }
    }

    // 生成摘要
    let summary = `
        <div class="preview-card">
            <img src="${state.previewData.poster}" alt="海报">
            <div class="preview-info">
                <h3>${state.previewData.title}</h3>
                <p>年份: ${state.previewData.year}</p>
                <p>TMDB ID: ${state.previewData.tmdb_id}</p>
    `;

    if (state.mediaType === 'tv') {
        if (state.importType === 'season') {
            summary += `<p>导入: 第 ${state.selectedSeason} 季</p>`;
        } else {
            summary += `<p>导入: S${state.seasonNum}E${state.episodeNum}</p>`;
        }
    }

    summary += '</div></div>';
    $('#importSummary').innerHTML = summary;

    state.step = 4;
    updateStep();
});

$('#step3Back').addEventListener('click', () => {
    state.step = 2;
    updateStep();
});

// 步骤 4: 确认导入
$('#confirmImport').addEventListener('click', async () => {
    try {
        const payload = {
            tmdb_id: state.tmdbId,
            media_type: state.mediaType
        };

        if (state.mediaType === 'tv') {
            if (state.importType === 'episode') {
                payload.media_type = 'episode';
                payload.season = state.seasonNum;
                payload.episode = state.episodeNum;
            }
            // tv 类型直接用 tv（整季信息）
        }

        const response = await fetch('/api/tmdb/import/final', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.success) {
            window.location.href = data.redirect;
        } else {
            showError(data.error || '导入失败');
        }
    } catch (error) {
        showError('网络错误，请重试');
    }
});

$('#step4Back').addEventListener('click', () => {
    state.step = state.mediaType === 'tv' ? 3 : 2;
    updateStep();
});
```

**Step 2: 刷新浏览器测试交互**

访问: `http://localhost:5000/import`
测试流程:
1. 点击"电影" → 输入 TMDB ID (如 299534) → 验证 → 确认导入
2. 点击"电视剧" → 输入 TMDB ID (如 1668) → 验证 → 选择季 → 确认导入

Expected: 完整流程可用，最终跳转到编辑页面

**Step 3: Commit**

```bash
git add web/static/js/import.js
git commit -m "feat: add import page interaction logic"
```

---

## Task 8: 在导航中添加导入入口

**Files:**
- Modify: `web/templates/edit.html` 和 `web/templates/files.html`

**Step 1: 在 edit.html 添加导入链接**

在 `web/templates/edit.html` 的导航区域添加：

找到 `<nav>` 或顶部导航部分，添加：

```html
<a href="{{ url_for('import_page') }}" class="nav-link">TMDB 导入</a>
```

**Step 2: 在 files.html 添加导入链接**

同样在 `web/templates/files.html` 的导航区域添加相同链接

**Step 3: 刷新页面验证链接**

访问编辑页面或文件列表页面，点击导航中的"TMDB 导入"链接

Expected: 跳转到 `/import` 页面

**Step 4: Commit**

```bash
git add web/templates/edit.html web/templates/files.html
git commit -m "feat: add import link to navigation"
```

---

## Task 9: 手动测试完整流程

**Files:** 无修改

**Step 1: 启动开发服务器**

```bash
cd /Volumes/1disk/项目/nfo-xg
python -m flask --app web.app run --debug
```

**Step 2: 测试电影导入流程**

1. 访问 `http://localhost:5000/import`
2. 点击"🎬 电影"
3. 输入 TMDB ID: `299534` (Avengers: Endgame)
4. 点击"验证"
5. 验证海报、标题、年份显示正确
6. 点击"下一步"（或确认按钮）
7. 确认导入信息
8. 点击"确认导入"
9. 验证跳转到编辑页面且数据已填充

**Step 3: 测试电视剧整季导入流程**

1. 访问 `http://localhost:5000/import`
2. 点击"📺 电视剧"
3. 导入 TMDB ID: `1668` (Game of Thrones)
4. 点击"验证"
5. 验证季列表显示
6. 选择"第 1 季"
7. 选择"导入整季信息"
8. 点击"下一步"
9. 确认导入
10. 验证跳转到编辑页面

**Step 4: 测试电视剧单集导入流程**

1. 重复步骤 3 的 1-5
2. 选择"导入单集"
3. 输入季数: `1`，集数: `1`
4. 点击"下一步"
5. 确认导入
6. 验证跳转到编辑页面，显示单集信息

**Step 5: 测试错误处理**

1. 输入无效 TMDB ID (如 `999999999`)
2. 验证显示错误提示
3. 输入负数或 0
4. 验证显示"无效的 TMDB ID"

**Step 6: 无需 commit（测试任务）**

---

## Task 10: 添加输入验证和安全增强

**Files:**
- Modify: `web/app.py` (tmdb_validate 和 tmdb_import_final 函数)

**Step 1: 增强 validate API 的输入验证**

修改 `tmdb_validate` 函数中的验证逻辑：

```python
# 现有代码
if not isinstance(tmdb_id, int) or tmdb_id <= 0:
    return jsonify({"error": "无效的 TMDB ID"}), 400

# 添加范围检查
if tmdb_id > 10000000:  # TMDB ID 一般不会超过 1000 万
    return jsonify({"error": "TMDB ID 超出范围"}), 400

# 验证 media_type
if media_type not in ["movie", "tv"]:
    return jsonify({"error": "无效的媒体类型"}), 400
```

**Step 2: 增强 import_final API 的输入验证**

修改 `tmdb_import_final` 函数：

```python
# 在现有验证后添加
if media_type not in ["movie", "tv", "episode"]:
    return jsonify({"error": "无效的媒体类型"}), 400

if media_type == "episode":
    if not season or not episode:
        return jsonify({"error": "缺少季数或集数"}), 400
    if season <= 0 or episode <= 0:
        return jsonify({"error": "季数和集数必须大于 0"}), 400
    if season > 100 or episode > 200:  # 合理上限
        return jsonify({"error": "季数或集数超出范围"}), 400
```

**Step 3: 测试边界情况**

```bash
# 测试超大 ID
curl -X POST http://localhost:5000/api/tmdb/validate \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"tmdb_id": 999999999, "media_type": "movie"}'

# 预期: {"error": "TMDB ID 超出范围"}

# 测试无效媒体类型
curl -X POST http://localhost:5000/api/tmdb/validate \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"tmdb_id": 123, "media_type": "invalid"}'

# 预期: {"error": "无效的媒体类型"}
```

**Step 4: Commit**

```bash
git add web/app.py
git commit -m "feat: add input validation and security checks"
```

---

## 完成检查清单

- [x] 创建导入页面路由
- [x] 创建导入页面 HTML 模板
- [x] 添加导入页面 CSS 样式
- [x] 实现 TMDB ID 验证 API
- [x] 实现季列表获取 API（复用现有）
- [x] 实现最终导入 API
- [x] 实现前端交互逻辑
- [x] 添加导航入口
- [x] 完整流程手动测试
- [x] 输入验证和安全增强

---

## 后续优化建议

1. **缓存优化**: 对已验证的 TMDB ID 进行前端缓存，避免重复请求
2. **历史记录**: 记录用户最近的导入历史，快速重用
3. **批量导入**: 支持一次导入多季/多集
4. **单元测试**: 为新增 API 端点添加 pytest 测试用例
