# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Main File containing the important definitions

from .idtech3lib.ID3VFS import Q3VFS
from .idtech3lib.ImportSettings import Import_Settings
from .mod_reload import reload_modules
reload_modules(locals(), __package__, ["JAG2AnimationCFG", "JAG2Constants", "JAG2GLM", "JAG2GLA"], [".error_types", ".casts"])  # nopep8

from typing import Optional, Tuple
from . import JAG2Constants
from . import JAG2AnimationCFG
from . import JAG2GLM
from . import JAG2GLA
from .error_types import ErrorMessage, NoError
from .casts import optional_cast

import bpy


def findSceneRootObject() -> Optional[bpy.types.Object]:
    return bpy.data.objects.get("scene_root", None)


class Scene:

    def __init__(self, VFS: Q3VFS, import_settings: Import_Settings):
        self.VFS = VFS
        self.import_settings = import_settings
        self.scale = 1.0
        self.glm: Optional[JAG2GLM.GLM] = None
        self.gla: Optional[JAG2GLA.GLA] = None
        self.animation_cfg: Optional[JAG2AnimationCFG.AnimationCFG] = None

    # Fills scene from on GLM file
    def loadFromGLM(self, glm_filepath: str) -> Tuple[bool, ErrorMessage]:
        self.glm = JAG2GLM.GLM()
        success, message = self.glm.loadFromFile(glm_filepath)
        if not success:
            return False, message
        return True, NoError

    # Loads animations sequences from a CFG file
    def loadFromCFG(self, cfg_filepath: str) -> Tuple[bool, ErrorMessage]:
        self.animation_cfg = JAG2AnimationCFG.AnimationCFG()
        success, message = self.animation_cfg.load_from_cfg(cfg_filepath)
        if not success:
            self.animation_cfg = None
            return False, message
        return True, message

    # Loads scene from on GLA file
    def loadFromGLA(self, gla_filepath: str, VFS: Q3VFS, loadAnimations=JAG2GLA.AnimationLoadMode.NONE, startFrame=0, numFrames=1) -> Tuple[bool, ErrorMessage]:
        # create default skeleton if necessary (doing it here is a bit of a hack)
        if gla_filepath == "*default":
            self.gla = JAG2GLA.GLA()
            self.gla.header.numBones = 1
            self.gla.isDefault = True
            return True, NoError
        self.gla = JAG2GLA.GLA()
        temp_filename = VFS.getAsFile(gla_filepath + ".gla")
        if temp_filename is None:
            return False, ErrorMessage("GLA File not found: " + gla_filepath)
        success, message = self.gla.loadFromFile(
            temp_filename, loadAnimations, startFrame, numFrames)
        if not success:
            return False, message
        return True, NoError

    # "Loads" model from Blender data
    def loadModelFromBlender(self, glm_filepath, gla_filepath):
        self.glm = JAG2GLM.GLM()
        success, message = self.glm.loadFromBlender(
            glm_filepath, gla_filepath)
        if not success:
            return False, message
        return True, ""

    # "Loads" skeleton & animation from Blender data
    def loadSkeletonFromBlender(self, gla_filepath, gla_reference_rel):
        self.gla = JAG2GLA.GLA()
        gla_reference_abs = ""
        success, message = self.gla.loadFromBlender(
            gla_filepath, gla_reference_abs)
        if not success:
            return False, message
        return True, ""

    # saves the model to a .glm file
    def saveToGLM(self, glm_filepath):
        success, message = optional_cast(JAG2GLM.GLM, self.glm).saveToFile(glm_filepath)
        if not success:
            return False, message
        return True, ""

    # saves the skeleton & animations to a .gla file
    def saveToGLA(self, glm_filepath):
        success, message = optional_cast(JAG2GLA.GLA, self.gla).saveToFile(glm_filepath)
        if not success:
            return False, message
        return True, ""

    # "saves" the scene to blender
    # skeletonFixes is an enum with possible skeleton fixes - e.g. 'JKA' for connection- and
    def saveToBlender(self, scale, skin_path, guessTextures: bool, useAnimation: bool, skeletonFixes: JAG2Constants.SkeletonFixes, shader_info: dict) -> Tuple[bool, ErrorMessage]:
        if (scene := bpy.context.scene) is None:
            return False, ErrorMessage("No active Scene")
        # is there already a scene root in blender?
        scene_root = findSceneRootObject()
        if scene_root:
            # make sure it's linked to the current scene
            if not "scene_root" in scene.collection.objects:
                scene.collection.objects.link(scene_root)
        else:
            # create it otherwise
            scene_root = bpy.data.objects.new("scene_root", None)
            scene_root.scale = (scale, scale, scale)
            scene.collection.objects.link(scene_root)
        # there's always a skeleton (even if it's *default)
        success, message = optional_cast(JAG2GLA.GLA, self.gla).saveToBlender(
            scene_root, useAnimation, skeletonFixes, self.animation_cfg)
        if not success:
            return False, message
        if self.glm:
            success, message = self.glm.saveToBlender(
                self.VFS, optional_cast(JAG2GLA.GLA, self.gla), scene_root, skin_path, guessTextures, self.import_settings, shader_info)
            if not success:
                return False, message
        return True, NoError

    # returns the relative path of the gla file referenced in the glm header
    def getRequestedGLA(self) -> str:
        return optional_cast(JAG2GLM.GLM, self.glm).getRequestedGLA()
