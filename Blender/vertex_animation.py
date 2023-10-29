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

# <pep8 compliant>


bl_info = {
    "name": "Vertex Animation",
    "author": "Mate Steinforth.",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "View3D > Sidebar > Spark AR VAT Tab",
    "description": "A tool for storing per frame vertex data for use in a vertex shader. Original code by Joshua Bogart.",
    "warning": "",
    "doc_url": "",
    "category": "Spark AR VAT",
}

import bpy
import bmesh
import mathutils

def get_per_frame_mesh_data(context, data, objects):
    """Return a list of combined mesh data per frame"""
    meshes = []
    for i in frame_range(context.scene):
        context.scene.frame_set(i)
        depsgraph = context.evaluated_depsgraph_get()
        bm = bmesh.new()
        for ob in objects:
            eval_object = ob.evaluated_get(depsgraph)
            me = data.meshes.new_from_object(eval_object)
            me.transform(ob.matrix_world)
            bm.from_mesh(me)
            data.meshes.remove(me)
        me = data.meshes.new("mesh")
        bm.to_mesh(me)
        bm.free()
        me.calc_normals()
        meshes.append(me)
    return meshes


def export_mesh(context, obj, name):
    if obj.name not in bpy.context.view_layer.objects:
        bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    output_dir = bpy.path.abspath(context.scene.output_dir) + name + ".fbx"

    bpy.ops.export_scene.fbx(filepath=output_dir, use_selection=True, apply_unit_scale=False, use_space_transform=False, apply_scale_options='FBX_SCALE_ALL')

    # Delete the mesh after saving
    bpy.ops.object.delete()


def create_export_mesh_object(context, data, me):
    """Return a mesh object with correct UVs"""
    while len(me.uv_layers) < 2:
        me.uv_layers.new()
    uv_layer = me.uv_layers[1]
    uv_layer.name = "vertex_anim"
    for loop in me.loops:
        uv_layer.data[loop.index].uv = (
            (loop.vertex_index + 0.5)/len(me.vertices), 128/255
        )
    ob = data.objects.new("export_mesh", me)
    context.scene.collection.objects.link(ob)
    return ob


def get_vertex_data(data, meshes):
    """Return lists of vertex offsets and normals from a list of mesh data"""
    original = meshes[0].vertices
    offsets = []
    normals = []
    for me in reversed(meshes):
        for v in me.vertices:
            offset = v.co - original[v.index].co
            x, y, z = offset
            offsets.extend(((x + 1) * 0.5, (- y + 1) * 0.5, (z + 1) * 0.5, 1))
            x, y, z = v.normal
            normals.extend(((x + 1) * 0.5, (y + 1) * 0.5, (z + 1) * 0.5, 1))
        if not me.users:
            data.meshes.remove(me)
    return offsets, normals



def frame_range(scene):
    """Return a range object with with scene's frame start, end, and step"""
    return range(scene.frame_start, scene.frame_end, scene.frame_step)


def bake_vertex_data(context, data, offsets, normals, size, name):
    """Stores vertex offsets and normals in seperate image textures"""
    width, height = size
    output_dir = bpy.path.abspath(context.scene.output_dir)
    write_output_image(offsets, name + "_position", size, output_dir)
    write_output_image(normals, name + "_normal", size, output_dir)


def float_to_bytes(float_value):
    """ Convert a float in range [0, 1] to high and low bytes. """
    int_value = int(float_value * 65535)
    high_byte = (int_value >> 8) & 0xFF
    low_byte = int_value & 0xFF
    return high_byte, low_byte


def write_output_image(pixel_list, name, size, output_dir):
    # Convert the pixel list to high and low bytes
    high_bytes_list = []
    low_bytes_list = []

    for pixel in pixel_list:
        high_byte, low_byte = float_to_bytes(pixel)
        high_bytes_list.append(high_byte / 255.0)
        low_bytes_list.append(low_byte / 255.0)

    # Create and save high byte image
    high_image = bpy.data.images.new(name + "_high", width=size[0], height=size[1])
    high_image.pixels = high_bytes_list
    high_image.save_render(output_dir + name + "_high.png", scene=bpy.context.scene)

    # Create and save low byte image
    low_image = bpy.data.images.new(name + "_low", width=size[0], height=size[1])
    low_image.pixels = low_bytes_list
    low_image.save_render(output_dir + name + "_low.png", scene=bpy.context.scene)


