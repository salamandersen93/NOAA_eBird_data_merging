# -*- coding: utf-8 -*-
"""27Feb2021_progress_project_phase2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13gA_id__cnbBCbOtL-MhbikzQu6o0d-_
"""

!pip install noaa_coops

"""The tidal data will be retrieved from the National Oceanic and Atmospheric Admistration Center for Operational Oceanographic Products and Services (NOAA CO-OPS) API. This API allows querying by tidal observation station ID. For the purpose of this project, the tidal observation stations in Atlantic City, Cumberland, Cape May, and Sandy Hook will be used. Data is retrieved using the 'get_data' function and is returned the pandas dataframe format. The pandas dataframes are converted into namedtuples below to allow flexible manipulation. Attributes of the dataset include high tide time, high tide water level, low tide time, low tide water level, and date. Fields releant to tide times and water levels will be joined with eBird data on the date.

NOTE ON LIMITATIONS OF APIS: The current eBird API is only capable of querying data from the past 30 days. Thus, todays date minus 30 days must be used for these queries. Additionally, the NOAA COOPS data is only updated weekly, thus today's date minus 7 days must be used. Therefore this program can only acquire data for 3 consecutive weeks, not counting the current week.

ADDITIONAL NOTE ON LIMITATIONS: Atlantic City tidal data was not updated in February. NOAA staff has been contacted regarding the issue. Instead, Ship John Shoals tidal station data will be used instead (Cumberland County). Long-term for this data-set, Atlantic city data should be used as well so the code has been copied out.
"""

# get tidal data from noaa coops api
import noaa_coops as nc # noaa_coops api
from datetime import date, timedelta, datetime
atlantic_city = nc.Station(8534720)
cape_may = nc.Station(8536110)
sandy_hook = nc.Station(8531680)
ship_john_shoal = nc.Station(8537121)

today = date.today().strftime('%Y-%m-%d')
today = str(today.replace('-', ''))

end_date = datetime.today() - timedelta(days=0)
end_date = end_date.strftime('%Y-%m-%d')
end_date = str(end_date.replace('-', ''))

start_date = datetime.today() - timedelta(days=30)
start_date = start_date.strftime('%Y-%m-%d')
start_date = str(start_date.replace('-', ''))

'''atlantic_city_tides = atlantic_city.get_data(
     begin_date= "20210101",
     end_date= "20210301",
     product="high_low",
     datum="STND",
     units="metric",
     time_zone="gmt")'''

ship_john_shoal_tides = ship_john_shoal.get_data(
     begin_date= start_date,
     end_date= end_date,
     product="high_low",
     datum="STND",
     units="metric",
     time_zone="gmt")

cape_may_tides = cape_may.get_data(
     begin_date=start_date,
     end_date=end_date,
     product="high_low",
     datum="STND",
     units="metric",
     time_zone="gmt")

sandy_hook_tides = sandy_hook.get_data(
     begin_date=start_date,
     end_date=end_date,
     product="high_low",
     datum="STND",
     units="metric",
     time_zone="gmt")

#ac_tides = list(atlantic_city_tides.itertuples(index=False, name='Atlantic_City'))
sjs_tides = list(ship_john_shoal_tides.itertuples(index=False, name='Cumberland_County'))
cm_tides = list(cape_may_tides.itertuples(index=False, name='Cape_May'))
sh_tides = list(sandy_hook_tides.itertuples(index=False, name='Sandy_Hook'))
#all_tides = ac_tides + cm_tides + sh_tides

tides_all = {'Cumberland': sjs_tides, 'Cape May': cm_tides, 'Monmouth': sh_tides}
for key, value in tides_all.items():
  current_list = value
  for i in range(len(current_list)):
    print(current_list[i])

"""FIPS codes will be needed to query the eBird database for sightings in a given county. FIPS are numbers used to uniquely identify geographic regions, such as counties. FIPS codes are five-digit integers, with the first two digits indicating the state and the last three digits being county identifers. To acquire a list of full five-digit FIPS codes, the fcc website will be scraped using beautifulsoup. This project scope is New Jersey only, while the website contains FIPS codes for all 50 states. The New Jersey state code is 34 - so a regex ('34\d{3}\s*.*') was used to parse out five-digit numbers followed by a string containign the county name. FIPS and county codes were then extracted individually. The eBird API accepts strings in the US-{two-digit state code}-{county FIPS ID} format. So for new Jersey, we would use something like US-NJ-001. The five-digit FIPS codes and county names are manipulated into the desired format below, then saved into a dictionary with county names as keys.  


"""

