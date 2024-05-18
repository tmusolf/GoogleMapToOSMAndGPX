#!/usr/bin/python
#========================================================================================
# Export the KML data for a google my maps custom map and convert the data to GPX files
# using the OSMAnd extensions.
# 
# The GPX file includes OSMAnd extensions and translation of google waypoint icons into a 
# similar OSMAnd icon. Tracks and waypoints are the only objects converted. 
# 
# The resulting GPX files are placed into a folder.  Each track is placed in its own GPX file.
# All waypoints are combined into a single GPX file.
#
# 5/17/2024: V1.0 Initial version
#========================================================================================
import sys
import argparse
import requests
from xml.etree import ElementTree as ET
from xml.dom import minidom
import os
import os.path
from pathlib import Path

PROGRAM_NAME = Path(sys.argv[0]).stem
PROGRAM_VERSION = "1.0"
DEFAULT_TRACK_TRANSPARENCY = "80"
DEFAULT_WAYPOINT_DESCRIPTION = ""
DEFAULT_TRACK_DESCRIPTION = ""
# Both of these should probably be command line arguments
DEFAULT_ICON_COLOR = "DB4436"	# rusty red
DEFAULT_TRACK_SPLIT_INTERVAL = "1.0"  #miles or minutes
SPLIT_TYPE_TIME = "time"
SPLIT_TYPE_DISTANCE = "distance"
SPLIT_TYPE_NONE = "no_split"
DEFAULT_TRACK_SPLIT_TYPE = SPLIT_TYPE_NONE # no_split, distance, time
KMLCOLOR = "KMLCOLOR"
# This is the magic URL that will initiate a get request to google and get the KML data
# for the specified google map.
GET_URL_PREFIX = "https://www.google.com/maps/d/u/0/kml?forcekml=1&mid="
GET_URL_SUFFIX = ""

# globals to keep track of some counts
countTotalWaypoints = 0
countTotalTracks = 0
#========================================================================================
class cWaypoint:
	def __init__ (self,icon,color,background):
		self.icon = icon
		self.color = color
		self.background = background
#========================================================================================
#========================================================================================
def setupParseCmdLine():
	parser = argparse.ArgumentParser(
	prog=PROGRAM_NAME,
	description="Export the KML data for a google my maps KML and convert it to OSMAnd style GPX files, including icon conversion.")
	# epilog="text at bottom of help")
	parser.add_argument("map_id",
		help="The google map id - found between the mid= and & in the map url.  Map must have sharing enabled")
	parser.add_argument("GPX_path",
		help="path name for the output GPX files")
	parser.add_argument('-w', '--width',
		action='store',
		required = False,
		type=int,
		choices=range(1,24),
		metavar="[1-24]",
		help="If present, this track width is used for all track widths, overiding values found in the KML file.")
	parser.add_argument('-t', '--transparency', 
		action='store', 
		required = False,
		default=DEFAULT_TRACK_TRANSPARENCY,
		help='Transparency value to use for all tracks.  Specified as a 2 digit hex value.  00 is fully transparent and FF is opaque.')
	parser.add_argument('-a', '--arrows',
		action='store_true',
		required=False,
		help="When present, OSMAnd will display directional arrows on a track."),
	parser.add_argument('-e','--ends',
		action='store_true',
		required=False,
		help="When present, OSMAnd will display start and finish icons at the ends of the track."),
	parser.add_argument('-s', '--split', 
		action='store',
		required=False,
		choices=[SPLIT_TYPE_NONE, SPLIT_TYPE_DISTANCE, SPLIT_TYPE_TIME],
		default=DEFAULT_TRACK_SPLIT_TYPE, 
		help="Display distance or time splits along tracks. Default: "+str(DEFAULT_TRACK_SPLIT_TYPE))
	parser.add_argument('-i', '--interval', 
		action='store',
		required=False,
		default=DEFAULT_TRACK_SPLIT_INTERVAL, 
		help="Distance in miles or time in seconds to display splits on track.  Split type must also be defined. Default: "+str(DEFAULT_TRACK_SPLIT_INTERVAL))

	return(parser.parse_args())
