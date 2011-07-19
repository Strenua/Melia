#!/usr/bin/python
# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Sebastian MacDonald Sebas310@gmail.com
# Copyright (C) 2010 Mehdi Rejraji mehd36@gmail.com
# Copyright (C) 2011 Vadim Rutkovsky roignac@gmail.com
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

#try:
#    from gi.repository import Gio
#except ImportError:
#    pass
import sys, os, shutil, tempfile
import gtk, pygtk, gobject, pynotify
pygtk.require('2.0')
from melia_lib import indicator
import urllib2, urllib
from urllib import urlencode
import re
import locale
from xml.dom.minidom import parseString
import datetime
import dbus
import time
import traceback
import types
# Will be used for humidex
#import math
import commands, threading
import logging, logging.handlers
import couchdb
from desktopcouch.records.server import CouchDatabase
from desktopcouch.records.record import Record as CouchRecord
import pywapi

import gettext
from gettext import gettext as _
from gettext import ngettext as __
gettext.textdomain('indicator-weather')

# Add project root directory (enable symlink, and trunk execution).
PROJECT_ROOT_DIRECTORY = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))))
PROJECT_ROOT_DIRECTORY = '/usr'

if (os.path.exists(os.path.join(PROJECT_ROOT_DIRECTORY, 'indicator_weather'))
    and PROJECT_ROOT_DIRECTORY not in sys.path):
    sys.path.insert(0, PROJECT_ROOT_DIRECTORY)
    os.putenv('PYTHONPATH', PROJECT_ROOT_DIRECTORY) # for subprocesses

VERSION = "11.05.30 'Cloudy 7'"

from weather_helper import *

global menu
menu = None
class Settings:
    """ Class to read/write settings """
    db = None

    # Open the DB and prepare views
    #TODO: Create view when package is installed?
    def prepare_settings_store(self):
        log.debug("Settings: preparing settings store")
        while True:
            try:
                self.db = CouchDatabase("weatherindicator", create = True)

                # Settings view
                self.settings_design_doc = "settings"
                self.settings_view = "function(doc) {if (doc.record_type == '%s') {emit(doc.name, doc);}}" % self.settings_design_doc
                self.db.add_view("get_setting", self.settings_view, None, self.settings_design_doc)

                # Cached weather view
                self.weather_design_doc = "weather"
                self.weather_view = "function(doc) {if (doc.record_type == '%s') {emit(doc.location, doc)} ;}" % self.weather_design_doc
                self.db.add_view("get_weather", self.weather_view, None, self.weather_design_doc)

                # Location info view
                self.location_design_doc = "location"
                self.location_view = "function(doc) {if (doc.record_type == '%s') {emit(doc.location, doc)} ;}" % self.location_design_doc
                self.db.add_view("get_location", self.location_view, None, self.location_design_doc)
                break
            except dbus.exceptions.DBusException as e:
                log.debug("Settings: DBus exception occurred:\n %s" % str(e))
                time.sleep(10)
            except Exception as e:
                log.debug("Settings: exception occurred while creating views:\n %s" % str(e))
                log.debug("Settings: dropping the DB")
                
                server = self.db._server
                del server['weatherindicator']

    # Get a value of the setting
    def get_value(self, setting, return_id = False):
        log.debug("Setting: getting value for %s" % setting)
        view = self.db.execute_view("get_setting", self.settings_design_doc)[setting]
        if hasattr(view, 'rows') and len(view.rows) > 0:
            if return_id:
                return str(view.rows[0].value['_id'])
            else:
                return str(view.rows[0].value['value'])
        else:
            log.debug("Setting: can't find value for %s" % setting)
            return None

    # Set a setting value
    def set_value(self, setting, value):
        log.debug("Setting: setting '%s'='%s'" % (setting, value))
        self.record = {
            "name" : setting,
            "value": value
        }
        #Update previously created document, if exists
        old_doc_id = self.get_value(setting, return_id=True)
        if old_doc_id != None:
            log.debug("Setting: setting '%s' was updated" % setting)
            self.db.update_fields(old_doc_id, self.record)
        else:
            log.debug("Setting: setting '%s' was created" % setting)
            while True:
                try:
                    self.db.put_record(CouchRecord(self.record, self.settings_design_doc))
                    break;
                except Exception as e:
                    log.debug("Settings: exception occurred:\n %s" % str(e))
                    time.sleep(10)

    # Get cached weather by location code.
    # If return_id is True, only document id is returned, otherwise - full weather data
    def get_weather(self, location_code, return_id = False):
        log.debug("Setting: getting cached weather for %s" % location_code)
        view = self.db.execute_view("get_weather", self.weather_design_doc)[location_code]
        if hasattr(view, 'rows') and len(view.rows) > 0:
            if return_id:
                return str(view.rows[0].value['_id'])
            else:
                return str(view.rows[0].value['data'])
        else:
            log.debug("Setting: can't find cached weather for %s" % location_code)
            return None

    # Save weather info in cache for specific location
    def save_weather(self, weather, location_code):
        log.debug("Setting: Saving cached weather data")
        self.record = {
          "location" : location_code,
          "data"      : {
            "label"    : weather.get_temperature(needs_rounding=True),
            "condition": weather.get_condition_label(),
            "icon"     : weather.get_icon_name(),
            "temper"   : weather.get_temperature_label(),
            "humidex"  : weather.get_humidex_label(),
            "humidity" : weather.get_humidity_label(),
            "wind"     : weather.get_wind_label(),
            "sunrise"  : weather.get_sunrise_label(),
            "sunset"   : weather.get_sunset_label()
          }
        }
        #Update previously created document, if exists
        old_doc_id = self.get_weather(location_code, return_id=True)
        if old_doc_id != None:
            self.db.update_fields(old_doc_id, self.record)
        else:    
            while True:
                try:
                    self.db.put_record(CouchRecord(self.record, self.weather_design_doc))
                    break;
                except Exception as e:
                    log.debug("Settings: exception occurred, retrying. exception:\n %s" % str(e))
                    time.sleep(3)

    # Get location details by location code
    # If return_id is True, only document id is returned, otherwise - full location data
    def get_location_details(self, location_code, return_id = False):
        log.debug("Setting: getting location details for %s" % location_code)
        view = self.db.execute_view("get_location", self.location_design_doc)[location_code]
        if hasattr(view, 'rows') and len(view.rows) > 0:
            if return_id:
                return str(view.rows[0].value['_id'])
            else:
                return str(view.rows[0].value['data'])
        else:
            log.debug("Setting: can't find location details for %s" % location_code)
            return None

    # Save location details
    def save_location_details(self, location_details, location_code):
        log.debug("Setting: Saving location details data")
        self.record = {
          "location" : location_code,
          "data"      : {
            "label"    : location_details['label'],
            "full name": location_details['full name'],
            "latitude" : location_details['latitude'],
            "longitude": location_details['longitude'],
          }
        }
        for key in ("google id", "yahoo id", "noaa id"):
            if key in location_details:
                self.record["data"][key]=location_details[key]

        # Update previously created element, if exists
        old_doc_id = self.get_location_details(location_code, return_id=True)
        if old_doc_id != None:
            self.db.update_fields(old_doc_id, self.record)
        else:
            while True:
                try:
                    self.db.put_record(CouchRecord(self.record, self.location_design_doc))
                    break;
                except Exception as e:
                    log.debug("Settings: exception occurred, retrying. exception:\n %s" % str(e))
                    time.sleep(3)

class MetricSystem:
    """ Class with available metric systems units """
    SI = 1
    IMPERIAL = 2

class WindUnits:
    """ Class for available wind unit systems """
    MPS = 1
    MPH = 2
    BEAUFORT = 3
    KPH = 4
    KNOTS = 5

class WeatherDataSource:
    """ Class for available weather data sources """
    GOOGLE = 1
    YAHOO = 2

