"""Flask Web Application for NFO Editor."""
import os
import json
import secrets
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from io import BytesIO
import zipfile

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    send_file,
    redirect,
    url_for,
)
from flask_session import Session
from cachelib.file import FileSystemCache
from werkzeug.utils import secure_filename

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from nfo_editor.models.nfo_model import NfoData, Actor
from nfo_editor.models.nfo_types import NfoType
from nfo_editor.utils.xml_parser import XmlParser
from nfo_editor.utils.exceptions import ParseError, FileError
from nfo_editor.batch import TaskManager, BatchPreviewRequest, BatchApplyRequest
from nfo_editor.batch.processor import BatchProcessor
from tmdb_search.client import TMDBClient
from tmdb_search.mapper import tmdb_to_nfo, TMDBMapper

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("FLASK_SECRET_KEY")
if not SECRET_KEY:
    logger.warning("SECRET_KEY not set, using temporary key. Set SECRET_KEY environment variable!")
    SECRET_KEY = secrets.token_hex(32)

NFO_PASSWORD = os.environ.get("NFO_PASSWORD", "")
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", "3600"))
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
MAX_FILES_PER_BATCH = int(os.environ.get("MAX_FILES_PER_BATCH", "50"))
SESSION_FILE_DIR = os.environ.get("SESSION_FILE_DIR", "/tmp/flask_session")

# Create Flask app
app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR=SESSION_FILE_DIR,
    SESSION_FILE_THRESHOLD=500,
    PERMANENT_SESSION_LIFETIME=timedelta(seconds=SESSION_TIMEOUT),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=MAX_UPLOAD_SIZE,
)

# Initialize Session
Session(app)

# Initialize parsers and processors
xml_parser = XmlParser()
batch_processor = BatchProcessor(xml_parser)
tmdb_client = TMDBClient()

# Ensure session directory exists
Path(SESSION_FILE_DIR).mkdir(parents=True, exist_ok=True)


# =============================================================================
# Authentication
# =============================================================================

def check_auth() -> bool:
    """Check if user is authenticated.

    Returns:
        True if authenticated, False otherwise.
    """
    if not NFO_PASSWORD:
        # No password set, allow anonymous access
        return True
    return session.get("authenticated", False)


