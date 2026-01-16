"""Template file I/O operations for NFO Editor.

Handles saving and loading templates to/from JSON files.
"""
import json
from pathlib import Path
from typing import List, Optional

from nfo_editor.models.template import NfoTemplate
from nfo_editor.utils.exceptions import FileError


def get_templates_directory() -> Path:
    """Get the default templates directory.
    
    Creates the directory if it doesn't exist.
    
    Returns:
        Path to templates directory
    """
    # Use user's home directory for templates
    templates_dir = Path.home() / ".nfo_editor" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    return templates_dir


def save_template(template: NfoTemplate, file_path: Optional[str] = None) -> str:
    """Save a template to a JSON file.
    
    Args:
        template: Template to save
        file_path: Optional file path; if None, saves to default directory
        
    Returns:
        Path where template was saved
        
    Raises:
        FileError: If save fails
    """
    if file_path is None:
        # Generate filename from template name
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in template.name)
        file_path = str(get_templates_directory() / f"{safe_name}.json")
    
    try:
        data = template.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path
    except Exception as e:
        raise FileError(f"Failed to save template: {e}")


def load_template(file_path: str) -> NfoTemplate:
    """Load a template from a JSON file.
    
    Args:
        file_path: Path to template file
        
    Returns:
        Loaded NfoTemplate
        
    Raises:
        FileError: If load fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return NfoTemplate.from_dict(data)
    except json.JSONDecodeError as e:
        raise FileError(f"Invalid template file format: {e}")
    except Exception as e:
        raise FileError(f"Failed to load template: {e}")


def list_templates() -> List[NfoTemplate]:
    """List all templates in the default directory.
    
    Returns:
        List of NfoTemplate objects
    """
    templates = []
    templates_dir = get_templates_directory()
    
    for file_path in templates_dir.glob("*.json"):
        try:
            template = load_template(str(file_path))
            templates.append(template)
        except FileError:
            # Skip invalid template files
            continue
    
    return sorted(templates, key=lambda t: t.name.lower())


def delete_template(template_name: str) -> bool:
    """Delete a template by name.
    
    Args:
        template_name: Name of template to delete
        
    Returns:
        True if deleted, False if not found
    """
    templates_dir = get_templates_directory()
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in template_name)
    file_path = templates_dir / f"{safe_name}.json"
    
    if file_path.exists():
        file_path.unlink()
        return True
    
    # Try to find by iterating (in case name was modified)
    for fp in templates_dir.glob("*.json"):
        try:
            template = load_template(str(fp))
            if template.name == template_name:
                fp.unlink()
                return True
        except FileError:
            continue
    
    return False


def export_template(template: NfoTemplate, file_path: str) -> None:
    """Export a template to a specific file path.
    
    Args:
        template: Template to export
        file_path: Destination file path
        
    Raises:
        FileError: If export fails
    """
    save_template(template, file_path)


def import_template(file_path: str) -> NfoTemplate:
    """Import a template from a file and save to default directory.
    
    Args:
        file_path: Source file path
        
    Returns:
        Imported NfoTemplate
        
    Raises:
        FileError: If import fails
    """
    template = load_template(file_path)
    save_template(template)  # Save to default directory
    return template
