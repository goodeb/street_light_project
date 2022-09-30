# street_light_project
Code and files for street light repair resource allocation project

# file descriptions
 explore.py: A scratch file for recording code used to explore the data sets
 street_light_project.py: The main project code
 distance_filtering.py: The code used produce a count of safety related requests geographically near and after every open street light repair request.
 geo_testing.py: Code used to work out how to filter data points inside from those outside the Promise Zone boundaries
 

# instructions
1) Reproduce the data directory
The data used for this project are publicaly available and large, so they are not included in this repository. The following files need to be downloaded to the data/ directory
-All "Get it done" request data: https://data.sandiego.gov/datasets/get-it-done-311/
-The Promise Zone definition file. Specifically the geojson file found here https://data.sandiego.gov/datasets/promise-zone/
If you want to explore the crime data set
-SANDAG Public Crime Data Extract: https://www.sandag.org/index.asp?classid=14&subclassid=21&projectid=446&fuseaction=projects.detail

2) Run the distance_filtering script

3) Run the project main script: street_light_project.py:
    If you want to make and save the graphs, give the graph argument after the name of the python file
