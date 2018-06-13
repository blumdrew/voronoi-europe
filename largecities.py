'''

Europe/middle east area with closest city of ~1 million people

'''
import os
from random import randint

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.geometry.base import BaseGeometry
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from scipy.spatial import Voronoi


original_dir = os.getcwd()
file_path = original_dir + '/ne_50m_admin_0_countries'
file_name = 'ne_50m_admin_0_countries.shp'
X_RANGE, Y_RANGE = (-25,63), (29,72)

def read_gis():
    
    os.chdir(file_path)
    data = gpd.read_file(file_name)
    data_europe = data[data.REGION_WB == 'Europe & Central Asia']
    data_middle_east = data[data.REGION_WB == 'Middle East & North Africa']
    data_afghan = data[data.ADMIN == 'Afghanistan']
    data = pd.concat((data_europe, data_middle_east, data_afghan))
    data = data.to_crs(epsg = 3395)
    os.chdir(original_dir)
    for col in data:
        if col != 'geometry':
            data = data.drop(col, axis = 1)
    
    return data
    
def voronoi_tesselation(region = read_gis()):
    region_shape = region.unary_union
    region['points'] = None
    region['city'] = None

    #read locations of city from file with pandas
    top_cities = pd.read_csv('europe_1mil.csv')
    x, y = top_cities['mercx'].tolist(), top_cities['mercy'].tolist()
    name = top_cities['city_ascii'].tolist()
    city_locs = [(name[index], (float(x[index]), float(y[index]))) for index in range(len(name))]
    
    points = [item[1] for item in city_locs]
    #add four extra points to later ignore
    points.append((-500000000,-500000000))
    points.append((-500000000,500000000))
    points.append((500000000,-500000000))
    points.append((500000000,500000000))

    vor = Voronoi(points)
    regions = vor.regions
    pts = vor.vertices

    i = 0
    for part in regions:
        loop_points = []
        if -1 not in part and part != []:
            loop_points = [pts[part[index]] for index in range(len(part))]
            poly = Polygon(loop_points)
            region.loc[i, 'points'] = poly

            name_index = 0
            for point in points:
                if poly.contains(Point(point)):
                    region.loc[i, 'city'] = city_locs[name_index][0]
                    break
                name_index += 1
            i += 1

    #only want to keep the ones that have city data
    keep = [index for index in range(len(region))
            if isinstance(region.iloc[index]['city'], str)]
    keep = [region.index[item] for item in keep]
    #filter out the rest
    region = region.filter(keep, axis = 0)

    #make geometry intersection of region geometry and voronoi tesselation
    extras = []
    for index in range(len(region)):
        current_vor = region.loc[index]['points']
        geom = BaseGeometry.intersection(current_vor.buffer(0),
                                         region_shape.buffer(0))
        region.at[index, 'geometry'] = geom
        current_city = region.loc[index]['city']
        color_1 = ['Dublin','London','Hamburg','Warsaw','Mannheim','Munich',
                   'Marseille', 'Rabat','Rome','Budapest','Athens','Bursa',
                   'Adana','El Giza','Amman','Karaj','Shiraz','Moscow',
                   'Yekaterinburg']
        color_2 = ['Birmingham','Paris','Essen','Madrid','Milan','Stockholm',
                   'Kiev','Nizhny Novgorod','Istanbul','Aleppo','Tel Aviv-Yafo',
                   'Baghdad','Tbilisi','Tehran','Chelyabinsk']
        color_3 = ['Lisbon','Copenhagen','Frankfurt','Turin','Algiers','Belgrade',
                   'Katowice','St. Petersburg','Kharkiv','Kazan','Tabriz',
                   'Kuwait','Cairo','Beirut','Ankara']
        color_4 = ['Brussels','Stuttgart','Tunis','Vienna','Alexandria','Minsk',
                   'Izmir','Rostov','Yerevan','Damascus','Mashhad']
        color_5 = ['Barcelona','Berlin','Bucharest','Naples','Tripoli','Mosul',
                   'Isfahan','Baku', 'Manchester','Casablanca']
                   
                   
        if current_city in color_1:
            region.loc[index, 'color'] = 1
        elif current_city in color_2:
            region.loc[index, 'color'] = 2
        elif current_city in color_3:
            region.loc[index, 'color'] = 3
        elif current_city in color_4:
            region.loc[index, 'color'] = 4
        elif current_city in color_5:
            region.loc[index, 'color'] = 5
        else:
            region.loc[index, 'color'] = 6
    
    return region.to_crs(epsg = 4326)

#both frames need to be in epsg 4326
def plot_maker(vframe, geo_frame, color_map = 'tab20'):
    if geo_frame.crs['init'] != 'epsg:4326':
        geo_frame = geo_frame.to_crs(epsg = 4326)

    if vframe.crs['init'] != 'epsg:4326':
        vframe = vframe.to_crs(epsg = 4326)

    top_cities = pd.read_csv('europe_1mil.csv')
    x, y = top_cities['lng'].tolist(), top_cities['lat'].tolist()
    name = top_cities['city_ascii'].tolist()
    city_data = [(name[index], (float(x[index]), float(y[index]))) for index in range(len(name))]

    plt.figure(dpi = 1000)
    ax = plt.gca()
    ax.set_xlim(X_RANGE)
    ax.set_ylim(Y_RANGE)
    ax.set_aspect('equal')
    ax.axis('off')
    for city in city_data:
        city_name = city[0]
        #plt.annotate(city_name, city[1], fontsize = 3)
        plt.plot(city[1][0], city[1][1], 'ko', markersize = 0.5)

    geo_frame.plot(ax = ax, edgecolor = 'black', facecolor = 'None', linewidth = 0.1, zorder = 2)
    vframe.plot(ax = ax, column = 'color',cmap = color_map, zorder = 1)
    plt.savefig('onemilano.png', bbox_inches = 'tight', pad_inches = 0)

 def main():
    v, g = voronoi_tesselation(), read_gis()
    plot_maker(v,g,'viridis_r')
    
if __name__ == '__main__':
    main()