#========================================================================================
# iconDictionary describes the mapping between a KML icon number and an OSMAnd icon name.
# It also contains a default OSMAnd color and shape to use for each OSMAnd icon type.
# 
# iconDictionary format:
# 	"KML icon number":["OSMAnd Icon name","HTML hex color code or flag to use KMLCOLOR","OSMAnd shape"]
# 
# Color code is a standard 6 digit HTML hex color code.  This is what OSMAnd uses
# 	Put the string "KMLCOLOR", without the double quotes, in for a color value if you want to use the color specified in the KML file
# 	for a particular icon.
# As of 8/2020 OSMAnd icons do not support transparent colors.
# As of 8/2020 OSMAnd supports 3 icon shapes: circle, octagon, square
# 
# To add additional KML icons to the dictionary.
#
# For each icon you want to translate you need to add a new entry/line into the iconDictionary table. 
# To determine what the KML and OSMAnd icons are you want go through the following steps:
#
# KML icon number
# 	1) Create a google my maps test file with the icons you want to use.
# 	2) Export this map as a KML file.  
# 	3) Open up the file in a text editor and look for your points. You can ignore all the <style> & <StyleMap> tags at the 
#	   beginning of the KML file.  The points/waypoints/Placemarks will look like this:
#
#		<Placemark>
#			<name>Mileage Marker dot</name>
#			<styleUrl>#icon-1739-0288D1-nodesc</styleUrl>
#			<Point>
#				<coordinates>-120.8427259,38.8170119,0</coordinates>
#			</Point>
#		</Placemark>

