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
# 5/20/2024: V1.1 Updated icon translation table 
# 6/7/2024:  V1.2 Added -l option to write out files as layers
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
PROGRAM_VERSION = "1.2"
DEFAULT_TRACK_TRANSPARENCY = "80"
DEFAULT_WAYPOINT_DESCRIPTION = ""
DEFAULT_TRACK_DESCRIPTION = ""
# Both of these should probably be command line arguments
DEFAULT_ICON_COLOR = "DB4436"	# rusty red.  If no color found in KML
ICON_NOT_FOUND_ICON  = "special_symbol_question_mark" # if KML icon is not in translation table
ICON_NOT_FOUND_COLOR = "e044bb"					# hot pink
ICON_NOT_FOUND_SHAPE = "octagon"
ICON_NO_TRANSLATION  = ICON_NOT_FOUND_ICON		#KML icon is in the table, but there is no good OSMAnd equivalent
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
countTotalLayers = 0
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
		help="Display distance or time splits along tracks. Default: "+str(DEFAULT_TRACK_SPLIT_TYPE)),
	parser.add_argument('-i', '--interval', 
		action='store',
		required=False,
		default=DEFAULT_TRACK_SPLIT_INTERVAL, 
		help="Distance in miles or time in seconds to display splits on track.  Split type must also be defined. Default: "+str(DEFAULT_TRACK_SPLIT_INTERVAL)),
	parser.add_argument('-l', '--layers', 
		action='store_true',
		required=False,
		help="If present, under the GPX path name a nested folder will be created for each, non-empty, layer found in the KML file.  Each of these folders will contain a single GPX file containing all of the waypoints in the KML file and one GPX file for each track found in the layer.")

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
# There is a nice GMap->OSMAnd icon translation proposal here: https://github.com/mariush444/gmapIcons2osmand/blob/main/icons-gmap-osmand.pdf
#
# ???: would be nice to have a command line option to read in a user supplied dictionary from a file
#========================================================================================
def KMLToOSMAndIcon(KMLIconID):

	iconDictionary ={
		"unknown":[ICON_NOT_FOUND_ICON, ICON_NOT_FOUND_COLOR, ICON_NOT_FOUND_SHAPE],	#unknown KML icon code - this entry will be used if the KML icon is not found the iconDictionary.
# These are some of the original gmap icons - bigger, bolder colors, without surrounding circle
		"503": ["special_marker",						KMLCOLOR,"circle"],			#OldGMap: school map point
		"979": ["special_sail_boat",					"a71de1","circle"],			#OldGMap: Passenger ferry - purple
		"993": ["special_photo_camera",					KMLCOLOR,"circle"],			#OldGMap: POI #1, camera "eecc22"
		"1023":["shop_supermarket",						KMLCOLOR,"circle"],			#OldGMap: grocery store, supermarket #2
		"1085":["restaurants",							KMLCOLOR,"circle"],			#OldGMap: retaurant, diner, dining
		"1095":["shop_department_store",				"10c0f0","circle"],			#OldGMap: Store/shopping - blue
		"1203":["tourism_information",					"1010a0","circle"],			#OldGMap: tourism information
		"1289":["Museum",								"10c0f0","circle"],			#OldGMap: Museum - light blue
		"1369":["special_trekking",						KMLCOLOR,"circle"],			#OldGMap: hiking trailhead 
		"1371":["special_trekking",						KMLCOLOR,"circle"],			#OldGMap: hiking trailhead 
		"1395":["sport_swimming",						"eecc22","circle"],			#OldGMap: Lake/swimmer - yellow
# These are the new gmap style icons
# This list and most of the suggested translations come from this document
#    https://github.com/mariush444/gmapIcons2osmand/blob/main/icons-gmap-osmand.pdf
		"1498":["product_brick",						KMLCOLOR,"circle"],			# gmap:shape_default	little square	OSMAnd Alts: military,natural_peak, product_brick
		"1499":["skimap_white_black_round_shield",		KMLCOLOR,"circle"],			# gmap:shape_circle
		"1500":["glaziery",								KMLCOLOR,"circle"],			# gmap:shape_square						OSMAnd Alts: chess, glaziery
		"1501":["natural_peak",							KMLCOLOR,"circle"],			# gmap:shape_diamond					OSMAnd Alts: building_type_pyramid, flooring, natural_peak
		"1502":["special_star",							KMLCOLOR,"circle"],			# gmap:shape_star						OSMAnd Alts:  shape_star, special_star, special_star_stroked (hollow), tourism_attraction,tourism_yes
		"1503":["erotic",								KMLCOLOR,"circle"],			# gmap:adult-xxx
		"1504":["air_transport",						KMLCOLOR,"circle"],			# gmap:airport-plane
		"1505":["emergency",							KMLCOLOR,"circle"],			# gmap:ambulance
		"1506":["shop_pet",								KMLCOLOR,"circle"],			# gmap:animal-head
		"1507":["shop_pet",								KMLCOLOR,"circle"],			# gmap:animal-paw
		"1508":["animal_shelter",						KMLCOLOR,"circle"],			# gmap:animal-shelter
		"1509":["amenity_arts_centre",					KMLCOLOR,"circle"],			# gmap:art-palette
		"1510":["amenity_atm",							KMLCOLOR,"circle"],			# gmap:atm
		"1511":["attraction_carousel",					KMLCOLOR,"circle"],			# gmap:balloons
		"1512":["amenity_bank",							KMLCOLOR,"circle"],			# gmap:bank-dollar
		"1513":["amenity_bank",							KMLCOLOR,"circle"],			# gmap:bank-euro
		"1514":["amenity_bank",							KMLCOLOR,"circle"],			# gmap:bank-pound
		"1515":["amenity_bank",							KMLCOLOR,"circle"],			# gmap:bank-yen
		"1516":["shop_hairdresser",						KMLCOLOR,"circle"],			# gmap:barber-scissors
		"1517":["amenity_bar",							KMLCOLOR,"circle"],			# gmap:bar-cocktail
		"1518":["amenity_pub",							KMLCOLOR,"circle"],			# gmap:bar-pub
		"1519":["sport_baseball",						KMLCOLOR,"circle"],			# gmap:baseball
		"1520":["sport_basketball",						KMLCOLOR,"circle"],			# gmap:basketball
		"1521":["leisure_beach_resort",					KMLCOLOR,"circle"],			# gmap:beach						OSMAnd Alts: beach, leisure_beach_resort
		"1522":["special_bicycle",						KMLCOLOR,"circle"],			# gmap:bicycle
		"1523":["supervised_yes",						KMLCOLOR,"circle"],			# gmap:binoculars
		"1524":["hazard",								KMLCOLOR,"circle"],			# gmap:biohazard
		"1525":["leisure_slipway",						KMLCOLOR,"circle"],			# gmap:boat-launch
		"1526":["shop_books",							KMLCOLOR,"circle"],			# gmap:book
		"1527":["sport_9pin",							KMLCOLOR,"circle"],			# gmap:bowling
		"1528":["bridge_structure_arch",				KMLCOLOR,"circle"],			# gmap:bridge
		"1529":["communication_tower",					KMLCOLOR,"circle"],			# gmap:broadcast
		"1530":["restaurants",							KMLCOLOR,"circle"],			# gmap:burger
		"1531":["bag",									KMLCOLOR,"circle"],			# gmap:business-briefcase
		"1532":["highway_bus_stop",						KMLCOLOR,"circle"],			# gmap:bus
		"1533":["funicular",							KMLCOLOR,"circle"],			# gmap:cablecar-funicular
		"1534":["amenity_cafe",							KMLCOLOR,"circle"],			# gmap:cafe-cup
		"1535":["camera",								KMLCOLOR,"circle"],			# gmap:camera-photo
		"1536":["sport_canoe",							KMLCOLOR,"circle"],			# gmap:canoe
		"1537":["cargo_vehicle",						KMLCOLOR,"circle"],			# gmap:car-ferry
		"1538":["shop_car",								KMLCOLOR,"circle"],			# gmap:car
		"1539":["shop_car_repair",						KMLCOLOR,"circle"],			# gmap:car-repair
		"1540":["amenity_casino",						KMLCOLOR,"circle"],			# gmap:casino-dice
		"1541":["hazard",								KMLCOLOR,"circle"],			# gmap:caution
		"1542":["cemetery",								KMLCOLOR,"circle"],			# gmap:cemetery
		"1543":["drinking_water_yes",					KMLCOLOR,"circle"],			# gmap:chance-rain
		"1544":["chemist",								KMLCOLOR,"circle"],			# gmap:chemical-beaker
		"1545":["dovecote",								KMLCOLOR,"circle"],			# gmap:chicken
		"1546":["place_city",							KMLCOLOR,"circle"],			# gmap:city-buildings
		"1547":["suburb",								KMLCOLOR,"circle"],			# gmap:city-buildings-pointed
		"1548":["building",								KMLCOLOR,"circle"],			# gmap:civic
		"1549":["shop_clothes",							KMLCOLOR,"circle"],			# gmap:clothing-hanger
		"1550":["cuisine",								KMLCOLOR,"circle"],			# gmap:cloudy
		"1551":["service",								KMLCOLOR,"circle"],			# gmap:construction-hammer
		"1552":["amenity_courthouse",					KMLCOLOR,"circle"],			# gmap:courthouse-gavel
		"1553":["shop_pet",								KMLCOLOR,"circle"],			# gmap:cow
		"1554":["sport_cricket",						KMLCOLOR,"circle"],			# gmap:cricket
		"1555":["payment_centre",						KMLCOLOR,"circle"],			# gmap:currency-exchange
		"1556":["hazard",								KMLCOLOR,"circle"],			# gmap:death-skull
		"1557":["amenity_dentist",						KMLCOLOR,"circle"],			# gmap:dentist-tooth
		"1558":["amenity_doctors",						KMLCOLOR,"circle"],			# gmap:doctor-bag
		"1559":["tourism_hostel",						KMLCOLOR,"circle"],			# gmap:dormitory-bunk-bed
		"1560":["hazard",								KMLCOLOR,"circle"],			# gmap:earthquake
		"1561":["electrical",							KMLCOLOR,"circle"],			# gmap:electrical-plug
		"1562":["shop_car",								KMLCOLOR,"circle"],			# gmap:enclosed-traffic
		"1563":["military_range",						KMLCOLOR,"circle"],			# gmap:epicenter					OSMAnd Alts: craft_sawmill, motorcycle_parts_yes,military_range
		"1564":["crater",								KMLCOLOR,"circle"],			# gmap:explosion					OSMAnd Alts: amenity_fire_station, crater
		"1565":["industrial",							KMLCOLOR,"circle"],			# gmap:factory
		"1566":["place_farm",							KMLCOLOR,"circle"],			# gmap:farm-barn
		"1567":["amenity_fast_food",					KMLCOLOR,"circle"],			# gmap:fast-food
		"1568":["attraction_big_wheel",					KMLCOLOR,"circle"],			# gmap:ferris-wheel
		"1569":["amenity_ferry_terminal",				KMLCOLOR,"circle"],			# gmap:ferry
		"1570":["finance",								KMLCOLOR,"circle"],			# gmap:finance
		"1571":["amenity_fire_station",					KMLCOLOR,"circle"],			# gmap:fire
		"1572":["shop_seafood",							KMLCOLOR,"circle"],			# gmap:fish-fins
		"1573":["shop_seafood",							KMLCOLOR,"circle"],			# gmap:fish
		"1574":["special_flag_start",					KMLCOLOR,"circle"],			# gmap:flag							OSMAnd Alts: locality,special_flag_finish,special_flag (triangle), special_flag_start (square), special_flag_stroke (hollow triangle), windsock (striped triangle)
		"1575":["hazard_flood",							KMLCOLOR,"circle"],			# gmap:flood
		"1576":["amenity_pharmacy",						KMLCOLOR,"circle"],			# gmap:fog
		"1577":["restaurants",							KMLCOLOR,"circle"],			# gmap:food-fork-knife
		"1578":["food_shop",							KMLCOLOR,"circle"],			# gmap:food-groceries
		"1579":["american_football",					KMLCOLOR,"circle"],			# gmap:football
		"1580":["amenity_fountain",						KMLCOLOR,"circle"],			# gmap:fountain
		"1581":["amenity_fuel",							KMLCOLOR,"circle"],			# gmap:fuel-gasoline
		"1582":["garden",								KMLCOLOR,"circle"],			# gmap:garden-flower
		"1583":["barrier_lift_gate",					KMLCOLOR,"circle"],			# gmap:gated-community
		"1584":["shop_gift",							KMLCOLOR,"circle"],			# gmap:gift
		"1585":["sport_golf",							KMLCOLOR,"circle"],			# gmap:golf
		"1586":["aerialway_gondola",					KMLCOLOR,"circle"],			# gmap:gondola
		"1587":["agrarian",								KMLCOLOR,"circle"],			# gmap:grain
		"1588":["weapons",								KMLCOLOR,"circle"],			# gmap:gun
		"1589":["fitness_centre",						KMLCOLOR,"circle"],			# gmap:gym
		"1590":["service",								KMLCOLOR,"circle"],			# gmap:hardware-wrench
		"1591":["ranger_station",						KMLCOLOR,"circle"],			# gmap:headquarters
		"1592":["special_heart",						KMLCOLOR,"circle"],			# gmap:heart
		"1593":["special_helicopter",					KMLCOLOR,"circle"],			# gmap:helicopter
		"1594":["special_symbol_question_mark",			KMLCOLOR,"circle"],			# gmap:help
		"1595":["special_trekking",						KMLCOLOR,"circle"],			# gmap:hiking-duo
		"1596":["special_trekking",						KMLCOLOR,"circle"],			# gmap:hiking-solo
		"1597":["special_trekking",						KMLCOLOR,"circle"],			# gmap:hiking-trailhead
		"1598":["historic_castle",						KMLCOLOR,"circle"],			# gmap:historic-building
		"1599":["monument",								KMLCOLOR,"circle"],			# gmap:historic-monument
		"1600":["memorial_plaque",						KMLCOLOR,"circle"],			# gmap:historic-plaque
		"1601":["special_horse",						KMLCOLOR,"circle"],			# gmap:horse
		"1602":["tourism_hotel",						KMLCOLOR,"circle"],			# gmap:hotel-bed
		"1603":["special_house",						KMLCOLOR,"circle"],			# gmap:house
		"1604":["construction",							KMLCOLOR,"circle"],			# gmap:housing-development
		"1605":["hazard",								KMLCOLOR,"circle"],			# gmap:hurricane-strong
		"1606":["hazard",								KMLCOLOR,"circle"],			# gmap:hurricane-weak
		"1607":["ice_cream",							KMLCOLOR,"circle"],			# gmap:ice-cream
		"1608":["special_information",					KMLCOLOR,"circle"],			# gmap:info
		"1609":["special_symbol_at_sign",				KMLCOLOR,"circle"],			# gmap:internet
		"1610":["cemetery",								KMLCOLOR,"circle"],			# gmap:japanese-cemetery
		"1611":["special_marker",						KMLCOLOR,"circle"],			# gmap:japanese-poi
		"1612":["amenity_post_box",						KMLCOLOR,"circle"],			# gmap:japanese-post-office
		"1613":["shop_jewelry",							KMLCOLOR,"circle"],			# gmap:jewelry
		"1614":["special_microphone",					KMLCOLOR,"circle"],			# gmap:karaoke
		"1615":["special_kayak",						KMLCOLOR,"circle"],			# gmap:kayak
		"1616":["hazard_erosion",						KMLCOLOR,"circle"],			# gmap:landslide
		"1617":["shop_laundry",							KMLCOLOR,"circle"],			# gmap:laundry-iron
		"1618":["man_made_lighthouse",					KMLCOLOR,"circle"],			# gmap:lighthouse
		"1619":["power",								KMLCOLOR,"circle"],			# gmap:lightning???
		"1620":["shop_pet",								KMLCOLOR,"circle"],			# gmap:lizard-gecko
		"1621":["observation_tower",					KMLCOLOR,"circle"],			# gmap:lookout-tower
		"1622":["special_sail_boat",					KMLCOLOR,"circle"],			# gmap:marina-yacht
		"1623":["leisure_marina",						KMLCOLOR,"circle"],			# gmap:marine-anchor
		"1624":["amenity_doctors",						KMLCOLOR,"circle"],			# gmap:medical 				OSMAnd Alts: healthcare
		"1625":["siren",								KMLCOLOR,"circle"],			# gmap:megaphone
		"1626":["subway_caracas",						KMLCOLOR,"circle"],			# gmap:metro 				OSMAnd Alts: special_subway
		"1627":["man_made_mineshaft",					KMLCOLOR,"circle"],			# gmap:mine
		"1628":["special_symbol_question_mark",			KMLCOLOR,"circle"],			# gmap:missing-person
		"1629":["route_monorail_ref",					KMLCOLOR,"circle"],			# gmap:monorail
		"1630":["shop_pet",								KMLCOLOR,"circle"],			# gmap:monster-friend
		"1631":["backrest_yes",							KMLCOLOR,"circle"],			# gmap:moon
		"1632":["special_motor_scooter",				KMLCOLOR,"circle"],			# gmap:moped
		"1633":["shop_motorcycle",						KMLCOLOR,"circle"],			# gmap:motorcycle
		"1634":["natural",								KMLCOLOR,"circle"],			# gmap:mountain
		"1635":["amenity_cinema",						KMLCOLOR,"circle"],			# gmap:movies-cinema
		"1636":["tourism_museum",						KMLCOLOR,"circle"],			# gmap:museum
		"1637":["special_audio",						KMLCOLOR,"circle"],			# gmap:music-note			OSMAnd Alts: music, special_audio
		"1638":["newspaper",							KMLCOLOR,"circle"],			# gmap:newspaper
		"1639":["ngo",									KMLCOLOR,"circle"],			# gmap:ngo
		"1640":["restaurants",							KMLCOLOR,"circle"],			# gmap:noodles
		"1641":["generator_source_nuclear",				KMLCOLOR,"circle"],			# gmap:nuclear-atomic
		"1642":["hazard_nuclear",						KMLCOLOR,"circle"],			# gmap:nuclear-radioactive
		"1643":["shop_optician",						KMLCOLOR,"circle"],			# gmap:optometrist-eye
		"1644":["parking",								KMLCOLOR,"circle"],			# gmap:parking
		"1645":["cuisine",								KMLCOLOR,"circle"],			# gmap:partly-cloudy
		"1646":["amenity_pharmacy",						KMLCOLOR,"circle"],			# gmap:pharmacy
		"1647":["shop_mobile_phone",					KMLCOLOR,"circle"],			# gmap:phone-mobile
		"1649":["barrier_cycle_barrier",				KMLCOLOR,"circle"],			# gmap:piano-music-hall
		"1650":["tourism_picnic_site",					KMLCOLOR,"circle"],			# gmap:picnic-table
		"1651":["restaurants",							KMLCOLOR,"circle"],			# gmap:pizza-slice
		"1652":["leisure_playground",					KMLCOLOR,"circle"],			# gmap:playground-swing
		"1653":["hazard",								KMLCOLOR,"circle"],			# gmap:poison-gas-mask
		"1654":["geocache",								KMLCOLOR,"circle"],			# gmap:poi-you-are-here
		"1655":["amenity_police",						KMLCOLOR,"circle"],			# gmap:police-badge
		"1656":["amenity_police",						KMLCOLOR,"circle"],			# gmap:police-car
		"1657":["amenity_police",						KMLCOLOR,"circle"],			# gmap:police-officer
		"1658":["hazard",								KMLCOLOR,"circle"],			# gmap:pollution-spill
		"1659":["amenity_post_box",						KMLCOLOR,"circle"],			# gmap:post-office-envelope
		"1660":["power",								KMLCOLOR,"circle"],			# gmap:power-lightning
		"1661":["special_flag_finish",					KMLCOLOR,"circle"],			# gmap:racetrack-flag
		"1662":["railway_station",						KMLCOLOR,"circle"],			# gmap:railway-track
		"1663":["drinking_water_yes",					KMLCOLOR,"circle"],			# gmap:rain
		"1664":["amenity_library",						KMLCOLOR,"circle"],			# gmap:reading-library
		"1665":["beach",								KMLCOLOR,"circle"],			# gmap:real-estate
		"1666":["place_of_worship",						KMLCOLOR,"circle"],			# gmap:religious-bahai
		"1667":["religion_buddhist",					KMLCOLOR,"circle"],			# gmap:religious-buddhist-hindu
		"1668":["religion_buddhist",					KMLCOLOR,"circle"],			# gmap:religious-buddhist-wheel
		"1669":["place_of_worship",						KMLCOLOR,"circle"],			# gmap:religious-buddhist-zen
		"1670":["religion_christian",					KMLCOLOR,"circle"],			# gmap:religious-christian
		"1671":["building_type_chapel",					KMLCOLOR,"circle"],			# gmap:religious-generic
		"1672":["religion_hindu",						KMLCOLOR,"circle"],			# gmap:religious-hindu
		"1673":["religion_muslim",						KMLCOLOR,"circle"],			# gmap:religious-islamic
		"1674":["place_of_worship",						KMLCOLOR,"circle"],			# gmap:religious-jain
		"1675":["religion_jewish",						KMLCOLOR,"circle"],			# gmap:religious-jewish
		"1676":["place_of_worship",						KMLCOLOR,"circle"],			# gmap:religious-kneeling
		"1677":["religion_shinto",						KMLCOLOR,"circle"],			# gmap:religious-shinto
		"1678":["religion_sikh",						KMLCOLOR,"circle"],			# gmap:religious-sikh
		"1679":["shop_pet",								KMLCOLOR,"circle"],			# gmap:rodent-rat
		"1680":["special_walking",						KMLCOLOR,"circle"],			# gmap:running-pedestrian
		"1681":["sport_sailing",						KMLCOLOR,"circle"],			# gmap:sailing-boat
		"1682":["amenity_school",						KMLCOLOR,"circle"],			# gmap:school-crossing
		"1683":["shop_shoes",							KMLCOLOR,"circle"],			# gmap:shoe
		"1684":["shop",									KMLCOLOR,"circle"],			# gmap:shopping-bag
		"1685":["shop_supermarket",						KMLCOLOR,"circle"],			# gmap:shopping-cart
		"1686":["food_shop",							KMLCOLOR,"circle"],			# gmap:shop
		"1687":["shower",								KMLCOLOR,"circle"],			# gmap:shower-bath
		"1688":["sport_skiing",							KMLCOLOR,"circle"],			# gmap:ski-downhill
		"1689":["aerialway_chair_lift",					KMLCOLOR,"circle"],			# gmap:ski-lift
		"1690":["special_ski_touring",					KMLCOLOR,"circle"],			# gmap:ski-xc
		"1691":["piste_sled",							KMLCOLOR,"circle"],			# gmap:sled
		"1692":["seasonal_winter",						KMLCOLOR,"circle"],			# gmap:sleet
		"1693":["man_made_chimney",						KMLCOLOR,"circle"],			# gmap:smokestack
		"1694":["seasonal_winter",						KMLCOLOR,"circle"],			# gmap:snowflake
		"1695":["seasonal_winter",						KMLCOLOR,"circle"],			# gmap:snow
		"1696":["sport_soccer",							KMLCOLOR,"circle"],			# gmap:soccer
		"1697":["tanning_salon",						KMLCOLOR,"circle"],			# gmap:spa
		"1698":["sport_stadium",						KMLCOLOR,"circle"],			# gmap:stadium-arena
		"1699":["bag",									KMLCOLOR,"circle"],			# gmap:suitcase-travel
		"1700":["seasonal_summer",						KMLCOLOR,"circle"],			# gmap:sunny
		"1701":["sport_swimming",						KMLCOLOR,"circle"],			# gmap:swimming
		"1702":["water_tap",							KMLCOLOR,"circle"],			# gmap:tap-dry
		"1703":["water_tap",							KMLCOLOR,"circle"],			# gmap:tap-flowing
		"1704":["special_taxi",							KMLCOLOR,"circle"],			# gmap:taxi
		"1705":["tea",									KMLCOLOR,"circle"],			# gmap:teapot
		"1706":["historic_castle",						KMLCOLOR,"circle"],			# gmap:temple
		"1707":["sport_tennis",							KMLCOLOR,"circle"],			# gmap:tennis
		"1708":["amenity_theatre",						KMLCOLOR,"circle"],			# gmap:theater-lecture
		"1709":["amenity_theatre",						KMLCOLOR,"circle"],			# gmap:theater
		"1710":["temperature",							KMLCOLOR,"circle"],			# gmap:thermometer				OSMAnd Alts: height,skimap_arrow_2triangles_black_big,special_arrow_up_and_down,thermometer
		"1711":["power",								KMLCOLOR,"circle"],			# gmap:thunder
		"1712":["shop_ticket",							KMLCOLOR,"circle"],			# gmap:ticket
		"1713":["shop_ticket",							KMLCOLOR,"circle"],			# gmap:ticket-star
		"1714":["hazard",								KMLCOLOR,"circle"],			# gmap:tornado
		"1715":["special_poi_eiffel_tower",				KMLCOLOR,"circle"],			# gmap:tower
		"1716":["railway_station",						KMLCOLOR,"circle"],			# gmap:train
		"1717":["locomotive",							KMLCOLOR,"circle"],			# gmap:train-steam
		"1718":["railway_tram_stop",					KMLCOLOR,"circle"],			# gmap:tram-overhead
		"1719":["railway_tram_stop",					KMLCOLOR,"circle"],			# gmap:tram
		"1720":["forest",								KMLCOLOR,"circle"],			# gmap:tree
		"1721":["forest",								KMLCOLOR,"circle"],			# gmap:tree-windy
		"1722":["special_truck",						KMLCOLOR,"circle"],			# gmap:truck
		"1723":["water",								KMLCOLOR,"circle"],			# gmap:tsunami					OSMAnd Alts: grass, water, hazard
		"1724":["tunnel",								KMLCOLOR,"circle"],			# gmap:tunnel
		"1725":["electronics",							KMLCOLOR,"circle"],			# gmap:tv
		"1726":["amenity_university",					KMLCOLOR,"circle"],			# gmap:university
		"1727":["special_video_camera",					KMLCOLOR,"circle"],			# gmap:video
		"1728":["for_tourists",							KMLCOLOR,"circle"],			# gmap:vista-half
		"1729":["tourism_viewpoint",					KMLCOLOR,"circle"],			# gmap:vista					OSMAnd Alts: for_tourists, motorcycle_parts_yes, shop_florist, tourism_viewpoint
		"1730":["volcano",								KMLCOLOR,"circle"],			# gmap:volcano
		"1731":["special_walking",						KMLCOLOR,"circle"],			# gmap:walking-pedestrian
		"1732":["male_yes",								KMLCOLOR,"circle"],			# gmap:wc-men
		"1733":["amenity_toilets",						KMLCOLOR,"circle"],			# gmap:wc-unisex
		"1734":["female_yes",							KMLCOLOR,"circle"],			# gmap:wc-women
		"1735":["wheelchair_designated",				KMLCOLOR,"circle"],			# gmap:wheelchair-handicapped
		"1736":["windsock",								KMLCOLOR,"circle"],			# gmap:wind
		"1737":["training_yoga",						KMLCOLOR,"circle"],			# gmap:yoga
		"1739":["military",								KMLCOLOR,"circle"],			# gmap:blank-measle 			OSMAnd Alts: military,barrier_bus_trap, fire_hydrant_type_underground, 
		"1740":["amenity_school",						KMLCOLOR,"circle"],			# gmap:academy
		"1741":["amenity_car_rental",					KMLCOLOR,"circle"],			# gmap:car-rental
		"1742":["baby_hatch",							KMLCOLOR,"circle"],			# gmap:baby-nursery
		"1743":["tourism_zoo",							KMLCOLOR,"circle"],			# gmap:zoo-elephant
		"1745":["1787",									KMLCOLOR,"circle"],			# gmap:charging_station_filter
		"1746":["1787",									KMLCOLOR,"circle"],			# gmap:charging_station
		"1747":["billiards",							KMLCOLOR,"circle"],			# gmap:8ball
		"1748":["hazard",								KMLCOLOR,"circle"],			# gmap:accident
		"1749":["defibrillator",						KMLCOLOR,"circle"],			# gmap:aed
		"1750":["air_transport",						KMLCOLOR,"circle"],			# gmap:airstrip
		"1751":["telescope",							KMLCOLOR,"circle"],			# gmap:alien
		"1752":["sport_archery",						KMLCOLOR,"circle"],			# gmap:archery
		"1753":["amenity_atm",							KMLCOLOR,"circle"],			# gmap:atm-intl
		"1754":["special_utv",							KMLCOLOR,"circle"],			# gmap:atv
		"1755":["badminton",							KMLCOLOR,"circle"],			# gmap:badminton
		"1756":["amenity_bank",							KMLCOLOR,"circle"],			# gmap:bank-intl
		"1757":["amenity_bank",							KMLCOLOR,"circle"],			# gmap:bank-jp
		"1758":["amenity_bank",							KMLCOLOR,"circle"],			# gmap:bank-won
		"1759":["shop_pet",								KMLCOLOR,"circle"],			# gmap:bear
		"1760":["leisure_bird_hide",					KMLCOLOR,"circle"],			# gmap:birdwatching
		"1761":[ICON_NO_TRANSLATION,					KMLCOLOR,"circle"],			# gmap:boxing
		"1762":["pastry",								KMLCOLOR,"circle"],			# gmap:cake-birthday
		"1763":["special_camper",						KMLCOLOR,"circle"],			# gmap:camper
		"1764":["firepit",								KMLCOLOR,"circle"],			# gmap:campfire
		"1765":["tourism_camp_site",					KMLCOLOR,"circle"],			# gmap:camping_tent
		"1766":["shop_pet",								KMLCOLOR,"circle"],			# gmap:cat
		"1767":["natural_cave_entrance",				KMLCOLOR,"circle"],			# gmap:cave
		"1768":["natural_cave_entrance",				KMLCOLOR,"circle"],			# gmap:caving
		"1769":["special_symbol_check_mark",			KMLCOLOR,"circle"],			# gmap:checkmark
		"1770":["craft_sawmill",						KMLCOLOR,"circle"],			# gmap:city-office-jp
		"1771":["sport_climbing",						KMLCOLOR,"circle"],			# gmap:climbing-carabiner
		"1772":["sport_climbing_adventure",				KMLCOLOR,"circle"],			# gmap:climbing-ropes
		"1773":["dance_floor",							KMLCOLOR,"circle"],			# gmap:dancing
		"1774":["conference_centre",					KMLCOLOR,"circle"],			# gmap:deer
		"1776":["dovecote",								KMLCOLOR,"circle"],			# gmap:eagle
		"1777":["sport_diving",							KMLCOLOR,"circle"],			# gmap:diving
		"1778":["shop_pet",								KMLCOLOR,"circle"],			# gmap:dog
		"1779":["shop_seafood",							KMLCOLOR,"circle"],			# gmap:dolphin
		"1780":["dovecote",								KMLCOLOR,"circle"],			# gmap:duck
		"1781":["sanitary_dump_station",				KMLCOLOR,"circle"],			# gmap:dump-station
		"1782":["elevator",								KMLCOLOR,"circle"],			# gmap:elevator
		"1783":["building_entrance",					KMLCOLOR,"circle"],			# gmap:entrance
		"1784":["conveying_yes",						KMLCOLOR,"circle"],			# gmap:escalator-down
		"1785":["conveying_yes",						KMLCOLOR,"circle"],			# gmap:escalator-up
		"1786":["conveying_yes",						KMLCOLOR,"circle"],			# gmap:escalator
		"1787":["charging_station",						KMLCOLOR,"circle"],			# gmap:ev-station
		"1788":["historic_battlefield",					KMLCOLOR,"circle"],			# gmap:fencing
		"1789":["dovecote",								KMLCOLOR,"circle"],			# gmap:finch
		"1790":["fire_extinguisher",					KMLCOLOR,"circle"],			# gmap:fire-extinguisher
		"1791":["amenity_fire_station",					KMLCOLOR,"circle"],			# gmap:fire-jp
		"1792":["frozen_food",							KMLCOLOR,"circle"],			# gmap:food-storage
		"1793":["shop_pet",								KMLCOLOR,"circle"],			# gmap:fox
		"1794":["leisure_sports_centre",				KMLCOLOR,"circle"],			# gmap:frisbee
		"1795":["attraction_animal",					KMLCOLOR,"circle"],			# gmap:gator
		"1796":["dive",									KMLCOLOR,"circle"],			# gmap:ghost
		"1797":["attraction_animal",					KMLCOLOR,"circle"],			# gmap:giraffe
		"1798":["craft_winery",							KMLCOLOR,"circle"],			# gmap:glass 					OSMAnd Alts: amenity_bar, craft_winery, shop_alcohol
		"1799":["golf_course",							KMLCOLOR,"circle"],			# gmap:golf-course
		"1800":["barbecue",								KMLCOLOR,"circle"],			# gmap:grill
		"1801":["club_music",							KMLCOLOR,"circle"],			# gmap:guitar
		"1802":[ICON_NO_TRANSLATION,					KMLCOLOR,"circle"],			# gmap:hatchet
		"1803":["special_arrow_down_left",				KMLCOLOR,"circle"],			# gmap:here
		"1804":["historic_manor",						KMLCOLOR,"circle"],			# gmap:historic-cn
		"1805":["ice_hockey",							KMLCOLOR,"circle"],			# gmap:hockey
		"1806":["clinic",								KMLCOLOR,"circle"],			# gmap:hospital-crescent
		"1807":["clinic",								KMLCOLOR,"circle"],			# gmap:hospital-h
		"1808":["clinic",								KMLCOLOR,"circle"],			# gmap:hospital-shield
		"1809":["sauna",								KMLCOLOR,"circle"],			# gmap:hot-tub
		"1810":["restaurants",							KMLCOLOR,"circle"],			# gmap:hotdog
		"1811":["natural_hot_spring",					KMLCOLOR,"circle"],			# gmap:hotspring-onsen
		"1812":["amenity_hunting_stand",				KMLCOLOR,"circle"],			# gmap:hunting
		"1813":["reef",									KMLCOLOR,"circle"],			# gmap:jellyfish
		"1814":[ICON_NO_TRANSLATION,					KMLCOLOR,"circle"],			# gmap:jetski
		"1815":["attraction_animal",					KMLCOLOR,"circle"],			# gmap:kangaroo
		"1816":["kitchen",								KMLCOLOR,"circle"],			# gmap:kitchen
		"1817":[ICON_NO_TRANSLATION,					KMLCOLOR,"circle"],			# gmap:kitesurfing
		"1818":["dovecote",								KMLCOLOR,"circle"],			# gmap:kiwi
		"1819":["reef",									KMLCOLOR,"circle"],			# gmap:kraken
		"1820":["shop_computer",						KMLCOLOR,"circle"],			# gmap:laptop
		"1821":["shop_laundry",							KMLCOLOR,"circle"],			# gmap:laundry
		"1822":["attraction_animal",					KMLCOLOR,"circle"],			# gmap:lion
		"1823":["craft_locksmith",						KMLCOLOR,"circle"],			# gmap:locker
		"1824":["special_symbol_question_mark",			KMLCOLOR,"circle"],			# gmap:lost-and-found
		"1825":["judo",									KMLCOLOR,"circle"],			# gmap:martial-arts
		"1826":["emergency_access_point",				KMLCOLOR,"circle"],			# gmap:meeting-point
		"1827":[ICON_NO_TRANSLATION,					KMLCOLOR,"circle"],			# gmap:message-in-a-bottle
		"1828":["attraction_animal",					KMLCOLOR,"circle"],			# gmap:monkey
		"1829":["customs",								KMLCOLOR,"circle"],			# gmap:moose
		"1831":["dance_floor",							KMLCOLOR,"circle"],			# gmap:mosquito
		"1832":["deadlock",								KMLCOLOR,"circle"],			# gmap:moustache
		"1834":["tourism_museum",						KMLCOLOR,"circle"],			# gmap:museum-jp
		"1835":["restaurants",							KMLCOLOR,"circle"],			# gmap:musubi-sushi
		"1836":["smoking_no",							KMLCOLOR,"circle"],			# gmap:no-smoking
		"1837":["piste_nordic",							KMLCOLOR,"circle"],			# gmap:nordic-walking
		"1838":["sport_free_flying",					KMLCOLOR,"circle"],			# gmap:parachute
		"1839":["dovecote",								KMLCOLOR,"circle"],			# gmap:parrot
		"1840":["dovecote",								KMLCOLOR,"circle"],			# gmap:penguin
		"1841":["amenity_pharmacy",						KMLCOLOR,"circle"],			# gmap:pharmacy-eu
		"1842":["amenity_police",						KMLCOLOR,"circle"],			# gmap:police-jp
		"1843":["equestrian",							KMLCOLOR,"circle"],			# gmap:polo
		"1844":["shop_baby_goods",						KMLCOLOR,"circle"],			# gmap:pram-stroller
		"1845":["shop_copyshop",						KMLCOLOR,"circle"],			# gmap:printer
		"1846":["dovecote",								KMLCOLOR,"circle"],			# gmap:quotation
		"1847":["hunting",								KMLCOLOR,"circle"],			# gmap:rabbit
		"1848":["shop_pet",								KMLCOLOR,"circle"],			# gmap:raccoon
		"1849":["sport_tennis",							KMLCOLOR,"circle"],			# gmap:racquetball
		"1850":["recycling_centre",						KMLCOLOR,"circle"],			# gmap:recycling
		"1851":["attraction_animal",					KMLCOLOR,"circle"],			# gmap:rhino
		"1852":[ICON_NO_TRANSLATION,					KMLCOLOR,"circle"],			# gmap:roach
		"1853":["quarry",								KMLCOLOR,"circle"],			# gmap:road-work-construction
		"1854":["educational_institution",				KMLCOLOR,"circle"],			# gmap:robot
		"1856":["telescope",							KMLCOLOR,"circle"],			# gmap:rocket
		"1857":["waste_basket",							KMLCOLOR,"circle"],			# gmap:rubbish-trash
		"1858":["sport_rugby_union",					KMLCOLOR,"circle"],			# gmap:rugby
		"1859":["special_campervan",					KMLCOLOR,"circle"],			# gmap:rv
		"1860":["amenity_school",						KMLCOLOR,"circle"],			# gmap:school-cn
		"1861":["sport_scuba_diving",					KMLCOLOR,"circle"],			# gmap:scuba
		"1862":["email",								KMLCOLOR,"circle"],			# gmap:seal
		"1863":["shop_seafood",							KMLCOLOR,"circle"],			# gmap:shark
		"1864":["wreck",								KMLCOLOR,"circle"],			# gmap:shipwreck
		"1865":["shower",								KMLCOLOR,"circle"],			# gmap:showers
		"1866":["sport_skateboard",						KMLCOLOR,"circle"],			# gmap:skateboarding
		"1867":["ice_skating",							KMLCOLOR,"circle"],			# gmap:skating-ice
		"1868":["smoking_yes",							KMLCOLOR,"circle"],			# gmap:smoking
		"1869":[ICON_NO_TRANSLATION,					KMLCOLOR,"circle"],			# gmap:snake
		"1870":["scuba_diving_shop",					KMLCOLOR,"circle"],			# gmap:snorkel
		"1871":["entertainment",						KMLCOLOR,"circle"],			# gmap:snowboarding
		"1872":["special_snowmobile",					KMLCOLOR,"circle"],			# gmap:snowmobile
		"1873":["piste_hike",							KMLCOLOR,"circle"],			# gmap:snowshoeing
		"1874":["dovecote",								KMLCOLOR,"circle"],			# gmap:songbird
		"1875":["sport_tennis",							KMLCOLOR,"circle"],			# gmap:squash
		"1876":["shop_pet",								KMLCOLOR,"circle"],			# gmap:squirrel
		"1877":["highway_steps",						KMLCOLOR,"circle"],			# gmap:stairs
		"1878":["telescope_type_optical",				KMLCOLOR,"circle"],			# gmap:stargazing-telescope
		"1879":["amenity_biergarten",					KMLCOLOR,"circle"],			# gmap:stein-beer
		"1880":["sport_surfing",						KMLCOLOR,"circle"],			# gmap:surfing
		"1881":["sport_sailing",						KMLCOLOR,"circle"],			# gmap:tall-ship
		"1882":["reef",									KMLCOLOR,"circle"],			# gmap:tidepool-starfish
		"1883":["craft_agricultural_engines",			KMLCOLOR,"circle"],			# gmap:tractor
		"1884":["highway_traffic_signals",				KMLCOLOR,"circle"],			# gmap:traffic-light
		"1885":[ICON_NO_TRANSLATION,					KMLCOLOR,"circle"],			# gmap:treasure-chest
		"1886":["nature_reserve",						KMLCOLOR,"circle"],			# gmap:tree-deciduous
		"1887":["female_no",							KMLCOLOR,"circle"],			# gmap:tree-palm
		"1888":["reef",									KMLCOLOR,"circle"],			# gmap:turtle
		"1889":["telescope",							KMLCOLOR,"circle"],			# gmap:ufo
		"1890":["sport_volleyball",						KMLCOLOR,"circle"],			# gmap:volleyball
		"1891":["backrest_yes",							KMLCOLOR,"circle"],			# gmap:waiting-room
		"1892":["waterfall",							KMLCOLOR,"circle"],			# gmap:waterfall
		"1893":["sports_hall",							KMLCOLOR,"circle"],			# gmap:weight-barbell
		"1894":["shop_seafood",							KMLCOLOR,"circle"],			# gmap:whale					OSMAnd Alts: shop_seafood, leisure_fishing, reef
		"1895":["internet_access_wlan",					KMLCOLOR,"circle"],			# gmap:wifi
		"1896":["firepit",								KMLCOLOR,"circle"],			# gmap:windsurfing
		"1897":["free_flying",							KMLCOLOR,"circle"],			# gmap:wingsuit
		"1898":["special_symbol_remove",				KMLCOLOR,"circle"],			# gmap:x-cross					OSMAnd Alts: level_crossing, special_symbol_remove
		"1899":["special_marker",						KMLCOLOR,"circle"],			# gmap:blank-shape_pin
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
			print(f"  ERROR: 403 Share permision for map not set")
			returnCode = 403
		case 404:
			print(f"  ERROR: 404 Bad map ID value")
			returnCode = 404
		case _:
			print(f"  ERROR: An unexpected error occurred: {str(response.status_code)}")
			returnCode = response.status_code
	return(returnCode,response.text)
#========================================================================================
# processWaypoint
#========================================================================================
def processWaypoint(placemark,waypointGPX):
	print(f"      Waypoint: ", end="")
	coordinates = placemark.find(".//{http://www.opengis.net/kml/2.2}coordinates")
	name        = placemark.find(".//{http://www.opengis.net/kml/2.2}name")
	description = placemark.find(".//{http://www.opengis.net/kml/2.2}description")
	style_url   = placemark.findtext(".//{http://www.opengis.net/kml/2.2}styleUrl")

	if name is None:
		print(f"No name found, skipping waypoint",end="")
	else:
		name = name.text.strip()
		print(f"{name} ", end="")

		if coordinates is None:
			print(f" No coordinates found, skipping waypoint",end="")
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
	return(0)
#========================================================================================
# processTrack
#========================================================================================
def processTrack(placemark,args,layerFolderName):
	print(f"      Track:    ",end="")

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
			filename = os.path.join(layerFolderName, name+'.gpx')
			#print("  Writing track to file: ",filename,end="")
			returnCode = writeGPXFile(GPXElement,filename)
	print("")
	return(returnCode)
#========================================================================================
# 
#========================================================================================
def processLayer(element,args):
	global countTotalTracks
	global countTotalWaypoints
	global countTotalLayers
	returnCode = 0
	countLayerTracks = 0
	countLayerWaypoints = 0
	countTotalLayers += 1

	# all waypoints get put into the same GPX file
	waypointGPX = addGPXElement()
	if args.layers:
		# Extract the layer name from the KML file
		layerName = element.find('{http://www.opengis.net/kml/2.2}name').text
		layerFolderName = os.path.join(args.GPX_path, Path(args.GPX_path).stem+"-"+layerName)
		layerFolderName = os.path.join(args.GPX_path, layerName)
		print(f"    Layer #{countTotalLayers:>2}    layer: {layerName}")
		print(f"      Output directory: {layerFolderName}")
		# Create a directory for the layer's GPX files
		try:
			os.makedirs(layerFolderName, exist_ok=True)
		except Exception as e:
			print(f"      ERROR: An unexpected error occurred creating layer GPX file directory: {str(e)}")
			return(10)
	else:
		layerFolderName = args.GPX_path

	for placemark in element.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
		if placemark.find(".//{http://www.opengis.net/kml/2.2}Point") is not None:
			returnCode = processWaypoint(placemark,waypointGPX)
			if returnCode != 0:
				return(returnCode)
			countLayerWaypoints += 1
			countTotalWaypoints += 1
		elif placemark.findall(".//{http://www.opengis.net/kml/2.2}LineString") is not None:
			returnCode = processTrack(placemark,args,layerFolderName)
			if returnCode != 0:
				break	# error in processing track, stop further processing
			countLayerTracks += 1
			countTotalTracks += 1

	if countLayerWaypoints > 0:
		# Write waypoints to a GPX file
		waypointFileName = os.path.join(layerFolderName, "WayPts.gpx")
		print(f"      Writing waypoints to file: {waypointFileName}")
		returnCode = writeGPXFile(waypointGPX,waypointFileName)
		if returnCode != 0:
			return(returnCode)

	print(f"      Waypoints: {countLayerWaypoints:>3}")
	print(f"      Tracks:    {countLayerTracks:>3}")
	return(0)
#========================================================================================
# Main
#========================================================================================
def main():
	global countTotalTracks
	global countTotalWaypoints
	global countTotalLayers

	# Parse the command line arguments
	args = setupParseCmdLine()

	layerFolderPrefix = args.GPX_path

	print("")
	print("Google map to OSMAnd GPX file conversion, one track per file.")
	print("  Program:                ", PROGRAM_NAME)
	print("  Version:                ", PROGRAM_VERSION)
	print("  MapID:                  ", args.map_id)
	print("  Output folder:          ", args.GPX_path)
	print("  Separate layer folders: ", args.layers)
	if args.layers:
		print("  Layer folder prefix:    ", layerFolderPrefix)
	print("  Transparency value: 0x  ", args.transparency)
	print("  Track width:            ", args.width)
	print("  Track split:            ", args.split)
	print("  Track split interval:   ", args.interval)
	print("  Track start/end icons:  ", args.ends)
	print("  Track direction arrows: ", args.arrows)
	print("")
	print("  Get map KML data")
	returnCode,KMLData = getMapKMLData(args)
	#print(KMLData)
	if returnCode == 0:
		# Parse the KML data
		tree = ET.ElementTree(ET.fromstring(KMLData))
		root = tree.getroot()
		mapName = root.find(".//{http://www.opengis.net/kml/2.2}name").text
		print(f"  Map: {mapName}")
		print(f"  ID:  {args.map_id}")

		# Create a directory for GPX files
		print(f"  Output directory:     {args.GPX_path}")
		try:
			os.makedirs(args.GPX_path, exist_ok=True)
			layers = root.iter('{http://www.opengis.net/kml/2.2}Folder')
			# Exporting KML data from a GMap will always have at least one layer
			layers = root.iter('{http://www.opengis.net/kml/2.2}Folder')
			if args.layers:
				# If layers arg is set we create a subdirectory under the GPX_path for each non-empty layer
				# Each of these subdirectories will contain:
				#	o A waypoints GPX file containing all of the waypoints in the layer.
				#	o A track GPX file for each track in the layer
				for layer in layers:
					returnCode = processLayer(layer,args)
					if returnCode != 0:
						break
			else:
				# # If layers arg is NOT set we create the following files
				# #	o A waypoints GPX file containing all of the waypoints in the KML file.
				# #	o A track GPX file for each track in the KML file
				# # We are not handling layers separately so use the root tree
				# # when processing waypoints and tracks.  Using root will return all
				# # of the waypoints and tracks regardless of if they are in a layer or not.
				# layers = root.iter('{http://www.opengis.net/kml/2.2}Folder')
				returnCode = processLayer(root,args)
		except Exception as e:
			print(f"  ERROR: An unexpected error occurred creating GPX file directory: {str(e)}")
			returnCode = 9
	print("")
	print(f"  Total waypoint count: {countTotalWaypoints:>3}")
	print(f"  Total track count:    {countTotalTracks:>3}")
	if args.layers:
		print(f"  Total layer count:    {countTotalLayers:>3}")
	print(f"  Return code:            {returnCode}")
	return(returnCode)
#========================================================================================
#
#========================================================================================
if __name__ == "__main__":
	sys.exit(main())