class Location:
    """ Data object to store location details """

    # Initialize an object with a label
    def __init__(self, metric_system, wind_unit, location_details = None):
        self.metric_system = metric_system
        self.wind_unit = wind_unit
        self.location_details = location_details

    # Convert coordinate for google
    def convert_coordinate_for_google(self, value):
       value = float(value) * 1e6
       return int(round(value))

    # Get necessary location details by its GeoNames details
    def prepare_location(self, geonames_details):
        self.location_details = {}
        self.location_details['full name'] = geonames_details[0]
        self.location_details['latitude'] = geonames_details[2]
        self.location_details['longitude'] = geonames_details[3]
        self.prepare_location_for_google(geonames_details)
        self.prepare_location_for_yahoo(geonames_details)
        #TODO: Get noaa id from geonames service
        self.location_details['noaa id'] = "woot"

        # check mandatory attributes
        if not hasattr(self, 'location_code') or \
                'latitude' not in self.location_details or \
                'longitude' not in self.location_details:
            return False

        # check that we have at least one supported data source
        if 'google id' not in self.location_details and \
                'yahoo id' not in self.location_details:
            log.error(("Location '%s'" %
                self.location_details['full name'])) + \
                "is not supported by current data sources"
            return False

        return True

    def prepare_location_for_google(self, geonames_details):
        # Format latitude and longitude for Google needs
        try:
            lat = self.convert_coordinate_for_google(geonames_details[2])
            lon = self.convert_coordinate_for_google(geonames_details[3])
            self.location_details['google id'] = ",,,%s,%s" % (lat, lon)
        
        except Exception, e:
            log.error(e)

    def prepare_location_for_yahoo(self, geonames_details):
        # Get location details in english for Yahoo
        baseurl = 'http://api.geonames.org/getJSON'
        params = {'geonameId': geonames_details[1], 'username': 'indicatorweather'}
        url = '?'.join((baseurl, urlencode(params)))
        log.debug("Location: Get GeoNames location details, url %s" % url)
        try:
            city = eval(urllib2.urlopen(url).read())
            if 'adminName1' in city:
                displayed_city_name = "%s, %s, %s" % (city['name'], city['adminName1'], city['countryName'])
            elif 'name' in city:
                displayed_city_name = "%s, %s" % (city['name'], city['countryName'])
            else:
                log.error("Location: Cannot find GeoNames info for code %s Full Response:\n %s" % (geonames_details[1], str(city)))
                return

            # Get YAHOO WOEID by english name of location
            baseurl = 'http://where.yahooapis.com/geocode'
            params = {'location': displayed_city_name, 'appid': 'mOawLd4s', 'flags': 'J'}
            url = '?'.join((baseurl, urlencode(params)))
            log.debug("Location: Get Yahoo WOEID, url %s" % url)
            f = urllib2.urlopen(url)
            s=f.read()
            null = None
            yahoo_woeid_result = eval(s)
            if (yahoo_woeid_result['ResultSet']['Error'] != 0) and  (yahoo_woeid_result['ResultSet']['Results'] != None):
                log.error("Location: Yahoo woeid return error. Full response:\n %s" % str(yahoo_woeid_result))
                return
            else:
                woeid = yahoo_woeid_result['ResultSet']['Results'][0]['woeid']
                self.location_code = woeid
                log.debug("Location: woeid is %s" % woeid)

                # Get old Yahoo id by woeid
                url = 'http://weather.yahooapis.com/forecastrss?w=%s' % woeid
                log.debug("Location: Get Yahoo RSS ID, url %s" % url)
                f = urllib2.urlopen(url)
                s=f.read()
                parsed = parseString(s)
                #TODO: Add a try-catch for empty guid_value
                guid = parsed.getElementsByTagName("guid")
                if len(guid) > 0:
                    guid_value = guid[0].firstChild.nodeValue
                    p = re.compile('([^_]*)_')
                    m = p.match(guid_value)
                    if m:
                        self.location_details['yahoo id'] = m.group(1)
                        log.debug("Location: yahoo id is %s" % self.location_details['yahoo id'])
                    else:
                        log.error("Location: Can't find yahoo id via woeid. Full response:\n %s" % guid_value)
                        return
                else:
                    log.error("Location: Can't guid in yahoo RSS response. Full response:\n %s" % s)
                    return

        except urllib2.URLError:
            log.error("Location: error reaching url '%s'" % url)

        except Exception, e:
            log.error(e)

    # Return lcoation code and location details
    def export_location_details(self):
        return (self.location_code, self.location_details)

    # Get fresh weather data and store it to weather object
    def update_weather_data(self, source):
        # gather existing source keys
        valid_source = None
        loc_ids = {}

        SOURCES = {
            WeatherDataSource.GOOGLE : ("google id", "Google"),
            WeatherDataSource.YAHOO : ("yahoo id", "Yahoo"),
        }

        for source_id in SOURCES.keys():
            if SOURCES[source_id][0] in self.location_details:
                loc_ids[source_id] = SOURCES[source_id][0]

        # try with the default source
        if source in loc_ids:
            valid_source = source
            log.debug(("Location: default weather source '%s' " +
                "chosen for '%s'") % (SOURCES[valid_source][1],
                self.location_details['label']))

        # try with the first alternative
        elif len(loc_ids.keys()):
            valid_source = loc_ids.keys()[0]
            log.debug(("Location: non default weather source '%s' " +
                "chosen for '%s'") % (SOURCES[valid_source][1],
                self.location_details['label']))

        if valid_source is None:
            log.error(("Location: no valid weather source can be " +
                "chosen for '%s'") % (
                self.location_details['label']))
            self.weather = None
        else:
            self.weather = Weather(
                self.location_details[loc_ids[valid_source]],
                valid_source, self.metric_system, self.wind_unit,
                self.location_details['latitude'],
                self.location_details['longitude'])

class Forecast:
    """ Class to get forecast information """

    # Initialize a class with metric system, wind units, location and current user locale
    def __init__ (self, units, lat, lon, locale):
        self.metric_system = units
        self.lat = self.convert_coordinate_for_google(lat)
        self.lon = self.convert_coordinate_for_google(lon)
        self.locale = locale

    # Convert coordinate for google
    def convert_coordinate_for_google(self, value):
       value = float(value) * 1e6
       return int(round(value))
       
    # Get and store forecast data. For now using Google only
    def prepare_forecast_data(self):
        self.daysofweek = []
        self.icons = []
        self.conditions = []
        self.error_message = None
        try:
            # Generate a fake location by current coordinates
            location_name = ",,,%s,%s" % (self.lat, self.lon)
            self.forecast = pywapi.get_weather_from_google (location_name, hl = self.locale)
            self.unitsystem = self.forecast['forecast_information']['unit_system']

            for forecast in self.forecast['forecasts']:
                self.daysofweek.append(forecast["day_of_week"])
                self.icons.append(forecast["icon"].split("http://g0.gstatic.com/images/icons/onebox/weather_")[-1].split("-40.gif")[0])
                self.conditions.append(forecast["condition"])
            self.error_message = None

        except urllib2.URLError:
            log.error("Forecast: error reading forecast for %s" % location_name)
        except KeyError:
            log.error("Forecast: returned empty forecast %s" % location_name)
            self.error_message = _('Unknown error occurred while picking up weather data')

    # Parse high values for forecast data
    def get_forecast_data(self):
        self.highdata = []
        self.lowdata = []

        if not hasattr(self, 'unitsystem'):
            return None

        if ((self.unitsystem == 'SI') and (self.metric_system == MetricSystem.SI)) or ((self.unitsystem == 'US') and (self.metric_system == MetricSystem.IMPERIAL)):
            #correct scale selected
            for forecast in self.forecast['forecasts']:
                self.highdata.append(forecast["high"])
                self.lowdata.append(forecast["low"])

        elif ((self.unitsystem == 'SI') and (self.metric_system == MetricSystem.IMPERIAL)):
            #convert from SI to imperial
            for forecast in self.forecast['forecasts']:
                self.highdata.append(int(((int(forecast["high"])*9)/5)+32))
                self.lowdata.append(int(((int(forecast["low"])*9)/5)+32))

        elif ((self.unitsystem == 'US') and (self.metric_system == MetricSystem.SI)):
            #convert from imperial to SI
            for forecast in self.forecast['forecasts']:
                self.highdata.append(int((((int(forecast["high"]))-32)*5)/9))
                self.lowdata.append(int((((int(forecast["low"]))-32)*5)/9))

        return (self.highdata, self.lowdata)

    # Parse a list of days of week with forecast data
    def get_forecast_daysofweek(self):
        return self.daysofweek

    # Parse icons for forecast data
    def get_forecast_icons(self):
        return self.icons

    # Parse conditions for forecast data
    def get_forecast_conditions(self):
        return self.conditions

class WIndicator(indicator.Indicator):
    def finit(self):
        ''

