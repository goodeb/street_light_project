import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point


promise_zone = gpd.GeoDataFrame.from_file('data/promise_zone_datasd.geojson')
open_reqs = pd.read_csv('data/get_it_done_requests_open_datasd.csv')
#open_reqs.rename(columns={"lng":"lon"},inplace=True)

open_reqs['coords'] = list(zip(open_reqs['lng'],open_reqs['lat']))
open_reqs['coords'] = open_reqs['coords'].apply(Point)
points = gpd.GeoDataFrame(open_reqs, geometry='coords',crs=promise_zone.crs)

points_in_zone = gpd.tools.sjoin(points,promise_zone, predicate="within",how="left")

match_points = open_reqs[points_in_zone.name=='Promise Zone']