# The <styleUrl> tag has the icon number.  In the preceeding example it's "1739".
#
# OSMAnd Icon name
#	1) Create some favorites using the icons you want.
#	2) Goto .../Android/data/net.osmand.plus/files/favorites/favorites.gpx
#	3) Open the favorites file in a text editor and look for the waypoints.
#	   in the following example the icon name is: "special_trekking"
#
#		<wpt lat="39.2906659" lon="-121.4965106">
#			<name>hiker, pale yellow</name>
#			<extensions>
#			<color>#eeee10</color>
#			<icon>special_trekking</icon>
#			<background>circle</background>
#			</extensions>
#		</wpt>
#
# ???: would be nice to have a command line option to read in a user supplied dictionary from a file
#========================================================================================
def KMLToOSMAndIcon(KMLIconID):

	iconDictionary ={
		"unknown":["special_symbol_question_mark","e044bb","octagon"],			#unknown KML icon code - this entry will be used if the KML icon is not found the iconDictionary.
		"1765":["tourism_camp_site",KMLCOLOR,"circle"],							#campsite
		"1525":["leisure_marina","a71de1","octagon"],							#river access
		"1739":["special_number_0",KMLCOLOR,"circle"],							#Mileage marker plus-KML dot on gmaps & Plus in OSMAnd. Did have this color:"1010a0"
		"1596":["special_trekking",KMLCOLOR,"circle"],							#hiking trailhead  Color I use is 9E963A
		"1369":["special_trekking",KMLCOLOR,"circle"],							#hiking trailhead -old style icon
		"1371":["special_trekking",KMLCOLOR,"circle"],							#hiking trailhead -old style icon
		"1723":["tourism_viewpoint",KMLCOLOR,"octagon"],						#rapid  "d90000"
		"1602":["tourism_hotel",KMLCOLOR,"circle"],								#hotel, lodge
		"1528":["bridge_structure_suspension","10c0f0","circle"],				#bridge
		"1577":["restaurants",KMLCOLOR,"circle"],								#retaurant, diner, dining
		"1085":["restaurants",KMLCOLOR,"circle"],								#retaurant, diner, dining, old style icon
		"1650":["tourism_picnic_site","eecc22","circle"],						#picnic site
		"1644":["amenity_parking",KMLCOLOR,"circle"],							#parking area
		"1578":["shop_supermarket",KMLCOLOR,"circle"],							#grocery store, supermarket #1 - light blue "10c0f0"
		"1685":["shop_supermarket",KMLCOLOR,"circle"],							#grocery store, supermarket #2 - light blue	"10c0f0"
		"1023":["shop_supermarket",KMLCOLOR,"circle"],							#grocery store, supermarket #2 - light blue	"10c0f0", old style grocery icon
		"1504":["air_transport","10c0f0","circle"],								#airport, airstrip
		"1581":["fuel",KMLCOLOR,"circle"],										#gas station
		"1733":["amenity_toilets","10c0f0","circle"],							#toilet, restroom
		"1624":["amenity_doctors","d00d0d","circle"],							#hospital, doctor, emergency room
		"1608":["tourism_information","1010a0","circle"],						#tourism information
		"1203":["tourism_information","1010a0","circle"],						#tourism information, old style icon - big "i"
		"1535":["special_photo_camera",KMLCOLOR,"circle"],						#POI #1, camera "eecc22"
		"993": ["special_photo_camera",KMLCOLOR,"circle"],						#POI #1, camera "eecc22" old icon style
		"1574":["special_flag_start",KMLCOLOR,"circle"],						#POI #2, flag "eecc22"
		"1899":["special_marker",KMLCOLOR,"circle"],							#POI #3, pin "eecc22"
		"1502":["special_star",KMLCOLOR,"circle"],								#POI #4, star "eecc22"
		"1501":["special_symbol_plus",KMLCOLOR,"circle"],						#POI #5, plus/diamond "eecc22"
		"1500":["special_flag_start",KMLCOLOR,"circle"],						#POI #6, square in google maps & square flag i OSMAnd
		"1592":["special_heart",KMLCOLOR,"circle"],								#POI #7, heart
		"1729":["tourism_viewpoint",KMLCOLOR,"circle"],							#Vista point / viewpoint
		"503": ["special_marker",KMLCOLOR,"circle"],							#Old school map point
		"1603":["special_house","eecc22","circle"],								#house
		"1879":["amenity_biergarten",KMLCOLOR,"circle"],						#brewery, brew pub
		"1541":["special_symbol_exclamation_mark","ff0000","octagon"],			#danger #1 GMaps: "!" 		OSMAnd: exclamation
		"1898":["special_symbol_exclamation_mark",KMLCOLOR,"octagon"],			#danger #1 GMaps: "X" 		OSMAnd: exclamation 
		"1564":["amenity_fire_station","ff0000","octagon"],						#danger #2 GMaps: 			OSMAnd: fire/explosion
		"1710":["special_arrow_up_and_down","10c0f0","circle"],					#river gauge, up/down arrow or thermometer
		"1655":["amenity_police","1010a0","circle"],							#ranger/police station #1
		"1657":["amenity_police","1010a0","circle"],							#ranger/police station #2
		"1720":["wood","eecc22","circle"],										#Park/National Park - yellow
		"1701":["sport_swimming","eecc22","circle"],							#Lake/swimmer - yellow
		"1395":["sport_swimming","eecc22","circle"],							#Lake/swimmer - yellow, old style icon
		"1811":["special_sun","eecc22","circle"],								#hot spring/sun - yellow
		"1716":["route_railway_ref",KMLCOLOR,"circle"],							#train station - purple
		"1532":["route_bus_ref",KMLCOLOR,"circle"],								#bus station or stop
		"1626":["route_monorail_ref",KMLCOLOR,"circle"],						#Metro, subway stop
		"1534":["amenity_cafe",KMLCOLOR,"circle"],								#cafe/coffe - blue
		"1607":["amenity_cafe",KMLCOLOR,"circle"],								#cafe/coffe - blue, old style ice cream cone icon
		"1892":["waterfall","eecc22","circle"],									#waterfall - yellow
		"1634":["building_type_pyramid","eecc22","circle"],						#Mountain Peak - yellow
		"1684":["shop_department_store","10c0f0","circle"],						#Store/shopping - blue
		"1095":["shop_department_store","10c0f0","circle"],						#Store/shopping - blue	old style shopping icon
		"1517":["amenity_bar",KMLCOLOR,"circle"],								#Bar/cocktails/lounge - blue, old style icon
		"979": ["special_sail_boat","a71de1","circle"],							#Passenger ferry - purple
		"1537":["special_sail_boat",KMLCOLOR,"circle"],							#Auto Ferry
		"1498":["place_town","0244D1","circle"],								#town/city/village - Google circle with small square in center
		"1521":["leisure_beach_resort","eecc22","circle"],						#beach - yellow
		"1703":["amenity_drinking_water","00842b","circle"],					#Water Faucet - green
		"1781":["sanitary_dump_station","10c0f0","circle"],						#RV Dump station - light blue
		"1798":["Winery",KMLCOLOR,"circle"],									#Winery - light blue
		"1636":["Museum",KMLCOLOR,"circle"],									#Museum - light blue
		"1289":["Museum","10c0f0","circle"],									#Museum - light blue, old style icon
		"1741":["special_wagon","10c0f0","circle"],								#car rental - light blue
		"1590":["shop_car_repair","10c0f0","circle"],							#car/tire repair - light blue
		"1659":["amenity_post_box","10c0f0","circle"],							#post office
		"1512":["amenity_atm","10c0f0","circle"],								#bank/atm
		"1870":["sport_scuba_diving",KMLCOLOR,"octagon"],						#scuba, dive, snorkel site, google maps - snorkel mask, OSMAnd scuba diver
		"1882":["reef",KMLCOLOR,"octagon"],										#reef, tide pool - google maps starfish icon, OSMAnd seahorse/coral
		"1573":["reef",KMLCOLOR,"octagon"],										#reef, tide pool, fishing spot - google maps fish icon, OSMAnd seahorse/coral
		"1569":["special_sail_boat",KMLCOLOR,"circle"],							#Passenger Ferry
		"1741":["special_wagon",KMLCOLOR,"circle"],								#Car Rental
		"1538":["special_wagon",KMLCOLOR,"circle"],								#Car Rental
		"1709":["amenity_cinema",KMLCOLOR,"circle"],							#Cinema, movie, theater
		"1615":["sport_canoe",KMLCOLOR,"circle"],								#Kayak, kayak rental
		"1598":["historic_castle",KMLCOLOR,"circle"],							#castle, ruins
		"1670":["building_type_church",KMLCOLOR,"circle"],						#church, mosque, temple
		"1877":["special_arrow_up_arrow_down",KMLCOLOR,"circle"],				#stairway, for OSMAnd it's up/down arrow icon
	}
	
	waypt = cWaypoint("unknown",KMLCOLOR,"circle")

	if not KMLIconID in iconDictionary:
		KMLIconID = "unknown"
	waypt.icon = iconDictionary[KMLIconID][0]
	if iconDictionary[KMLIconID][1] == KMLCOLOR:
		#use the icon color from the KML file
		waypt.color = KMLCOLOR
	else:
		#use the icon color from the dictionary table
		waypt.color = iconDictionary[KMLIconID][1]
	waypt.background = iconDictionary[KMLIconID][2]
	#print("icon:", waypt.icon, "color:", waypt.color, "background:",waypt.background)
	return(waypt)
