# 

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
import datetime
import sys

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
    # read command line inputs if any
    arg_list = sys.argv[1:]
    
    if "graph" in arg_list:
        make_graphs = True
    else:
        make_graphs = False
    if "weighting_matrix.csv" in arg_list:
        weighting_matrix = pd.read_csv('weighting_matrix.csv')
    else:
        weighting_matrix = None
    
    # read in the closed requests from past years
    full_data = read_closed_requests([2017,2018,2019,2020,2021])    
    
    # filter for street light issues only
    street_light_data = full_data[full_data['service_name'].eq('Street Light Maintenance') & full_data['status'].ne('Referred')].reset_index(drop=True)
    
    # make a plot of city wide maintenance time growth and number closed as a double axis plot 
    city_wide_data = street_light_data[['year','case_age_days']].groupby(['year']).agg(['median','count']).reset_index()
    city_wide_data.columns = city_wide_data.columns.map('_'.join)
    city_wide_data.rename(columns={"year_":"Year",'case_age_days_median':'Median Time to Repair', 'case_age_days_count':'Count'},inplace=True)
    if make_graphs:
        fig, ax = plt.subplots(figsize=(12,5))
        plt.plot(city_wide_data['Year'],city_wide_data['Median Time to Repair'],color='tab:blue')
        plt.xlabel('Year')
        plt.ylabel('Median Time to Repair',color='tab:blue')
        plt.axis(ymin=0)
        ax.set_xticks([2017,2018,2019,2020,2021],minor=False)
        ax2 = ax.twinx()
        ax2.plot(city_wide_data['Year'],city_wide_data['Count'],color='tab:red')
        ax2.set_ylabel('Number of Repairs Completed',color='tab:red')
        ax2.axis(ymin=0)
        plt.savefig('graphs/overall_performance.png',transparent=False,dpi=80,bbox_inches="tight")
        plt.show()
    
    # just nice to have
    city_wide_median = street_light_data[['case_age_days']].median()
    
    # make a histogram plot of the spread to show long tail
    hist_data = street_light_data[['case_age_days']].reset_index(drop=True)
    hist_data = hist_data[hist_data['case_age_days'].notna()].reset_index(drop=True)
    print(f"Longest repair took {hist_data['case_age_days'].max()} days")
    #hist_data.hist(column=['case_age_days'],bins=20)
    if make_graphs:
        fig, ax = plt.subplots(figsize=(12,5))
        ax.hist(hist_data['case_age_days'],bins=30)
        plt.xlabel('Time to Repair')
        plt.ylabel('Number of Street Light Repairs')
        plt.savefig('graphs/histogram.png',transparent=False,dpi=80,bbox_inches="tight")
        plt.show()
    
    # make a plot of the countcil district growth
    district_data = street_light_data[['year','council_district','case_age_days']].groupby(['year','council_district']).median().reset_index()
    district_data['year'] = district_data['year'].astype('int')
    district_data['council_district'] = district_data['council_district'].astype('int')
    district_data.rename(columns={'year':'Year','council_district':'Council District'},inplace=True)
    district_plot_prep = district_data.pivot(index='Year',columns='Council District',values='case_age_days')
    #district_plot_prep.plot(figsize=(10,7),ylabel='median Time to Repair (days)')
    if make_graphs:
        fig, ax = plt.subplots(figsize=(12,5))
        plt.plot(district_plot_prep,label=district_plot_prep.columns)
        plt.xlabel('Year')
        plt.ylabel('Median Time to Repair')
        ax.set_xticks([2017,2018,2019,2020,2021],minor=False)
        plt.legend(title="Council District")
        plt.savefig('graphs/council.png',transparent=False,dpi=80,bbox_inches="tight")
        plt.show()

    # make table of district data
    district_data = street_light_data[['council_district','case_age_days']].groupby(['council_district']).agg(['median','count']).reset_index()
    district_data.columns = district_data.columns.map('_'.join)
    district_data.rename(columns={'council_district_':'Council District', 'case_age_days_median':'Median Time to Repair', 'case_age_days_count':'Count'},inplace=True)
    district_income_data = pd.DataFrame({'Council District':[1,2,3,4,5,6,7,8,9],"Median Household Income (dollars)":[100768,75942,65810,56857,105047,85734,76946,50778,43222]})
    district_data = district_data.merge(district_income_data,how='inner',on='Council District')
    #if make_graphs:
    #    plt.table(district_data)
    # create the district equity factor for later joining on open reqs data
    district_data['district_weighting_factor'] = (district_data['Median Time to Repair']-district_data['Median Time to Repair'].min())/(district_data['Median Time to Repair'].max()-district_data['Median Time to Repair'].min())
    
    # make table of zipcode data
    zipcode_data = street_light_data[['zipcode','case_age_days']].groupby(['zipcode']).agg(['median','count']).reset_index()
    zipcode_data.columns = zipcode_data.columns.map('_'.join)
    zipcode_data.rename(columns={'zipcode_':'Zip Code', 'case_age_days_median':'Median Time to Repair', 'case_age_days_count':'Count'},inplace=True)
    zipcode_data = zipcode_data[zipcode_data['Count'].ge(10)].reset_index(drop=True)
    #if make_graphs:
    #    plt.table(zipcode_data)
    # create the zip code equity factor for later joining on open reqs data
    zipcode_data['zipcode_weighting_factor'] = (zipcode_data['Median Time to Repair']-zipcode_data['Median Time to Repair'].min())/(zipcode_data['Median Time to Repair'].max()-zipcode_data['Median Time to Repair'].min())
    
    # make table of community data
    community_data = street_light_data[['comm_plan_name','case_age_days']].groupby(['comm_plan_name']).agg(['median','count']).reset_index()
    community_data.columns = community_data.columns.map('_'.join)
    community_data.rename(columns={'comm_plan_name_':'Community', 'case_age_days_median':'Median Time to Repair', 'case_age_days_count':'Count'},inplace=True)
    community_data = community_data[community_data['Count'].ge(10)].reset_index(drop=True)
    #if make_graphs:
    #    plt.table(community_data)
    # create the community equity factor for later joining on open reqs data
    community_data['community_weighting_factor'] = (community_data['Median Time to Repair']-community_data['Median Time to Repair'].min())/(community_data['Median Time to Repair'].max()-community_data['Median Time to Repair'].min())
    # make an xy plot of Median Time to Repair vs. weighting factor
    
    # make a plot of in Promise Zone vs. rest of city
    in_out_of_zone = find_points_in_zone(street_light_data[['case_age_days','lat','lng','council_district','year']].reset_index(drop=True),'data/promise_zone_datasd.geojson')
    in_out_of_zone['name'] = in_out_of_zone['name'].fillna(value='Rest of City')
    
    in_out_data  = in_out_of_zone[['year','name','case_age_days']].groupby(['year','name']).median().reset_index()
    in_out_data['year'] = in_out_data['year'].astype('int')
    in_out_plot_prep = in_out_data.pivot(index='year',columns='name',values='case_age_days')
    #in_out_plot_prep.plot(figsize=(10,7),ylabel='median Time to Repair (days)')
    if make_graphs:
        fig, ax = plt.subplots(figsize=(12,5))
        plt.plot(in_out_plot_prep,label=in_out_plot_prep.columns)
        plt.xlabel('Year')
        plt.ylabel('Median Time to Repair')
        ax.set_xticks([2017,2018,2019,2020,2021],minor=False)
        plt.legend()
        plt.savefig('graphs/promise_zone.png',transparent=False,dpi=80,bbox_inches="tight")
        plt.show()
    # maybe a small map of promise zone vs rest of city as a thumbnail 
    
    # get the open requests wiht safety data added from the file writen by distance_filtering.py and add safety factor
    open_street_light_data = pd.read_csv('data/open_street_light_requests_with_saftey_counts.csv')
    
    # plot number of safety issues vs age of request
    if make_graphs:
        plt.subplots(figsize=(12,5))
        plt.plot(open_street_light_data['case_age_days'],open_street_light_data['number_safety_related_near'],'bo')
        plt.xlabel('Days the request has been open')
        plt.ylabel('Number of safety related reuests')
        plt.savefig('graphs/promise_zone.png',transparent=False,dpi=80,bbox_inches="tight")
        plt.show()
    # add promise zone equity factors
    open_street_light_data = find_points_in_zone(open_street_light_data,'data/promise_zone_datasd.geojson')
    open_street_light_data['name'] = open_street_light_data['name'].fillna(value='Rest of City')
    open_street_light_data['promise_zone_weighting'] = 1
    open_street_light_data.loc[open_street_light_data['name'].eq('Rest of City'),'promise_zone_weighting'] = 0
    
    # create uniform weighting factor for case_age_days and safety factor
    open_street_light_data['safety_weighting_factor'] = (open_street_light_data['number_safety_related_near']-open_street_light_data['number_safety_related_near'].min())/(open_street_light_data['number_safety_related_near'].max()-open_street_light_data['number_safety_related_near'].min())
    open_street_light_data['age_weighting_factor'] = (open_street_light_data['case_age_days']-open_street_light_data['case_age_days'].min())/(open_street_light_data['case_age_days'].max()-open_street_light_data['case_age_days'].min())
    
    # join the other weighting factors to this data
    open_street_light_data = open_street_light_data.merge(district_data[['district_weighting_factor','Council District']],how='left',left_on='council_district',right_on='Council District')
    open_street_light_data.drop(columns='Council District',inplace=True)
    zipcode_data['Zip Code'] = zipcode_data['Zip Code'].astype('float64')
    open_street_light_data = open_street_light_data.merge(zipcode_data[['zipcode_weighting_factor','Zip Code']],how='left',left_on='zipcode',right_on='Zip Code')
    open_street_light_data.drop(columns='Zip Code',inplace=True)
    open_street_light_data['zipcode_weighting_factor'].fillna(0.5)
    open_street_light_data = open_street_light_data.merge(community_data[['community_weighting_factor','Community']],how='left',left_on='comm_plan_name',right_on='Community')
    open_street_light_data.drop(columns='Community',inplace=True)
    open_street_light_data['community_weighting_factor'].fillna(0.5)
    if weighting_matrix:
        # create single priority column with weighting facotrs
        pass
    else:
        # create single priority column with equal weight
        pass