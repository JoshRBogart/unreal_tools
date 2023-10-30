# Meta Spark AR Vertex Animation Textures

## Description
A combination of scripts for Blender and Meta Spark AR to play back arbitrarily deformed geometry in Spark without using bones. It is super performant and flexible. 

![](https://github.com/MateSteinforth/SparkAR-VAT/blob/master/animatedCube.gif)


### Known Limitations
Because of Texture Size limits in Spark, this workflow can only process meshes of up to 1024 vertices and up to 1024 frames


### Installing the Script in Blender

Edit > Preferences... > Add-Ons > Install...

Select [vertex_animation.py](https://github.com/MateSteinforth/SparkAR-VAT/blob/master/Blender/vertex_animation.py)

enable Spark AR VAT: Vertex Animation


### Exporting an Animation

Select the animated Object

Open the Spark AR VAT Tab

select frame range and output directory

click 'Process Anim Meshes'

observe the changed 'Scale Factor' in the UI...


### Installing the Shader in Spark AR

Enable Vertex Texture Fetch in Project > Edirt Properties... > Capabilities > + > Vertex Texture Fetch

Drag and drop [SparkVAT.sca](https://github.com/MateSteinforth/SparkAR-VAT/blob/master/SparkVATExample/shaders/SparkVAT.sca) into your project

Drag and drop everything from the output directory above into your project

set compression to 'none' for all imported textures

make a new material with the shader and populate the outputs

assign it to the exported mesh from the output directory

**enter the Scale Factor from the Blender UI in the appropriate field**



## Authors

* **Mate Steinforth**

## Acknowledgments
* Adapted for Spark from the Blender scripts created by **Joshua Bogart**
* Adapted for Blender from 3ds Max scripts created by **Jonathan Lindquist** at **Epic Games**.

## Tech Info
If you're interested in the internals of the workflow, check [Texture Animation: Applying Morphing and Vertex Animation Techniques](https://medium.com/tech-at-wildlife-studios/texture-animation-techniques-1daecb316657)
