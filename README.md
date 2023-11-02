# Meta Spark AR Vertex Animation Textures

## Description
A combination of scripts for Blender and Meta Spark AR to play back arbitrarily deformed geometry in Spark without using bones. It is super performant and flexible. 

![](https://github.com/MateSteinforth/SparkAR-VAT/blob/packedVertices/Triceratops.gif)

## Tutorial

[![Tutorial](https://img.youtube.com/vi/I7gRhAeAm30/0.jpg)](https://www.youtube.com/watch?v=I7gRhAeAm30)


## Quickstart

### Installing the Script in Blender

Edit > Preferences... > Add-Ons > Install...

Select [vertex_animation.py](https://github.com/MateSteinforth/SparkAR-VAT/blob/master/Blender/vertex_animation.py)

enable Spark AR VAT: Vertex Animation


### Exporting an Animation

Select the animated Object

Open the Spark AR VAT Tab

select frame range and output directory

click 'Process Anim Meshes'

**observe the changed 'Scale Factor' in the UI...**

**observe the changed 'Chunks' in the UI...**


### Installing the Shader in Spark AR

Enable Vertex Texture Fetch in Project > Edirt Properties... > Capabilities > + > Vertex Texture Fetch

Drag and drop [SparkVAT.sca](https://github.com/MateSteinforth/SparkAR-VAT/blob/master/SparkVATExample/shaders/SparkVAT.sca) into your project


### Importing an Animation

Drag and drop everything from the output directory above into your project

set compression to 'none' for all imported textures

make a new material with the shader and populate the outputs

assign it to the exported mesh from the output directory

**enter the Scale Factor from the Blender UI in the appropriate field**

**enter the Chunks from the Blender UI in the appropriate field**

![](https://github.com/MateSteinforth/SparkAR-VAT/blob/packedVertices/Factors.png)


### Known Limitations
Because of Texture Size limits in Spark, the maximum framerange of the animation depends on the mesh resolution. Many animations don't need many frames, while most models have a few thousand vertices. An average walk cycle for a character is only about 30 frames.

| Vertices        | Max Frames           | Seconds @25fps  |
| ------------- |:-------------:| -----:|
| <1024        | 1024 | 40 |
| <2048        | 512      |   20 |
| <3072 | 340      |    13 |
| <4096 | 256      |    10 |
| <5120 | 204      |    8 |
| <6144 | 170      |    6 |
| <7168 | 146      |    5 |
| <8192 | 128      |    4 |
| ... | ...      |    ... |
| <16384 | 64      |    2,56 |
| <32768 | 32      |   1,28 |

Vertex Order can't change between frames, which means that the mesh has to stay consistent between frames


## Authors

* **Mate Steinforth**

## Acknowledgments
* Adapted for Spark from the Blender scripts created by **Joshua Bogart**
* Adapted for Blender from 3ds Max scripts created by **Jonathan Lindquist** at **Epic Games**.
* [Triceratops model](https://sketchfab.com/3d-models/triceratops-horridus-marsh-e9c507f179ed4455aac3b208c9e6c973) licenced under CC0 Public Domain by The Smithsonian Institute

## Tech Info
If you're interested in the internals of the workflow, check [Texture Animation: Applying Morphing and Vertex Animation Techniques](https://medium.com/tech-at-wildlife-studios/texture-animation-techniques-1daecb316657)
