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
    "name": "Vertex Animation",
    "author": "Joshua Bogart",
    "version": (1, 0),
    "blender": (2, 78, 0),
    "location": "View3D > Tool Shelf > Unreal Tools",
    "description": "Based on the 3ds Max script created by Jonathan Lindquist at Epic Games for use in conjunction with Unreal Engine 4",
    "warning": "Remember to keep vertex and frame count low neither should go above 8192",
    "wiki_url": "",
    "category": "Unreal Tools",
    }

import bpy
import bmesh
import mathutils
from bpy.types import Operator, Panel
from mathutils import Vector

#gets mesh data from an object in world coordinates with modifiers and transforms applied
def copyMeshData(data, object, newBmesh, scene):
    meshData = object.to_mesh(scene, True, 'PREVIEW')
    
    for vert in meshData.vertices:
        vert.co = object.matrix_world * vert.co
    
    newBmesh.from_mesh(meshData)
    data.meshes.remove(meshData)
    
    return newBmesh

#creates a list of combined mesh data per frame from selected objects
def buildMorphList(data, selectedObjects, scene):
    morphList = []
    
    for frame in range(scene.frame_start, scene.frame_end + 1, scene.frame_step):
        scene.frame_set(frame)
        newBmesh = bmesh.new()
        
        for object in selectedObjects:
            
            if object.type == 'MESH':
                copyMeshData(data, object, newBmesh, scene)
        
        newMesh = data.meshes.new("mesh")
        newBmesh.to_mesh(newMesh)
        newBmesh.free()
        newMesh.calc_normals()
        newMorph = data.objects.new("morph", newMesh) 
        morphList.append(newMorph)
        
    return morphList

#packs UVs for export mesh evenly spacing verts across V axis
def packUVs(mesh):
    numVerts = len(mesh.data.vertices)
    
    while len(mesh.data.uv_layers.items()) < 2:
        mesh.data.uv_textures.new()
        
    for poly in mesh.data.polygons:
        
        for vertId, loopId in zip(poly.vertices, poly.loop_indices):
            currentPos = ((1.0 - (vertId + 0.5)/numVerts))
            mesh.data.uv_layers[1].data[loopId].uv = (currentPos, (1/255) * 128)

#create mesh to export from mesh data taken on the first frame
def generateExportMesh(data, morphList, scene):
    exportMesh = morphList[0].copy()
    exportMesh.name = "Export_Mesh"
    scene.objects.link(exportMesh)
    
    return exportMesh

#stores offsets for vertex coordinates and normals in world space from the morphList
def buildMorphData(data, morphList):
    offsetVertPos = []
    morphNormals = []
    offsetValues = []
    normalValues = []
    morphData = []
    
    originalVertPos = [morphList[0].matrix_world * vert.co for vert in morphList[0].data.vertices]
    
    for morph in morphList:
        
        for i in range(len(morph.data.vertices)):
            currentNormal = morph.data.vertices[i].normal * morph.matrix_world
            currentNormal = Vector([(currentNormal[0] + 1.0) * 0.5, ((currentNormal[1] * -1.0) + 1.0) * 0.5, (currentNormal[2] + 1.0) * 0.5])
            morphNormals.append(currentNormal)
            currentVertPos = (morph.matrix_world * morph.data.vertices[i].co) - originalVertPos[i]
            currentVertPos = Vector([currentVertPos[0], -1.0 * currentVertPos[1], currentVertPos[2]])
            offsetVertPos.append((currentVertPos) * 100.0)

        data.objects.remove(morph)

    for mesh in data.meshes:
        if mesh.users == 0:
            data.meshes.remove(mesh)

    morphNormals.reverse()
    offsetVertPos.reverse()
    
    for i in range(len(morphNormals)):
        
        for idx in morphNormals[i]:
            normalValues.append(idx)
        
        normalValues.append(1.0)
        
        for idx in offsetVertPos[i]:
            offsetValues.append(idx)
        
        offsetValues.append(1.0)
    
    morphData = [offsetValues, normalValues]
    
    return morphData
    
#create textures from morphData
def bakeMorphData(data, exportMesh, scene, morphData):
    size = [len(exportMesh.data.vertices), len(range(scene.frame_start, scene.frame_end + 1, scene.frame_step))]
    morphs = morphData[0]
    normals = morphData[1]
    
    morphTexture = data.images.new(name = "morphs", width = size[0], height = size[1], alpha = True, float_buffer = True)
    normalTexture = data.images.new(name = "normals", width = size[0], height = size[1], alpha = True)
    
    morphTexture.pixels = morphs
    normalTexture.pixels = normals

#called by operator on UI panel            
def main(context):
    scene = context.scene
    data = bpy.data
    selectedObjects = context.selected_objects
    
    morphList = buildMorphList(data, selectedObjects, scene)    
    exportMesh = generateExportMesh(data, morphList, scene)
    packUVs(exportMesh)
    morphData = buildMorphData(data, morphList)
    bakeMorphData(data, exportMesh, scene, morphData)

#create operator class for panel button    
class UT_ProcessMeshesOperator(Operator):
    bl_label = "Process Animated Meshes"
    bl_idname = "unreal_tools.process_anim_meshes"
    
    @classmethod
    def poll(cls, context):
        return True in [object.type == 'MESH' for object in context.selected_objects] and context.mode == 'OBJECT'
    
    def execute(self, context):
        units = context.scene.unit_settings
        
        if units.system != 'METRIC' or units.scale_length != 1.0:
            
            self.report({'ERROR'}, "Scene units must be Metric with a Unit Scale of 1!")
        
            return {'CANCELLED'}
                        
        else:
            main(context)
            
            return {'FINISHED'}

#create panel class for UI in object mode tool shelf
class UT_VertexAnimPanel(Panel):
    bl_label = "Vertex Animation"
    bl_idname = "ut_vertex_anim_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Unreal Tools"
    bl_context = "objectmode"
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
               
        col = layout.column(align = True)
        col.prop(scene, "frame_start")
        col.prop(scene, "frame_end")
        col.prop(scene, "frame_step")
        
        row = layout.row()
        row.scale_y = 1.5
        row.operator("unreal_tools.process_anim_meshes")

#create register functions for adding and removing script          
def register():
    bpy.utils.register_class(UT_VertexAnimPanel)
    bpy.utils.register_class(UT_ProcessMeshesOperator)
    
def unregister():
    bpy.utils.unregister_class(UT_VertexAnimPanel)
    bpy.utils.unregister_class(UT_ProcessMeshesOperator)
    
if __name__ == "__main__":
    register()
