import pandas as pd
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, ctx
import dash_bootstrap_components as dbc

import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px

import requests

from datetime import datetime
import time

def generate_figs():

    array_dump = []

    base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca" 
        
    # Datasets are called "packages". Each package can contain many "resources"	
    # To retrieve the metadata for this package and its resources, use the package name in this page's URL:
        
    url = base_url + "/api/3/action/package_show"
        
    params = { "id": "ttc-bus-delay-data"}
        
    package = requests.get(url, params = params).json() 


    # Setting this up to get the max year from the array # 
    # 
    years_array = []

    for i, j in enumerate(package['result']['resources']):
        if j['datastore_active'] == False:

            if j['name'][-4:].isdigit() == True:

                years_array.append({'id': j['id'], 'year':int(j['name'][-4:])})

    # Will need to do this for busses, streetcars, and subways # 

    years_array_max = max(years_array, key=lambda x:x['year'])

    url = base_url + "/api/3/action/resource_show?id=" + years_array_max['id']

    resource_metadata = requests.get(url).json()

    test_busses_df = pd.read_excel(resource_metadata['result']['url'], 0, engine='openpyxl')

    test_busses_df['Vehicle Type'] = 'Bus'

    test_busses_df['Incident Hour'] = pd.to_datetime(test_busses_df['Time'], format='%H:%M').dt.hour

    # Setting Time of Day Blocks #
    test_busses_df['Time Block Incident'] = ''

    test_busses_df.loc[(test_busses_df['Incident Hour'].astype(int) >= 0) & (test_busses_df['Incident Hour'].astype(int) <= 6), 'Time Block Incident'] = 'Overnight'
    test_busses_df.loc[(test_busses_df['Incident Hour'] >= 7) & (test_busses_df['Incident Hour'] <= 12), 'Time Block Incident'] = 'Morning'
    test_busses_df.loc[(test_busses_df['Incident Hour'] >= 13) & (test_busses_df['Incident Hour'] <= 18), 'Time Block Incident'] = 'Afternoon'
    test_busses_df.loc[(test_busses_df['Incident Hour'] >= 19), 'Time Block Incident'] = 'Evening'




    ## Categorical setup of Data ##
    test_busses_df['Min Delay Cat'] = ''

    test_busses_df.loc[(test_busses_df['Min Delay'].astype(int) >= 0) & (test_busses_df['Min Delay'].astype(int) < 10), 'Min Delay Cat'] = 'Less Than 10 Minutes'
    test_busses_df.loc[(test_busses_df['Min Delay'].astype(int) >= 10) & (test_busses_df['Min Delay'].astype(int) < 20), 'Min Delay Cat'] = '10 - 20 Minutes'
    test_busses_df.loc[(test_busses_df['Min Delay'].astype(int) >= 20) & (test_busses_df['Min Delay'].astype(int) < 30), 'Min Delay Cat'] = '20 - 30 Minutes'
    test_busses_df.loc[(test_busses_df['Min Delay'].astype(int) >= 30) & (test_busses_df['Min Delay'].astype(int) < 40), 'Min Delay Cat'] = '30 - 40 Minutes'
    test_busses_df.loc[(test_busses_df['Min Delay'].astype(int) >= 40) & (test_busses_df['Min Delay'].astype(int) < 50), 'Min Delay Cat'] = '40 - 50 Minutes'
    test_busses_df.loc[(test_busses_df['Min Delay'].astype(int) >= 50) & (test_busses_df['Min Delay'].astype(int) < 60), 'Min Delay Cat'] = '50 - 60 Minutes'
    test_busses_df.loc[(test_busses_df['Min Delay'].astype(int) >= 60), 'Min Delay Cat'] = 'Over An Hour'

    category_orders_1 = ['Less Than 10 Minutes', '10 - 20 Minutes', '20 - 30 Minutes', '30 - 40 Minutes', '40 - 50 Minutes', '50 - 60 Minutes', 'Over An Hour']
    category_orders_2 = [str(i) for i in range(0, 24)]

    ## Categorical Setup End ##

    test_busses_df_clean = test_busses_df.loc[~((test_busses_df['Incident'] == 'Operations - Operator') & (test_busses_df['Vehicle'] == 0))]

    test_busses_df_clean['Day Of Week'] = test_busses_df_clean['Date'].dt.day_name()

    days_of_week_group = test_busses_df_clean.groupby('Day Of Week').agg({'Min Delay': 'sum', 'Vehicle': 'sum'}).reset_index()

    date_groupby = test_busses_df_clean.groupby(['Date', 'Time Block Incident']).agg({'Min Delay': 'sum', 'Vehicle': 'count'}).reset_index()

    date_groupby = date_groupby.groupby([pd.Grouper(key='Date', freq='W'), 'Time Block Incident']).agg({'Min Delay': 'sum', 'Vehicle': 'sum'}).reset_index()

    line_delay_groupby = test_busses_df_clean.groupby(['Date','Route']).agg({'Min Delay': 'sum', 'Min Gap': 'sum', 'Vehicle': 'count'}).reset_index()

    line_delay_groupby_2 = test_busses_df_clean.groupby(['Route', 'Min Delay Cat']).agg({'Min Delay': 'sum', 'Min Gap': 'sum', 'Vehicle': 'count'}).reset_index()

    line_delay_groupby_3 = test_busses_df_clean.groupby(['Route', 'Time Block Incident']).agg({'Min Delay': 'sum', 'Min Gap': 'sum', 'Vehicle': 'count'}).reset_index()

    # fig = px.density_heatmap(test_busses_df_clean, x=test_busses_df_clean['Route'].astype('str'), y='Incident', z='Min Delay', histfunc = 'sum')

    fig = px.histogram(test_busses_df_clean, x='Incident Hour', marginal="box", labels = {'Incident Hour': 'Time of Day (Hour, 24h Format)'}, title = 'Histogram: Number of Incidents By Time of Day (YTD)', text_auto=True)

    fig.update_layout(bargap=0.1, yaxis_title = 'Number of Incidents', margin = {'r': 0, 'b': 0, 'l': 0 })

    array_dump.append(fig)

    # fig.show()


    fig2 = px.histogram(test_busses_df_clean, x='Min Delay Cat', facet_row='Time Block Incident', color = 'Time Block Incident', category_orders={'Min Delay Cat': category_orders_1}, text_auto = True, title = 'Number of Delays By Duration and Time Of Day (YTD)')
    fig2.update_layout(bargap=0.1,  margin = {'r': 0, 'b': 0, 'l': 0 })

    array_dump.append(fig2)
    # fig2.show()

    fig4 = px.area(date_groupby,  x = "Date", y = "Min Delay", color = "Time Block Incident", title = 'Total Delay in Minutes Split By Time Of Day (Weekly)')
    fig4.update_layout(hovermode = 'x unified',  margin = {'r': 0, 'b': 0, 'l': 0 })

    array_dump.append(fig4)

    return array_dump
    # fig4.show()

    # fig5 = go.Figure()
    # days_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # for i in days_list:
    #     fig5.add_trace(go.Box(
    #         y=test_busses_df_clean['Min Delay'][test_busses_df_clean['Day Of Week'] == i],
    #         name=i,
    #         boxpoints='suspectedoutliers', # only suspected outliers
    #         marker=dict(
    #             color='rgb(8,81,156)',
    #             outliercolor='rgba(219, 64, 82, 0.6)',
    #             line=dict(
    #                 outliercolor='rgba(219, 64, 82, 0.6)',
    #                 outlierwidth=2)),
    #         line_color='rgb(8,81,156)'
    #     ))

    # fig5.show()


# facet_col = "Time Block Incident", facet_col_wrap=2

# df = px.data.stocks(indexed=True)-1
# fig = px.area(df, facet_col="company", facet_col_wrap=2)
# fig.show()


# fig3 = px.bar(line_delay_groupby_3, y='Min Delay', x=line_delay_groupby_3['Route'].astype('str'), color = 'Time Block Incident', text_auto='.2s', title="Total Minutes Delayed By Route")
# fig3.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
# fig3.update_layout(xaxis={'categoryorder':'total descending'}, bargap=0.2, xaxis_rangeslider_visible=True, xaxis_range=[0, 10])
# fig3.show()


# fig3 = 
	
# To get resource data:
	
# for idx, resource in enumerate(package["result"]["resources"]):
	
 
	
#        # To get metadata for non datastore_active resources:
	
#        if not resource["datastore_active"]:
	
#            url = base_url + "/api/3/action/resource_show?id=" + resource["id"]
	
#            resource_metadata = requests.get(url).json()
	
#            print(resource_metadata)
	
#            # From here, you can use the "url" attribute to download this file