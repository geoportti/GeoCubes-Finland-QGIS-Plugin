# Geocubes Finland - QGIS plugin
A QGIS plugin to access GeoCubes Finland, maintained by Finnish Geospatial Research Institute (FGI).

## What is Geocubes Finland?
Geocubes Finland is a harmonised, multi-resolution raster geodata repository that contains several key national datasets on themes such as elevation, land cover and forestry. Read more on [Geocubes Finland main site](http://86.50.168.160/geocubes) and [description on usage and citing](https://github.com/geoportti/GeoCubes).
#### Harmonised? What does that mean?
Simply that the data is as simple to access and use as can be. All of the data is in the same CRS (EPSG:3067), is georeferenced uniformly and is available as both a GeoTIFF image or a VRT virtual file. The data is available in resolutions ranging from 1 to 1000 meters and can be cropped flexibly with e.g. a bounding box or administrative area boundaries. Read more [here](http://86.50.168.160/geocubes/description/).
All of this means that **accessing raster datasets is easier than ever before**.
#### Who's the service for?
Geocubes Finland is aimed to support the needs of Finnish research community, but the service and its data is freely usable by anyone interested. Please see the [citing guidelines](https://github.com/geoportti/GeoCubes#usage-and-citing) if you use Geocubes Finland in your work.

## Geocubes Finland plugin
This QGIS 3.x plugin enables using all of the abovementioned features effortlessly in your QGIS 3 installation. Simply select three parameters: raster layers to download, cropping method and raster resolution. Crop with a bounding box, administrative areas or draw a polygon to crop with. Then select either GeoTIFF or VRT file. After download, a layer is added to QGIS, where you can use it for further analysis. You may use files from the Geocubes Finland server or save the file locally to disk: the latter is beneficial for larger files.
#### Plugin installation
- Download the plugin to your computer from *Select clone or download* -> *Download ZIP*
- Open QGIS, click *Plugins* drop-down menu and select *Manage and install plugins*
- Select *Install from ZIP* in the plugin manager. Navigate to the zip file.
#### I found a bug and/or want to suggest a new feature. What do I do?
We are grateful for all feedback. If you've found errors or have suggestions to improve the plugin, please open an issue in the repository or see infobox on top of *geocubes_plugin.py* for email information.