class Weather:
    """
    Data object to parse weather data with unit convertion
    """

    #Available conditions by google icon
    #Format: Google icon name: (day icon, night icon, is a severe weather condition)
    #Reference: http://www.blindmotion.com/2009/03/google-weather-api-images/
    _GoogleConditions = {
        "sunny"            : ( "weather-clear",      "weather-clear-night",      False),
        "mostlysunny"      : ( "weather-clear",      "weather-clear-night",      False),
        "partlycloudy"     : ( "weather-few-clouds", "weather-few-clouds-night", False),
        "mostlycloudy"     : ( "weather-overcast",   "weather-overcast",         False),
        "cloudy"           : ( "weather-clouds",     "weather-clouds-night",     False),
        "rain"             : ( "weather-showers",    "weather-showers",          False),
        "chanceofrain"     : ( "weather-showers",    "weather-showers",          False),
        "sleet"            : ( "weather-snow",       "weather-snow",             False),
        "rainsnow"         : ( "weather-snow",       "weather-snow",             False),
        "snow"             : ( "weather-snow",       "weather-snow",             False),
        "chanceofsnow"     : ( "weather-snow",       "weather-snow",             False),
        "icy"              : ( "weather-snow",       "weather-snow",             False),
        "flurries"         : ( "weather-snow",       "weather-snow",             False),
        "dust"             : ( "weather-fog",        "weather-fog",              False),
        "fog"              : ( "weather-fog",        "weather-fog",              False),
        "mist"             : ( "weather-fog",        "weather-fog",              False),
        "smoke"            : ( "weather-fog",        "weather-fog",              False),
        "haze"             : ( "weather-fog",        "weather-fog",              False),
        "chanceofstorm"    : ( "weather-storm",      "weather-storm",            True),
        "storm"            : ( "weather-storm",      "weather-storm",            True),
        "thunderstorm"     : ( "weather-storm",      "weather-storm",            True),
        "chanceoftstorm"   : ( "weather-storm",      "weather-storm",            True),
        "scatteredshowers" : ( "weather-showers-scattered", "weather-showers-scattered", True),
        "scatteredthunderstorms" : ( "weather-storm",       "weather-storm",             True),
    }

    #Available conditions by yahoo condition code
    #Format: condition code: (day icon, night icon, is a severe weather condition, localized condition name)
    _YahooConditions = {
        '0' : ("weather-storm",             "weather-storm",            True,  _("Tornado")),
        '1' : ("weather-storm",             "weather-storm",            True,  _("Tropical storm")),
        '2' : ("weather-storm",             "weather-storm",            True,  _("Hurricane")),
        '3' : ("weather-storm",             "weather-storm",            True,  _("Severe thunderstorms")),
        '4' : ("weather-storm",             "weather-storm",            True,  _("Thunderstorms")),
        '5' : ("weather-snow",              "weather-snow",             False, _("Mixed rain and snow")),
        # Use American meaning of sleet - see http://en.wikipedia.org/wiki/Sleet
        '6' : ("weather-showers",           "weather-showers",          False, _("Mixed rain and sleet")),
        '7' : ("weather-snow",              "weather-snow",             False, _("Mixed snow and sleet")),
        '8' : ("weather-showers",           "weather-showers",          False, _("Freezing drizzle")),
        '9' : ("weather-showers",           "weather-showers",          False, _("Drizzle")),
        '10': ("weather-snow",              "weather-snow",             False, _("Freezing rain")),
        '11': ("weather-showers",           "weather-showers",          False, _("Showers")),
        '12': ("weather-showers",           "weather-showers",          False, _("Showers")),
        '13': ("weather-snow",              "weather-snow",             False, _("Snow flurries")),
        '14': ("weather-snow",              "weather-snow",             False, _("Light snow showers")),
        '15': ("weather-snow",              "weather-snow",             False, _("Blowing snow")),
        '16': ("weather-snow",              "weather-snow",             False, _("Snow")),
        '17': ("weather-showers",           "weather-showers",          False, _("Hail")),
        '18': ("weather-snow",              "weather-snow",             False, _("Sleet")),
        '19': ("weather-fog",               "weather-fog",              False, _("Dust")),
        '20': ("weather-fog",               "weather-fog",              False, _("Foggy")),
        '21': ("weather-fog",               "weather-fog",              False, _("Haze")),
        '22': ("weather-fog",               "weather-fog",              False, _("Smoky")),
        '23': ("weather-clear",             "weather-clear-night",      False, _("Blustery")),
        '24': ("weather-clear",             "weather-clear-night",      False, _("Windy")),
        '25': ("weather-clear",             "weather-clear-night",      False, _("Cold")),
        '26': ("weather-clouds",            "weather-clouds-night",     False, _("Cloudy")),
        '27': ("weather-clouds",            "weather-clouds-night",     False, _("Mostly cloudy")),
        '28': ("weather-clouds",            "weather-clouds-night",     False, _("Mostly cloudy")),
        '29': ("weather-few-clouds",        "weather-few-clouds-night", False, _("Partly cloudy")),
        '30': ("weather-few-clouds",        "weather-few-clouds-night", False, _("Partly cloudy")),
        '31': ("weather-clear",             "weather-clear-night",      False, _("Clear")),
        '32': ("weather-clear",             "weather-clear-night",      False, _("Sunny")),
        '33': ("weather-clear",             "weather-clear-night",      False, _("Fair")),
        '34': ("weather-clear",             "weather-clear-night",      False, _("Fair")),
        '35': ("weather-showers-scattered", "weather-showers-scattered",False, _("Mixed rain and hail")),
        '36': ("weather-clear",             "weather-clear-night",      False, _("Hot")),
        '37': ("weather-storm",             "weather-storm",            True,  _("Isolated thunderstorms")),
        '38': ("weather-storm",             "weather-storm",            True,  _("Scattered thunderstorms")),
        '39': ("weather-storm",             "weather-storm",            True,  _("Scattered thunderstorms")),
        '40': ("weather-showers-scattered", "weather-showers-scattered",False, _("Scattered showers")),
        '41': ("weather-snow",              "weather-snow",             False, _("Heavy snow")),
        '42': ("weather-snow",              "weather-snow",             False, _("Scattered snow showers")),
        '43': ("weather-snow",              "weather-snow",             False, _("Heavy snow")),
        '44': ("weather-few-clouds",        "weather-few-clouds-night", False, _("Partly cloudy")),
        '45': ("weather-storm",             "weather-storm",            True,  _("Thundershowers")),
        '46': ("weather-snow",              "weather-snow",             False, _("Snow showers")),
        '47': ("weather-storm",             "weather-storm",            True,  _("Isolated thundershowers")),
        '3200': (False,                    False,                      False, _("Unknown condition"))
    }

    # Initialize and get fresh data
    def __init__(self, location_id, weather_datasource, metric_system, wind_unit, lat, lon):
        self.__weather_datasource = weather_datasource
        self.__metric_system = metric_system
        self._wind_unit = wind_unit
        self.__current_condition = None
        self.__lat = lat
        self.__lon = lon

        # Get data from Google
        if self.__weather_datasource == WeatherDataSource.GOOGLE:
            # Get data in english locale, then - switch back
            self.__report = pywapi.get_weather_from_google (location_id, hl = 'en')
            # Get data in original locale for condition name
            self.__localized_report = pywapi.get_weather_from_google (location_id, hl = locale_name)
            icon_name = self.__report['current_conditions']['icon'].replace('http://g0.gstatic.com/images/icons/onebox/weather_', '').replace('-40.gif', '')

            self.__current_condition = self._GoogleConditions.get(icon_name)
            if self.__current_condition == None:
                log.error("ExtendedForecast: unknown Google weather condition '%s'" % icon_name)
                self.__current_condition = (False, False, False, _(self.__report['current_conditions']['condition']))

        # Get data from Yahoo
        if self.__weather_datasource == WeatherDataSource.YAHOO:
            self.__report = pywapi.get_weather_from_yahoo (location_id, 'imperial')
            self.__localized_report = self.__report
            icon_name = self.__report['condition']['code']
            self.__current_condition = self._YahooConditions.get(icon_name)
        log.debug("Weather: current condition: '%s', '%s'" % (icon_name, str(self.__current_condition)))
        #Prepare sunrise/sunset data
        self.get_sun_data()

    #Get sunrise/sunset times, calculate whether it is night already
    def get_sun_data(self):
        self.__night = False
        self.__sunrise_t = None
        self.__sunset_t = None
        # Grab local datetime and the daylight saving status (1/0)
        # from earthtools.org
        url = 'http://www.earthtools.org/timezone-1.1/%s/%s' % \
            (self.__lat, self.__lon)
        try:
            f = urllib2.urlopen(url)
            s = f.read()
            parsed = parseString(s)
            localtime = parsed.getElementsByTagName(
                "isotime")[0].firstChild.nodeValue
            dst = parsed.getElementsByTagName(
                "dst")[0].firstChild.nodeValue
            # strip timezone info
            localtime = datetime.datetime.strptime(localtime.rsplit(' ',1)[0],
                '%Y-%m-%d %H:%M:%S')
            dst = 1 if dst == "True" else 0

        except urllib2.URLError:
            log.error("Weather: error reaching url '%s'" % url)
            return
        
        # Grab sunrise/sunset from earthtools.org
        url = 'http://www.earthtools.org/sun/%s/%s/%s/%s/99/%s' % \
            (self.__lat, self.__lon, localtime.day, localtime.month, dst)
        try:
            f = urllib2.urlopen(url)
            s=f.read()
            parsed = parseString(s)
            sunrise = parsed.getElementsByTagName("morning")[0].getElementsByTagName("sunrise")[0].firstChild.nodeValue
            sunset  = parsed.getElementsByTagName("evening")[0].getElementsByTagName("sunset")[0].firstChild.nodeValue
            self.__sunrise_t = datetime.datetime.strptime(sunrise, '%H:%M:%S').time()
            self.__sunset_t = datetime.datetime.strptime(sunset, '%H:%M:%S').time()
        except urllib2.URLError:
            log.error("Weather: error reaching url '%s'" % url)
            return

        # Calculate, whether it is night or day
        if localtime.time()<self.__sunrise_t or localtime.time()>self.__sunset_t:
            self.__night = True
        else:
            self.__night = False
        log.debug("Weather: got localtime " +
            "%s, dst %s, sunrise '%s', sunset '%s', night = %s" % (
            localtime, dst, self.__sunrise_t, self.__sunset_t, self.__night))

    # Return True, if weather condition is severe
    def condition_is_severe(self):
        if self.__current_condition != None:
            log.debug("Weather: got severe condition '%s'" % self.__current_condition[2])
            return self.__current_condition[2]
        else:
            log.error("Weather: condition is not set while condition severity check")
            return False;

    # Get associated icon name
    def get_icon_name(self):
        if self.__current_condition != None:
            if self.__night:
                log.debug("Weather: night, show '%s' icon" % self.__current_condition[1])
                return self.__current_condition[1]
            else:
                log.debug("Weather: day, show '%s' icon" % self.__current_condition[0])
                return self.__current_condition[0]
        else:
            log.error("Weather: return 'offline' icon due to empty condition")
            return False

    # Get condition text
    def get_condition_label(self):
        if self.__weather_datasource == WeatherDataSource.GOOGLE:
            if 'condition' in self.__localized_report['current_conditions'].keys():
                condition = self.__localized_report['current_conditions']['condition']
            else:
                condition = _("Unknown condition")
        if self.__weather_datasource == WeatherDataSource.YAHOO:
            condition = self.__current_condition[3]
        return condition

    # Get humidity label
    def get_humidity_label(self):
        if self.__weather_datasource == WeatherDataSource.GOOGLE:
            humidity = self.__localized_report['current_conditions']['humidity']
        if self.__weather_datasource == WeatherDataSource.YAHOO:
            humidity = "%s: %s%%" % (_("Humidity"), self.__localized_report['atmosphere']['humidity'])
        return humidity

    # Get dew point - using in humidex calculation
    #TODO: Update with NOAA
    def get_dew_point_label(self):
        if self.__weather_datasource == WeatherDataSource.GOOGLE or self.__weather_datasource == WeatherDataSource.YAHOO:
            # Not returned by Google and Yahoo
            return None

    # Get pressure label
    def get_pressure_label(self):
        if self.__weather_datasource == WeatherDataSource.GOOGLE:
            # TODO: Empty for Google, use NOAA data?
            value = "---"
            unit = ""
        if self.__weather_datasource == WeatherDataSource.YAHOO:
            value = self.__localized_report['atmosphere']['pressure']
            unit = self.__localized_report['units']['pressure']
        return "%s: %s %s" % (_("Pressure"), value, units)

    # Get temperature with units value - doesn't include 'Temperature' label
    def get_temperature(self, needs_rounding = False):
        if self.__weather_datasource == WeatherDataSource.GOOGLE:
            if (self.__metric_system == MetricSystem.SI):
                _value = self.__report['current_conditions']['temp_c']
                _unit  = "˚C"
            else:
                _value = self.__report['current_conditions']['temp_f']
                _unit  = "˚F"
        if self.__weather_datasource == WeatherDataSource.YAHOO:
            if (self.__metric_system == MetricSystem.SI):
                _value = NumberFormatter.format_float(
                    ((float(self.__report['condition']['temp']) - 32) * 5/9), 1)
                _unit  = "˚C"
            else:
                _value = self.__report['condition']['temp']
                _unit  = "˚F"
        # round the value if required
        if needs_rounding:
            _value = NumberFormatter.format_float(locale.atof(_value), 0)
        return ("%s %s" % (_value, _unit))

    # Get temperature label
    def get_temperature_label(self):
        return "%s: %s" % (_("Temperature"), self.get_temperature())

    # Get humidex parameter
    def get_humidex_label(self):
        if self.__weather_datasource == WeatherDataSource.GOOGLE or self.__weather_datasource == WeatherDataSource.YAHOO:
            #Empty for Yahoo and Google
            return None
        #TODO: Update with NOAA data
        #dewPoint=2
        #temp_c = 1
        #self.vapour_pressure = 6.11 * math.exp(5417.7530 * ( (1/273.16) - (1/(dewPoint+273.16))))
        #self.humidex = temp_c + (0.5555)*(self.vapour_pressure  - 10.0);
        #return ("%s: %.1f" % (_("Humidex"), self.humidex)).replace(".0", "")

    # Get wind label
    def get_wind_label(self):
        if self.__weather_datasource == WeatherDataSource.GOOGLE:
            # Convert units picked up from Google and replace units with currently configured
            if 'wind_condition' in self.__localized_report['current_conditions'].keys():
                localized_wind_info = self.__localized_report['current_conditions']['wind_condition'].split(' ')
                wind_direction = localized_wind_info[1]
                wind_info = self.__report['current_conditions']['wind_condition'].split(' ')
                wind_speed = wind_info[3]
            else:
                wind_direction = _("Unknown")
                wind_info = _("Unknown")
                wind_speed = _("Unknown")

        if self.__weather_datasource == WeatherDataSource.YAHOO:
            # Create a similar to Google wind_info structure from Yahoo data
            wind_direction = self.__localized_report['wind']['direction']
            wind_speed = self.__localized_report['wind']['speed']
            wind_units = self.__localized_report['units']['speed']
            localized_wind_info = [_("Wind") + ":", self.get_wind_direction(wind_direction), ',', wind_speed, wind_units] 

        # Parse Wind_direction - convert to selected scale
        if (self._wind_unit == WindUnits.MPH):
            _value = float(wind_speed)
            _unit  = __("mph", "mph", _value)
        if (self._wind_unit == WindUnits.MPS):
            _value = float(wind_speed) * 0.44704
            _unit  = __("m/s", "m/s", _value)
        if (self._wind_unit == WindUnits.BEAUFORT):
            _value = self.get_beaufort_from_mph(float(wind_speed))
            _unit  = ""
        if (self._wind_unit == WindUnits.KPH):
            _value = float(wind_speed) * 1.609344
            _unit  = __("km/h", "km/h", _value)
        if (self._wind_unit == WindUnits.KNOTS):
            _value = float(wind_speed) * 0.868976241900648
            _unit  = __("knot", "knots", _value)

        # Join wind_info data in a label
        localized_wind_info[len(localized_wind_info)-1] = _unit
        localized_wind_info[len(localized_wind_info)-2] = \
            NumberFormatter.format_float(_value, 1)
        return ' '.join(localized_wind_info)

    # Get sunrise label
    def get_sunrise_label(self):
        return "%s: %s" % (_("Sunrise"), TimeFormatter.format_time(self.__sunrise_t))

    # Get sunset label
    def get_sunset_label(self):
        return "%s: %s" % (_("Sunset"), TimeFormatter.format_time(self.__sunset_t))


    # Additional functions
    # Convert wind direction from degrees to localized direction
    def get_wind_direction(self, degrees):
        try:
            degrees = int(degrees)
        except ValueError:
            return ''
    
        if degrees < 23 or degrees >= 338:
            #Short wind direction - north
            return _('N')
        elif degrees < 68:
            return _('NE')
        elif degrees < 113:
            return _('E')
        elif degrees < 158:
            return _('SE')
        elif degrees < 203:
            return _('S')
        elif degrees < 248:
            return _('SW')
        elif degrees < 293:
            return _('W')
        elif degrees < 338:
            return _('NW')

    # Convert mph to Beufort scale
    def get_beaufort_from_mph(self, value):
        if value < 1:
            return 0
        elif value < 4:
            return 1
        elif value < 8:
            return 2
        elif value < 13:
            return 3
        elif value < 18:
            return 4
        elif value < 25:
            return 5
        elif value < 27:
            return 6
        elif value < 39:
            return 7
        elif value < 47:
            return 8
        elif value < 89:
            return 9
        elif value < 64:
            return 10
        elif value < 73:
            return 11
        elif value >= 73:
            return 12