#========================================================================================
# writeGPXFile
#========================================================================================
def writeGPXFile(gpx,outputFilename):
	# Create the ElementTree object with pretty printing options
	tree = ET.ElementTree(gpx)
	tree_str = ET.tostring(gpx, encoding="utf-8", xml_declaration=True)
	pretty_tree_str = minidom.parseString(tree_str).toprettyxml(indent="  ", encoding="utf-8").decode()

	# Write the pretty-printed GPX XML to a file
	try:
		with open(outputFilename, "w",encoding="utf-8") as f:
			f.write(pretty_tree_str)
		returnCode = 0
	except Exception as e:
		print(f"  Error: An unexpected error occurred writing GPX file: {outputFilename} {str(e)}")
		returnCode = 10
	return(returnCode)
#========================================================================================
# addGPXElement
#========================================================================================
def addGPXElement():
	namespaces = {
			"xmlns":				"http://www.topografix.com/GPX/1/1",
			"xmlns:xsi":			"http://www.w3.org/2001/XMLSchema-instance",
			"xsi:schemaLocation":	"http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd",
			"xmlns:osmand":			"https://osmand.net",
	}
	gpx = ET.Element("gpx", namespaces)
	gpx.set("version", "1.1")
	gpx.set("creator", PROGRAM_NAME+ " V"+PROGRAM_VERSION)
	return(gpx)
