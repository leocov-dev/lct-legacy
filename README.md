# LCT Tools - Legacy
![tested_maya_2016](https://img.shields.io/badge/maya-2016-128189.svg?style=flat)
![license](https://img.shields.io/badge/license-MIT-A31F34.svg?style=flat)

## Description
This repository is for historical reference and the source code may not be functional in current versions of Maya. Some functionality relies on web services that are no longer active, so auto-updating and error reporting features do not work.

This is a suite of Maya artist tools developed between 2013 and 2017.  It was targeted at Maya 2016 but should be compatible with other versions.

See the [Releases](/releases/latest) page for pre-built packages.

#### Notes of Interest
* The tools were designed to be artist friendly. They installed with one command by adding a shelf icon to the current shelf.
* Tools had a unified UI window with contextual menus.
    * They could load in the shared window as needed, and remember their settings.
    * They could be popped-out to free floating windows.
* Tools had auto updating functionality.
    * They would query a web server to check for the latest version.
    * They would automatically download, unpack and update the new files.
* Tools could post automated error logs to a web server so that I could track issues.


## Screenshots
This is the main interface window.

![lct_main](screenshots/lct_main.png)
-----------
This tool baked textures and vertex color using mental ray bake sets.

![lct_mentalray](screenshots/lct_mentalray.png)
-----------
This tool exported and imported OBJ files in a unified way. It could also process low/high pairs and explode them for baking. 

![lct_obj](screenshots/lct_obj.png)
-----------
This tool offered an easy place to tweak camera settings.

![lct_cam](screenshots/lct_cam.png)
-----------
This tool let you easily rename many scene objects at once.

![lct_rename](screenshots/lct_rename.png)
-----------
This tool let you easily and quickly retopologize high res geometry.

![lct_retopo](screenshots/lct_retopo.png)
-----------
This tool let you easily generate gradient textures and textures based on lit-sphere images.

![lct_texgen](screenshots/lct_texgen.png)
-----------
This tool was intended for easy reloading, naming and opening of file texture nodes.

![lct_texture](screenshots/lct_texture.png)
-----------
This tool made common UV operations easy

![lct_uv](screenshots/lct_uv.png)