class indicator_weather(threading.Thread):
    """ Indicator class """
    last_update_time = None

    # Settings values
    # Formats: setting value, object name (for preferences dialog), value assigned (optional)
    metric_systems = { 'S': ('si',       MetricSystem.SI),
                       'I': ('imperial', MetricSystem.IMPERIAL)}

    weather_sources = { 'G': ('google', WeatherDataSource.GOOGLE),
                        'Y': ('yahoo',  WeatherDataSource.YAHOO)}

    notifications = {'N': 'nonotif',
                     'O': 'notifsevere',
                     'A': 'notifall'}

    wind_systems = {'mps':      ("mps",      WindUnits.MPS),
                    'mph':      ("mph",      WindUnits.MPH),
                    'kph':      ("kph",      WindUnits.KPH),
                    'beaufort': ("beaufort", WindUnits.BEAUFORT),
                    'knots':    ("knots",    WindUnits.KNOTS)}

    # Initializing and reading settings
    def __init__(self):
        log.debug("Indicator: creating")
        threading.Thread.__init__(self)
        self.main_icon = os.path.join
        global menu
        self.button = WIndicator ("weather-clear")
        
        menu = self.button
        #self.button.set_status (appindicator.STATUS_ACTIVE)
        #self.button.set_attention_icon ("weather-indicator-error")

        self.menu_update_lock = threading.Lock()
        self.refreshed_minutes_ago = -1
        monitor_upower(self.on_system_sleep, self.on_system_resume, log)

        log.debug("Indicator: reading settings")
        self.settings = Settings()
        self.settings.prepare_settings_store()      
        self.rate  = self.settings.get_value("refresh_rate")
        self.unit  = self.settings.get_value("unit")
        self.notif = self.settings.get_value("notif")
        self.wind  = self.settings.get_value("wind")
        self.source = self.settings.get_value("data_source")
        self.placechosen = self.settings.get_value("placechosen")
        self.places = self.settings.get_value("places")
        self.show_label = self.settings.get_value("show_label")

        log.debug("Preferences: got settings: rate=%s, unit=%s, notif=%s, wind=%s, placechosen=%s, places=%s" %
                (self.rate, self.unit, self.notif, self.wind, self.placechosen, self.places))

        #Setting default values
        self.metric_system = MetricSystem.SI
        self.wind_unit = WindUnits.MPH
        self.place = None
        self.menu = None
        self.condition = None
        self.icon = None

        #Parsing settings
        # Metric system
        if self.unit in (False, None):
            default_value = 'S'
            log.debug("Indicator: could not parse unit, setting to %s" % default_value)
            self.settings.set_value("unit", default_value)
            self.unit = default_value
        self.metric_system = self.metric_systems[self.unit][1]

        # Notification
        if self.notif in (False, None):
            default_value = 'N'
            log.debug("Indicator: could not parse notif, setting to %s" % default_value)
            self.settings.set_value("notif", default_value)
            self.notif = default_value

        # Wind units
        if self.wind in (False, None):
            default_value = 'mph'
            log.debug("Indicator: could not parse notif, setting to %s" % default_value)
            self.settings.set_value("wind", default_value)
            self.wind = default_value
        self.wind_unit = self.wind_systems[self.wind][1]

        # Show label in indicator?
        self.show_label = True if self.show_label == 'True' else False

        # Weather source
        if self.source in (False, None):
            default_value = 'Y'
            log.debug("Indicator: could not parse data source, setting to %s" % default_value)
            self.settings.set_value("data_source", default_value)
            self.source = default_value
        self.weather_source = self.weather_sources[self.source][1]

        # Rate
        if self.rate in (False, None):
            default_value = 15
            log.debug("Indicator: could not parse rate, setting to %s" % str(default_value))
            self.settings.set_value("refresh_rate", default_value)
            self.rate = default_value

        # Place chosen
        if self.placechosen == None:
            log.debug("Indicator: could not parse placechosen, setting to 0")
            self.settings.set_value("placechosen", 0)
            self.placechosen = 0
        else:
            self.placechosen = int(self.placechosen)

        # Places list
        if self.places in (False, None, '', '[]', "['']"):
            log.debug("Indicator: could not parse places")
            self.menu_noplace()
        else:
            self.places = eval(self.places)
            if self.placechosen >= len(self.places):
                self.placechosen = 0
            self.place = self.places[self.placechosen]
            self.location_details = self.settings.get_location_details(self.place[0])
            if self.location_details in (False, None, '', '[]', "['']"):
                log.debug("Indicator: could not parse current location details")
                self.menu_noplace()
            else:
                self.location_details = eval(self.location_details)
                self.menu_normal()
                self.update_weather()

    # Set a label of indicator
    def update_label(self, label):
        if (hasattr(self.button, 'set_label')):
            log.debug("Indicator: update_label: setting label to '%s'" % label)
            self.previous_label_value = label
            self.button.set_label(label) if self.show_label else self.button.set_label(" ")
            #self.button.set_status(appindicator.STATUS_ATTENTION)
            #self.button.set_status(appindicator.STATUS_ACTIVE)

    # Show a menu if no places specified
    def menu_noplace(self):
        log.debug("Indicator: making a menu for no places")
        menu_noplace = gtk.Menu()

        setup = gtk.MenuItem(_("Set Up Weather..."))
        setup.connect("activate", self.prefs)
        setup.show()
        menu_noplace.append(setup)

        quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quit.connect("activate", self.quit)
        quit.show()
        menu_noplace.append(quit)

        self.button.set_menu(menu_noplace)
        self.button.set_icon(os.path.join(PROJECT_ROOT_DIRECTORY, "share/indicator-weather/media/icon.png"))
        #self.button.set_status(appindicator.STATUS_ATTENTION)
        #self.button.set_status(appindicator.STATUS_ACTIVE)

    # Show menu with data
    def menu_normal(self):
        log.debug("Indicator: menu_normal: filling in a menu for found places")
        self.menu = gtk.Menu()
            
    ##City
        self.city_show = gtk.MenuItem()
        self.city_show.set_sensitive(True)
        self.menu.append(self.city_show)
        self.city_show.show()
        
    ##Condition
        self.cond_show = gtk.MenuItem()
        self.cond_show.set_sensitive(True)
        self.cond_show.show()
        self.menu.append(self.cond_show)
        
    ##Temperature        
        self.temp_show = gtk.MenuItem()
        self.temp_show.set_sensitive(True)
        self.temp_show.show()
        self.menu.append(self.temp_show)

    ##Humidex        
        self.humidex_show = gtk.MenuItem()
        self.humidex_show.set_sensitive(True)
        self.humidex_show.show()
        self.menu.append(self.humidex_show)
        
    ##Humidity
        self.humid_show = gtk.MenuItem()
        self.humid_show.set_sensitive(True)
        self.humid_show.show()
        self.menu.append(self.humid_show)
        
    ##Wind
        self.wind_show = gtk.MenuItem()
        self.wind_show.set_sensitive(True)
        self.wind_show.show()
        self.menu.append(self.wind_show)
                
    ##Sunrise
        self.sunrise_show = gtk.MenuItem()
        self.sunrise_show.set_sensitive(True)
        self.sunrise_show.show()
        self.menu.append(self.sunrise_show)

    ##Sunset
        self.sunset_show = gtk.MenuItem()
        self.sunset_show.set_sensitive(True)
        self.sunset_show.show()
        self.menu.append(self.sunset_show)
        
    ##Cities
        if len(self.places) != 1:
            ##Breaker
            breaker = gtk.SeparatorMenuItem()
            breaker.show()
            self.menu.append(breaker)

            log.debug("Indicator: menu_normal: adding first location menu item '%s'" % self.places[0][1])
            loco1 = gtk.RadioMenuItem(None, self.places[0][1])
            if self.placechosen == 0:
                loco1.set_active(True)
            loco1.connect("toggled", self.on_city_changed)
            loco1.show()
            self.menu.append(loco1)
            for place in self.places[1:]:
                log.debug("Indicator: menu_normal: adding location menu item '%s'" % place[1])
                loco = gtk.RadioMenuItem(loco1, place[1])
                if self.places.index(place) == self.placechosen:
                    loco.set_active(True)
                loco.connect("toggled", self.on_city_changed)
                loco.show()
                self.menu.append(loco)
        
    ##Breaker
        breaker = gtk.SeparatorMenuItem()
        breaker.show()
        self.menu.append(breaker)

        self.refresh_show = gtk.MenuItem()
        #label will be set later
        self.refresh_show.connect("activate", self.update_weather)
        self.refresh_show.show()
        self.menu.append(self.refresh_show)
        
        ext_show = gtk.MenuItem(_("Forecast"))
        ext_show.connect("activate", self.extforecast)
        ext_show.show()
        self.menu.append(ext_show)

    ##Preferences      
        prefs_show = gtk.MenuItem(_("Preferences..."))
        prefs_show.connect("activate", self.prefs)
        prefs_show.show()
        self.menu.append(prefs_show)

    ##About      
        about_show = gtk.MenuItem(_("About..."))
        about_show.connect("activate", self.about)
        about_show.show()
        self.menu.append(about_show)

    ##Quit
        quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quit.connect("activate", self.quit)
        quit.show()
        self.menu.append(quit)

        self.button.set_menu(self.menu)
        self.update_label(" ")

    # Another city has been selected from radiobutton
    def on_city_changed(self,widget):
        if widget.get_active():
            for place in self.places:
                if (place[1] == widget.get_label()):
                    log.debug("Indicator: new location selected: %s" % self.places.index(place))
                    self.placechosen = self.places.index(place)
                    break

            if self.placechosen >= len(self.places):
                self.placechosen = 0
            self.place = self.places[self.placechosen]
            self.location_details = self.settings.get_location_details(self.place[0])
            if self.location_details in (False, None, '', '[]', "['']"):
                log.debug("Indicator: could not parse location details for placechosen='%s'" % self.placechosen)
                self.menu_noplace()
            else:
                self.location_details = eval(self.location_details)
            self.settings.set_value("placechosen", self.placechosen)
            self.update_weather(False)

    def on_system_sleep(self):
        """
        Callback from UPower that system suspends/hibernates
        """
        # store time
        self.sleep_time = datetime.datetime.now()
        log.debug("Indicator: system goes to sleep at %s" % self.sleep_time)
        # remove gobject timeouts
        if hasattr(self, "refresh_id"):
            gobject.source_remove(self.refresh_id)
        if hasattr(self, "rate_id"):
            gobject.source_remove(self.rate_id)

    def on_system_resume(self):
        """
        Callback from UPower that system resumes
        """
        now = datetime.datetime.now()
        log.debug("Indicator: system resumes at %s" % now)
        # if we have places set
        if isinstance(self.places, types.ListType) and len(self.places)>0:
            td = now - self.sleep_time
            mins_elapsed = td.days/24*60 + td.seconds/60
            # update refresh label
            if self.refreshed_minutes_ago >= 0:
                mins_elapsed += self.refreshed_minutes_ago
                self.update_refresh_label(mins_elapsed)
            # check if we need to update the weather now or to reschedule the update
            min_diff = int(self.rate) - mins_elapsed
            if min_diff > 0:
                self.schedule_weather_update(min_diff)
            else:
                self.update_weather()

    # Schedule weather update
    def schedule_weather_update(self, rate_override = None):
        if hasattr(self, "rate_id"):
            gobject.source_remove(self.rate_id)
        if rate_override:
            log.debug("Indicator: scheduling update in %s mins" % rate_override)
            self.rate_id = gobject.timeout_add(
                int(rate_override) * 60000, self.update_weather)
        else:
            log.debug("Indicator: scheduling update in %s mins" % self.rate)
            self.rate_id = gobject.timeout_add(
                int(self.rate) * 60000, self.update_weather)

    # Schedule weather update
    def schedule_refresh_label_update(self):
        if hasattr(self, "refresh_id"):
            gobject.source_remove(self.refresh_id)
        log.debug("Indicator: scheduling refresh label update in 1 min")
        self.refresh_id = gobject.timeout_add(60000, self.update_refresh_label)

    # Update 'Refresh' label with time since last successful data refresh
    def update_refresh_label(self, reset_minutes = None):
        if reset_minutes is not None:
            self.refreshed_minutes_ago = reset_minutes
        else:
            self.refreshed_minutes_ago += 1
        self.set_refresh_label()
        self.schedule_refresh_label_update()
        return False

    def set_refresh_label(self, refreshing=False):
        if refreshing:
            refresh_label=_("Refreshing, please wait")
        elif self.refreshed_minutes_ago < 0:
            refresh_label=_("Refresh")
        elif self.refreshed_minutes_ago == 0:
            refresh_label="%s (%s)" % (_("Refresh"), _("just now"))
        else:
            refresh_label = "%s (%s)" % (_("Refresh"), _("%d min. ago") % self.refreshed_minutes_ago)
        log.debug("Indicator: setting refresh label to '%s'" % refresh_label)
        self.refresh_show.set_label(refresh_label)

    # Load weather data from cache and display its values
    def show_cached_weather(self):
        try:
            self.menu_update_lock.acquire(True)

            cached_weather = self.settings.get_weather(self.places[self.placechosen][0])
            if cached_weather is not None:
                cached_weather = eval(cached_weather)
                log.debug("Indicator: loading weather from cache for %s" % self.places[self.placechosen])
                self.menu_normal()
                self.set_refresh_label(True)
                self.icon = cached_weather['icon']
                if (self.icon == False):
                    self.button.set_icon(os.path.join(PROJECT_ROOT_DIRECTORY, "share/indicator-weather/media/icon_unknown_condition.png"))
                else:
                    self.button.set_icon(self.icon)

                self.city_show.set_label(self.places[self.placechosen][1])
                self.cond_show.set_label(cached_weather['condition'])
                self.temp_show.set_label(cached_weather['temper'])
                if cached_weather['humidex'] != None:
                    self.humidex_show.set_label(cached_weather['humidex'])
                else:
                    self.humidex_show.destroy()
                self.humid_show.set_label(cached_weather['humidity'])
                self.wind_show.set_label(cached_weather['wind'])
                self.sunrise_show.set_label(cached_weather['sunrise'])
                self.sunset_show.set_label(cached_weather['sunset'])
                self.update_label(cached_weather['label'])
                #self.button.set_status(appindicator.STATUS_ATTENTION)
                #self.button.set_status(appindicator.STATUS_ACTIVE)           

        except Exception, e:
            log.error(e)
            log.debug(traceback.format_exc(e))

        self.menu_update_lock.release()

    # Get fresh weather data
    def get_new_weather_data(self, notif = True):
        
        # get weather and catch any exception
        weather = None
        try:
            weather = self.get_weather()

        except urllib2.URLError, e:
            weather = None
            log.error("Indicator: networking error: %s" % e)

        except Exception, e:
            weather = None
            log.error(e)
            log.debug(traceback.format_exc(e))

        try:
            # wait until cacher finishes
            log.debug("Indicator: updateWeather: waiting for 'Cacher' thread to terminate")
            self.menu_update_lock.acquire(True)
            self.menu_update_lock.release()
                
            if weather is None:
                # remove the "Refreshing" status
                self.set_refresh_label()
                # No data returned - leave cached data to be displayed
                log.error("Indicator: updateWeather: could not get weather, leaving cached data")
                # Repeat an attempt in one minute
                self.schedule_weather_update(1)
                return

            # Fill in menu with data
            log.debug("Indicator: updateWeather: got condition '%s', icon '%s'" % (self.condition, self.icon))
            self.condition = weather.get_condition_label()
            self.icon = weather.get_icon_name()
            log.debug("Indicator: fill in menu with params: city='%s', temp='%s', humid='%s', wind='%s', sunrise='%s', sunset='%s', puretemp=%s" % (self.places[self.placechosen][1], weather.get_temperature_label(), weather.get_humidity_label(), weather.get_wind_label(), weather.get_sunrise_label(), weather.get_sunset_label(), weather.get_temperature()))

            self.menu_normal()
            self.update_refresh_label(0)
            self.city_show.set_label(self.places[self.placechosen][1])
            self.cond_show.set_label(self.condition)
            self.temp_show.set_label(weather.get_temperature_label())
            if (weather.get_humidex_label() != None):
                self.humidex_show.set_label(weather.get_humidex_label())
            else:
                self.humidex_show.destroy()
            self.humid_show.set_label(weather.get_humidity_label())
            self.wind_show.set_label(weather.get_wind_label())
            self.sunrise_show.set_label(weather.get_sunrise_label())
            self.sunset_show.set_label(weather.get_sunset_label())

            # Saving cached data, unless correct icon is supplied
            if (self.icon == False):
                self.button.set_icon(os.path.join(PROJECT_ROOT_DIRECTORY, "share/indicator-weather/media/icon_unknown_condition.png"))
            else:
                self.button.set_icon(self.icon)
                self.settings.save_weather(weather, self.places[self.placechosen][0])
            self.update_label(weather.get_temperature(needs_rounding=True))

            # Notify user, if notifications are enabled
            if self.condition != self.settings.get_value("current") and self.notif == 'U':
                # Weather condition has changed
                log.debug("Indicator: updateWeather: weather has changed, notify")
                self.notify(self.condition, self.icon)
            if self.notif == 'S' and weather.condition_is_severe():
                # Severe weather condition notification
                log.debug("Indicator: updateWeather: severe condition notification")
                self.notify(self.condition, self.icon, severe=True)

            self.settings.set_value("current", self.condition)

        except Exception, e:
            log.error(e)
            log.debug(traceback.format_exc(e))

        self.schedule_weather_update()

    # Update weather
    def update_weather(self, notif=True, widget=None):
        log.debug("Indicator: updateWeather: updating weather for %s" % self.places[self.placechosen])
        # First, display cached data
        threading.Thread(target=self.show_cached_weather, name='Cache').start()
        # Then, start a new thread with real data pickup
        threading.Thread(target=self.get_new_weather_data, name='Fetcher').start()

    # Get current weather for selected location
    def get_weather(self):
        log.debug("Indicator: getWeather for location '%s'" % self.location_details['full name'])  
        self.current_location = Location(self.metric_system, self.wind_unit, self.location_details)
        log.debug("Indicator: getWeather: updating weather report")  
        self.current_location.update_weather_data(self.weather_source)
        return self.current_location.weather

    # Show notification to user
    def notify(self,conditon,icon,severe=False):
        log.debug("Indicator: Notify on weather condition, severe=%s, condition=%s, icon=%s" % (severe, self.condition, icon))  
        if severe:
			n = pynotify.Notification (_("Severe weather alert"),
                self.condition,
                icon)
        else:
		    n = pynotify.Notification (self.condition, "", icon)
        n.show ()

    # Menu callbacks
    # Open Preferences dialog
    def prefs(self, widget):
        log.debug("Indicator: open Preferences")
        if ((not hasattr(self, 'prefswindow')) or (not self.prefswindow.get_visible())):
            self.prefswindow = WeatherPreferencesDialog()
            self.prefswindow.show()

    def about(self, widget):
        log.debug("Indicator: open About dialog")  
        self.aboutdialog = gtk.AboutDialog()
        self.aboutdialog.set_name(_("Weather Indicator"))
        self.aboutdialog.set_version(VERSION)

        ifile = open(os.path.join(PROJECT_ROOT_DIRECTORY, "share/doc/indicator-weather/AUTHORS"), "r")
        self.aboutdialog.set_copyright(ifile.read().replace('\x0c', ''))
        ifile.close()

        ifile = open(os.path.join(PROJECT_ROOT_DIRECTORY, "share/common-licenses/GPL-3"), "r")
        self.aboutdialog.set_license(ifile.read().replace('\x0c', ''))
        ifile.close()

        self.aboutdialog.set_website("https://launchpad.net/weather-indicator")
        self.aboutdialog.set_translator_credits(_("translator-credits"))
        logo_path = os.path.join(PROJECT_ROOT_DIRECTORY, "share/indicator-weather/media/icon.png")
        self.aboutdialog.set_logo(gtk.gdk.pixbuf_new_from_file(logo_path))


        self.aboutdialog.connect("response", self.about_close)
        self.aboutdialog.show()

    def about_close(self, widget, event=None):
        log.debug("Indicator: closing About dialog")  
        self.aboutdialog.destroy()
    
    # Open Extended forecast window
    def extforecast(self, widget):
        log.debug("Indicator: open Forecast")
        if ((not hasattr(self, 'forecastwd')) or (not self.forecastwd.get_visible())):
            self.forecastwd = ExtendedForecast()
            self.forecastwd.show()

    # Quit the applet
    def quit(self, widget, data=None):
        log.debug("Indicator: Quitting")
        try:
            # Compact the settings DB
            #self.settings.db.db.compact()
            #
            # There is a bug in python client v0.6, db.compact raises error
            # http://code.google.com/p/couchdb-python/issues/detail?id=141
            #
            # It seems that the client should always set the
            # 'Content-Type': 'application/json' header
            # So we bypass that compact command and execute a post directly
            # until the python client gets fixed
            headers = {
                'Content-Type': 'application/json'
            }
            self.settings.db.db.resource.post('_compact', headers=headers)
        except Exception, e:
            log.debug(e)
        gtk.main_quit()

