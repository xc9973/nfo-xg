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