class OBJECT_OT_ProcessAnimMeshes(bpy.types.Operator):
    """Store combined per frame vertex offsets and normals for all
    selected mesh objects into seperate image textures"""
    bl_idname = "object.process_anim_meshes"
    bl_label = "Process Anim Meshes"

    @property
    def allowed_modifiers(self):
        return [
            'ARMATURE', 'CAST', 'CURVE', 'DISPLACE', 'HOOK',
            'LAPLACIANDEFORM', 'LATTICE', 'MESH_DEFORM', 'MESH_SEQUENCE_CACHE',
            'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH',
            'CORRECTIVE_SMOOTH', 'LAPLACIANSMOOTH',
            'SURFACE_DEFORM', 'WARP', 'WAVE',
        ]

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and ob.mode == 'OBJECT'

    def execute(self, context):
        units = context.scene.unit_settings
        data = bpy.data
        objects = [ob for ob in context.selected_objects if ob.type == 'MESH']
        vertex_count = sum([len(ob.data.vertices) for ob in objects])
        frame_count = len(frame_range(context.scene))
        for ob in objects:
            for mod in ob.modifiers:
                if mod.type not in self.allowed_modifiers:
                    self.report(
                        {'ERROR'},
                        f"Objects with {mod.type.title()} modifiers are not allowed!"
                    )
                    return {'CANCELLED'}
        if units.system != 'METRIC' or round(units.scale_length, 2) != 0.01:
            self.report(
                {'ERROR'},
                "Scene Unit must be Metric with a Unit Scale of 0.01!"
            )
            return {'CANCELLED'}
        if vertex_count > 8192:
            self.report(
                {'ERROR'},
                f"Vertex count of {vertex_count :,}, execedes limit of 8,192!"
            )
            return {'CANCELLED'}
        if frame_count > 8192:
            self.report(
                {'ERROR'},
                f"Frame count of {frame_count :,}, execedes limit of 8,192!"
            )
            return {'CANCELLED'}
        myname = bpy.context.active_object.name
        meshes = get_per_frame_mesh_data(context, data, objects)
        export_mesh_data = meshes[0].copy()
        obj = create_export_mesh_object(context, data, export_mesh_data)
        offsets, normals = get_vertex_data(data, meshes)
        texture_size = vertex_count, frame_count
        bake_vertex_data(context, data, offsets, normals, texture_size, myname)
        export_mesh(context, obj, myname)
        return {'FINISHED'}


class VIEW3D_PT_VertexAnimation(bpy.types.Panel):
    """Creates a Panel in 3D Viewport"""
    bl_label = "Vertex Animation"
    bl_idname = "VIEW3D_PT_vertex_animation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Spark AR VAT"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene
        col = layout.column(align=True)
        col.prop(scene, "frame_start", text="Frame Start")
        col.prop(scene, "frame_end", text="End")
        col.prop(scene, "frame_step", text="Step")
        col.prop(scene, "output_dir", text="Output Directory")
        row = layout.row()
        row.operator("object.process_anim_meshes")


def register():
    bpy.utils.register_class(OBJECT_OT_ProcessAnimMeshes)
    bpy.utils.register_class(VIEW3D_PT_VertexAnimation)
    bpy.types.Scene.output_dir = bpy.props.StringProperty(
        name="Output Directory",
        subtype='DIR_PATH',
        default="//",
        description="Directory where the output files will be saved"
    )


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ProcessAnimMeshes)
    bpy.utils.unregister_class(VIEW3D_PT_VertexAnimation)
    del bpy.types.Scene.output_dir


if __name__ == "__main__":
    register()
