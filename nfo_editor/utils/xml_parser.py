"""XML parser for NFO files."""
from typing import Optional, Dict, Any, List
from pathlib import Path

from lxml import etree

from nfo_editor.models.nfo_model import NfoData, Actor
from nfo_editor.models.nfo_types import NfoType
from nfo_editor.utils.exceptions import ParseError, FileError


# Known tags for each NFO type
COMMON_TAGS = {
    'title', 'originaltitle', 'year', 'plot', 'runtime', 'genre',
    'director', 'actor', 'studio', 'rating', 'poster', 'fanart'
}

TVSHOW_TAGS = COMMON_TAGS | {'season', 'episode', 'aired'}
EPISODE_TAGS = COMMON_TAGS | {'season', 'episode', 'aired'}

KNOWN_TAGS = {
    NfoType.MOVIE: COMMON_TAGS,
    NfoType.TVSHOW: TVSHOW_TAGS,
    NfoType.EPISODE: EPISODE_TAGS,
}


class XmlParser:
    """Parser for NFO XML files."""

    def parse(self, file_path: str) -> NfoData:
        """Parse NFO file and return NfoData object.
        
        Args:
            file_path: Path to the NFO file
            
        Returns:
            NfoData object with parsed content
            
        Raises:
            FileError: If file doesn't exist or can't be read
            ParseError: If XML is invalid or malformed
        """
        path = Path(file_path)
        if not path.exists():
            raise FileError(f"File not found: {file_path}")
        
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding='latin-1')
            except Exception as e:
                raise FileError(f"Cannot read file: {e}")
        except Exception as e:
            raise FileError(f"Cannot read file: {e}")
        
        return self.parse_string(content)

    def parse_string(self, xml_content: str) -> NfoData:
        """Parse XML string and return NfoData object.
        
        Args:
            xml_content: XML content as string
            
        Returns:
            NfoData object with parsed content
            
        Raises:
            ParseError: If XML is invalid or malformed
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            raise ParseError(f"Invalid XML: {e}", line=e.lineno, column=e.offset)
        
        nfo_type = self._detect_type_from_root(root)
        return self._parse_root(root, nfo_type)

    def _detect_type_from_root(self, root: etree._Element) -> NfoType:
        """Detect NFO type from root element tag."""
        tag = root.tag.lower()
        for nfo_type in NfoType:
            if nfo_type.value == tag:
                return nfo_type
        # Default to movie if unknown
        return NfoType.MOVIE

    def _parse_root(self, root: etree._Element, nfo_type: NfoType) -> NfoData:
        """Parse root element into NfoData."""
        data = NfoData(nfo_type=nfo_type)
        known_tags = KNOWN_TAGS.get(nfo_type, COMMON_TAGS)
        
        genres = []
        directors = []
        actors = []
        extra_tags: Dict[str, Any] = {}
        
        for child in root:
            tag = child.tag
            text = child.text or ""
            
            if tag == 'title':
                data.title = text
            elif tag == 'originaltitle':
                data.originaltitle = text
            elif tag == 'year':
                data.year = text
            elif tag == 'plot':
                data.plot = text
            elif tag == 'runtime':
                data.runtime = text
            elif tag == 'studio':
                data.studio = text
            elif tag == 'rating':
                data.rating = text
            elif tag == 'poster':
                data.poster = text
            elif tag == 'fanart':
                data.fanart = text
            elif tag == 'season':
                data.season = text
            elif tag == 'episode':
                data.episode = text
            elif tag == 'aired':
                data.aired = text
            elif tag == 'genre':
                genres.append(text)
            elif tag == 'director':
                directors.append(text)
            elif tag == 'actor':
                actor = self._parse_actor(child)
                actors.append(actor)
            else:
                # Unknown tag - preserve it
                self._add_extra_tag(extra_tags, tag, child)
        
        data.genres = genres
        data.directors = directors
        data.actors = actors
        data.extra_tags = extra_tags
        
        return data

    def _parse_actor(self, actor_elem: etree._Element) -> Actor:
        """Parse actor element."""
        name = ""
        role = ""
        thumb = ""
        order = 0
        
        for child in actor_elem:
            text = child.text or ""
            if child.tag == 'name':
                name = text
            elif child.tag == 'role':
                role = text
            elif child.tag == 'thumb':
                thumb = text
            elif child.tag == 'order':
                try:
                    order = int(text)
                except ValueError:
                    order = 0
        
        return Actor(name=name, role=role, thumb=thumb, order=order)

    def _add_extra_tag(self, extra_tags: Dict[str, Any], tag: str, elem: etree._Element) -> None:
        """Add unknown tag to extra_tags dict, preserving structure."""
        # Serialize the element to preserve its full structure
        elem_str = etree.tostring(elem, encoding='unicode')
        
        if tag in extra_tags:
            # Multiple tags with same name
            if isinstance(extra_tags[tag], list):
                extra_tags[tag].append(elem_str)
            else:
                extra_tags[tag] = [extra_tags[tag], elem_str]
        else:
            extra_tags[tag] = elem_str

    def detect_type(self, file_path: str) -> NfoType:
        """Detect NFO file type.
        
        Args:
            file_path: Path to the NFO file
            
        Returns:
            NfoType enum value
            
        Raises:
            FileError: If file doesn't exist or can't be read
            ParseError: If XML is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileError(f"File not found: {file_path}")
        
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = path.read_text(encoding='latin-1')
        except Exception as e:
            raise FileError(f"Cannot read file: {e}")
        
        return self.detect_type_from_string(content)

    def detect_type_from_string(self, xml_content: str) -> NfoType:
        """Detect NFO type from XML string.
        
        Args:
            xml_content: XML content as string
            
        Returns:
            NfoType enum value
            
        Raises:
            ParseError: If XML is invalid
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            raise ParseError(f"Invalid XML: {e}", line=e.lineno, column=e.offset)
        
        return self._detect_type_from_root(root)

    def save(self, data: NfoData, file_path: str) -> None:
        """Save NfoData to NFO file.
        
        Args:
            data: NfoData object to save
            file_path: Path to save the file
            
        Raises:
            FileError: If file can't be written
        """
        xml_content = self.format_xml(data)
        
        try:
            path = Path(file_path)
            path.write_text(xml_content, encoding='utf-8')
        except Exception as e:
            raise FileError(f"Cannot write file: {e}")

    def format_xml(self, data: NfoData) -> str:
        """Format NfoData as XML string.
        
        Args:
            data: NfoData object to format
            
        Returns:
            Formatted XML string
        """
        root = etree.Element(data.nfo_type.value)
        
        # Add simple tags
        self._add_text_element(root, 'title', data.title)
        self._add_text_element(root, 'originaltitle', data.originaltitle)
        self._add_text_element(root, 'year', data.year)
        self._add_text_element(root, 'plot', data.plot)
        self._add_text_element(root, 'runtime', data.runtime)
        self._add_text_element(root, 'studio', data.studio)
        self._add_text_element(root, 'rating', data.rating)
        
        # Add multi-value tags
        for genre in data.genres:
            self._add_text_element(root, 'genre', genre)
        
        for director in data.directors:
            self._add_text_element(root, 'director', director)
        
        # Add actors
        for actor in data.actors:
            self._add_actor_element(root, actor)
        
        # Add image paths
        self._add_text_element(root, 'poster', data.poster)
        self._add_text_element(root, 'fanart', data.fanart)
        
        # Add TV show specific fields
        if data.nfo_type in (NfoType.TVSHOW, NfoType.EPISODE):
            self._add_text_element(root, 'season', data.season)
            self._add_text_element(root, 'episode', data.episode)
            self._add_text_element(root, 'aired', data.aired)
        
        # Add extra tags (unknown tags preserved from original)
        self._add_extra_tags(root, data.extra_tags)
        
        # Format with XML declaration and indentation
        xml_str = etree.tostring(
            root,
            encoding='unicode',
            pretty_print=True,
            xml_declaration=False
        )
        
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    def _add_text_element(self, parent: etree._Element, tag: str, text: str) -> None:
        """Add a text element to parent if text is not empty."""
        if text:
            elem = etree.SubElement(parent, tag)
            elem.text = text

    def _add_actor_element(self, parent: etree._Element, actor: Actor) -> None:
        """Add actor element to parent."""
        actor_elem = etree.SubElement(parent, 'actor')
        
        name_elem = etree.SubElement(actor_elem, 'name')
        name_elem.text = actor.name
        
        if actor.role:
            role_elem = etree.SubElement(actor_elem, 'role')
            role_elem.text = actor.role
        
        if actor.thumb:
            thumb_elem = etree.SubElement(actor_elem, 'thumb')
            thumb_elem.text = actor.thumb
        
        order_elem = etree.SubElement(actor_elem, 'order')
        order_elem.text = str(actor.order)

    def _add_extra_tags(self, parent: etree._Element, extra_tags: Dict[str, Any]) -> None:
        """Add preserved unknown tags back to XML."""
        for tag, value in extra_tags.items():
            if isinstance(value, list):
                for v in value:
                    self._append_xml_string(parent, v)
            else:
                self._append_xml_string(parent, value)

    def _append_xml_string(self, parent: etree._Element, xml_str: str) -> None:
        """Append XML string as element to parent."""
        try:
            elem = etree.fromstring(xml_str.encode('utf-8'))
            parent.append(elem)
        except etree.XMLSyntaxError:
            # If parsing fails, skip this tag
            pass
