from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple

class Preset(Enum):
    PREVIEW = "PREVIEW"
    RENDERING = "RENDERING"

class NormalMapOption(Enum):
    OPENGL = "OPENGL"
    DIRECTX = "DIRECTX"
    SKIP = "SKIP"

@dataclass
class Import_Settings:
    base_paths: List[str] = field(default_factory=list)
    shader_dirs: Tuple[str] = ("shaders/", "scripts/") # type: ignore
    preset: Preset = Preset.RENDERING
    normal_map_option: NormalMapOption = NormalMapOption.DIRECTX
    allLODs: bool = False