#========================================================================================
# getMapKMLData
#========================================================================================
def getMapKMLData(args):
	getURLRequest = GET_URL_PREFIX+str(args.map_id)+GET_URL_SUFFIX
	#print("  URLRequst:       ",getURLRequest)
	response = requests.get(getURLRequest)
	match response.status_code:
		case 200:
			# Successful GET request
			returnCode = 0
		case 403:
			print("  Error: 403 Share permision for map not set")
			returnCode = 403
		case 404:
			print("  Error: 404 Bad map ID value")
			returnCode = 404
		case _:
			print(f"  Error: An unexpected error occurred: {str(response.status_code)}")
			returnCode = response.status_code
	return(returnCode,response.text)
#========================================================================================
# processWaypoint
#========================================================================================
def processWaypoint(placemark,waypointGPX):
	print("  Waypoint: ", end="")
	coordinates = placemark.find(".//{http://www.opengis.net/kml/2.2}coordinates")
	name        = placemark.find(".//{http://www.opengis.net/kml/2.2}name")
	description = placemark.find(".//{http://www.opengis.net/kml/2.2}description")
	style_url   = placemark.findtext(".//{http://www.opengis.net/kml/2.2}styleUrl")

	if name is None:
		print("No name found, skipping waypoint,end=""")
	else:
		name = name.text.strip()
		print(name+" ", end="")

		if coordinates is None:
			print(" No coordinates found, skipping waypoint",end="")
		else:
			coordinates = coordinates.text.strip().split(",")
			longitude   = coordinates[0]
			latitude    = coordinates[1]
			elevation   = f"{float(coordinates[2]):.1f}"
			#print("["+latitude+","+longitude+","+elevation+"]",end="")
			# If it exists, add the description from the KML Placemark element
			if description is None:
				description = DEFAULT_WAYPOINT_DESCRIPTION
			else:
				description = description.text.strip()
			# add extensions elements
			# Use styleURL tag value to extract color and icon ID
			# New icons appear to be of this style with an icon ID and a color
			#	<styleUrl>#icon-1577-DB4436-labelson</styleUrl>
			# Old style icons come in two flavors, neither of which has color info
			#	<styleUrl>#icon-1369</styleUrl>
			#	<styleUrl>#icon-1085-labelson</styleUrl>
			#
			# if there is no color field (get an exception on trying to access the field)
			# then we will use the DEFAULT_ICON_COLOR value.  If the second field contains
			# the string "labelson" we'll also use the DEFAULT_ICON_COLOR value.
			# print("     style URL: ",style_url)
			if style_url:
				style = style_url.split("-")
				waypt = KMLToOSMAndIcon(style[1])
			else:
				waypt = KMLToOSMAndIcon("unknown")
			if waypt.color == KMLCOLOR: # we use value from KML file
				try:
					if style[2] == "labelson":  # there is no color value in styleURL string
						waypt.color = DEFAULT_ICON_COLOR
					else:
						waypt.color=style[2]
				except IndexError:
					waypt.color=DEFAULT_ICON_COLOR
			#print(" ["+waypt.icon+","+waypt.color+","+waypt.background+"]",end="")
			
			# Add the data into the waypoint GPX file
			waypointElement = ET.SubElement(waypointGPX, "wpt", lat=latitude, lon=longitude)
			ET.SubElement(waypointElement,"ele").text = elevation
			ET.SubElement(waypointElement, "name").text = name
			ET.SubElement(waypointElement, "desc").text = description
			extensionsElement = ET.SubElement(waypointElement,"extensions")
			ET.SubElement(extensionsElement,"osmand:icon").text = waypt.icon
			ET.SubElement(extensionsElement,"osmand:background").text = waypt.background
			ET.SubElement(extensionsElement, "osmand:color").text = "#" + waypt.color
	print("")
	return
