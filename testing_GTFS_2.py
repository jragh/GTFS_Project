import pandas as pd
import numpy as np
import dash
from dash import dcc, html, ctx
import dash_bootstrap_components as dbc
import os 

#import plotly
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px

import requests

import time

import xmltodict
import json

from datetime import datetime

##########

#  This script will need to be run daily and / or weekly in order to keep the up to date tags and route titles

# route_list_request = requests.get('https://retro.umoiq.com/service/publicXMLFeed?command=routeList&a=ttc')

# route_list = xmltodict.parse(route_list_request.content, attr_prefix='')

# route_listDF = pd.DataFrame.from_dict(route_list['body']['route'])

# directionDF = pd.DataFrame()

# for i in route_listDF.loc[0:, 'tag']:
#     temp_request = requests.get(f'https://retro.umoiq.com/service/publicXMLFeed?command=routeConfig&a=ttc&r={str(i)}')

#     temp = xmltodict.parse(temp_request.content, attr_prefix='')

#     tempDF = pd.DataFrame.from_dict(temp['body']['route']['direction'])

#     directionDF = directionDF.append(tempDF)

# print(len(directionDF))

# print(directionDF.head(25))

# os.chdir("c:/Users/Bushman/Documents")

# cwd = os.getcwd()

# print(cwd)

# path = cwd + "/directionDFCSV.csv"

# directionDF.to_csv(index=False, path_or_buf= path)



request_route_config = f'https://webservices.umoiq.com/service/publicXMLFeed?command=routeConfig&a=ttc&r=54'

stops_route_dict = xmltodict.parse(requests.get(request_route_config).content, attr_prefix = '')
        
stops_route_df = pd.DataFrame.from_dict(stops_route_dict['body']['route']['stop'])

stops_route_df['tagTitle'] = stops_route_df['tag'].astype(str) + ' - ' + stops_route_df['title'].astype(str)

stop_id_test = str(stops_route_df['stopId'].loc[(stops_route_df['tag'] =='3203')].values[0]) #24060 #3203

predictions_request = f'https://retro.umoiq.com/service/publicXMLFeed?command=predictions&a=ttc&r=54&s=3203' #24060 #3203

predictions_dict = xmltodict.parse(requests.get(predictions_request).content, attr_prefix = '')

# predictions_df = pd.DataFrame.from_dict(predictions_dict['body']['predictions'])


#preds_provided = [(i['title'], int(j['seconds'])) for i in predictions_dict['body']['predictions']['direction'] for j in i['prediction']]

#preds_provided.sort(key = lambda y: y[1])

print(predictions_dict['body']['predictions']['direction']) # Difference is list for multiple branches, dictionary for single branch

title_a = predictions_dict['body']['predictions']['direction']


# testing_block = {'title': 'East - 54b Lawrence East towards Orton Park', 'prediction': {'epochTime': '1664688961448', 'seconds': '597', 'minutes': '9', 'isDeparture': 'false', 'branch': '54B', 'dirTag': '54_0_54Bpm', 'vehicle': '8842', 'block': '54_4_40', 'tripTag': '44279698'}}


# testing_return = [(testing_block['title'], int(testing_block['prediction']['seconds']))]


# print(testing_return)

#### Main Code Block for predictions ####

if isinstance(predictions_dict['body']['predictions']['direction'], dict) == True:

    title_a = predictions_dict['body']['predictions']['direction']['title']
    
    if isinstance(predictions_dict['body']['predictions']['direction']['prediction'], list) == True:

        preds_provided = [(title_a, int(i['seconds'])) for i in predictions_dict['body']['predictions']['direction']['prediction']]

        preds_provided.sort(key = lambda y: y[1])

        print(preds_provided)

    elif isinstance(predictions_dict['body']['predictions']['direction']['prediction'], dict) == True:

        preds_provided = [(title_a, int(predictions_dict['body']['predictions']['direction']['prediction']['seconds']))]

elif isinstance(predictions_dict['body']['predictions']['direction'], list) == True:
    preds_provided = [(i['title'], int(j['seconds'])) for i in predictions_dict['body']['predictions']['direction'] for j in i['prediction']]

    preds_provided.sort(key = lambda y: y[1])

    print(preds_provided[:3])


# for i in predictions_dict['body']['predictions']['direction']['prediction']:
#     print(i.items())
    #print((title_a, int(i['seconds'])))


### print(preds_provided[:3])

# for i in predictions_dict['body']['predictions']['direction']:
#     a = i['title']
#     for j in i['prediction']:
#         print('{0}: {1}'.format(i['title'], j['seconds']))
# for i, row in predictions_df.iterrows():
#     print(predictions_df.iloc[i, 1])
########

# bus_direction_tag_title = pd.read_csv('C:\\Users\\Bushman\\Documents\\directionDFCSV.csv', nrows=999999)

# for i, j in bus_direction_tag_title.iterrows():
#     print(i)

# # bus_direction_tag_title_dict = {bus_direction_tag_title.loc[i, 'tag']: str(bus_direction_tag_title.loc[i, 'title']) for i, j in enumerate(bus_direction_tag_title)}

# # print(bus_direction_tag_title_dict)



# request_route_config = f'https://webservices.umoiq.com/service/publicXMLFeed?command=routeConfig&a=ttc&r=54'

# stops_route_dict = xmltodict.parse(requests.get(request_route_config).content, attr_prefix = '')

# #print(stops_route_dict)

# stops_route_df = pd.DataFrame.from_dict(stops_route_dict['body']['route']['direction'])

# print(stops_route_df.head(5))

#### Will need to create a new dataframe to contain the stops and the title, and then do a nested selection ####


#stops_route_df['lat'] = stops_route_df['lat'].astype(float)

#stops_route_df['lon'] = stops_route_df['lon'].astype(float)