# importing beautifulsoup to scrape fcc.gov for fips codes (county data)
from bs4 import BeautifulSoup
import urllib.request
import re

urlpage =  'https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt'
page = urllib.request.urlopen(urlpage)
soup = BeautifulSoup(page, 'html.parser')

# get all matches for FIPS -whitespace- county name (34 is NJ state code)
matches = re.findall( r'34\d{3}\s*.*', str(soup))
# the first match is the new jersey state fips code - we only need county fips codes. omitting first match
matches = matches[1:]

counties = {}
for i in range(len(matches)):
    fips_codes = re.findall(r'34\d{3}', matches[i])
    fips_code = fips_codes[0]
    county_names = re.findall(r'\s(.*County)', matches[i])
    county_name = county_names[0]
    county_name = county_name.lstrip()
    counties[county_name] = fips_code

# county fips codes are the last 3 digits of the whole code
county_fips = {}
for key, value in counties.items():
    corrected_value = value[2:5]
    corrected_value = 'US-NJ-' + corrected_value
    corrected_key = key[:-7]
    county_fips[corrected_key] = corrected_value
print(county_fips)

"""eBird query:"""

!pip install ebird-api

# import ebird API package and assign API key
from ebird.api import get_observations
from ebird.api import get_species_observations
from ebird.api import get_nearby_observations
from ebird.api import get_visits
from ebird.api import get_checklist
from ebird.api import get_taxonomy, get_taxonomy_forms, get_taxonomy_versions
from ebird.api import get_notable_observations
api_key = 'aape5hn8f10a' # api key obtained by request from eBird (personal use only - PLEASE DO NOT USE OR SHARE!)

taxonomy = get_taxonomy(api_key) # get scientific name, common name, species Code, category, taxonomic order, etc.

# we are interested in Charadriiformes* (Shorebirds, Gulls, Terns, Jaegers and Alcids)
# extracting only the data we need for this project into a new dictionary
shorebirds = [] # list of dictionaries from taxonomy for shorebirds
for d in taxonomy:
    for key, value in d.items():
        if key == 'order':
            if d[key] == 'Charadriiformes':
                shorebirds.append(d)

common_names = []
species_codes = []
for i in range(len(shorebirds)):
    current_species = shorebirds[i]
    for key, value in current_species.items():
        if key == 'comName':
            common_names.append(current_species['comName'])
        if key == 'speciesCode':
            species_codes.append(current_species['speciesCode'])

shorebirds_dict_pre = {}
for i in range(len(common_names)):
    current_name = common_names[i]
    shorebirds_dict_pre[current_name] = species_codes[i]

# cutting down the scope here to semi-common shorebirds (not gulls, terns, jaegers)
# need to decrease API request volume and tighten the scope of the project
# 18 semi-common shorebird abbreviations x 3 counties = 36 individual requests
narrowed_scope_abbv = ['killde', 'sander', 'dunlin', 'pursan', 'ameoys',
                       'bkbplo', 'greyel', 'semplo', 'lobdow', 'sposan',
                       'lesyel', 'leasan', 'margod', 'willet1', 'shbdow',
                       'wessan', 'pecsan', 'amgplo', 'solsan', 'stisan',
                       'hudgod', 'pipplo', 'uplsan']
shorebirds_dict = {}
for key, value in shorebirds_dict_pre.items():
  if value in narrowed_scope_abbv:
    shorebirds_dict[key] = value

for key, value in shorebirds_dict.items():
  print(key, value)

# relevant counties are Atlantic, Monmouth, and Cape May for query
# these queries pull a lot of data - so data will only be queried once from the API
# the data will be written into a csv file for later use, and the code in this cell will be commented out

relevant_county_codes = []
for key, value in county_fips.items():
    if key in 'Cumberland' or key in 'Monmouth' or key in 'Cape May': # Atlantic was removed due to NOAA limitations
        relevant_county_codes.append(value)

# list of shorebird species codes for query
relevant_species_codes = []
for key, value in shorebirds_dict.items():
    relevant_species_codes.append(value)

def append_sightings(start, stop, county, specie): # use this sparingly, data is expensive
  try: # ignore bad requests (404 errors)
      get_obs = get_species_observations(api_key, specie, county, back=30) 
      for i in range(len(get_obs)):
        current_dict = get_obs[i]
        if current_dict:
          current_dict['county'] = county
          records.append(current_dict)
  except:
    print('error')

records = []

i = 0 # the limit of records per query is 30, so we need to break it down into intervals of 30
j = 30

for c in range(len(relevant_county_codes)):
  current_county = relevant_county_codes[c]
  for n in range(len(relevant_species_codes)):
    current_specie = relevant_species_codes[n]
    append_sightings(i, j, current_county, current_specie)
    i += 30
    j += 30