class WeatherPreferencesDialog(gtk.Dialog):
    """ Class for preferences dialog """
    __gtype_name__ = "WeatherPreferencesDialog"

    # Creating a new preferences dialog
    def __new__(cls):
        log.debug("Preferences: creating")
        builder = get_builder('WeatherPreferencesDialog')
        new_object = builder.get_object("preferences_dialog")
        new_object.finish_initializing(builder)
        return new_object

    # Fill in preferences dialog with currect data
    def finish_initializing(self, builder):
        log.debug("Preferences: finishing initialization")
        log.debug("Preferences: got settings: unit=%s, notif=%s, wind=%s, rate=%s, source=%s" %
                (wi.unit, wi.notif, wi.wind, wi.rate, wi.source))
        self.builder = builder

        # Set correct wind_unit using dictionary of wind value and object name
        self.builder.get_object(wi.metric_systems[wi.unit][0]).set_active(True)
        self.builder.get_object(wi.notifications[wi.notif]).set_active(True)
        self.builder.get_object(wi.wind_systems[wi.wind][0]).set_active(True)
        self.builder.get_object(wi.weather_sources[wi.source][0]).set_active(True)
        self.builder.get_object('show_label').set_active(wi.show_label)
        self.builder.get_object('show_label').set_visible(hasattr(wi.winder, 'set_label'))
        self.builder.get_object('rate').set_value(float(wi.rate))

        log.debug("Preferences: Loading places")
        if wi.places != None:
            for place in wi.places:
                log.debug("Preferences: Places: got (%s, %s)" % (place[1], place[0]))
                newplace = list()
                newplace.append(place[1])
                newplace.append(place[0])
                newplace.append(wi.settings.get_location_details(place[0]))
            
                self.builder.get_object('citieslist').append(newplace)
            self.builder.get_object('ok_button').set_sensitive(True)
            
        self.builder.connect_signals(self)

    # 'Remove' clicked - remove location from list
    #TODO: Update settings object
    def on_remove_location(self, widget):
        selection = self.builder.get_object('location_list').get_selection()
        model, iter = selection.get_selected()
        if iter != None:
            log.debug("Preferences: Removing location %s (code %s)" % (model[iter][0], model[iter][1]))
            model.remove(iter)

        if (self.builder.get_object('citieslist').get_iter_first() == None):
            self.builder.get_object('ok_button').set_sensitive(False)

    # 'Add' clicked - create a new Assistant
    def on_add_location(self, widget):
        log.debug("Preferences: Add location clicked")
        if ((not hasattr(self, 'assistant')) or (not self.assistant.get_visible())):
            self.assistant = Assistant()
            self.assistant.show()

    # 'OK' clicked - save settings
    def ok(self, widget, data=None):
        log.debug("Preferences: Saving settings")
        need_to_update_weather = False
        need_to_update_indicator = False

        #Show label near icon
        new_show_label = self.builder.get_object('show_label').get_active()
        if (wi.show_label != new_show_label):
            wi.show_label = new_show_label
            wi.settings.set_value("show_label", new_show_label)
            need_to_update_weather = False
            need_to_update_indicator = True
            log.debug("Preferences: Show Label changed to '%s'" % wi.show_label)

        # Metric systems
        for k in wi.metric_systems.keys():
            if self.builder.get_object(wi.metric_systems[k][0]).get_active():
                new_unit = k
                new_metric_system = wi.metric_systems[k][1]

        if (wi.unit != new_unit):
            wi.unit = new_unit
            wi.metric_system = new_metric_system
            wi.settings.set_value("unit", wi.unit)
            need_to_update_weather = True
            log.debug("Preferences: Unit changed to '%s'" % wi.unit)

        # Notifications
        for k in wi.notifications.keys():
            if self.builder.get_object(wi.notifications[k]).get_active():
                new_notification  = k

        if (wi.notif != new_notification):
            wi.notif = new_notification
            wi.settings.set_value("notif", wi.notif)
            need_to_update_weather = True
            log.debug("Preferences: Notifications changed to '%s'" % wi.notif)

        # Wind Units
        for k in wi.wind_systems.keys():
            if self.builder.get_object(wi.wind_systems[k][0]).get_active():
                new_wind_unit   = k
                new_wind_system = wi.wind_systems[k][1]

        if (wi.wind != new_wind_unit):
            wi.wind = new_wind_unit
            wi.wind_unit = new_wind_system
            wi.settings.set_value("wind", wi.wind)
            need_to_update_weather = True
            log.debug("Preferences: Wind Unit changed to '%s'" % wi.wind)

        # Weather source
        for k in wi.weather_sources.keys():
            if self.builder.get_object(wi.weather_sources[k][0]).get_active():
                new_source   = k
                new_weather_source = wi.weather_sources[k][1]

        if (wi.source != new_source):
            wi.source = new_source
            wi.weather_source = new_weather_source
            wi.settings.set_value("data_source", wi.source)
            need_to_update_weather = True
            log.debug("Preferences: Weather Source changed to '%s'" % wi.source)

        # Rate
        if int(self.builder.get_object('rate').get_value()) != wi.rate:
            wi.settings.set_value("refresh_rate", int(self.builder.get_object('rate').get_value()))
            wi.rate = int(self.builder.get_object('rate').get_value())
            log.debug("Preferences: Rate changed to '%s'" % wi.rate)
            wi.schedule_weather_update()
            
        # Get places from location list
        newplaces = list()
        item = self.builder.get_object('citieslist').get_iter_first()
        while (item != None):
            newplace = list()
            newplace.append(self.builder.get_object('citieslist').get_value (item, 1))
            newplace.append(self.builder.get_object('citieslist').get_value (item, 0))
            newplaces.append(newplace)
            item = self.builder.get_object('citieslist').iter_next(item)

        # If places have changed - update weather data
        if newplaces != wi.places:
            wi.places = newplaces
            log.debug("Preferences: Places changed to '%s'" % str(wi.places))
            wi.settings.set_value("places", str(wi.places))
            if (type(wi.place) != None) and (wi.place in wi.places):
                wi.placechosen = wi.places.index(wi.place)
            else:
                wi.placechosen = 0
                wi.place = wi.places[0]
            log.debug("Preferences: Place Chosen changed to '%s'" % wi.placechosen)
            wi.settings.set_value("placechosen", wi.placechosen)
            wi.location_details = eval(wi.settings.get_location_details(wi.place[0]))
            wi.menu_normal()
            wi.set_refresh_label()
            need_to_update_weather = True

        if need_to_update_weather:
            wi.update_weather(False)

        if need_to_update_indicator:
            wi.update_label(wi.previous_label_value)
        
        self.destroy()

    # 'Cancel' click - forget all changes
    def cancel(self, widget, data=None):
        log.debug("Preferences: Cancelling")
        self.destroy()
        
