#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 10:36:54 2022

@author: brentgoode
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
import datetime

def read_closed_requests(year_list):
    """
    reads in closed request data for multiple years, adds year data, and puts all the data together in a single df
        Args:
            year_list: a list of the years to be read
        Returns: a dataframe with the appropriate columns of the closed request data

    """
    full_data = pd.DataFrame()
    
    # loop over years to read in closed request data
    for year in year_list:
        file_name = f"data/get_it_done_requests_closed_{year}_datasd.csv"
        years_raw_data = pd.read_csv(file_name,
                                usecols=['date_requested', 'case_age_days',
                                         'service_name', 'service_name_detail',
                                         'date_closed', 'status', 'lat', 'lng', 'street_address', 'zipcode',
                                         'council_district', 'comm_plan_name', 'park_name',
                                         'case_origin'])
        years_raw_data['year']=year
        full_data = full_data.append(years_raw_data)
    return full_data


# read and format the open requests
open_reqs = pd.read_csv('data/get_it_done_requests_open_datasd.csv',usecols=['date_requested', 'case_age_days', 'service_name', 'service_name_detail',
         'date_closed', 'status', 'lat', 'lng', 'street_address', 'zipcode',
         'council_district', 'comm_plan_name', 'park_name', 'case_origin'])
open_reqs['date_requested'] = pd.to_datetime(open_reqs['date_requested'])
open_reqs['location'] = list(zip(open_reqs['lat'],open_reqs['lng']))
open_reqs['location'] = open_reqs['location'].apply(Point)

# read and format the recently closed requests
recently_closed_reqs = read_closed_requests([2022])
recently_closed_reqs['date_requested'] = pd.to_datetime(recently_closed_reqs['date_requested'])
recently_closed_reqs['location'] = list(zip(recently_closed_reqs['lat'],recently_closed_reqs['lng']))
recently_closed_reqs['location'] = recently_closed_reqs['location'].apply(Point)

# merge the open and recently closed requests
recent_reqs = open_reqs.append(recently_closed_reqs)

# filter open requests for street light issues
open_street_lights = open_reqs[open_reqs['service_name'].eq('Street Light Maintenance') & open_reqs['status'].ne('Referred')].reset_index(drop=True)
open_street_lights['number_safety_related_near'] = 0

# filter all events for ones that related to safety
safety_adjacent_data = recent_reqs[recent_reqs['service_name'].isin(['Graffiti - Code Enforcement', 'Illegal Dumping','Graffiti','Encampment','Homeless Outreach',])].reset_index(drop=True)
safety_adjacent_data  = gpd.GeoDataFrame(safety_adjacent_data ,geometry='location')
i=0
# find open_street_lights with start date before a safety_adjacent_data start date close by and add the number of safety related reports to the open light reqs 
# doing this as a loop is a terible way to do it. But it only has to be done once for now so optimization can wait this the need to run it a second time
for light_req in open_street_lights.itertuples():
   after_the_light_broke =  safety_adjacent_data[safety_adjacent_data['date_requested'].gt(light_req.date_requested)].reset_index(drop=True)
   # a very cludge fix for the geopandas unit issue to use 150ft as the radius
   near_the_broken_light = after_the_light_broke[after_the_light_broke['location'].distance(light_req.location).lt(0.0004838709677)]
   open_street_lights.at[light_req.Index, 'number_safety_related_near'] = len(near_the_broken_light)
   print(i)
   i += 1
   
# write this to a file so that this doesn't need to be re-run to get the the counts again
open_street_lights.to_csv('data/open_street_light_requests_with_saftey_counts.csv')