#========================================================================================
# processTrack
#========================================================================================
def processTrack(placemark,args):
	print("  Track: ",end="")

	coordinates = placemark.find(".//{http://www.opengis.net/kml/2.2}coordinates")
	name        = placemark.find(".//{http://www.opengis.net/kml/2.2}name")
	description = placemark.find(".//{http://www.opengis.net/kml/2.2}description")

	if name is None:
		print("No name found, skipping track",end="")
	else:
		name = name.text.strip()
		print(name+" ", end="")

		if coordinates is None:
			print("No coordinates found, skipping track",end="")
		else:
			if description is None:
				description = DEFAULT_TRACK_DESCRIPTION
			else:
				description = description.text.strip()
			#print("description:>>>"+description+"<<<")
			GPXElement = addGPXElement()
			metadataElement   = ET.SubElement(GPXElement,"metadata")
			ET.SubElement(metadataElement, "desc").text = description
			trackElement = ET.SubElement(GPXElement,"trk")
			ET.SubElement(trackElement, "name").text = name
			coordinates = coordinates.text.strip().split()
			trksegElement = ET.SubElement(trackElement, "trkseg")
			# Iterate over the coordinates and create GPX trackpoints
			for coordinate in coordinates:
				longitude, latitude, altitude = coordinate.split(",")
				trackpointElement = ET.SubElement(trksegElement,"trkpt", lat=latitude, lon=longitude)
				if altitude is not None:
					ET.SubElement(trackpointElement, "ele").text = f"{float(altitude):.1f}"
			#   <styleUrl>#line-0F9D58-1000</styleUrl>
			#               [0]   [1]    [2]
			#                    color width
			#Color is standard RGB color with no transparency
			#Line width is 1000-32000.  This maps to 1.0-24.0 for OSMAnd line width
			style_url = placemark.findtext(".//{http://www.opengis.net/kml/2.2}styleUrl")
			if style_url:
				style = style_url.split("-")
				color = style[1]
				widthKML = style[2]
				# To scale the width range of 1000-32000 from the KML file to a range of 1-24
				# for OSMAnd in the gpx file, you can use the following formula:
				#		y = ((x - 1000) / 31000) * 23 + 1
				#		Where:
				#			x is the value in the original KML range of 1000-32000
				#			y is the scaled value in the GPX range of 1-24
				width = str(round(((int(widthKML) - 1000) / 31000) * 23 + 1))
			else:
				color = DEFAULT_TRACK_COLOR
				#width will default to whatever OSMAnd does
			color = "#" + args.transparency + color
			#print(" color: ",color,end="")
			#print(" width: ",width,end="")

			extensionsElement = ET.SubElement(GPXElement,"extensions")
			ET.SubElement(extensionsElement, "osmand:color").text = color
			# if a width is specified in the command line it is used for every track width,
			# overriding any value specified in the KML file
			if args.width is not None:
				width = str(args.width)
			ET.SubElement(extensionsElement, "osmand:width").text = width
			ET.SubElement(extensionsElement, "osmand:show_arrows").text = str(args.arrows).lower()
			ET.SubElement(extensionsElement, "osmand:show_start_finish").text = str(args.ends).lower()
			ET.SubElement(extensionsElement, "osmand:split_type").text = args.split
			#??? Can't get OSMAnd to recognize these extensions. If I activate them manually in OSMAnd and then export
			# the GPX file it appears to be the same tags in the same element. Arrows and ends work fine.
			if args.split == SPLIT_TYPE_TIME:
				#split time is in seconds and args.interval is in minutes, so convert.
				ET.SubElement(extensionsElement, "osmand:split_interval").text = str(int(float(args.interval) * 60))
			elif args.split == SPLIT_TYPE_DISTANCE:
				#split interval is in meters and args.interval is in miles, so convert miles to meters
				ET.SubElement(extensionsElement, "osmand:split_interval").text = f"{(float(args.interval) * 1609.34):.2f}"
			# Write track to a GPX file.  
			# Track file names are taken from the track name which may contain illegal finename characters.
			# Strip out these illegal characters.  Allow all alpha numerics and characters from allowedChars
			allowedChars = " ._-"
			name = "".join(i for i in name if (i.isalnum() or i in allowedChars))
			#print("  name: ",name,end="")
			filename = os.path.join(args.GPX_path, name+'.gpx')
			#print("  Writing track to file: ",filename,end="")
			returnCode = writeGPXFile(GPXElement,filename)
	print("")
	return(returnCode)
