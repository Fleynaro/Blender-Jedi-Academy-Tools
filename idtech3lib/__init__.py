import importlib
if "ID3VFS" in locals():
    importlib.reload(ID3VFS)
if "Parsing" in locals():
    importlib.reload(Parsing)
if "ImportSettings" in locals():
    importlib.reload(ImportSettings)
if "ID3Image" in locals():
    importlib.reload(ID3Image)
if "ID3Shader" in locals():
    importlib.reload(ID3Shader)

from . import ID3Shader, ID3VFS
from . import ImportSettings, Parsing


