# Blender-UnrealTools
Vertex Animation-
This script creates a new panel in the object mode tool shelf as well as a new operator.
When called the operator will take all selected mesh objects in the active scene and copy their mesh data per frame.
The difference in each vertex location and normals in world space is then stored as color data in two images respectfully.
A new mesh is created for export with it's second UV channel's vertices spaced evenly across the V axis.
