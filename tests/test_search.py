"""Unit tests for search API.

Feature: web-search
"""
import pytest
import tempfile
import os
from pathlib import Path

from web.app import (
    SearchRequest,
    SearchResultItem,
    scan_nfo_files,
    match_filename,
    match_nfo_content,
    search_nfo_files,
)
from nfo_editor.utils.xml_parser import XmlParser


class TestMatchFilename:
    """测试文件名匹配逻辑"""

    def test_exact_match(self):
        """精确匹配"""
        assert match_filename("test.nfo", "test") is True

    def test_partial_match(self):
        """部分匹配"""
        assert match_filename("my_test_file.nfo", "test") is True

    def test_case_insensitive_match(self):
        """大小写不敏感匹配"""
        assert match_filename("TEST.nfo", "test") is True
        assert match_filename("test.nfo", "TEST") is True
        assert match_filename("TeSt.nfo", "tEsT") is True

    def test_no_match(self):
        """不匹配"""
        assert match_filename("movie.nfo", "test") is False

    def test_empty_query(self):
        """空查询匹配所有"""
        assert match_filename("test.nfo", "") is True


class TestScanNfoFiles:
    """测试目录扫描逻辑"""

    def test_scan_empty_directory(self):
        """扫描空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scan_nfo_files(Path(tmpdir), max_depth=5)
            assert result == []

    def test_scan_finds_nfo_files(self):
        """扫描找到 NFO 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试 NFO 文件
            nfo_path = Path(tmpdir) / "test.nfo"
            nfo_path.write_text("<movie><title>Test</title></movie>")
            
            result = scan_nfo_files(Path(tmpdir), max_depth=5)
            assert len(result) == 1
            assert result[0].name == "test.nfo"

    def test_scan_ignores_non_nfo_files(self):
        """扫描忽略非 NFO 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建非 NFO 文件
            txt_path = Path(tmpdir) / "test.txt"
            txt_path.write_text("not an nfo file")
            
            result = scan_nfo_files(Path(tmpdir), max_depth=5)
            assert result == []

    def test_scan_recursive(self):
        """递归扫描子目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建子目录和 NFO 文件
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            nfo_path = subdir / "test.nfo"
            nfo_path.write_text("<movie><title>Test</title></movie>")
            
            result = scan_nfo_files(Path(tmpdir), max_depth=5)
            assert len(result) == 1
            assert result[0].name == "test.nfo"

    def test_scan_respects_max_depth(self):
        """扫描遵守最大深度限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建深层目录结构
            deep_dir = Path(tmpdir) / "a" / "b" / "c"
            deep_dir.mkdir(parents=True)
            nfo_path = deep_dir / "test.nfo"
            nfo_path.write_text("<movie><title>Test</title></movie>")
            
            # max_depth=1 应该找不到深层文件
            result = scan_nfo_files(Path(tmpdir), max_depth=1)
            assert len(result) == 0
            
            # max_depth=3 应该能找到
            result = scan_nfo_files(Path(tmpdir), max_depth=3)
            assert len(result) == 1

    def test_scan_ignores_hidden_files(self):
        """扫描忽略隐藏文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建隐藏文件
            hidden_path = Path(tmpdir) / ".hidden.nfo"
            hidden_path.write_text("<movie><title>Test</title></movie>")
            
            result = scan_nfo_files(Path(tmpdir), max_depth=5)
            assert result == []


class TestMatchNfoContent:
    """测试 NFO 内容匹配逻辑"""

    def test_match_title(self):
        """匹配标题"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nfo_path = Path(tmpdir) / "test.nfo"
            nfo_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>My Test Movie</title>
</movie>""")
            
            parser = XmlParser()
            result = match_nfo_content(nfo_path, "test", parser)
            
            assert result is not None
            assert result[0] == "title"
            assert "Test" in result[1]

    def test_match_originaltitle(self):
        """匹配原始标题"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nfo_path = Path(tmpdir) / "test.nfo"
            nfo_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>English Title</title>
    <originaltitle>Original Test Title</originaltitle>
</movie>""")
            
            parser = XmlParser()
            result = match_nfo_content(nfo_path, "original", parser)
            
            assert result is not None
            assert result[0] == "originaltitle"

    def test_match_actor(self):
        """匹配演员"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nfo_path = Path(tmpdir) / "test.nfo"
            nfo_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Movie</title>
    <actor>
        <name>John Smith</name>
    </actor>
</movie>""")
            
            parser = XmlParser()
            result = match_nfo_content(nfo_path, "john", parser)
            
            assert result is not None
            assert result[0] == "actor"
            assert "John" in result[1]

    def test_match_plot(self):
        """匹配剧情"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nfo_path = Path(tmpdir) / "test.nfo"
            nfo_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Movie</title>
    <plot>This is a story about adventure and discovery.</plot>
</movie>""")
            
            parser = XmlParser()
            result = match_nfo_content(nfo_path, "adventure", parser)
            
            assert result is not None
            assert result[0] == "plot"

    def test_no_content_match(self):
        """内容不匹配"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nfo_path = Path(tmpdir) / "test.nfo"
            nfo_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Movie</title>
</movie>""")
            
            parser = XmlParser()
            result = match_nfo_content(nfo_path, "nonexistent", parser)
            
            assert result is None

    def test_case_insensitive_content_match(self):
        """内容匹配大小写不敏感"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nfo_path = Path(tmpdir) / "test.nfo"
            nfo_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>UPPERCASE TITLE</title>
</movie>""")
            
            parser = XmlParser()
            result = match_nfo_content(nfo_path, "uppercase", parser)
            
            assert result is not None