class ExtendedForecast(gtk.Window):
    """ Class for forecast window """
    __gtype_name__ = "ExtendedForecast"

    # Create forecast
    def __new__(cls):
        log.debug("ExtendedForecast: creating")
        builder = get_builder('ExtendedForecast')
        new_object = builder.get_object("extended_forecast")
        new_object.finish_initializing(builder)
        return new_object

    # Fill in forecast parameters
    def finish_initializing(self, builder):
        log.debug("ExtendedForecast: finishing initialization")
        self.builder = builder
        self.builder.connect_signals(self)

        # Get forecast data using Forecast object
        log.debug("ExtendedForecast: chosen place: %s (code %s)" % (wi.places[wi.placechosen][1], wi.places[wi.placechosen][0]))
        self.builder.get_object('extended_forecast').set_title("%s %s" % (_('Weather Forecast for '), wi.places[wi.placechosen][1]))
        log.debug("ExtendedForecast: getting forecast data")
        forecast = Forecast(wi.metric_system, wi.current_location.location_details['latitude'], wi.current_location.location_details['longitude'], locale_name)
        forecast.prepare_forecast_data()
        if forecast.error_message != None:
            #Error occurred while getting forecast data
            self.builder.get_object('connection_error').set_text("%s" % forecast.error_message)
            self.builder.get_object('connection_error').set_visible(True)
            self.builder.get_object('hbox1').set_visible(False)
        else:
            daysofweek = forecast.get_forecast_daysofweek()
            forecast_data = forecast.get_forecast_data()
            if forecast_data == None:
                # Forecast data unavailable - hide elements and show 'connection_error' label
                self.builder.get_object('connection_error').set_visible(True);
                self.builder.get_object('hbox1').set_visible(False);
                self.builder.get_object('hseparator1').set_visible(False);
                return
            (highdata, lowdata) = forecast_data
            icons      = forecast.get_forecast_icons()
            conditions = forecast.get_forecast_conditions()

            log.debug("ExtendedForecast: parsing forecast data")
            # Create labels for each weekday
            self.builder.get_object('day1lbl').set_label('<big>%s</big>' % daysofweek[0].capitalize())
            self.builder.get_object('day2lbl').set_label('<big>%s</big>' % daysofweek[1].capitalize())
            self.builder.get_object('day3lbl').set_label('<big>%s</big>' % daysofweek[2].capitalize())
            self.builder.get_object('day4lbl').set_label('<big>%s</big>' % daysofweek[3].capitalize())

            # Fill in icons
            for i in xrange(1,5):
                # Get icon name from dictionary in Weather object for Google icons
                conds = Weather._GoogleConditions.get(icons[i-1])
                if conds != None:
                    google_icon = conds[0]
                else:
                    log.error("ExtendedForecast: unknown Google weather condition '%s'" % icons[i-1])
                    log.error(forecast.forecast)
                    google_icon = 'weather-unknown-condition'
                self.builder.get_object('day%simage' % str(i)).set_from_icon_name(google_icon,gtk.ICON_SIZE_BUTTON)

            # Fill in condition labels
            for i in xrange(1,5):
                self.builder.get_object('day%scond' % str(i)).set_label(conditions[i-1])
                
            # Fill in High and Low temperatures
            if wi.metric_system == MetricSystem.SI:
                tempunit = '°C'
            else:
                tempunit = '°F'
            for i in xrange(1,5):
                label = "%s: %s%s" % (_('High'), highdata[i-1],tempunit)
                self.builder.get_object('day%stemphigh' % str(i)).set_label(label)
                label = "%s: %s%s" % (_('Low'), lowdata[i-1],tempunit)
                self.builder.get_object('day%stemplow' % str(i)).set_label(label)

    # Closing forecast window
    def close(self, widget, data=None):
        log.debug("ExtendedForecast: closing window")
        self.destroy()

    def on_destroy(self, widget):
        pass