# some checklists were empty (as they did not contain target species) - let's remove these
valid_records = []
for i in range(len(records)):
    if not records[i]:
        continue
    else:
        valid_records.append(records[i])

for i in range(len(valid_records)):
  current_record = valid_records[i]
  valid_records[i]['sightingId'] = current_record['locId'] + '-' + current_record['obsDt'] + current_record['subId']
  print(valid_records[i])

from typing import NamedTuple
test_list = []

class eBird_Tidal_Join(NamedTuple):
    sightingId: str
    date: datetime.date
    obsTime: datetime.time
    speciesName: str
    speciesCode: str
    locName: str
    locId: str
    lat: str
    lon: str
    county: str
    howMany: int
    tidal_station: str
    hh_time: datetime
    hh_water_level: float
    h_time: datetime
    h_water_level: float
    l_time: datetime
    l_water_level: float
    ll_time: datetime
    ll_water_level: float

list_of_sightings = []
test_list = []

# for all valid eBird records
for i in range(len(valid_records)):
  # get current record
  current_record = valid_records[i]
  # get the eBird observation date
  obs_date_str = str(current_record['obsDt'])
  # then convert to a datetime object
  obs_date_obj = datetime.strptime(obs_date_str, '%Y-%m-%d %H:%M')


  test_dict = {}

  # for all items in the county tide dictionary
  for county, tides in tides_all.items():
    current_county = county
    # get the current county's tides
    current_county_tides = tides
    # for all records in the county tide list
    for i in range(len(current_county_tides)):
      # get the current day's tides
      current_tide = current_county_tides[i]
      # get the date
      tide_date_str = str(current_tide[0])
      # if that date is not 'NaT'...
      if tide_date_str != 'NaT':
        # convert it to a datetime to match the eBird datetime so they can be compared
        tide_time_obj = datetime.strptime(tide_date_str, '%Y-%m-%d %H:%M:%S')
        # if the dates match...
        if str(obs_date_obj.date()) == str(tide_time_obj.date()):
          # get all these variables
          sID = current_record['sightingId']
          oDate = obs_date_obj.date()
          oTime = obs_date_obj.time()
          sName = current_record['comName']
          sCode = current_record['speciesCode']
          lName = current_record['locName']
          lID = current_record['locId']
          lat = current_record['lat']
          lng = current_record['lng']
          cnty = current_record['county']
          test_dict['sightingID'] = sID
          test_dict['observationDate'] = oDate
          test_dict['observationTime'] = oTime
          test_dict['county'] = cnty
          test_dict['speciesName'] = sName
          test_dict['speciesCode'] = sCode
          test_dict['locationName'] = lName
          test_dict['locationID'] = lID
          test_dict['lat'] = lat
          test_dict['lng'] = lng
        
          hMany = 0
          try:
            howMany = current_record['howMany']
            test_dict['howMany'] = howMany
          except:
            test_dict['howMany'] = 1

          cnty_name = next(key for key, value in county_fips.items() if value == cnty)
          cnty_name = cnty_name.strip()
          currenty_county = current_county + " County"

          if current_county == cnty_name:  
            test_dict['tideStationName'] = county
            test_dict['highhighTime'] = current_tide[0]
            test_dict['highhighWaterLevel'] = current_tide[1]
            test_dict['highTime'] = current_tide[2]
            test_dict['highWaterLevel'] = current_tide[3]
            test_dict['lowTime'] = current_tide[4]
            test_dict['lowWaterLevel'] = current_tide[5]
            test_dict['lowlowTime'] = current_tide[6]
            test_dict['lowlowWaterLevel'] = current_tide[7]
            
            test_list.append(test_dict)

for i in range(len(test_list)):
  print(test_list[i])

import pandas as pd
all_data_df = pd.DataFrame(test_list)
all_data_df.head(20)

# there are not always two high/low tides per day -- hence NaN values in the tidal columns are acceptable
all_data_df['observationDate'] =  pd.to_datetime(all_data_df['observationDate'], format='%Y-%M-%d')
all_data_df['observationTime'] =  pd.to_datetime(all_data_df['observationDate'], format='%H:%M:%S')
all_data_df.dtypes

from google.colab import drive
drive.mount('/content/gdrive')
nbdir = "/content/gdrive/My Drive/DSCI511/Colab/data/"

filepath = '/content/gdrive/My Drive/DSCI511/Colab/data/project/' + str(start_date) + '_' + str(end_date) + '.csv'
all_data_df.to_csv(filepath, index = False)