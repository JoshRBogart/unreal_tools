# Meta Spark AR Vertex Animation Textures

## Description
A combination of scripts for Blender and Meta Spark AR to play back arbitrarily deformed geometry in Spark without using bones. It is super performant and flexible. 


### Known Limitations
Vertex offset between the first and last frame can't be more than 1 scene unit (will be fixed/adapted)


### Installing the Script in Blender

Edit > Preferences... > Add-Ons > Install...

Select [vertex_animation.py](https://github.com/MateSteinforth/SparkAR-VAT/blob/master/Blender/vertex_animation.py)

enable Spark AR VAT: Vertex Animation


### Exporting an Animation

Select the animated Object

Open the Spark AR VAT Tab

select frame range and output directory

click 'Process Anim Meshes'


### Installing the Shader in Spark AR

Drag and drop [SparkVAT.sca](https://github.com/MateSteinforth/SparkAR-VAT/blob/master/SparkVATExample/shaders/SparkVAT.sca) into your project

Drag and drop everything from the output directory above into your project

make a new material with the shader and populate the outputs

assign it to the exported mesh from the output directory



## Authors

* **Mate Steinforth**

## Acknowledgments
* Adapted for Spark from the Blender scripts created by **Joshua Bogart**
* Adapted for Blender from 3ds Max scripts created by **Jonathan Lindquist** at **Epic Games**.
