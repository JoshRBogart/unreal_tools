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
import math

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


def create_export_mesh_object(context, data, me):
    """Return a mesh object with correct UVs spread across a single texture."""
    max_vertices_per_chunk = 1024  # Our set maximum vertices for each chunk.

    while len(me.uv_layers) < 2:
        me.uv_layers.new()
    uv_layer = me.uv_layers[1]
    uv_layer.name = "vertex_anim"

    max_vertex_index = len(me.vertices)

    # If fewer than 1024 vertices, spread them across U 0...1.
    if max_vertex_index <= max_vertices_per_chunk:
        u_step = 1.0 / max_vertex_index
        half_pixel_h_offset = 0.5 / max_vertex_index  # For horizontal positioning
        for loop in me.loops:
            u_coord = (loop.vertex_index + 0.5) * u_step  # Center the vertex in the UV space allocated for it
            v_coord = half_pixel_h_offset  # Slightly above the bottom of the texture to avoid sampling issues

            uv_layer.data[loop.index].uv = (u_coord, v_coord)
    else:
        total_chunks = -(-max_vertex_index // max_vertices_per_chunk)  # Ceiling division to get total number of chunks.

        # Determine the vertical step for each chunk in UV coordinates.
        vertical_step = 1.0 / total_chunks
        half_pixel_v_offset = 0.5 / max_vertices_per_chunk  # For vertical positioning.

        for loop in me.loops:
            chunk_number = loop.vertex_index // max_vertices_per_chunk
            index_in_chunk = loop.vertex_index % max_vertices_per_chunk

            # Calculate U coordinate: position it in the middle of the pixel, based on a 1024 grid.
            u_coord = (index_in_chunk + 0.5) / max_vertices_per_chunk

            # Calculate V coordinate: position it based on the chunk and add the half-pixel offset.
            v_base = chunk_number * vertical_step
            v_coord = v_base + (half_pixel_v_offset * vertical_step)

            uv_layer.data[loop.index].uv = (u_coord, v_coord)

    ob = data.objects.new("export_mesh", me)
    context.scene.collection.objects.link(ob)
    return ob



# def create_export_mesh_object(context, data, me):
#     """Return a mesh object with correct UVs spread across a single texture."""
#     max_vertices_per_chunk = 1024  # Our set maximum vertices for each chunk.

#     while len(me.uv_layers) < 2:
#         me.uv_layers.new()
#     uv_layer = me.uv_layers[1]
#     uv_layer.name = "vertex_anim"

#     max_vertex_index = len(me.vertices)
#     total_chunks = -(-max_vertex_index // max_vertices_per_chunk)  # Ceiling division to get total number of chunks.

#     # Determine the vertical step for each chunk in UV coordinates.
#     vertical_step = 1.0 / total_chunks
#     half_pixel_v_offset = 0.5 / max_vertices_per_chunk  # For vertical positioning.

#     for loop in me.loops:
#         chunk_number = loop.vertex_index // max_vertices_per_chunk
#         index_in_chunk = loop.vertex_index % max_vertices_per_chunk

#         # Calculate U coordinate: position it in the middle of the pixel, based on a 1024 grid.
#         u_coord = (index_in_chunk + 0.5) / max_vertices_per_chunk

#         # Calculate V coordinate: position it based on the chunk and add the half-pixel offset.
#         v_base = chunk_number * vertical_step
#         v_coord = v_base + (half_pixel_v_offset * vertical_step)

#         uv_layer.data[loop.index].uv = (u_coord, v_coord)

#     ob = data.objects.new("export_mesh", me)
#     context.scene.collection.objects.link(ob)
#     return ob



def get_vertex_data(context, data, meshes):
    """Return lists of vertex offsets and normals from a list of mesh data"""
    original = meshes[0].vertices
    offsets = []
    normals = []

    # First, find the maximum offset to use for normalization
    max_offset_length = 0
    for me in reversed(meshes):
        for v in me.vertices:
            offset_length = (v.co - original[v.index].co).length
            if offset_length > max_offset_length:
                max_offset_length = offset_length

    context.scene.scale_factor = max_offset_length

    for me in reversed(meshes):
        for v in me.vertices:
            offset = (v.co - original[v.index].co) / max_offset_length
            # offset = v.co - original[v.index].co
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
    write_output_image(offsets, name + "_position", size, output_dir, context)
    write_output_image(normals, name + "_normal", size, output_dir, context)


def float_to_bytes(float_value):
    """ Convert a float in range [0, 1] to high and low bytes. """
    int_value = int(float_value * 65535)
    high_byte = (int_value >> 8) & 0xFF
    low_byte = int_value & 0xFF
    return high_byte, low_byte


def create_and_save_image(name_postfix, size, byte_list, output_dir, context):
    """
    Create images from byte list in 1024-pixel wide chunks, preserving the Y-order of the data.
    """
    width, height = size
    max_chunk_width = 1024
    padding_color = [127/255, 127/255, 127/255, 1]  # RGBA padding

    # Calculate the number of full max_chunk_width wide chunks and any remaining width
    full_chunk_count = width // max_chunk_width
    remainder_width = width % max_chunk_width

    combined_byte_list = []

    num_chunks = full_chunk_count + (1 if remainder_width else 0)
    context.scene.num_chunks = num_chunks

    # Process full chunks first
    for i in range(full_chunk_count):
        for y in range(height):
            start_index = (y * width + i * max_chunk_width) * 4
            end_index = start_index + max_chunk_width * 4
            combined_byte_list.extend(byte_list[start_index:end_index])

    # Process the remainder
    if remainder_width:
        # Process remainder as rows
        for y in range(height):
            start_index = (y * width + full_chunk_count * max_chunk_width) * 4
            end_index = start_index + remainder_width * 4
            combined_byte_list.extend(byte_list[start_index:end_index])
            # Only add padding if there are more than one chunk
            if full_chunk_count > 0:
                combined_byte_list.extend(padding_color * (max_chunk_width - remainder_width))  # Fill the remainder with padding

    # Calculate combined image dimensions
    if full_chunk_count > 0:
        # If more than one chunk, use full max_chunk_width
        combined_image_width = max_chunk_width
    else:
        # If only remainder, use the remainder width
        combined_image_width = remainder_width
    combined_image_height = height * num_chunks

    # Ensure minimum dimensions of 32 pixels
    combined_image_width = max(32, combined_image_width)
    combined_image_height = max(32, combined_image_height)

    # Create the image
    combined_image = bpy.data.images.new(f"{name_postfix}", width=combined_image_width, height=combined_image_height)
    combined_image.pixels = combined_byte_list

    # Scale if necessary (only if original size was below 32 in either dimension)
    if width < 32 or height < 32:
        combined_image.scale(combined_image_width, combined_image_height)

    # Save and remove the temporary image
    combined_image.save_render(f"{output_dir}{name_postfix}.png", scene=context.scene)
    bpy.data.images.remove(combined_image)

    # Return the number of chunks
    return num_chunks




def write_output_image(pixel_list, name, size, output_dir, context):
    # Convert the pixel list to high and low bytes
    high_bytes_list = []
    low_bytes_list = []

    for pixel in pixel_list:
        high_byte, low_byte = float_to_bytes(pixel)
        high_bytes_list.append(high_byte / 255.0)
        low_bytes_list.append(low_byte / 255.0)

    # Create and save high byte image
    create_and_save_image(name + "_high", size, high_bytes_list, output_dir, context)

    # Create and save low byte image
    create_and_save_image(name + "_low", size, low_bytes_list, output_dir, context)


# Function to store the current scene's unit settings
def store_unit_settings(context):
    original_units = context.scene.unit_settings.system
    original_scale = context.scene.unit_settings.scale_length
    return (original_units, original_scale)

# Function to set the scene's units to metric and scale to 0.01
def set_metric_units(context):
    context.scene.unit_settings.system = 'METRIC'
    context.scene.unit_settings.scale_length = 0.01

# Function to reset the scene's unit settings to the original
def reset_unit_settings(context, original_settings):
    context.scene.unit_settings.system, context.scene.unit_settings.scale_length = original_settings


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
        # Store original settings
        original_settings = store_unit_settings(context)

        # Set to metric and scale 0.01
        set_metric_units(context)

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
        max_frame_count =  1024 // ((math.ceil(vertex_count / 1024) * 1024) // 1024)
        if frame_count > max_frame_count:
            self.report(
                {'ERROR'},
                f"Frame count of {frame_count :,}, execedes limit of {max_frame_count :,}, based on {vertex_count :,} vertices mesh."
            )
            return {'CANCELLED'}

        # Store the current display device
        current_display_device = bpy.context.scene.display_settings.display_device

        # Set display device to 'None'
        bpy.context.scene.display_settings.display_device = 'None'

        myname = bpy.context.active_object.name
        meshes = get_per_frame_mesh_data(context, data, objects)
        export_mesh_data = meshes[0].copy()
        obj = create_export_mesh_object(context, data, export_mesh_data)
        offsets, normals = get_vertex_data(context, data, meshes)
        texture_size = vertex_count, frame_count
        bake_vertex_data(context, data, offsets, normals, texture_size, myname)
        export_mesh(context, obj, myname)

        # Delete the mesh after saving
        bpy.ops.object.delete()

        # Reset display device to its original value
        bpy.context.scene.display_settings.display_device = current_display_device

        # Reset unit settings
        reset_unit_settings(context, original_settings)

        # display chunkies
        self.report({'INFO'}, f"Exported {num_chunks} chunk(s).")

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
        # col.prop(scene, "frame_step", text="Step")
        col.prop(scene, "output_dir", text="Output Directory")
        col.prop(scene, "scale_factor", text="Scale Factor")
        col.prop(scene, "num_chunks", text="Chunks")
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
    bpy.types.Scene.scale_factor = bpy.props.FloatProperty(
        name="Scale Factor",
        description="Maximum vertex offset length used for normalization",
        default=1.0  # A reasonable default value
    )
    bpy.types.Scene.num_chunks = bpy.props.FloatProperty(
        name="Number of Chunks",
        description="Put this into the Spark Shader",
        default=1.0  # A reasonable default value
    )


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ProcessAnimMeshes)
    bpy.utils.unregister_class(VIEW3D_PT_VertexAnimation)
    del bpy.types.Scene.output_dir
    del bpy.types.Scene.scale_factor
    del bpy.types.Scene.num_chunks


if __name__ == "__main__":
    register()
