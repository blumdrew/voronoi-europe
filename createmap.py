#europe if countries were based on which capital city they are closest to

import os

import geopandas as gpd
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from unidecode import unidecode
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi

original_dir = os.getcwd()
file_path = original_dir + '/ne_10m_admin_0_countries'
file_name = 'ne_10m_admin_0_countries.shp'
X_RANGE, Y_RANGE = (-25,41), (35,72)

#create geoframe of europe (include turkey)
def create_geoframe():
    os.chdir(file_path)
    data = gpd.read_file(file_name)
    os.chdir(original_dir)

    europe_capitals = []
    with open('country capitals.txt','r') as file:
        for line in file:
            line_data = line.split(',')
            if line_data[-1] == 'Europe\n':
                name = line_data[0]
                lat_long = (line_data[2], line_data[3])
                cap_name = line_data[1]
                europe_capitals.append((name, lat_long, cap_name))

    europe_frame = gpd.GeoDataFrame()
    europe_frame['name'] = None
    europe_frame['geometry'] = None
    europe_frame['capital_name'] = None
    europe_frame['capital'] = None

    euro_index = 0
    for index in range(len(data)):
        country_data = data.loc[index]
        
        if country_data['CONTINENT'] == 'Europe' or country_data['NAME'] == 'Turkey':
            terr_name = unidecode(country_data['NAME'])
            sov_name = country_data['SOVEREIGNT']

            #bosnia and herzegovina is abreviated in data, serbia is Republic of Serbia
            if terr_name != sov_name and 'Bosnia' not in sov_name and 'Serbia' not in sov_name:
                skip = True
            else:
                skip = False
                
            terr_geo = country_data['geometry']
            for capital in europe_capitals:
                if terr_name == capital[0]:
                    cap_loc, terr_cap = capital[1], capital[2]
            if skip == False:
                europe_frame.loc[euro_index, 'name'] = terr_name
                europe_frame.loc[euro_index, 'geometry'] = terr_geo
                europe_frame.loc[euro_index, 'capital_name'] = terr_cap
                europe_frame.loc[euro_index, 'capital'] = cap_loc
                if terr_name == 'Vatican':
                    europe_frame.loc[euro_index, 'capital_name'] = 'Vatican'
                    europe_frame.loc[euro_index, 'capital'] = (41.9022, 12.4539)
                euro_index += 1
        
    return europe_frame

def voronoi_tesselation(geo_frame):
    
    voronoi_frame = gpd.GeoDataFrame()
    voronoi_frame['points'] = None
    voronoi_frame['geometry'] = None
    voronoi_frame['name'] = None

    capital_locations = [geo_frame.loc[index]['capital'] for index in range(len(geo_frame))
                if geo_frame.loc[index]['name'] != 'Vatican']
    #to deal with annoying far away parts, add points far outside of viewing range
    capital_locations.append((-80,170))
    capital_locations.append((-80,-65))
    capital_locations.append((140,170))
    capital_locations.append((140,-65))
    capital_locations.append((10,-65))
    capital_locations.append((60,10))
    
    vor = Voronoi(capital_locations)
    pts = vor.vertices
    regions = vor.regions

    i = 0
    for part in regions:
        loop_points = []
        for index in range(len(part)):
            skip = False
            if -1 in part:
                skip = True
            if skip == False:
                loop_points.append(pts[part[index]])
        try:
            x, y = list(zip(*loop_points))
            loop_points = list(zip(y,x))
            poly = Polygon(loop_points)

            #add country name to voronoi frame
            for cap in range(len(capital_locations[:45])):
                xc, yc = float(capital_locations[cap][1]), float(capital_locations[cap][0])
                if poly.contains(Point(xc,yc)):
                    voronoi_frame.loc[i, 'name'] = geo_frame.loc[cap, 'name']
            voronoi_frame.loc[i, 'points'] = poly
            i += 1
        except ValueError:
            True
            #do nothing
    
    return voronoi_frame

#most time-consuming part
def make_geom(geo_frame, voronoi_frame):
    #new columns to add
    voronoi_frame['area'] = None

    #create full continent of europe
    euro_geoms = [geo_frame.loc[index]['geometry'] for index in range(len(geo_frame))]
    all_europe = unary_union(euro_geoms)
    

    #test to see if voronoi shapes intersect with the europe shape
    for index in range(len(voronoi_frame)):
        current_shape = voronoi_frame.loc[index]['points']
        intersect = BaseGeometry.intersection(all_europe.buffer(0), current_shape.buffer(0))
        voronoi_frame.loc[index, 'geometry'] = intersect
        voronoi_frame.loc[index, 'area'] = intersect.area

    
    #there is always an error where index 39 should be a part of norway (index 40)
    nshape = voronoi_frame.loc[40]['geometry']
    missing_part = voronoi_frame.loc[39]['geometry']

    voronoi_frame.loc[40]['geometry'] = unary_union([nshape, missing_part])
    voronoi_frame.loc[39] = None
    
    return voronoi_frame
    
def plot(geo_frame, voronoi_frame, color_map ='viridis'):

    #select colors manually so no two colors are touching on map
    voronoi_frame['map color'] = [1,2,2,1,5,3,4,1,1,5,2,3,3,1,4,3,4,5,2,4,3,1,4,
                                  2,1,3,2,1,3,1,2,4,2,4,3,4,4,3,5,0,1,2,4,3,2,5]
    
    capital_pts = [geo_frame.loc[index]['capital'] for index in range(len(geo_frame))]
    
    fig, ax = plt.subplots()
    plt.figure(dpi = 500)
    ax = plt.gca()
    ax.set_xlim(X_RANGE)
    ax.set_ylim(Y_RANGE)
    ax.set_aspect('equal')
    ax.axis('off')
    clist = list(zip(*capital_pts))
    xcap = [float(val) for val in clist[1]]
    ycap = [float(val) for val in clist[0]]
    plt.plot(xcap, ycap, 'ko', markersize=1)
    
    voronoi_frame.plot(ax=ax, column = 'map color', cmap = color_map, linewidth = 0.5)
    
    plt.savefig('test.png', bbox_inches='tight')

def main():

    europe = create_geoframe()
    voronoi_shapes = voronoi_tesselation(europe)

    final_shapes = make_geom(europe, voronoi_shapes)

    plot(europe, final_shapes)

    return

if __name__ == '__main__':
    if input('Run program (y/n)?') == 'y':
        main()