#========================================================================================
# Main
#========================================================================================
def main():
	global countTotalTracks
	global countTotalWaypoints

	# Parse the command line arguments
	args = setupParseCmdLine()

	waypointFileName = os.path.join(args.GPX_path, "WayPts-"+Path(args.GPX_path).stem+".gpx")

	print("")
	print("Google map to OSMAnd GPX file conversion, one track per file.")
	print("  Program:                ", PROGRAM_NAME)
	print("  Version:                ", PROGRAM_VERSION)
	print("  MapID:                  ", args.map_id)
	print("  Output folder:          ", args.GPX_path)
	print("  Waypt file name:        ", waypointFileName)
	print("  Transparency value: 0x  ", args.transparency)
	print("  Track width:            ", args.width)
	print("  Track split:            ", args.split)
	print("  Track split interval:   ", args.interval)
	print("  Track start/end icons:  ", args.ends)
	print("  Track direction arrows: ", args.arrows)
	print("")
	print("  Get map KML data")
	returnCode,KMLData = getMapKMLData(args)
	if returnCode == 0:
		
		# Create a folder for GPX files
		try:
			os.makedirs(args.GPX_path, exist_ok=True)
			# Create waypoint GPX file
			waypointGPX = addGPXElement()

			# Parse the KML data
			tree = ET.ElementTree(ET.fromstring(KMLData))
			root = tree.getroot()

			for placemark in root.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
				if placemark.find(".//{http://www.opengis.net/kml/2.2}Point") is not None:
					processWaypoint(placemark,waypointGPX)
					countTotalWaypoints += 1
				elif placemark.findall(".//{http://www.opengis.net/kml/2.2}LineString") is not None:
					returnCode = processTrack(placemark,args)
					if returnCode != 0:
						break	# error in processing track, stop further processing
					countTotalTracks += 1
			
			if returnCode == 0:
				if countTotalWaypoints > 0:
					# Write waypoints to a GPX file
					print(f"  Writing waypoints to file: {waypointFileName}")
					returnCode = writeGPXFile(waypointGPX,waypointFileName)
		except Exception as e:
			print(f"  Error: An unexpected error occurred creating GPX file directory: {str(e)}")
			returnCode = 9
	print("")
	print(f"  Total waypoint count: {countTotalWaypoints:>3}")
	print(f"  Total track count:    {countTotalTracks:>3}")
	print(f"  Return code:          {returnCode}")
	return(returnCode)
#========================================================================================
#
#========================================================================================
if __name__ == "__main__":
	sys.exit(main())
