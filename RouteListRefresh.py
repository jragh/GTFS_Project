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

def RouteRefresh():

    route_list_request = requests.get('https://retro.umoiq.com/service/publicXMLFeed?command=routeList&a=ttc')

    route_list = xmltodict.parse(route_list_request.content, attr_prefix='')

    route_listDF = pd.DataFrame.from_dict(route_list['body']['route'])

    directionDF = pd.DataFrame()

    for i in route_listDF.loc[0:, 'tag']:
        temp_request = requests.get(f'https://retro.umoiq.com/service/publicXMLFeed?command=routeConfig&a=ttc&r={str(i)}')

        temp = xmltodict.parse(temp_request.content, attr_prefix='')

        tempDF = pd.DataFrame.from_dict(temp['body']['route']['direction'])

        directionDF = directionDF.append(tempDF)

    print(len(directionDF))

    print(directionDF.head(25))

    # os.chdir("c:/Users/Bushman/Documents")

    # cwd = os.getcwd()

    # print(cwd)

    # path = cwd + "/directionDFCSV.csv"

    # directionDF.to_csv(index=False, path_or_buf= path)

    return directionDF