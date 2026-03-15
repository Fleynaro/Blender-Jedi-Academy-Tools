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

from .QuakeShader import create_white_image, quake_shader
from .idtech3lib.ImportSettings import Import_Settings
from .idtech3lib.ID3VFS import Q3VFS
from .mod_reload import reload_modules
reload_modules(locals(), __package__, ["QuakeShader", "JAStringhelper"], [".casts", ".error_types"])  # nopep8

from typing import Optional, Tuple
from . import JAStringhelper
from .casts import downcast, optional_cast
from .error_types import ErrorMessage, NoError

import bpy

class MaterialManager():
    def __init__(self):
        self.VFS = None
        self.import_settings = None
        self.guessTextures = False
        self.shader_info = dict()
        self.useSkin = False
        self.initialized = False

    def init(self, VFS: Q3VFS, import_settings: Import_Settings, skin_path: str, guessTextures: bool, shader_info: dict) -> Tuple[bool, ErrorMessage]:
        self.VFS = VFS
        self.import_settings = import_settings
        self.guessTextures = guessTextures
        self.shader_info = shader_info
        if skin_path != "":
            try:
                file = open(skin_path, mode="r")
            except IOError:
                print("Could not open file: ", skin_path, sep="")
                return False, ErrorMessage("Could not open skin!")
            self.skin = {}
            for line in file:
                pos = line.find(',')
                if pos != -1:
                    self.skin[line[:pos].strip()] = line[pos + 1:].strip()
            self.useSkin = True
        self.initialized = True
        return True, NoError

    def getMaterial(self, name, bsShader):
        assert (self.initialized and self.VFS and self.import_settings)
        # "fix" removed textures (which should force using .skin file)
        if self.guessTextures:
            # I don't need to fix nomaterial - empty materials don't get loaded anyway.
            # if bsShader[:12] == b"\0nomaterial]":
            # bsShader = b""
            if bsShader[:7] == b"\0odels/":
                bsShader = b"models/" + bsShader[7:]
        shader = JAStringhelper.decode(bsShader)
        if self.useSkin:
            if name in self.skin:
                shader = self.skin[name]
        shader = shader.lower()
        if shader == "[nomaterial]" or shader == "" or shader == "*off":
            return None
        shader = shader.split(".")[0] # remove extension
        
        mat = bpy.data.materials.get(shader)
        if mat is None:
            mat = bpy.data.materials.new(shader)

        # make sure the $whiteimage is loaded
        create_white_image()

        qs = quake_shader(shader, mat)
        #print("*** shader: ", shader)
        qs.set_grid_lit()
        if shader in self.shader_info:
            attributes, stages = self.shader_info[shader]
            #print("------ attributes: ", attributes)
            #print("------ stages: ", stages)
            if ("surfaceparm" in attributes and
            "nodraw" in attributes["surfaceparm"]):
                qs.is_system_shader = True
            qs.attributes = attributes
            if qs.mat is not None:
                if "first_line" in attributes:
                    qs.mat["first_line"] = attributes["first_line"]
                if "shader_file" in attributes:
                    qs.mat["shader_file"] = attributes["shader_file"]
            for stage in stages:
                qs.add_stage(stage)
        qs.finish_shader(self.VFS, self.import_settings)
        return mat
