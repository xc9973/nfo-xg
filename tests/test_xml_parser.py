"""Property-based tests for XML parser.

Feature: nfo-editor
"""
import pytest
from hypothesis import given, strategies as st, settings

from nfo_editor.models.nfo_model import NfoData, Actor
from nfo_editor.models.nfo_types import NfoType
from nfo_editor.utils.xml_parser import XmlParser
from nfo_editor.utils.exceptions import ParseError


# Strategies for generating test data
@st.composite
def actor_strategy(draw):
    """Generate valid Actor objects."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='<>&"\''
    )))
    role = draw(st.text(max_size=50, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='<>&"\''
    )))
    thumb = draw(st.text(max_size=100, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P'),
        blacklist_characters='<>&"\''
    )))
    order = draw(st.integers(min_value=0, max_value=100))
    return Actor(name=name, role=role, thumb=thumb, order=order)


@st.composite
def safe_text_strategy(draw, min_size=0, max_size=200):
    """Generate text safe for XML (no special chars that break XML)."""
    return draw(st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(
            whitelist_categories=('L', 'N', 'P', 'Z'),
            blacklist_characters='<>&"\'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f'
        )
    ))


@st.composite
def nfo_data_strategy(draw):
    """Generate valid NfoData objects."""
    nfo_type = draw(st.sampled_from(list(NfoType)))
    title = draw(safe_text_strategy(min_size=0, max_size=100))
    originaltitle = draw(safe_text_strategy(max_size=100))
    year = draw(st.integers(min_value=1900, max_value=2100).map(str) | st.just(""))
    plot = draw(safe_text_strategy(max_size=500))
    runtime = draw(st.integers(min_value=1, max_value=500).map(str) | st.just(""))
    studio = draw(safe_text_strategy(max_size=100))
    rating = draw(st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False).map(lambda x: f"{x:.1f}") | st.just(""))
    poster = draw(safe_text_strategy(max_size=100))
    fanart = draw(safe_text_strategy(max_size=100))
    
    genres = draw(st.lists(safe_text_strategy(min_size=1, max_size=30), max_size=5))
    directors = draw(st.lists(safe_text_strategy(min_size=1, max_size=50), max_size=3))
    actors = draw(st.lists(actor_strategy(), max_size=5))
    
    # TV show specific
    season = ""
    episode = ""
    aired = ""
    if nfo_type in (NfoType.TVSHOW, NfoType.EPISODE):
        season = draw(st.integers(min_value=1, max_value=50).map(str) | st.just(""))
        episode = draw(st.integers(min_value=1, max_value=100).map(str) | st.just(""))
        aired = draw(st.dates().map(str) | st.just(""))
    
    return NfoData(
        nfo_type=nfo_type,
        title=title,
        originaltitle=originaltitle,
        year=year,
        plot=plot,
        runtime=runtime,
        genres=genres,
        directors=directors,
        actors=actors,
        studio=studio,
        rating=rating,
        poster=poster,
        fanart=fanart,
        season=season,
        episode=episode,
        aired=aired,
        extra_tags={}  # Don't generate extra_tags for round-trip test
    )


class TestXmlParserRoundTrip:
    """Property 1: XML 解析保存往返一致性
    
    Feature: nfo-editor, Property 1: XML Round-Trip Consistency
    Validates: Requirements 1.2, 1.4
    """

    @given(nfo_data=nfo_data_strategy())
    @settings(max_examples=100)
    def test_round_trip_consistency(self, nfo_data: NfoData):
        """For any valid NfoData, serializing to XML then parsing back
        should produce an equivalent NfoData object.
        """
        parser = XmlParser()
        
        # Serialize to XML
        xml_output = parser.format_xml(nfo_data)
        
        # Parse back
        parsed_data = parser.parse_string(xml_output)
        
        # Verify equivalence
        assert parsed_data.nfo_type == nfo_data.nfo_type
        assert parsed_data.title == nfo_data.title
        assert parsed_data.originaltitle == nfo_data.originaltitle
        assert parsed_data.year == nfo_data.year
        assert parsed_data.plot == nfo_data.plot
        assert parsed_data.runtime == nfo_data.runtime
        assert parsed_data.studio == nfo_data.studio
        assert parsed_data.rating == nfo_data.rating
        assert parsed_data.poster == nfo_data.poster
        assert parsed_data.fanart == nfo_data.fanart
        
        # Multi-value fields
        assert parsed_data.genres == nfo_data.genres
        assert parsed_data.directors == nfo_data.directors
        
        # Actors
        assert len(parsed_data.actors) == len(nfo_data.actors)
        for orig, parsed in zip(nfo_data.actors, parsed_data.actors):
            assert parsed.name == orig.name
            assert parsed.role == orig.role
            assert parsed.thumb == orig.thumb
            assert parsed.order == orig.order
        
        # TV show specific
        if nfo_data.nfo_type in (NfoType.TVSHOW, NfoType.EPISODE):
            assert parsed_data.season == nfo_data.season
            assert parsed_data.episode == nfo_data.episode
            assert parsed_data.aired == nfo_data.aired


@st.composite
def invalid_xml_strategy(draw):
    """Generate invalid XML strings."""
    invalid_patterns = [
        # Unclosed tags
        lambda: f"<movie><title>Test{draw(st.text(max_size=20))}</movie>",
        # Mismatched tags
        lambda: f"<movie><title>Test</year></movie>",
        # Invalid characters in tag names
        lambda: f"<movie><123invalid>Test</123invalid></movie>",
        # Missing root element
        lambda: f"<title>Test</title><year>2024</year>",
        # Malformed XML declaration
        lambda: f"<?xml version='1.0'><movie><title>Test</title></movie>",
        # Unclosed root
        lambda: f"<movie><title>Test</title>",
        # Double root elements
        lambda: f"<movie></movie><tvshow></tvshow>",
        # Invalid entity
        lambda: f"<movie><title>&invalid;</title></movie>",
        # Unescaped special chars
        lambda: f"<movie><title>Test < > & </title></movie>",
    ]
    pattern = draw(st.sampled_from(invalid_patterns))
    return pattern()


class TestXmlParserInvalidXml:
    """Property 2: 无效 XML 错误处理
    
    Feature: nfo-editor, Property 2: Invalid XML Error Handling
    Validates: Requirements 1.3
    """

    @given(invalid_xml=invalid_xml_strategy())
    @settings(max_examples=100)
    def test_invalid_xml_raises_parse_error(self, invalid_xml: str):
        """For any invalid XML string, the parser should raise ParseError
        without crashing or producing corrupted data.
        """
        parser = XmlParser()
        
        with pytest.raises(ParseError):
            parser.parse_string(invalid_xml)

    def test_empty_string_raises_parse_error(self):
        """Empty string should raise ParseError."""
        parser = XmlParser()
        with pytest.raises(ParseError):
            parser.parse_string("")

    def test_whitespace_only_raises_parse_error(self):
        """Whitespace-only string should raise ParseError."""
        parser = XmlParser()
        with pytest.raises(ParseError):
            parser.parse_string("   \n\t  ")

    def test_non_xml_content_raises_parse_error(self):
        """Non-XML content should raise ParseError."""
        parser = XmlParser()
        with pytest.raises(ParseError):
            parser.parse_string("This is not XML at all")


class TestNfoTypeDetection:
    """Property 6: NFO 类型自动检测
    
    Feature: nfo-editor, Property 6: NFO Type Auto-Detection
    Validates: Requirements 5.4
    """

    @given(nfo_type=st.sampled_from(list(NfoType)))
    @settings(max_examples=100)
    def test_type_detection_from_xml(self, nfo_type: NfoType):
        """For any valid NFO file, the parser should correctly identify
        its type (movie, tvshow, episodedetails).
        """
        parser = XmlParser()
        
        # Create minimal valid XML for the type
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<{nfo_type.value}>
    <title>Test</title>
</{nfo_type.value}>'''
        
        detected_type = parser.detect_type_from_string(xml)
        assert detected_type == nfo_type

    def test_movie_type_detection(self):
        """Test movie type detection."""
        parser = XmlParser()
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Test Movie</title>
    <year>2024</year>
</movie>'''
        assert parser.detect_type_from_string(xml) == NfoType.MOVIE

    def test_tvshow_type_detection(self):
        """Test TV show type detection."""
        parser = XmlParser()
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<tvshow>
    <title>Test Show</title>
    <season>1</season>
</tvshow>'''
        assert parser.detect_type_from_string(xml) == NfoType.TVSHOW

    def test_episode_type_detection(self):
        """Test episode type detection."""
        parser = XmlParser()
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<episodedetails>
    <title>Test Episode</title>
    <season>1</season>
    <episode>5</episode>
</episodedetails>'''
        assert parser.detect_type_from_string(xml) == NfoType.EPISODE

    @given(nfo_data=nfo_data_strategy())
    @settings(max_examples=100)
    def test_type_preserved_after_round_trip(self, nfo_data: NfoData):
        """NFO type should be preserved after serialization and parsing."""
        parser = XmlParser()
        
        xml_output = parser.format_xml(nfo_data)
        detected_type = parser.detect_type_from_string(xml_output)
        
        assert detected_type == nfo_data.nfo_type


@st.composite
def unknown_tag_strategy(draw):
    """Generate valid unknown tag names and values."""
    # Generate tag name that's not in known tags
    known_names = {'title', 'originaltitle', 'year', 'plot', 'runtime', 'genre',
                   'director', 'actor', 'studio', 'rating', 'poster', 'fanart',
                   'season', 'episode', 'aired', 'movie', 'tvshow', 'episodedetails'}
    
    # XML tag names must start with a letter and contain only ASCII letters, digits, underscores
    first_char = draw(st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    rest_chars = draw(st.text(
        min_size=2,
        max_size=19,
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
    ))
    tag_name = first_char + rest_chars
    
    # Filter out known tag names
    if tag_name.lower() in known_names:
        tag_name = 'custom_' + tag_name
    
    tag_value = draw(safe_text_strategy(min_size=1, max_size=100))
    
    return tag_name, tag_value


class TestUnknownTagPreservation:
    """Property 7: 未知标签保留
    
    Feature: nfo-editor, Property 7: Unknown Tag Preservation
    Validates: Requirements 5.5
    """

    @given(
        nfo_type=st.sampled_from(list(NfoType)),
        unknown_tags=st.lists(unknown_tag_strategy(), min_size=1, max_size=5)
    )
    @settings(max_examples=100)
    def test_unknown_tags_preserved_after_round_trip(self, nfo_type: NfoType, unknown_tags):
        """For any NFO file with unknown/custom tags, these tags should be
        completely preserved after parsing and saving.
        """
        parser = XmlParser()
        
        # Build XML with unknown tags
        unknown_xml_parts = []
        for tag_name, tag_value in unknown_tags:
            unknown_xml_parts.append(f"    <{tag_name}>{tag_value}</{tag_name}>")
        
        unknown_xml = "\n".join(unknown_xml_parts)
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<{nfo_type.value}>
    <title>Test</title>
{unknown_xml}
</{nfo_type.value}>'''
        
        # Parse
        data = parser.parse_string(xml)
        
        # Verify unknown tags were captured
        assert len(data.extra_tags) > 0
        
        # Round-trip
        xml_output = parser.format_xml(data)
        data2 = parser.parse_string(xml_output)
        
        # Verify unknown tags are still present
        for tag_name, tag_value in unknown_tags:
            assert tag_name in data2.extra_tags

    def test_unknown_tag_with_attributes_preserved(self):
        """Unknown tags with attributes should be preserved."""
        parser = XmlParser()
        
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Test</title>
    <customtag attr="value" another="test">Content</customtag>
</movie>'''
        
        data = parser.parse_string(xml)
        assert 'customtag' in data.extra_tags
        
        # Round-trip
        xml_output = parser.format_xml(data)
        
        # Verify attributes are preserved
        assert 'attr="value"' in xml_output
        assert 'another="test"' in xml_output

    def test_multiple_unknown_tags_same_name_preserved(self):
        """Multiple unknown tags with the same name should all be preserved."""
        parser = XmlParser()
        
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Test</title>
    <customtag>Value1</customtag>
    <customtag>Value2</customtag>
    <customtag>Value3</customtag>
</movie>'''
        
        data = parser.parse_string(xml)
        assert 'customtag' in data.extra_tags
        
        # Should be a list for multiple tags
        assert isinstance(data.extra_tags['customtag'], list)
        assert len(data.extra_tags['customtag']) == 3
        
        # Round-trip
        xml_output = parser.format_xml(data)
        data2 = parser.parse_string(xml_output)
        
        # All three should still be present
        assert isinstance(data2.extra_tags['customtag'], list)
        assert len(data2.extra_tags['customtag']) == 3

    def test_nested_unknown_tags_preserved(self):
        """Unknown tags with nested structure should be preserved."""
        parser = XmlParser()
        
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Test</title>
    <customparent>
        <child1>Value1</child1>
        <child2>Value2</child2>
    </customparent>
</movie>'''
        
        data = parser.parse_string(xml)
        assert 'customparent' in data.extra_tags
        
        # Round-trip
        xml_output = parser.format_xml(data)
        
        # Verify nested structure is preserved
        assert '<child1>Value1</child1>' in xml_output
        assert '<child2>Value2</child2>' in xml_output
