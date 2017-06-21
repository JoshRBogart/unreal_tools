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

bl_info = {
    "name": "Mesh Morpher",
    "author": "Joshua Bogart",
    "version": (1, 0),
    "blender": (2, 78, 0),
    "location": "View3D > Tool Shelf > Unreal Tools",
    "description": "Based on the 3ds Max script created by Jonathan Lindquist at Epic Games for use in conjunction with Unreal Engine 4",
    "warning": "This script stores data in a meshes UV layers and Vertex Colors. If storing 2 shape keys or 1 and the object's pivot location UV layers 2-4 will be overwritten while preserving layer 1, 4 or higher."
    "If not storing either 2 shape keys or the object's pivot location layer 2 will also be preserved. If storing morph 2 normals object's vertex color layer will be overwritten",
    "wiki_url": "",
    "category": "Unreal Tools",
    }

import bpy
import mathutils
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import BoolProperty, PointerProperty
from mathutils import Vector

#get shape key vertex offsets
def buildOffsetList(obj, props):
    offsetList = []
    
    originalVertPos = [v.co for v in obj.data.shape_keys.key_blocks[0].data]
    targetVertPos1 = [v.co for v in obj.data.shape_keys.key_blocks[1].data]  
    vertOffset1 = [targetVertPos1[i] - originalVertPos[i] for i in range(len(originalVertPos))]
    offsetList.append(vertOffset1)
    
    if props.store_pivot_location == False and len(obj.data.shape_keys.key_blocks) > 2:
        targetVertPos2 = [v.co for v in obj.data.shape_keys.key_blocks[2].data]
        vertOffset2 = [targetVertPos2[i] - originalVertPos[i] for i in range(len(originalVertPos))]
        offsetList.append(vertOffset2)
        
    else:
        vertOffset2 = [obj.location for i in range(len(originalVertPos))]
        offsetList.append(vertOffset2)
    
    return offsetList

#store normals in vertex colors
def packVertexColors(obj):
    
    morphNormals = [i for i in zip(*(iter(obj.data.shape_keys.key_blocks[1].normals_vertex_get()),)*3)]
    
    for id, normal in enumerate(morphNormals):
        currentNormal = normal
        currentNormal = ((currentNormal[0] + 1.0) * 0.5, ((currentNormal[1] * -1.0) + 1.0) * 0.5, (currentNormal[2] + 1.0) * 0.5)
        morphNormals[id] = currentNormal
    
    while len(obj.data.vertex_colors) < 1:
        obj.data.vertex_colors.new()
        
    for poly in obj.data.polygons:
        
        for vertId, loopId in zip(poly.vertices, poly.loop_indices):
            obj.data.vertex_colors[0].data[loopId].color = morphNormals[vertId]

#store offsets in UVs
def packUVs(obj, offsetList, props):
    vertOffset1 = offsetList[0]
    
    if props.store_pivot_location == True or len(obj.data.shape_keys.key_blocks) > 2:
        vertOffset2 = offsetList[1]
    
    while len(obj.data.uv_layers.items()) < 4:
        obj.data.uv_textures.new()
    
    for poly in obj.data.polygons:
    
        for vertId, loopId in zip(poly.vertices, poly.loop_indices):
            
            if props.store_pivot_location == True or len(obj.data.shape_keys.key_blocks) > 2:
                obj.data.uv_layers[1].data[loopId].uv = (vertOffset2[vertId][0], 1.0 - (vertOffset2[vertId][1] * -1.0))
                obj.data.uv_layers[2].data[loopId].uv = (vertOffset2[vertId][2], 1.0 - vertOffset1[vertId][0])
                obj.data.uv_layers[3].data[loopId].uv = (vertOffset1[vertId][1] * -1.0, 1.0 - vertOffset1[vertId][2])
                
            else:
                obj.data.uv_layers[2].data[loopId].uv = (0.0, 1.0 - vertOffset1[vertId][0])
                obj.data.uv_layers[3].data[loopId].uv = (vertOffset1[vertId][1] * -1.0, 1.0 - vertOffset1[vertId][2])
    
#called by operator on UI panel
def main(context):
    obj = context.object
    props = context.scene.mesh_morpher_properties
    
    offsetList = buildOffsetList(obj, props)
    packUVs(obj, offsetList, props)
    
    if props.store_morph1_normals == True:
        packVertexColors(obj)

#create property group for user options
class UT_MeshMorpherProperties(PropertyGroup):
    store_morph1_normals = BoolProperty(name = "Store Morph 1 Normals")
    store_pivot_location = BoolProperty(name = "Store Pivot Location")
        
#create operator class for panel button
class UT_PackMorphTargetsOperator(Operator):
    bl_label = "Pack Morph Targets"
    bl_idname = "unreal_tools.pack_morph_targets"
    
    @classmethod
    def poll(cls, context):
        c = context
        
        return  len(c.selected_objects) > 0 and c.active_object.type == 'MESH' and c.mode == 'OBJECT'

    def execute(self, context):
        units = context.scene.unit_settings
        
        if units.system != 'METRIC' or round(units.scale_length, 2) != 0.01:
            
            self.report({'ERROR'}, "Scene units must be Metric with a Unit Scale of 0.01!")
            
            return {'CANCELLED'}
        
        elif not context.object.data.shape_keys or len(context.object.data.shape_keys.key_blocks) < 2:
            
            self.report({'ERROR'}, "Object needs additional shape keys!")
            
            return {'CANCELLED'}
        
        else:
            main(context)
            
            return {'FINISHED'}
        
#create panel class for UI in object mode tool shelf
class UT_MeshMorpherPanel(Panel):
    bl_label = "Mesh Morpher"
    bl_idname = "ut_mesh_morpher_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Unreal Tools"
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
      
        col = layout.column(align = True)
        col.prop(scene.mesh_morpher_properties, "store_morph1_normals")
        col.prop(scene.mesh_morpher_properties, "store_pivot_location")

        row = layout.row()
        row.scale_y = 1.5
        row.operator("unreal_tools.pack_morph_targets")

#create register functions for adding and removing script          
def register():
    bpy.utils.register_class(UT_MeshMorpherPanel)
    bpy.utils.register_class(UT_PackMorphTargetsOperator)
    bpy.utils.register_class(UT_MeshMorpherProperties)
    bpy.types.Scene.mesh_morpher_properties = PointerProperty(type = UT_MeshMorpherProperties)
    
def unregister():
    bpy.utils.unregister_class(UT_MeshMorpherPanel)
    bpy.utils.unregister_class(UT_PackMorphTargetsOperator)
    bpy.utils.unregister_class(UT_MeshMorpherProperties)
    del bpy.types.Scene.unreal_tools.mesh_morpher_properties
    
if __name__ == "__main__":
    register()