class TestSearchNfoFiles:
    """测试搜索功能"""

    def test_search_by_filename(self):
        """按文件名搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nfo_path = Path(tmpdir) / "my_movie.nfo"
            nfo_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<movie><title>Some Title</title></movie>""")
            
            parser = XmlParser()
            results, truncated = search_nfo_files(
                query="my_movie",
                base_path=Path(tmpdir),
                max_depth=5,
                max_results=50,
                xml_parser=parser
            )
            
            assert len(results) == 1
            assert results[0].match_type == "filename"
            assert truncated is False

    def test_search_by_content(self):
        """按内容搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nfo_path = Path(tmpdir) / "movie.nfo"
            nfo_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<movie><title>Unique Title Here</title></movie>""")
            
            parser = XmlParser()
            results, truncated = search_nfo_files(
                query="unique",
                base_path=Path(tmpdir),
                max_depth=5,
                max_results=50,
                xml_parser=parser
            )
            
            assert len(results) == 1
            assert results[0].match_type == "title"

    def test_search_empty_query(self):
        """空查询返回空结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nfo_path = Path(tmpdir) / "test.nfo"
            nfo_path.write_text("<movie><title>Test</title></movie>")
            
            parser = XmlParser()
            results, truncated = search_nfo_files(
                query="",
                base_path=Path(tmpdir),
                max_depth=5,
                max_results=50,
                xml_parser=parser
            )
            
            assert results == []

    def test_search_whitespace_query(self):
        """空白查询返回空结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = XmlParser()
            results, truncated = search_nfo_files(
                query="   ",
                base_path=Path(tmpdir),
                max_depth=5,
                max_results=50,
                xml_parser=parser
            )
            
            assert results == []

    def test_search_max_results_limit(self):
        """搜索结果数量限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建多个匹配的文件
            for i in range(10):
                nfo_path = Path(tmpdir) / f"test_{i}.nfo"
                nfo_path.write_text(f"<movie><title>Test {i}</title></movie>")
            
            parser = XmlParser()
            results, truncated = search_nfo_files(
                query="test",
                base_path=Path(tmpdir),
                max_depth=5,
                max_results=5,
                xml_parser=parser
            )
            
            assert len(results) == 5
            assert truncated is True

    def test_search_deduplication(self):
        """搜索结果去重（文件名和内容都匹配时只返回一次）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 文件名和标题都包含 "test"
            nfo_path = Path(tmpdir) / "test.nfo"
            nfo_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<movie><title>Test Movie</title></movie>""")
            
            parser = XmlParser()
            results, truncated = search_nfo_files(
                query="test",
                base_path=Path(tmpdir),
                max_depth=5,
                max_results=50,
                xml_parser=parser
            )
            
            # 应该只返回一个结果（文件名匹配优先）
            assert len(results) == 1
            assert results[0].match_type == "filename"


# ========== Property-Based Tests ==========

from hypothesis import given, strategies as st, settings


@st.composite
def safe_filename_strategy(draw):
    """Generate safe filenames for NFO files."""
    # Generate filename without extension
    name = draw(st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=('L', 'N'),
            blacklist_characters='<>&"\'/\\:*?|'
        )
    ))
    return name + ".nfo"


@st.composite
def search_query_strategy(draw):
    """Generate search query strings."""
    return draw(st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(
            whitelist_categories=('L', 'N'),
            blacklist_characters='<>&"\'/\\:*?|'
        )
    ))


class TestFilenameMatchProperty:
    """Property 1: 文件名匹配正确性
    
    Feature: web-search, Property 1: 文件名匹配正确性
    Validates: Requirements 2.1
    
    *For any* search query string Q and NFO filename F, if F.lower() contains Q.lower(),
    then the search results SHALL include this file with match_type="filename".
    """

    @given(
        filename=safe_filename_strategy(),
        query=search_query_strategy()
    )
    @settings(max_examples=100)
    def test_filename_match_correctness(self, filename: str, query: str):
        """For any filename and query, if filename.lower() contains query.lower(),
        then match_filename should return True.
        """
        expected = query.lower() in filename.lower()
        actual = match_filename(filename, query)
        assert actual == expected, f"Expected {expected} for filename='{filename}', query='{query}'"

    @given(query=search_query_strategy())
    @settings(max_examples=100)
    def test_filename_containing_query_always_matches(self, query: str):
        """For any query Q, a filename that contains Q should always match."""
        # Construct a filename that definitely contains the query
        filename = f"prefix_{query}_suffix.nfo"
        assert match_filename(filename, query) is True

    @given(
        prefix=st.text(min_size=0, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
        suffix=st.text(min_size=0, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
        query=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    )
    @settings(max_examples=100)
    def test_case_insensitive_matching(self, prefix: str, suffix: str, query: str):
        """For any ASCII query, matching should be case-insensitive."""
        # Test with uppercase query in lowercase filename
        filename_lower = f"{prefix}{query.lower()}{suffix}.nfo"
        assert match_filename(filename_lower, query.upper()) is True
        
        # Test with lowercase query in uppercase filename
        filename_upper = f"{prefix}{query.upper()}{suffix}.nfo"
        assert match_filename(filename_upper, query.lower()) is True



class TestResultCountLimitProperty:
    """Property 5: 结果数量限制
    
    Feature: web-search, Property 5: 结果数量限制
    Validates: Requirements 6.2
    
    *For any* search operation with max_results=M, the returned results list length SHALL be <= M.
    """

    @given(
        max_results=st.integers(min_value=1, max_value=100),
        num_files=st.integers(min_value=0, max_value=50)
    )
    @settings(max_examples=100)
    def test_results_never_exceed_max_results(self, max_results: int, num_files: int):
        """For any max_results value M and any number of matching files,
        the returned results list length should always be <= M.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create num_files NFO files that will match the query
            for i in range(num_files):
                nfo_path = Path(tmpdir) / f"test_file_{i}.nfo"
                nfo_path.write_text(f"<movie><title>Test {i}</title></movie>")
            
            parser = XmlParser()
            results, truncated = search_nfo_files(
                query="test",
                base_path=Path(tmpdir),
                max_depth=5,
                max_results=max_results,
                xml_parser=parser
            )
            
            # Core property: results length <= max_results
            assert len(results) <= max_results, \
                f"Results count {len(results)} exceeds max_results {max_results}"
            
            # Additional property: truncated flag correctness
            if num_files > max_results:
                assert truncated is True, \
                    f"truncated should be True when num_files ({num_files}) > max_results ({max_results})"
            elif num_files <= max_results:
                assert truncated is False, \
                    f"truncated should be False when num_files ({num_files}) <= max_results ({max_results})"

    @given(max_results=st.integers(min_value=1, max_value=20))
    @settings(max_examples=100)
    def test_exact_limit_boundary(self, max_results: int):
        """When exactly max_results files match, truncated should be False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create exactly max_results matching files
            for i in range(max_results):
                nfo_path = Path(tmpdir) / f"match_{i}.nfo"
                nfo_path.write_text(f"<movie><title>Match {i}</title></movie>")
            
            parser = XmlParser()
            results, truncated = search_nfo_files(
                query="match",
                base_path=Path(tmpdir),
                max_depth=5,
                max_results=max_results,
                xml_parser=parser
            )
            
            assert len(results) == max_results
            assert truncated is False

    @given(max_results=st.integers(min_value=1, max_value=20))
    @settings(max_examples=100)
    def test_one_over_limit_boundary(self, max_results: int):
        """When max_results + 1 files match, truncated should be True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create max_results + 1 matching files
            for i in range(max_results + 1):
                nfo_path = Path(tmpdir) / f"match_{i}.nfo"
                nfo_path.write_text(f"<movie><title>Match {i}</title></movie>")
            
            parser = XmlParser()
            results, truncated = search_nfo_files(
                query="match",
                base_path=Path(tmpdir),
                max_depth=5,
                max_results=max_results,
                xml_parser=parser
            )
            
            assert len(results) == max_results
            assert truncated is True