class Assistant(gtk.Assistant):
    """ Class for a wizard, which helps to add a new location in location list """
    __gtype_name__ = "Assistant"

    # Create new object
    def __new__(cls):
        log.debug("Assistant: creating new Assistance instance")
        builder = get_builder('Assistant')
        new_object = builder.get_object("assistant")
        new_object.finish_initializing(builder)  
        return new_object

    # Finish UI initialization - prepare combobox
    def finish_initializing(self, builder):
        log.debug("Assistant: finishing initialization")
        self.builder = builder
        self.builder.connect_signals(self)
        self.assistant = self.builder.get_object("assistant")
        self.assistant.set_page_complete(self.builder.get_object("label"),True)
        self.assistant.set_page_complete(self.builder.get_object("review"),True)

        # Set up combobox
        log.debug("Assistant: setting up location combobox")
        self.store = gtk.ListStore(str, str, str, str, str)
        self.location_input_combo = self.builder.get_object("combolocations")
        self.location_input_combo.set_model(self.store)
        self.location_input_combo.set_text_column(0)
        self.location_entry = self.builder.get_object("entrylocation")
        self.place_selected = None
        self.location = None

        self.assistant.set_forward_page_func(self.next_page)

    # 'Get cities' button clicked - get suggested cities list
    def on_get_city_names(self, widget):
        new_text = self.location_entry.get_text()
        log.debug("Assistant: looking for location '%s'" % new_text)
        try:
            # Clear up exising suggestions
            self.store.clear()
            # Get suggested city names from GeoNames DB in native locale
            new_text = urllib.quote(new_text)
            url = 'http://api.geonames.org/searchJSON?q=%s&featureClass=P&maxRows=10&lang=%s&username=indicatorweather' % (new_text, locale_name)
            cities = eval(urllib2.urlopen(url).read())
            for city in cities['geonames']:
                # Create a full city name, consisting of city name, administrative areas names and country name
                if 'adminName2' in city:
                    displayed_city_name = "%s, %s, %s, %s" % (city['name'], city['adminName1'], city['adminName1'], city['countryName'])
                elif 'adminName1' in city:
                    displayed_city_name = "%s, %s, %s" % (city['name'], city['adminName1'], city['countryName'])
                else:
                    displayed_city_name = "%s, %s" % (city['name'], city['countryName'])
                self.store.append([displayed_city_name, str(city['geonameId']), str(city['lat']), str(city['lng']), str(city['name'])])
                self.location_input_combo.popup()
        except urllib2.URLError:
            log.error("Assistant: error reaching url '%s'" % url)

    # A city is selected from suggested list
    def on_select_city(self, entry):
        if self.location_input_combo.get_active() != -1:
            self.place_selected = self.store[self.location_input_combo.get_active()]
            self.assistant.set_page_complete(self.builder.get_object("placeinput"),True)
        else:
            self.place_selected = None
            self.location = None
            self.assistant.set_page_complete(self.builder.get_object("placeinput"), False)

    # Create a location object out of a selected location
    def next_page(self, current_page):
        log.debug("Assistant: moved to page %s" % current_page)
        if (self.assistant.get_current_page() == 0) and not self.location and self.place_selected:
            # Label input page
            log.debug("Assistant: Page %s: got location with code %s" % (current_page, self.place_selected[1]))
            self.location = Location(wi.metric_system, wi.wind_unit)
            if self.location.prepare_location(self.place_selected):
                log.debug("Assistant: Page %s: City %s found" % (current_page, self.place_selected[0]))
                # Set a short city name as default label
                self.builder.get_object("entrylbl").set_text(self.place_selected[4])
            else:
                log.error("Assistant: Page %s: City with code %s was NOT found" % (current_page, self.place_selected[0]))
                return 3
        elif self.assistant.get_current_page() == 1:
            # Confirmation page
            lbl = self.builder.get_object("entrylbl").get_text()
            log.debug("Assistant: Page %s: City label is %s" % (current_page, lbl))
            # If empty label was input, set label to short city name
            if lbl == '':
                log.debug("Assistant: Page %s: Empty label found, setting lbl to short name - %s" % (current_page, self.place_selected[4]))
                lbl = self.place_selected[4]
            self.location.location_details['label'] = lbl
            self.builder.get_object("lbl3").set_label(_('Label:'))
            self.builder.get_object("labellbl").set_label('<b>%s</b>' % lbl)
            self.builder.get_object("placelbl").set_label('<b>%s</b>' % self.place_selected[0])
            
        return self.assistant.get_current_page() + 1

    # 'Cancel' clicked
    def on_cancel(self,widget):
        log.debug("Assistant: Cancelled")
        self.destroy()

    # 'Apply' clicked - save location details, add an entry in a location list
    def on_apply(self,widget):
        (location_code, location_details) = self.location.export_location_details()
        log.debug("Assistant: Apply: adding location ('%s', '%s')" % (self.location.location_details['label'], location_code))
        newplace = list()
        newplace.append(self.location.location_details['label'])
        newplace.append(str(location_code))
        newplace.append(str(location_details))
        wi.settings.save_location_details(eval(str(location_details)), str(location_code))
        wi.prefswindow.builder.get_object('citieslist').append(newplace)
        # Enable 'OK' button in Preferences
        wi.prefswindow.builder.get_object('ok_button').set_sensitive(True)
        self.hide()

