"""
Topic Specialist Detectors
8 specialized detectors for different content topics
"""
from typing import Dict, List, Any
import re


class BaseTopicDetector:
    """Base class for topic-specific detectors"""
    
    def __init__(self):
        self.topic_name = "base"
        self.keywords = []
    
    async def extract_content(self, gathered_content: Dict[str, Any], depth_level: int) -> Dict[str, Any]:
        """Extract topic-relevant content"""
        raise NotImplementedError
    
    async def apply_basic_filter(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Filter for surface/basic level (0-2)"""
        if "items" in content:
            content["items"] = content["items"][:5]
        return content
    
    async def apply_intermediate_filter(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Filter for intermediate/advanced level (3-4)"""
        if "items" in content:
            content["items"] = content["items"][:10]
        return content
    
    async def apply_expert_filter(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Filter for expert/academic level (5)"""
        return content
    
    async def personalize_content(self, content: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize content based on user profile"""
        return content
    
    def calculate_confidence(self, content: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        if not content or "items" not in content:
            return 0.0
        items = content["items"]
        if not items:
            return 0.0
        item_count = len(items)
        has_details = sum(1 for item in items if len(str(item)) > 100)
        confidence = min((item_count / 10.0) * 0.5 + (has_details / item_count) * 0.5, 1.0)
        return confidence
    
    def _extract_text(self, content: Dict[str, Any]) -> str:
        """Extract all text from content"""
        text_parts = []
        for key, value in content.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                text_parts.extend([str(v) for v in value if isinstance(v, str)])
        return " ".join(text_parts)


class HistoricalContentDetector(BaseTopicDetector):
    """Historical content specialist"""
    
    def __init__(self):
        super().__init__()
        self.topic_name = "history"
        self.keywords = ["historical", "ancient", "medieval", "century", "heritage"]
    
    async def extract_content(self, gathered_content: Dict[str, Any], depth_level: int) -> Dict[str, Any]:
        text = self._extract_text(gathered_content)
        items = []
        
        # Extract periods
        period_patterns = [r"(\d{1,4})\s*(AD|BC|BCE|CE)", r"(ancient|medieval|modern)"]
        for pattern in period_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                items.append({"type": "periods", "content": matches[:5], "relevance": 0.9})
                break
        
        # Extract events
        event_keywords = ["battle", "founded", "built", "established"]
        events = []
        for keyword in event_keywords:
            if keyword in text.lower():
                pattern = rf"(.{{0,60}}{keyword}.{{0,60}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                events.extend([m.strip() for m in matches[:2]])
        if events:
            items.append({"type": "events", "content": events[:8], "relevance": 0.85})
        
        return {"items": items, "depth_level": depth_level, "keyword_matches": sum(1 for kw in self.keywords if kw in text.lower())}


class CulturalContentDetector(BaseTopicDetector):
    """Cultural content specialist"""
    
    def __init__(self):
        super().__init__()
        self.topic_name = "culture"
        self.keywords = ["cultural", "tradition", "ritual", "festival", "custom"]
    
    async def extract_content(self, gathered_content: Dict[str, Any], depth_level: int) -> Dict[str, Any]:
        text = self._extract_text(gathered_content)
        items = []
        
        # Extract traditions
        tradition_pattern = r"(traditional|tradition).{0,80}"
        matches = re.findall(tradition_pattern, text, re.IGNORECASE)
        if matches:
            items.append({"type": "traditions", "content": [m.strip() for m in matches[:5]], "relevance": 0.9})
        
        # Extract festivals
        festival_keywords = ["festival", "celebration", "ceremony"]
        festivals = []
        for keyword in festival_keywords:
            if keyword in text.lower():
                pattern = rf"(.{{0,50}}{keyword}.{{0,50}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                festivals.extend([m.strip() for m in matches[:2]])
        if festivals:
            items.append({"type": "festivals", "content": festivals[:6], "relevance": 0.85})
        
        return {"items": items, "depth_level": depth_level, "keyword_matches": sum(1 for kw in self.keywords if kw in text.lower())}


class ArchitecturalContentDetector(BaseTopicDetector):
    """Architectural content specialist"""
    
    def __init__(self):
        super().__init__()
        self.topic_name = "architecture"
        self.keywords = ["architecture", "building", "structure", "monument", "design"]
    
    async def extract_content(self, gathered_content: Dict[str, Any], depth_level: int) -> Dict[str, Any]:
        text = self._extract_text(gathered_content)
        items = []
        
        # Extract styles
        style_keywords = ["gothic", "baroque", "moorish", "islamic", "colonial"]
        styles = [style for style in style_keywords if style in text.lower()]
        if styles:
            items.append({"type": "styles", "content": styles, "relevance": 0.9})
        
        # Extract materials
        material_keywords = ["stone", "marble", "wood", "brick", "tile"]
        materials = [mat for mat in material_keywords if mat in text.lower()]
        if materials:
            items.append({"type": "materials", "content": materials, "relevance": 0.8})
        
        return {"items": items, "depth_level": depth_level, "keyword_matches": sum(1 for kw in self.keywords if kw in text.lower())}


class NatureContentDetector(BaseTopicDetector):
    """Nature content specialist"""
    
    def __init__(self):
        super().__init__()
        self.topic_name = "nature"
        self.keywords = ["nature", "wildlife", "ecosystem", "flora", "fauna"]
    
    async def extract_content(self, gathered_content: Dict[str, Any], depth_level: int) -> Dict[str, Any]:
        text = self._extract_text(gathered_content)
        items = []
        
        # Extract species
        species_keywords = ["species", "bird", "animal", "plant", "endemic"]
        species = []
        for keyword in species_keywords:
            if keyword in text.lower():
                pattern = rf"(.{{0,40}}{keyword}.{{0,40}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                species.extend([m.strip() for m in matches[:2]])
        if species:
            items.append({"type": "species", "content": species[:8], "relevance": 0.9})
        
        # Extract ecosystems
        ecosystem_keywords = ["forest", "desert", "mountain", "wetland", "coastal"]
        ecosystems = [eco for eco in ecosystem_keywords if eco in text.lower()]
        if ecosystems:
            items.append({"type": "ecosystems", "content": ecosystems, "relevance": 0.85})
        
        return {"items": items, "depth_level": depth_level, "keyword_matches": sum(1 for kw in self.keywords if kw in text.lower())}


class CulinaryContentDetector(BaseTopicDetector):
    """Culinary content specialist"""
    
    def __init__(self):
        super().__init__()
        self.topic_name = "food"
        self.keywords = ["food", "cuisine", "dish", "recipe", "culinary"]
    
    async def extract_content(self, gathered_content: Dict[str, Any], depth_level: int) -> Dict[str, Any]:
        text = self._extract_text(gathered_content)
        items = []
        
        # Extract dishes
        dish_pattern = r"(traditional|local|famous) (dish|food|cuisine).{0,50}"
        matches = re.findall(dish_pattern, text, re.IGNORECASE)
        if matches:
            items.append({"type": "dishes", "content": [f"{m[1]} {m[0]}" for m in matches[:5]], "relevance": 0.9})
        
        # Extract ingredients
        ingredient_keywords = ["spice", "herb", "olive", "saffron", "lamb"]
        ingredients = [ing for ing in ingredient_keywords if ing in text.lower()]
        if ingredients:
            items.append({"type": "ingredients", "content": ingredients, "relevance": 0.8})
        
        return {"items": items, "depth_level": depth_level, "keyword_matches": sum(1 for kw in self.keywords if kw in text.lower())}


class ArtsContentDetector(BaseTopicDetector):
    """Arts content specialist"""
    
    def __init__(self):
        super().__init__()
        self.topic_name = "arts"
        self.keywords = ["art", "artist", "painting", "sculpture", "craft"]
    
    async def extract_content(self, gathered_content: Dict[str, Any], depth_level: int) -> Dict[str, Any]:
        text = self._extract_text(gathered_content)
        items = []
        
        # Extract art forms
        art_form_keywords = ["painting", "sculpture", "pottery", "mosaic", "calligraphy"]
        art_forms = [form for form in art_form_keywords if form in text.lower()]
        if art_forms:
            items.append({"type": "art_forms", "content": art_forms, "relevance": 0.9})
        
        # Extract techniques
        technique_keywords = ["fresco", "glazing", "carving", "weaving"]
        techniques = [tech for tech in technique_keywords if tech in text.lower()]
        if techniques:
            items.append({"type": "techniques", "content": techniques, "relevance": 0.8})
        
        return {"items": items, "depth_level": depth_level, "keyword_matches": sum(1 for kw in self.keywords if kw in text.lower())}


class ScientificContentDetector(BaseTopicDetector):
    """Scientific content specialist"""
    
    def __init__(self):
        super().__init__()
        self.topic_name = "science"
        self.keywords = ["scientific", "research", "discovery", "phenomenon", "study"]
    
    async def extract_content(self, gathered_content: Dict[str, Any], depth_level: int) -> Dict[str, Any]:
        text = self._extract_text(gathered_content)
        items = []
        
        # Extract discoveries
        discovery_pattern = r"(discovered|found|revealed).{0,60}"
        matches = re.findall(discovery_pattern, text, re.IGNORECASE)
        if matches:
            items.append({"type": "discoveries", "content": [m.strip() for m in matches[:5]], "relevance": 0.9})
        
        # Extract phenomena
        phenomena_keywords = ["phenomenon", "geological", "biological", "chemical"]
        phenomena = []
        for keyword in phenomena_keywords:
            if keyword in text.lower():
                pattern = rf"(.{{0,50}}{keyword}.{{0,50}})"
                matches = re.findall(pattern, text, re.IGNORECASE)
                phenomena.extend([m.strip() for m in matches[:2]])
        if phenomena:
            items.append({"type": "phenomena", "content": phenomena[:6], "relevance": 0.85})
        
        return {"items": items, "depth_level": depth_level, "keyword_matches": sum(1 for kw in self.keywords if kw in text.lower())}


class FolkloreContentDetector(BaseTopicDetector):
    """Folklore content specialist"""
    
    def __init__(self):
        super().__init__()
        self.topic_name = "folklore"
        self.keywords = ["folklore", "legend", "myth", "tale", "supernatural"]
    
    async def extract_content(self, gathered_content: Dict[str, Any], depth_level: int) -> Dict[str, Any]:
        text = self._extract_text(gathered_content)
        items = []
        
        # Extract legends
        legend_pattern = r"(legend|legendary|tale).{0,80}"
        matches = re.findall(legend_pattern, text, re.IGNORECASE)
        if matches:
            items.append({"type": "legends", "content": [m.strip() for m in matches[:5]], "relevance": 0.9})
        
        # Extract supernatural elements
        supernatural_keywords = ["spirit", "ghost", "magical", "mystical", "enchanted"]
        supernatural = [elem for elem in supernatural_keywords if elem in text.lower()]
        if supernatural:
            items.append({"type": "supernatural", "content": supernatural, "relevance": 0.8})
        
        return {"items": items, "depth_level": depth_level, "keyword_matches": sum(1 for kw in self.keywords if kw in text.lower())}