@app.route("/import", methods=["GET"])
def import_page():
    """TMDB 导入页面."""
    if not check_auth():
        return redirect(url_for("login"))
    return render_template("import.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    # If no password is set, redirect to index
    if not NFO_PASSWORD:
        return redirect(url_for("index"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if secrets.compare_digest(password, NFO_PASSWORD):
            session["authenticated"] = True
            session.permanent = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="密码错误")
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout."""
    session.clear()
    return redirect(url_for("login"))


# =============================================================================
# Main Page
# =============================================================================

@app.route("/")
def index():
    """Main page."""
    if not check_auth():
        return redirect(url_for("login"))
    return render_template("files.html", max_files=MAX_FILES_PER_BATCH)


@app.route("/edit/<file_id>")
def edit_file(file_id: str):
    """Edit page for a single file."""
    if not check_auth():
        return redirect(url_for("login"))

    session_files = session.get("files", {})
    if file_id not in session_files:
        return redirect(url_for("index"))

    file_data = session_files[file_id]
    return render_template("edit.html", file_id=file_id, file_name=file_data["name"])


# =============================================================================
# File Management API
# =============================================================================

@app.route("/api/files/upload", methods=["POST"])
def upload_files():
    """Upload and parse NFO files."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    if "files" not in request.files:
        return jsonify({"error": "没有文件"}), 400

    files = request.files.getlist("files")
    if len(files) > MAX_FILES_PER_BATCH:
        return jsonify({"error": f"最多上传 {MAX_FILES_PER_BATCH} 个文件"}), 400

    uploaded = []
    for file in files:
        if file.filename == "":
            continue

        try:
            # Read file content
            content = file.read().decode("utf-8")

            # Parse NFO
            nfo_data = xml_parser.parse_string(content)

            # Store in session
            file_id = str(uuid.uuid4())
            session_files = session.get("files", {})

            session_files[file_id] = {
                "id": file_id,
                "name": file.filename,
                "original_data": nfo_data,
                "edited_data": None,
                "modified_fields": [],
                "upload_time": datetime.now().isoformat(),
            }
            session["files"] = session_files

            uploaded.append({
                "id": file_id,
                "name": file.filename,
                "title": nfo_data.title,
            })

        except (ParseError, FileError, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse {file.filename}: {e}")
            uploaded.append({
                "name": file.filename,
                "error": str(e),
            })

    return jsonify({"uploaded": uploaded})


@app.route("/api/files", methods=["GET"])
def list_files():
    """List all uploaded files."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    session_files = session.get("files", {})
    files_list = []
    for file_id, file_data in session_files.items():
        files_list.append({
            "id": file_id,
            "name": file_data["name"],
            "title": file_data["original_data"].title,
            "modified": bool(file_data["modified_fields"]),
            "modified_fields": file_data["modified_fields"],
            "upload_time": file_data["upload_time"],
        })

    return jsonify({"files": files_list})


@app.route("/api/files/<file_id>", methods=["GET"])
def get_file(file_id: str):
    """Get file data."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    session_files = session.get("files", {})
    if file_id not in session_files:
        return jsonify({"error": "文件不存在"}), 404

    file_data = session_files[file_id]
    # Use edited data if available, otherwise original
    data = file_data["edited_data"] or file_data["original_data"]

    return jsonify({
        "id": file_id,
        "name": file_data["name"],
        "data": serialize_nfo_data(data),
    })


@app.route("/api/files/<file_id>", methods=["PUT"])
def update_file(file_id: str):
    """Update file data."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    session_files = session.get("files", {})
    if file_id not in session_files:
        return jsonify({"error": "文件不存在"}), 404

    try:
        update_data = request.get_json()

        # Get original data
        original_data = session_files[file_id]["original_data"]

        # Parse nfo_type from string
        nfo_type_str = update_data.get("nfo_type", "movie")
        if isinstance(nfo_type_str, str):
            nfo_type = NfoType(nfo_type_str)
        else:
            nfo_type = original_data.nfo_type

        # Create updated NfoData
        updated_data = NfoData(
            nfo_type=nfo_type,
            title=update_data.get("title", original_data.title),
            originaltitle=update_data.get("originaltitle", original_data.originaltitle),
            year=update_data.get("year", original_data.year),
            plot=update_data.get("plot", original_data.plot),
            runtime=update_data.get("runtime", original_data.runtime),
            genres=update_data.get("genres", original_data.genres),
            directors=update_data.get("directors", original_data.directors),
            actors=[Actor(**a) for a in update_data.get("actors", [])],
            studio=update_data.get("studio", original_data.studio),
            rating=update_data.get("rating", original_data.rating),
            poster=update_data.get("poster", original_data.poster),
            fanart=update_data.get("fanart", original_data.fanart),
            season=update_data.get("season", original_data.season),
            episode=update_data.get("episode", original_data.episode),
            aired=update_data.get("aired", original_data.aired),
            extra_tags=update_data.get("extra_tags", original_data.extra_tags),
        )

        # Track modified fields
        modified_fields = []
        for key in update_data.keys():
            if key != "extra_tags":  # Skip extra_tags for simple comparison
                original_value = getattr(original_data, key, None)
                new_value = update_data.get(key)
                if original_value != new_value:
                    modified_fields.append(key)

        # Store edited data
        session_files[file_id]["edited_data"] = updated_data
        session_files[file_id]["modified_fields"] = modified_fields
        session["files"] = session_files

        return jsonify({"success": True, "modified_fields": modified_fields})

    except Exception as e:
        logger.error(f"Failed to update file {file_id}: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/files/<file_id>", methods=["DELETE"])
def delete_file(file_id: str):
    """Delete a file."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    session_files = session.get("files", {})
    if file_id not in session_files:
        return jsonify({"error": "文件不存在"}), 404

    del session_files[file_id]
    session["files"] = session_files

    return jsonify({"success": True})


@app.route("/api/files/<file_id>/download", methods=["GET"])
def download_file(file_id: str):
    """Download a single NFO file."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    session_files = session.get("files", {})
    if file_id not in session_files:
        return jsonify({"error": "文件不存在"}), 404

    file_data = session_files[file_id]
    # Use edited data if available, otherwise original
    nfo_data = file_data["edited_data"] or file_data["original_data"]

    # Generate NFO content
    content = xml_generator(nfo_data)

    # Send file
    filename = secure_filename(file_data["name"])
    return send_file(
        BytesIO(content.encode("utf-8")),
        as_attachment=True,
        download_name=filename,
        mimetype="text/xml",
    )


# =============================================================================
# Batch Operations API
# =============================================================================

@app.route("/api/batch/update", methods=["POST"])
def batch_update():
    """Batch update fields across multiple files."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.get_json()
        file_ids = data.get("file_ids", [])
        field = data.get("field")
        value = data.get("value")
        operation = data.get("operation", "set")

        if not file_ids or not field:
            return jsonify({"error": "缺少参数"}), 400

        session_files = session.get("files", {})
        updated = []

        for file_id in file_ids:
            if file_id not in session_files:
                continue

            file_data = session_files[file_id]
            original_data = file_data["original_data"]
            edited_data = file_data["edited_data"] or original_data

            # Apply operation
            current_value = getattr(edited_data, field, None)

            if operation == "set":
                new_value = value
            elif operation == "append":
                if isinstance(current_value, list):
                    new_value = current_value + [value]
                else:
                    new_value = f"{current_value} {value}".strip()
            elif operation == "replace":
                if isinstance(current_value, str) and value:
                    parts = value.split("::", 1)
                    if len(parts) == 2:
                        old_val, new_val = parts
                        new_value = current_value.replace(old_val, new_val)
                    else:
                        new_value = current_value
                else:
                    new_value = current_value
            else:
                new_value = current_value

            # Create updated data
            updated_data = NfoData(
                nfo_type=edited_data.nfo_type,
                title=edited_data.title,
                originaltitle=edited_data.originaltitle,
                year=edited_data.year,
                plot=edited_data.plot,
                runtime=edited_data.runtime,
                genres=getattr(edited_data, "genres", []),
                directors=getattr(edited_data, "directors", []),
                actors=getattr(edited_data, "actors", []),
                studio=edited_data.studio,
                rating=edited_data.rating,
                poster=edited_data.poster,
                fanart=edited_data.fanart,
                season=edited_data.season,
                episode=edited_data.episode,
                aired=edited_data.aired,
                extra_tags=getattr(edited_data, "extra_tags", {}),
            )

            # Update the specific field
            setattr(updated_data, field, new_value)

            # Store updated data
            session_files[file_id]["edited_data"] = updated_data
            if field not in session_files[file_id]["modified_fields"]:
                session_files[file_id]["modified_fields"].append(field)

            updated.append({
                "id": file_id,
                "name": file_data["name"],
                "field": field,
                "old_value": str(current_value) if current_value else "",
                "new_value": str(new_value) if new_value else "",
            })

        session["files"] = session_files

        return jsonify({"updated": updated})

    except Exception as e:
        logger.error(f"Batch update failed: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/batch/download", methods=["GET"])
def batch_download():
    """Download multiple files as ZIP."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    file_ids = request.args.getlist("file_ids")
    if not file_ids:
        return jsonify({"error": "没有选择文件"}), 400

    session_files = session.get("files", {})

    # Create ZIP in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_id in file_ids:
            if file_id not in session_files:
                continue

            file_data = session_files[file_id]
            nfo_data = file_data["edited_data"] or file_data["original_data"]
            content = xml_generator(nfo_data)

            filename = secure_filename(file_data["name"])
            zip_file.writestr(filename, content.encode("utf-8"))

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name="nfo_files.zip",
        mimetype="application/zip",
    )


@app.route("/api/batch/delete", methods=["DELETE"])
def batch_delete():
    """Batch delete files."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    file_ids = request.get_json().get("file_ids", [])
    if not file_ids:
        return jsonify({"error": "没有选择文件"}), 400

    session_files = session.get("files", {})
    deleted = []

    for file_id in file_ids:
        if file_id in session_files:
            deleted.append(session_files[file_id]["name"])
            del session_files[file_id]

    session["files"] = session_files

    return jsonify({"deleted": deleted, "count": len(deleted)})


# =============================================================================
# TMDB Search API
# =============================================================================

@app.route("/api/tmdb/search", methods=["GET"])
def tmdb_search():
    """Search TMDB for movies and TV shows."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "缺少搜索关键词"}), 400

    try:
        result = tmdb_client.search_multi(query)
        results = []

        for item in result.get("results", []):
            if item.get("media_type") in ("movie", "tv"):
                results.append({
                    "id": item.get("id"),
                    "media_type": item.get("media_type"),
                    "title": item.get("title") or item.get("name"),
                    "original_title": item.get("original_title") or item.get("original_name"),
                    "year": (item.get("release_date") or item.get("first_air_date") or "")[:4],
                    "overview": item.get("overview"),
                    "poster_path": item.get("poster_path"),
                    "vote_average": item.get("vote_average"),
                })

        return jsonify({"results": results})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"TMDB search failed: {e}")
        return jsonify({"error": "搜索失败"}), 500


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


@app.route("/api/tmdb/import/<media_type>/<path:tmdb_path>", methods=["GET"])
def tmdb_import(media_type: str, tmdb_path: str):
    """Import data from TMDB.

    Args:
        media_type: Type of media (movie, tv, episode)
        tmdb_path: TMDB ID or path (e.g., "12345" or "12345/1/5" for episode)
    """
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    try:
        # Get details from TMDB
        if media_type == "movie":
            tmdb_id = int(tmdb_path)
            details = tmdb_client.get_movie_details(tmdb_id)
            nfo_data = tmdb_to_nfo(details, media_type)
        elif media_type == "tv":
            tmdb_id = int(tmdb_path)
            details = tmdb_client.get_tv_details(tmdb_id)
            nfo_data = tmdb_to_nfo(details, media_type)
        elif media_type == "episode":
            # tmdb_path format: tv_id/season/episode
            parts = tmdb_path.split("/")
            if len(parts) != 3:
                return jsonify({"error": "无效的剧集路径"}), 400
            tv_id, season, episode = int(parts[0]), int(parts[1]), int(parts[2])
            details = tmdb_client.get_tv_episode_details(tv_id, season, episode)
            # Map episode data to NFO
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

        return jsonify(serialize_nfo_data(nfo_data))

    except Exception as e:
        logger.error(f"TMDB import failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tmdb/tv/<int:tmdb_id>", methods=["GET"])
def get_tv_details(tmdb_id: int):
    """Get TV show details with seasons list."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401
    try:
        details = tmdb_client.get_tv_details(tmdb_id)
        seasons = details.get("seasons", [])
        # Filter out special seasons (season_number > 0)
        seasons = [s for s in seasons if s.get("season_number", 0) > 0]
        return jsonify({"seasons": seasons})
    except Exception as e:
        logger.error(f"Failed to get TV details: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tmdb/tv/<int:tmdb_id>/season/<int:season_number>", methods=["GET"])
def get_season_episodes(tmdb_id: int, season_number: int):
    """Get episodes for a season."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401
    try:
        season_data = tmdb_client.get_tv_season_details(tmdb_id, season_number)
        episodes = season_data.get("episodes", [])
        return jsonify({"episodes": episodes})
    except Exception as e:
        logger.error(f"Failed to get season episodes: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tmdb/batch_import_episodes", methods=["POST"])
def batch_import_episodes():
    """Batch import multiple episodes and save to session."""
    if not check_auth():
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.get_json()
        tmdb_id = data.get("tmdb_id")
        season = data.get("season")
        episodes = data.get("episodes", [])  # List of episode numbers

        if not tmdb_id or not season or not episodes:
            return jsonify({"error": "缺少参数"}), 400

        # Get TV show details for naming
        tv_details = tmdb_client.get_tv_details(tmdb_id)
        show_title = tv_details.get("name", "Unknown")

        session_files = session.get("files", {})
        imported = []

        for episode_num in episodes:
            try:
                # Get episode details
                episode_details = tmdb_client.get_tv_episode_details(tmdb_id, season, episode_num)
                mapper = TMDBMapper(tmdb_client)
                episode_data = mapper.map_episode(episode_details)

                # Create NfoData
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

                # Create filename
                episode_title = episode_data.title or f"Episode_{episode_num}"
                filename = secure_filename(f"{show_title}.S{season}E{episode_num}.{episode_title}.nfo")
                file_id = str(uuid.uuid4())

                # Save to session
                session_files[file_id] = {
                    "name": filename,
                    "original_data": nfo_data,
                    "edited_data": None,
                    "modified_fields": [],
                    "upload_time": datetime.now().isoformat(),
                }

                imported.append({"file_id": file_id, "filename": filename, "episode": episode_num})

            except Exception as e:
                logger.error(f"Failed to import episode {episode_num}: {e}")
                continue

        session["files"] = session_files

        return jsonify({
            "success": True,
            "imported": imported,
            "total": len(episodes),
            "count": len(imported)
        })

    except Exception as e:
        logger.error(f"Batch import failed: {e}")
        return jsonify({"error": str(e)}), 500


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


# =============================================================================
# Helpers
# =============================================================================

def serialize_nfo_data(nfo_data: NfoData) -> dict:
    """Serialize NfoData object to dictionary.

    Args:
        nfo_data: NfoData object

    Returns:
        Serializable dictionary
    """
    # Convert nfo_type enum to string
    nfo_type_value = nfo_data.nfo_type.value if isinstance(nfo_data.nfo_type, NfoType) else str(nfo_data.nfo_type)

    return {
        "nfo_type": nfo_type_value,
        "title": nfo_data.title or "",
        "originaltitle": nfo_data.originaltitle or "",
        "year": nfo_data.year or "",
        "plot": nfo_data.plot or "",
        "runtime": nfo_data.runtime or "",
        "genres": nfo_data.genres or [],
        "directors": nfo_data.directors or [],
        "actors": [
            {
                "name": a.name,
                "role": a.role or "",
                "thumb": a.thumb or "",
                "order": a.order
            }
            for a in (nfo_data.actors or [])
        ],
        "studio": nfo_data.studio or "",
        "rating": nfo_data.rating or "",
        "poster": nfo_data.poster or "",
        "fanart": nfo_data.fanart or "",
        "season": nfo_data.season or "",
        "episode": nfo_data.episode or "",
        "aired": nfo_data.aired or "",
        "extra_tags": nfo_data.extra_tags or {},
    }


def xml_generator(nfo_data: NfoData) -> str:
    """Generate NFO XML from NfoData.

    Args:
        nfo_data: NfoData object

    Returns:
        XML string
    """
    from lxml import etree

    # Root element based on type
    if nfo_data.nfo_type == NfoType.MOVIE:
        root = etree.Element("movie")
    elif nfo_data.nfo_type == NfoType.TVSHOW:
        root = etree.Element("tvshow")
    elif nfo_data.nfo_type == NfoType.EPISODE:
        root = etree.Element("episodedetails")
    else:
        root = etree.Element("root")

    # Add fields
    def add_field(parent, name, value):
        if value is None or value == "":
            return
        elem = etree.SubElement(parent, name)
        elem.text = str(value)

    add_field(root, "title", nfo_data.title)
    add_field(root, "originaltitle", nfo_data.originaltitle)
    add_field(root, "year", nfo_data.year)
    add_field(root, "plot", nfo_data.plot)
    add_field(root, "runtime", nfo_data.runtime)
    add_field(root, "studio", nfo_data.studio)
    add_field(root, "rating", nfo_data.rating)
    add_field(root, "poster", nfo_data.poster)
    add_field(root, "fanart", nfo_data.fanart)
    add_field(root, "season", nfo_data.season)
    add_field(root, "episode", nfo_data.episode)
    add_field(root, "aired", nfo_data.aired)

    # Genres
    for genre in nfo_data.genres or []:
        add_field(root, "genre", genre)

    # Directors
    for director in nfo_data.directors or []:
        add_field(root, "director", director)

    # Actors
    for actor in nfo_data.actors or []:
        actor_elem = etree.SubElement(root, "actor")
        add_field(actor_elem, "name", actor.name)
        add_field(actor_elem, "role", actor.role)
        add_field(actor_elem, "thumb", actor.thumb)
        add_field(actor_elem, "order", str(actor.order))

    # Extra tags
    for key, value in (nfo_data.extra_tags or {}).items():
        add_field(root, key, value)

    return etree.tostring(root, encoding="unicode", pretty_print=True)


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    if request.path.startswith("/api/"):
        return jsonify({"error": "未找到"}), 404
    return render_template("login.html")


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    if request.path.startswith("/api/"):
        return jsonify({"error": "服务器错误"}), 500
    return render_template("login.html", error="服务器错误")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
