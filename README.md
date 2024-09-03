# GoogleMapToOSMAndGPX
Creates a folder of OSMAnd style GPX files from a google my maps map (GMap)

If you do trip planning in GMaps this utility will export the track and waypoint information from a GMap and create a folder of OSMAnd style GPX files.

There is a command line utility and a GUI wrapper that provides a simple graphical user interface to execute the utility.  

<img src="https://github.com/user-attachments/assets/c47ac0c9-e962-478c-b41a-574152052b24" alt="Options" width="400">

Both the utility and wrapper can be run as python utilities or you can use the provided Windows executable (exe) files, so python is not required.

The utility uses the GMap MapID to directly export the map's data in KML format and then it converts it to OSMAnd style GPX files. Both tracks and waypoints and translated. Descriptions, icon symbol, icon color, track color, track width are all translated. For a given map each track is put in its own GPX file and all waypoints are put in a single GPX file. Optionally, the GMap layers will be preserved, creating a separate subdirectory for each GMap layer.
## Example of a GMap and OSMAnd equivalent
Here is a small section of a GMap and the corresponding GPX data created by this utility displayed in OSMAnd

  <img src="https://github.com/user-attachments/assets/18a7dcb9-df87-4bfc-8ed9-4601be209d8e" alt="Options" width="600">
  <img src="https://github.com/user-attachments/assets/788fcf3b-4759-4bbb-b8af-e25bacf93832" alt="Options" width="600">

## Command Line Syntax
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

## Google Map Layers
A google map can have layers as a way to organize the waypoints and tracks.  By default, this structure is ignored.  A directory <gpx_path> is created containing a single GPX file for all waypoints found in the GMap and one GPX file for each track in the GMap. 

Using the -l parameter the layer organization is preserved.  A subdirectory, named after the layer, is created under <gpx_path>for each layer.  Each of these subdirectories will contain a GPX file for each track in the layer and one GPX file containing all of the waypoints in the layer.

## Using the GPX files with OSMAnd
To use these converted GPX files in OSMAnd they need to be placed in the appropriate OSMAnd tracks folder on your phone. Transfer the folder and it's GPX files to your phone and then use a file manager app to copy the entire folder to the **Android/media/net.osmand.plus/files/tracks** directory.  You can also create folders under the tracks directory to contain these folders. For example, ...tracks\Germany & ...tracks\Sweden.  This type of organization can make it easier to find and manage these tracks.

To remove the GPX files from OSMAnd you can use a file manager app or OSMAnd My Places to delete individual GPX files or the entire folder.

NOTE: As of V4.8.6 the OSMAnd import feature only allows you to import a single GPX file at a time, not a folder of GPX files.  In addition, if you use the OSMAnd import feature you will lose a track's color and line width and they will be imported with OSMAnd default values.

NOTE: Starting with Android 11 there are enhanced file protection protocals put in place that prevent you from accessing the files in the Android/obb/net.osmand.plus folders. You can change this location to one that is accessible by other Android applications by going to **settings/OSMAnd settings/Data storage folder** and selecting **manually specified /storage/emulated/0/Android/media/net.osmand.plus/files**.

## Making a GPX file visible

Once the folder is transfered into OSMAnd you can make all the GPX files in the entire folder visible/not visible as a group or you can select them individually.  When they are made visible the tracks will display with the same line color as you specified in the original GMap.  Waypoints will be converted to an OSMAnd equivalent icon and color using a translation dictionary in the GoogleMapToOSMAndGPX utility.  
<br>From the OSMAnd main menu select the **My Places / Track** tab and navigate to the folder containing your GPX files. Touch the folder you wish to open up.  In this example the Kayak folder.<br>
<img src="https://github.com/user-attachments/assets/f938a1ce-694f-4e38-b716-8a7953a695e1" alt="Options" width="200">

<br>In this example the kayak folder contains another layer of folders, one for each river.  Select the elispis next the folder you want.  In this example, Tuolumne is chosen.<br>
<img src="https://github.com/user-attachments/assets/6f3c3516-6a5f-4856-914d-60c9205b2ac9" alt="Options" width="200">

<br>Select the **Show all tracks on the map** option.<br>
<img src="https://github.com/user-attachments/assets/a7ce2d39-bd95-4d9a-bae7-ec7eeef52cb3" alt="Options" width="200">

<br>Now a list of the GPX track files and waypoint files are displayed.  Check all the listed GPX files you want displayed and select **APPLY**.<br>
<img src="https://github.com/user-attachments/assets/a5c6adba-793a-4289-8ad7-817955ec4fcb" alt="Options" width="200">

<br>At this point you can navigate back to your map and the tracks and waypoints from the GPX files will be visible.<br>
<img src="https://github.com/user-attachments/assets/7c7b5a2b-55e1-496a-a11e-dbdf4e878209" alt="Options" width="600">

<br>Here is a sample of the corresponding GMap used in this example:<br>
<img src="https://github.com/user-attachments/assets/18a7dcb9-df87-4bfc-8ed9-4601be209d8e" alt="Options" width="600">

<br>Because each track is in its own GPX file it will be individually selectable in OSMAnd.  Once selected you can see the track's description, length and other attributes.<br>
<img src="https://github.com/user-attachments/assets/4e57d04b-b3ae-450c-99e0-cd264ddac1aa" alt="Options" width="200">


<br>NOTE: If an icon is not translated or translated as you wish you can update the translation dictionary in the python utility code.

## Making a GPX file not visible

<br>To make a folder of GPX files not visible nagivate to the appropriate folder, as shown above, select **Show all tracks on the map** then uncheck or deselect the files you want turn off and finally select **apply**.<br>
<img src="https://github.com/user-attachments/assets/b5f04330-cbbc-4c9f-b134-fa6b4c3851c9" alt="Options" width="200">


## Windows Executables
There are two .exe files provided which are windows executables.  They are standalone files and do not need to be installed, they can be run directly.  You do not need to use or install python to run these exe files.  

GoogleMapsToOSMAndGPX.exe is the command line utility itself and GoogleMapsToOSMAndGPX-gui.exe is the graphical user interface (GUI) wrapper that allows you to run the utility via a simple user inteface instead of the command line.  For this to work both files must be placed in the same directory.

## Batch File
There is a batch file example which takes a user created text file containing lines of comma separated paths and GMap ids with optional parameter overides. This file can then be fed to the batch file and it will call the conversion utility once for each GMap line in the file.  This is a quick way to update the GPX files from a large group of google maps without having to do them individually.

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

## Parting words
This is a work in progress as I learn more about OSMAnd's handling of GPX files and its GPX extensions. 

I'm not python guru so the code structure is probably not totally pythonic.

