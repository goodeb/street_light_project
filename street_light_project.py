# 

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point


# functions
def find_points_in_zone(df,shape_file_name):
    """
    takes a dataframe and a finds which points are in the geaographic zones given in an input shape file
        Args:
            df: the dataframe with lat and lng columns
            shape_file_name: the path to a shape file with geographicl regions to be used as filters (units in file must be lat and long)
        Returns:
            df: the input dataframe with a name column added with a name column containing the name of the 
                geographic region where the point is located. Points outside any zone get nan for a name
    """
    # read shape file
    geographic_data = gpd.GeoDataFrame.from_file(shape_file_name)
    # work on input dataframe to add points and convert to geodataframe
    df['coords'] = list(zip(df['lng'],df['lat']))
    df['coords'] = df['coords'].apply(Point)
    points = gpd.GeoDataFrame(df, geometry='coords',crs=geographic_data.crs)
    # merge shape data with input df to get points in regions
    points_in_zone = gpd.tools.sjoin(points,geographic_data, predicate="within",how="left")
    # clean coluns in prep for return
    points_in_zone.drop(columns=['coords','index_right','objectid','juris'],inplace=True)
    
    return points_in_zone

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

# main code
if __name__ == "__main__":
    
    full_data = read_closed_requests([2017,2018,2019,2020,2021])    
    
    street_light_data = full_data[full_data['service_name'].eq('Street Light Maintenance') & full_data['status'].ne('Referred')].reset_index(drop=True)
    
    # make a plot of city wide maintenance time growth, get all years mean
    city_wide_data = street_light_data[['year','case_age_days']].groupby(['year']).mean().reset_index()
    city_wide_mean = street_light_data[['case_age_days']].mean()
    
    # make a histogram plot of the spread to show long tail
    hist_data_by_year = street_light_data[['year','case_age_days']].reset_index(drop=True)
    hist_data_by_year = hist_data_by_year[hist_data_by_year['case_age_days'].notna()].reset_index(drop=True)
    hist_data_by_year.hist(column=['case_age_days'],by='year',bins=20)
    
    hist_data = street_light_data[['case_age_days']].reset_index(drop=True)
    hist_data = hist_data[hist_data['case_age_days'].notna()].reset_index(drop=True)
    hist_data.hist(column=['case_age_days'],bins=20)
    
    # make a plot of the countcil district growth
    district_data = street_light_data[['year','council_district','case_age_days']].groupby(['year','council_district']).mean().reset_index()
    district_data['year'] = district_data['year'].astype('int')
    district_data['council_district'] = district_data['council_district'].astype('int')
    district_data.rename(columns={'year':'Year','council_district':'Council District'},inplace=True)
    district_plot_prep = district_data.pivot(index='Year',columns='Council District',values='case_age_days')
    district_plot_prep.plot(figsize=(10,7),ylabel='Mean Time to Repair (days)')
    
    
    # make table of district data
    district_data = street_light_data[['council_district','case_age_days']].groupby(['council_district']).agg(['mean','count']).reset_index()
    district_data.columns = district_data.columns.map('_'.join)
    district_data.rename(columns={'council_district_':'Council District', 'case_age_days_mean':'Mean Time to Repair', 'case_age_days_count':'count'},inplace=True)
    
    # make table of zipcode data
    zipcode_data = street_light_data[['zipcode','case_age_days']].groupby(['zipcode']).agg(['mean','count']).reset_index()
    zipcode_data.columns = zipcode_data.columns.map('_'.join)
    zipcode_data.rename(columns={'zipcode_':'Zipcode', 'case_age_days_mean':'Mean Time to Repair', 'case_age_days_count':'count'},inplace=True)
    zipcode_data = zipcode_data[zipcode_data['count'].ge(10)].reset_index(drop=True)
    
    # make table of Community data
    community_data = street_light_data[['comm_plan_name','case_age_days']].groupby(['comm_plan_name']).agg(['mean','count']).reset_index()
    community_data.columns = community_data.columns.map('_'.join)
    community_data.rename(columns={'comm_plan_name_':'Community', 'case_age_days_mean':'Mean Time to Repair', 'case_age_days_count':'count'},inplace=True)
    community_data = community_data[community_data['count'].ge(10)].reset_index(drop=True)

    # make a plot of in Promise Zone vs. rest of city
    in_out_of_zone = find_points_in_zone(street_light_data[['case_age_days','lat','lng','council_district','year']].reset_index(drop=True),'data/promise_zone_datasd.geojson')
    in_out_of_zone['name'] = in_out_of_zone['name'].fillna(value='Rest of City')
    in_out_data = in_out_of_zone[['year','name','case_age_days']].groupby(['year','name']).agg(['mean','median','count','std'])
    
    in_out_data  = in_out_of_zone[['year','name','case_age_days']].groupby(['year','name']).mean().reset_index()
    in_out_data['year'] = in_out_data['year'].astype('int')
    in_out_plot_prep = in_out_data.pivot(index='year',columns='name',values='case_age_days')
    in_out_plot_prep.plot(figsize=(10,7),ylabel='Mean Time to Repair (days)')
    
    # get safety adjacent data, correlate positions and time with 
    safety_adjacent_data = full_data[full_data['service_name'].isin(['Graffiti - Code Enforcement', 'Illegal Dumping','Graffiti','Encampment','Homeless Outreach',])].reset_index(drop=True)