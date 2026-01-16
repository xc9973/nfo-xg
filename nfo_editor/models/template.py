"""NFO Template model."""
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class NfoTemplate:
    """NFO template for quick creation."""
    name: str
    nfo_type: str = "movie"
    genres: List[str] = field(default_factory=list)
    directors: List[str] = field(default_factory=list)
    studio: str = ""
    # 可以预设更多字段
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NfoTemplate":
        return cls(**data)


class TemplateManager:
    """Manage NFO templates."""
    
    def __init__(self, config_path: str = "templates.json"):
        self.config_path = Path(config_path)
        self.templates: Dict[str, NfoTemplate] = {}
        self.load()
    
    def load(self) -> None:
        """Load templates from config file."""
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding='utf-8'))
                self.templates = {
                    name: NfoTemplate.from_dict(t) 
                    for name, t in data.items()
                }
            except (json.JSONDecodeError, KeyError):
                self.templates = {}
    
    def save(self) -> None:
        """Save templates to config file."""
        data = {name: t.to_dict() for name, t in self.templates.items()}
        self.config_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
    
    def add(self, template: NfoTemplate) -> None:
        """Add or update a template."""
        self.templates[template.name] = template
        self.save()
    
    def delete(self, name: str) -> bool:
        """Delete a template."""
        if name in self.templates:
            del self.templates[name]
            self.save()
            return True
        return False
    
    def get(self, name: str) -> Optional[NfoTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def list_all(self) -> List[NfoTemplate]:
        """List all templates."""
        return list(self.templates.values())