class SingleInstance(object):
    """ Class to ensure, that single instance of the applet is run for each user """

    # Initialize, specifying a path to store pids
    def __init__(self, pidPath):
        self.pidPath=pidPath
        # See if pidFile exists
        if os.path.exists(pidPath):
            log.debug("SingleInstance: pid file %s exists" % pidPath)
            # Make sure it is not a "stale" pidFile
            pid=open(pidPath, 'r').read().strip()
            # Check list of running pids, if not running it is stale so overwrite
            pidRunning = commands.getoutput('ls /proc | grep %s' % pid)
            log.debug("SingleInstance: pid running %s" % pidRunning)
            self.lasterror = True if pidRunning else False
        else:
            self.lasterror = False

        if not self.lasterror:
            log.debug("SingleInstance: writing new pid %s" % str(os.getpid()))
            # Create a temp file, copy it to pidPath and remove temporary file
            (fp, temp_path)=tempfile.mkstemp()
            try:
                os.fdopen(fp, "w+b").write(str(os.getpid()))
                shutil.copy(temp_path, pidPath)
                os.unlink(temp_path)
            except Exception as e:
                log.error("SingleInstance: exception while renaming '%s' to '%s':\n %s" % (temp_path, pidPath, str(e)))  

    def is_already_running(self):
        return self.lasterror

    def __del__(self):
        if not self.lasterror:
            log.debug("SingleInstance: deleting %s" % self.pidPath)
            os.unlink(self.pidPath)

def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    #Enable and configure logs
    global log
    cachedir = os.environ.get('XDG_CACHE_HOME','').strip()
    if not cachedir:
        cachedir = os.path.expanduser("~/.cache")
    log_filename = os.path.join(cachedir, "indicator-weather.log")
    log = logging.getLogger('IndicatorWeather')
    log.propagate = False
    log.setLevel(logging.DEBUG)
    log_handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=1024*1024, backupCount=5)
    log_formatter = logging.Formatter("[%(threadName)s] %(asctime)s - %(levelname)s - %(message)s")
    log_handler.setFormatter(log_formatter)
    log.addHandler(log_handler)

    log.info("------------------------------")
    log.info("Started Weather Indicator from %s" % PROJECT_ROOT_DIRECTORY)
    log.info("Weather Indicator version %s" % VERSION)

    # Single instance stuff for weather indicator
    myapp = SingleInstance("/tmp/indicator-weather-%d.pid" % os.getuid())
    # check is another instance of same program running
    if myapp.is_already_running():
        log.info("Another instance of this program is already running")
        sys.exit(_("Another instance of this program is already running"))

    # Set http proxy support
    ProxyMonitor.monitor_proxy(log)
    # Use date-time format as in indicator-datetime
    TimeFormatter.monitor_indicator_datetime(log)
        
    # not running, safe to continue...
    gtk.gdk.threads_init()
    gtk.gdk.threads_enter()
    # Remember locale name
    global locale_name
    locale_name = locale.getlocale()[0]
    if locale_name is not None:
        locale_name = locale_name.split('_')[0]
    else:
        locale.setlocale(locale.LC_ALL, 'C') # use default (C) locale
        locale_name = "en"
    wi = indicator_weather()
    main()
    gtk.gdk.threads_leave()
