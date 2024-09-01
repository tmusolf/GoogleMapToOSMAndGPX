# GoogleMapToOSMAndGPX
Create a folder of OSMAnd GPX files from a google my maps map (GMap)

It's a python command line utility that works directly from a GMap (using it's map ID) to export the map's KML data and directly convert it into a folder of OSMAnd style GPX files. Both tracks and waypoints and translated.   Descriptions, icon symbol, icon color, track color, track width are all translated. Each track is put in it's own GPX file and all waypoints are put in a single GPX file. 

A second program is wrapper for the command line utility. This wrapper creates a simple graphical user interface for executing the utility.  In addition to the python scripts both the command line utility and GUI wrapper are supplied as windows executable files that can be run directly, without having to install or use python
## Syntax
```
py GoogleMapToOSMAndGPX.py <map_id> <gpx_path> <width 1-24> -t <transparency 00 to FF> -s <split type> -i <split interval miles/seconds> -a -e
``` 
Parm | Long Parm | Description
--- | --- | ---
map_id | | Required: The GMap id of the map to be converted.  The map_id is found in the URL when the map is being displayed in a browser.  It the string of characters between mid= and & in the map url.  The map must have sharing enabled.
gpx_path | | Required: Path name for the created GPX files.  If it doesn't exist a folder of this name is created.  If the folder exists any existing files are NOT deleted, but files with the same names will be overwritten.
-t | --transparency | Transparency value to use for all tracks.  Specified as a 2 digit hex value without the preceeding "0x".  00 is fully transparent and FF is opaque.
-a | --arrows | When present, OSMAnd will display directional arrows on a track.
-e | --ends | When present, OSMAnd will display start and finish icons at the ends of the track.
-s | --split | Display distance or time splits along tracks. Accepted values are: no_split, distance, time.  Default: no_split NOTE: The split and interval tags appear to be ignored by OSMAnd when placed in a track GPX file. The XML is identical to what OSMAnd generates when you edit a track's appearance to turn on splits and export the track.
-i | --interval | Distance in miles or time in minutes to display splits on track.  Split type (-s) must also be defined. Default: 1.0)
-w | --width | If present, this track width is used for all track widths, overiding values found in the KML file.
-l | --layers | If present, will create a subdirectory under the gpx_path for each layer in the GMap file. Each of these layer subdirectories will contain a GPX file for each track and one for all the waypoints. 

## Using GPX files with OSMAnd
NOTE: Starting with Android 11 there are enhanced file protection protocals put in place that prevent you from accessing the files in the Android/obb/net.osmand.plus folders. You can change this location to that is accessible by other Android applications by going to settings/OSMAnd settings/Data storage folder and selecting manually specified /storage/emulated/0/Android/media/net.osmand.plus/files.

To use these converted GPX files in OSMAnd they need to be placed in the appropriate OSMAnd tracks folder on your phone. Transfer the folder and it's GPX files to your phone and then use a file manager to copy the entire folder to the Android/media/net.osmand.plus/files/tracks directory.  You can also create folders under the tracks directory to contain these folders. For example, ...tracks\Germany & ...tracks\Sweden.  This type of organization can make it easier to find and manage these tracks.

Once the folder is transfered you can goto OSMAnd My Places and navigate to the folder.  You can make all the GPX files in the entire folder visible/not visible as a group or you can select them individually.  When they are made visible the tracks will display with the same line color as you specified in your google map.  Waypoints will be converted to an OSMAnd equivalent icon and color.  If an icon is not translated you will need to update the translation library table in this utility to show how you want a maps icon translated.

If you use the OSMAnd import feature you will lose a track's color and line width and they will be imported with OSMAnd default values.

To remove the GPX files from OSMAnd you can use a file manager or OSMAnd My Places to delete individual GPX files or the entire folder.

You can also use My Places to edit the appearance of the tracks and waypoints. These changes appear not to be written back to the GPX files so any changes you make in this way will be temporary.  If anyone knows where OSMAnd stores this information and how it can be accessed, please let me know.

## GPX Track file example
Here is an example of the GPX XML code created by this utility for a track

```
<?xml version="1.0" encoding="utf-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:osmand="https://osmand.net" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" version="1.1" creator="GoogleMapToOSMAndGPX V1.1">
  <metadata>
    <desc>Description text to be displayed in OSMAnd</desc>
  </metadata>
  <trk>
    <name>My track name</name>
    <trkseg>
      <trkpt lat="37.5793230067939" lon="-121.966263027862">
        <ele>12.4</ele>
      </trkpt>
      <trkpt lat="37.5793280359358" lon="-121.966279959306">
        <ele>10.4</ele>
      </trkpt>
    </trkseg>
  </trk>
  <extensions>
    <osmand:color>#80F48FB1</osmand:color>
    <osmand:width>12</osmand:width>
    <osmand:show_arrows>false</osmand:show_arrows>
    <osmand:show_start_finish>false</osmand:show_start_finish>
    <osmand:split_type>no_split</osmand:split_type>
  </extensions>
</gpx>
```

## GPX Waypoint file example
Here is an example of the GPX XML code created by this utility for waypoints.

```
<?xml version="1.0" encoding="utf-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:osmand="https://osmand.net" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" version="1.1" creator="GoogleMapToOSMAndGPX V1.1">
  <wpt lat="37.5793131999671" lon="-121.966220028698">
    <ele>25.6</ele>
    <name>Waypoint name</name>
    <desc>Waypoint description to be displayed in OSMAnd</desc>
    <extensions>
      <osmand:icon>leisure_marina</osmand:icon>
      <osmand:background>octagon</osmand:background>
      <osmand:color>#a71de1</osmand:color>
    </extensions>
  </wpt>
</gpx>
```

## Google Map Layers
A google map can have layers as a way to organize the waypoints and tracks.  By default, this structure is ignored.  A directory <gpx_path> is created containing a single GPX file for all waypoints found in the GMap and one GPX file for each track in the GMap. 

Using the -l parameter the layer organization is preserved.  A subdirectory, named after the layer, is created under <gpx_path>for each layer.  Each of these subdirectories will contain a GPX file for each track in the layer and one GPX file containing all of the waypoints in the layer.

## Batch File
There is a batch file example which allows you to create a text file containing lines of comma separated paths and map ids. These files can then be fed to the batch file and it will call this utility once for each pair/line in the file.  This is a quick way to update the GPX files from a large group of google maps without having to do them individually.

## Windows Executables
There are two .exe files provided which are windows executables.  These can be run from a command window without having to use or install python.  

GoogleMapsToOSMAndGPX.exe is the command line utility itself and GoogleMapsToOSMAndGPX-gui.exe is the graphical user interface (GUI) wrapper that allows you to run the utility via a simple user inteface instead of the command line.  For this to work both files must be placed in the same directory.

## Parting words
This is a work in progress as I learn more about OSMAnd's handling of imported GPX files. I'm not python guru so the code structure is probably not totally pythonic. There is error checking in the code, but it could probably be improved.
