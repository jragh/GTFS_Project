import pandas as pd
import numpy as np
import dash
from dash import dcc, html, ctx
import dash_bootstrap_components as dbc

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


from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

epoch_time = int(time.time())

# "https://codepen.io/chriddyp/pen/bWLwgP.css", 

vehiclesString = f'https://webservices.umoiq.com/service/publicXMLFeed?command=vehicleLocations&a=ttc&t={epoch_time}'

# Downloading GTFS Realtime Vehicle Locations from request ##

vehicleLocationsRequest = requests.get(vehiclesString)

vehicleLocations = xmltodict.parse(vehicleLocationsRequest.content, attr_prefix='')

vehicleLocationsDf = pd.DataFrame.from_dict(vehicleLocations['body']['vehicle'])

vehicleLocationsDf['lat'] = vehicleLocationsDf['lat'].astype(float)

vehicleLocationsDf['lon'] = vehicleLocationsDf['lon'].astype(float)
print(vehicleLocationsDf.head(5))

routeListingStringRequest = requests.get('https://webservices.umoiq.com/service/publicXMLFeed?command=routeList&a=ttc')

routeListing = xmltodict.parse(routeListingStringRequest.content, attr_prefix = '')

routeListingDF = pd.DataFrame.from_dict(routeListing['body']['route'])
print(routeListingDF)

## Initial Service Alerts Pull ##

def sa_initial_pull():

    url_service_alerts = 'https://www.ttc.ca/service-alerts'

    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options, executable_path=r'C:\\Users\\Bushman\\geckodriver.exe')
    driver.get(url_service_alerts)

    results = driver.find_elements(By.CLASS_NAME, "ServiceAlerts_ListAlerts__2BUmu")

    results_list_split = results[0].text.split('\n')

    ## Function loops through above list to split line and route number into separate stuff

    result_return = []
    result_inner_list = []
    counter = 0

    for i in results_list_split:
        print(i)
        print(i[0].isdigit())
        if i[0].isdigit() == True:
            counter = 1
            result_inner_list.append(i)

        elif i[0].isdigit() == False:
            counter = 0
            result_inner_list.append(i)
            result_return.append(result_inner_list)
        
            result_inner_list = []

    service_alerts_num = len(result_return)

    # Loop through result return list to create accordion items
    
    accordion_items = []
    
    if len(result_return) > 0:
        for lst in result_return:

            if len(lst) == 2: 

                accordion_items.append(dbc.AccordionItem(children = [
                    dbc.Row(children=[
                        dbc.Col(width = '20%', children=[html.H5(f'{str(lst[0])}')]),
                        dbc.Col(width = '80%', children=[html.P(f'{str(lst[1])}')])
                        ])
                    ], title = f'{lst[0]}')
                )

            elif len(lst) == 1:

                string_test = ''

                if str(lst[0])[0:4] == 'Line':

                    string_test = str(lst[0])[0:6]
                
                else:

                    string_test = 'Additional Alert, See Below'


                accordion_items.append(dbc.AccordionItem(children = [
                    html.P(f'{str(lst[0])}')
                ], title = f'{string_test}'))

    return [service_alerts_num, dbc.CardBody([html.H5('Current TTC Alerts', style = {'color':'white'}),html.H3(f'{service_alerts_num} Alerts', style = {'color':'white'}),dbc.Button(id='service-alerts-toggle', children='Current Alerts Details', color = 'primary', outline=True)]), html.Div(id = 'alerts-offcanvas-div', children = [dbc.Offcanvas(id='service-alerts-offcanvas', is_open = False, placement = 'end', title = 'Current Service Alerts', children = [dbc.Accordion(children=accordion_items)])])]

sa_res = sa_initial_pull()

## Loading in the Route Config information for the routes
## This will need to be handled better in the future, for daily / weekly updating of the file
## Lookup anywhere in the file that is loading in the bus realtime locations, use a left join on the tag
bus_direction_tag_title = pd.read_csv('C:\\Users\\Bushman\\Documents\\directionDFCSV.csv')

bus_direction_tag_title_dict = {bus_direction_tag_title.loc[i, 'tag']: ' '.join(str(bus_direction_tag_title.loc[i, 'title']).split(' ')[3:]) for i, j in bus_direction_tag_title.iterrows()}
external_stylesheets = ['dbc.themes.FLATLY'] 

## Need to specify the stylesheet by the URL, in the future will store the CSS as a file on a cloud system or something
app = dash.Dash(__name__, external_stylesheets=['https://cdn.jsdelivr.net/npm/bootswatch@5.1.3/dist/flatly/bootstrap.min.css'])

app.layout = dbc.Container(fluid = True, children = [
    dbc.Row(id = 'main-row', class_name="g-0", style = {"height" : "100%", "background-color": "#f8f9fa"}, children = [
        dbc.Col(id = 'side-bar', align = "start", width = 3, style = {"background-color": "#f8f9fa", "height": "100%", "padding": "2rem"}, children = [
            html.Div([html.H3('Test Title for R&D App')]),
            html.Br(),
            html.Div(id = 'store-data-div', children = [dcc.Store(id = 'reset-store', storage_type = 'memory', data = "0")]),
            html.Div(id = 'selection-div', children = [
                html.H4('Route Selection'),
                dcc.Interval(id='timing-component', interval = 15000),
                dcc.Dropdown(id = 'line-selection', searchable = True, placeholder="Select a TTC Route", options = sorted(list(routeListingDF['title']))),
                dbc.Button(id = 'select-line-button', color='info', children = ['Zoom to Selected Line']),
                dbc.Button(id = 'reset-map-button', outline=True, color='secondary', children = ['Reset Map']),
                html.P(id = 'description-paragraph', children = ['Feel free to select a TTC Bus Route to view line details at a closer glance. Or just view all the currently running vehicles on the network!'])], className = "d-grid gap-1"),
            html.Div(id = 'stop-selection-div', children = []),
            html.Div(id = 'parent-stop-predictions-div', children = [html.Div(id='stop-predictions-div', children = [])])
            ]),
        dbc.Col(id = 'map-area', align = "end", width = 9, style ={"height": "100%"}, children = [
            dbc.Row(id='row-1', style = {'height': "15%"}, children =[
                # Code needs to go here to introduce the div and cards for displaying Number of Busses, Service alerts, etc # 
                dcc.Interval(id='service-alerts-timer', interval = 600000),
                dcc.Store(id='service-alerts-store', storage_type = 'memory', data = sa_res[0]),
                dbc.CardGroup(id = 'info-cards-group', children = [
                    dbc.Card(id = 'current-vehicles-card', color = 'success', children = [
                        dbc.CardBody([
                            html.H5('Current TTC Vehicles', style = {'color':'white'}),
                            html.H3('200 Vehicles', style = {'color':'white'}),
                            html.P('Displaying the current number of TTC vehicles', style = {'color':'white'})
                    ])]),
                    # dbc.Card(id = 'current-alerts-card', color = 'warning', children = [
                    #     dbc.CardBody([
                    #         html.H5('Current TTC Alerts', style = {'color':'white'}),
                    #         html.H3('17 Alerts', style = {'color':'white'}),
                    #         dbc.Button('Current Alerts Details', color = 'primary', outline=True),
                    #         html.Div(id = 'alerts-offcanvas-div', children = [
                    #             dbc.Offcanvas(id='service-alerts-offcanvas', children = [
                    #             ])
                    #         ])
                    #     ])
                    # ]),
                    dbc.Card(id = 'current-alerts-card', color = 'warning', children = [sa_res[1]]),
                    dbc.Card(id = 'historical-trends-card', color = 'info', children = [
                        dbc.CardBody([
                            html.H5('Historical TTC Performance Trends', style = {'color': 'white'}),
                            html.P('Click the link below to view historical TTC performace trends for previous years', style = {'color': 'white'}),
                            dbc.CardLink('Link to Historical TTC Trends', href = '#', style = {'color': 'white'})
                        ])
                    ])
                ]),
                sa_res[2],
            ], class_name="g-0"),
            dbc.Row(id ='map-row', style = {'height': "85%"}, children =[
                html.Div(id = 'map-div', style ={"height": "100%"}, children = [dcc.Graph(style = {'height': "84vh"}, id='main-graph')])
                ], class_name="g-0")
            ])
        ]), 
    ], style = {'height': "100%"}, class_name="g-0")

## Try to replace the div as opposed to just the map component
## This section of code resets the div when the reset button is clicked
@app.callback([Output('line-selection', 'value')], Input('reset-map-button', 'n_clicks'), prevent_initial_call=True)
def dropdown_menu_reset(n_clicks):
    if n_clicks:
        return [""]


@app.callback([Output('map-div', 'children'), Output('description-paragraph', 'children'), Output('reset-store', 'data'), Output('stop-selection-div', 'children'), Output('parent-stop-predictions-div', 'children'), Output('current-vehicles-card', 'children')],Input('reset-map-button', 'n_clicks'), Input('select-line-button', 'n_clicks'), State('line-selection', 'value'), prevent_initial_call=True)
def update_graph(n_clicks, n_clicks2, state1):
    triggered_id = ctx.triggered_id
    print(triggered_id)
    if triggered_id == 'reset-map-button':
        return map_reset(n_clicks)
    if triggered_id == 'select-line-button':
        return line_selection_zoom(state1)


def map_reset(n_clicks):

    layout_int = go.Layout(mapbox_style="carto-positron", hovermode='closest', showlegend = True, autosize=True, margin = {'r': 0, 't': 0, 'b': 0, 'l': 0 },
    legend = {'orientation': 'h', 'xanchor': 'left', 'yanchor': 'bottom', "y": 1.02, "x": 0}, mapbox = {'center': {'lat': 43.6532, 'lon': -79.3832}, 'zoom': 12, 'bearing' : 344})

    updated_epoch = int(time.time())

    # Request for Vehicles
    vlr = requests.get(f'https://webservices.umoiq.com/service/publicXMLFeed?command=vehicleLocations&a=ttc&t={updated_epoch}')

    # Locations transformation
    vl = xmltodict.parse(vlr.content, attr_prefix='')

    vlDF = pd.DataFrame.from_dict(vl['body']['vehicle'])

    vlDF['lat'] = vlDF['lat'].astype(float)

    vlDF['lon'] = vlDF['lon'].astype(float)

    vlDF['routeTitle'] = vlDF['dirTag'].map(bus_direction_tag_title_dict)

    len_df = len(vlDF.index)

    ## This section is to generate the data for the Vehicles on the map ##

    data_int = go.Scattermapbox(uirevision = True, lat = vlDF['lat'], lon = vlDF['lon'], mode = 'markers', 
    marker = go.scattermapbox.Marker(size = 8, opacity = 0.75, color = 'orange'), name='TTC Vehicle Locations',
    customdata=np.stack((vlDF['routeTag'], vlDF['routeTitle'], vlDF['speedKmHr']), axis=-1),
    hovertemplate = '<b>Main Route: </b>%{customdata[0]}' + '<br><b>Route Direction:</b> %{customdata[1]}' + '<br><b>Current Speed: </b> %{customdata[2]} km/h')

    ## This section is to return the information for Active Vehicles Banner Card ##

    active_vehicles_sentence = f'{len_df} Vehicles'

    av_card_return = [dbc.CardBody([html.H5('Current TTC Vehicles', style = {'color':'white'}), html.H3(active_vehicles_sentence, style = {'color':'white'}), html.P('Displaying the current number of TTC vehicles', style = {'color':'white'})])]

    ## Callback 

    return [[dcc.Graph(id='main-graph', style = {'height': "84vh"}, figure = go.Figure(data = [data_int], layout = layout_int))], ['Feel free to select a TTC Bus Route to view line details at a closer glance. Or just view all the currently running vehicles on the network!'], "0", [], [html.Div(id='stop-predictions-div', children = [])], av_card_return]


def line_selection_zoom(value_line):
    if value_line != '' and value_line is not None:

        print(str(value_line))

        value_route = str(value_line).split('-')[0]

        

        ## Returning Stop locations in a different color, smaller as well
        request_route_config = f'https://webservices.umoiq.com/service/publicXMLFeed?command=routeConfig&a=ttc&r={value_route}'

        stops_route_dict = xmltodict.parse(requests.get(request_route_config).content, attr_prefix = '')
        
        stops_route_df = pd.DataFrame.from_dict(stops_route_dict['body']['route']['stop'])

        stops_route_df['lat'] = stops_route_df['lat'].astype(float)

        stops_route_df['lon'] = stops_route_df['lon'].astype(float)

        stops_route_df['tagTitle'] = stops_route_df['tag'].astype(str) + ' - ' + stops_route_df['title'].astype(str)

        stops_smb = go.Scattermapbox(lat = stops_route_df['lat'], lon = stops_route_df['lon'], mode = 'markers', text = stops_route_df['title'], uirevision = True,
        marker = go.scattermapbox.Marker(size = 5, opacity = 0.75, color = 'red'), name='TTC Stops',
        hovertemplate = '<b>%{text}</b>' + '<br><b>Stop ID:</b> %{stopID}')

        ## Returning Bus Locations

        updated_epoch = int(time.time())

        vlr = requests.get(f'https://webservices.umoiq.com/service/publicXMLFeed?command=vehicleLocations&a=ttc&t={updated_epoch}&r={value_route}')

        # Locations transformation
        vl = xmltodict.parse(vlr.content, attr_prefix='')
        

        if isinstance(vl['body']['vehicle'], list):

            vlDF = pd.DataFrame.from_dict(vl['body']['vehicle'], orient='columns')
        
        else:
            vlDF = pd.DataFrame.from_dict([vl['body']['vehicle']], orient='columns')

        vlDF = vlDF.loc[(vlDF['routeTag'] == value_route) & (vlDF['routeTag'] == str(vlDF['dirTag']).split('_')[0])]

        vlDF['lat'] = vlDF['lat'].astype(float)

        vlDF['lon'] = vlDF['lon'].astype(float)

        vlDF['routeTitle'] = vlDF['dirTag'].map(bus_direction_tag_title_dict)

        vehicle_smb = go.Scattermapbox(lat = vlDF['lat'], lon = vlDF['lon'], mode = 'markers', 
        marker = go.scattermapbox.Marker(size = 10, opacity = 0.75, color = '#0078d7'), name='TTC Vehicle Locations', uirevision = True,
        customdata=np.stack((vlDF['routeTag'], vlDF['routeTitle'], vlDF['speedKmHr']), axis=-1),
        hovertemplate = '<b>Main Route: </b>%{customdata[0]}' + '<br><b>Route Direction:</b> %{customdata[1]}' + '<br><b>Current Speed: </b> %{customdata[2]} km/h')

        ## This section is to return information for the active vehicles card ##
        
        len_df = len(vlDF.index)

        active_vehicles_sentence = f'{len_df} Vehicles'

        av_card_return = [dbc.CardBody([html.H5(f'Current TTC Vehicles: Line {value_route}', style = {'color':'white'}), html.H3(active_vehicles_sentence, style = {'color':'white'}), html.P(f'Displaying the current number of TTC vehicles on line {value_route}', style = {'color':'white'})])]


        # Layout generation with auto zoom depending on the stops
        maxlon, minlon = max(stops_route_df['lon']), min(stops_route_df['lon'])
        maxlat, minlat = max(stops_route_df['lat']), min(stops_route_df['lat'])
        
        center = {
        'lat': round((maxlat + minlat) / 2, 6),
        'lon': round((maxlon + minlon) / 2, 6)
        }

        max_bound = max(abs(maxlat-minlat), abs(maxlon-minlon)) * 111
        zoom = 14 - np.log(max_bound)

        layout_int = go.Layout(mapbox_style="carto-positron", hovermode='closest', showlegend = True, uirevision = True, autosize=True, margin = {'r': 0, 't': 0, 'b': 0, 'l': 0 },
        legend = {'orientation': 'h', 'xanchor': 'left', 'yanchor': 'bottom', "y": 1.02, "x": 0}, mapbox = {'center': center, 'zoom': zoom, 'bearing' : 344})

        ## Stop Selection Layout
        stops_break = html.Br()
        stops_title = html.H4('Stop Selection')
        stops_dropdown = dcc.Dropdown(id='stop-selection', searchable = True, placeholder="Select a Stop Within the Chosen Route", options = sorted(list(stops_route_df['tagTitle'])))
        stops_desc = html.P(children =['Select a stop from the line to zoom to the stop and get vehicle arrival predictions!'])
        predictions_button_activate = dbc.Button(id='get-predictions-button', color = 'primary', children = ['Get Stop Predictions'], style = {'width':'100%'})
        predictions_store = dcc.Store(id = 'predictions-store', storage_type = 'memory', data = "0")
        prediction_stop_id_store = dcc.Store(id = 'predictions-stop-id-store', storage_type = 'memory', data = "0")
        predictions_interval = dcc.Interval(id='predictions-timing-component', interval = 60000)

        stops_children = [stops_break, stops_title, stops_dropdown,stops_desc, predictions_store, prediction_stop_id_store, predictions_interval, html.Br(), predictions_button_activate]


        return [[dcc.Graph(id='main-graph', style = {'height': "84vh"}, figure = go.Figure(data = [stops_smb, vehicle_smb], layout = layout_int))], [f"You have selected line {value_route}!"], value_route, stops_children, [html.Div(id='stop-predictions-div', children = [])], av_card_return]

    else:
        return dash.no_update

## Will need 2 callbacks: one to generate the initial prediction and update the stores
## Second callback will update the values using the interval timer
@app.callback([Output('stop-predictions-div', 'children'), Output('predictions-store', 'data')], Input('get-predictions-button', 'n_clicks'), State('line-selection', 'value'), State('stop-selection', 'value'), prevent_initial_call=True)
def provide_predictions(prediction_button_click, value_line, stop_value):
    if value_line != '' and value_line is not None and prediction_button_click is not None:

        print(value_line)

        value_route = str(value_line).split('-')[0]

        stop_value_updated = str(stop_value).split(' - ')[0]

        request_predictions = f'https://retro.umoiq.com/service/publicXMLFeed?command=predictions&a=ttc&r={value_route}&s={stop_value_updated}'

        predictions_dict = xmltodict.parse(requests.get(request_predictions).content, attr_prefix = '')

        
        ## Main Block for generating predictions from the api call ##
        ## Currently need a fix for returning bad results from api (No Busses arriving at stop, stop id / route combination does not exist, etc) ##

        if 'direction' in predictions_dict['body']['predictions']:
        
            if isinstance(predictions_dict['body']['predictions']['direction'], dict) == True:

                title_a = predictions_dict['body']['predictions']['direction']['title']

                if isinstance(predictions_dict['body']['predictions']['direction']['prediction'], list) == True:

                    preds_provided = [(title_a, int(i['seconds'])) for i in predictions_dict['body']['predictions']['direction']['prediction']]

                    preds_provided.sort(key = lambda y: y[1])

                elif isinstance(predictions_dict['body']['predictions']['direction']['prediction'], dict) == True:

                    preds_provided = [(title_a, int(predictions_dict['body']['predictions']['direction']['prediction']['seconds']))]

            elif isinstance(predictions_dict['body']['predictions']['direction'], list) == True:

                preds_provided = []
                
                for i in predictions_dict['body']['predictions']['direction']:

                    if isinstance(i['prediction'], list) == True:

                        for j in i['prediction']:

                            preds_provided.append((i['title'], int(j['seconds'])))
                                     
                    else:

                        preds_provided.append((i['title'], int(i['prediction']['seconds'])))

                preds_provided.sort(key = lambda y: y[1])

            header = html.H4('Stop Arrival Predictions')
            subheader = html.H6(f'Showing Next Arrival Predictions for {stop_value}')

            accordion_items = []
        
            ## While loop to return only 3 at most predictions ##
            counter = 0
            max_len = len(preds_provided)

            while counter < 3:

                mins = preds_provided[counter][1] // 60

                leftover_secs = preds_provided[counter][1] % 60

                message = ''

                if mins > 0 :
                    message = f'This vehicle is arriving in {mins} Minutes and {leftover_secs} Seconds'

                else:
                    message = f'This vehicle is arriving in {leftover_secs} Seconds'

                accordion_items.append(dbc.AccordionItem(
                    id=f'prediction-{counter}', children = [
                        html.P(message)
                    ], title = f'{preds_provided[counter][0]} - {preds_provided[counter][1]} seconds'
                ))

                counter += 1

                if counter == max_len:

                    break

            accordion_div = html.Div(id='accordion-div', children = [
                dbc.Accordion(id = 'predictions-accordion', children = accordion_items, flush = True)
            ])

            return [[html.Br(),header, subheader, accordion_div], stop_value_updated]
        
        else:

            header = html.H4('Stop Arrival Predictions')
            subheader = html.H6(f'Showing Next Arrival Predictions for {stop_value}')

            return [[html.Br(), header, subheader, html.Br()], stop_value_updated]

    else:
        return dash.no_update

        

## This callback will now use the stop value updated, and the interval timer to provide predictions for the bus stops ##

@app.callback(Output('accordion-div', 'children'),[Input('predictions-timing-component', 'n_intervals'), State('reset-store', 'data'), State('predictions-store', 'data')], prevent_initial_call=True)
def predictions_interval_update(n_intervals, reset_store, predictions_store):
    if reset_store != '0' and predictions_store != '0':

        request_predictions = f'https://retro.umoiq.com/service/publicXMLFeed?command=predictions&a=ttc&r={reset_store}&s={predictions_store}'

        predictions_dict = xmltodict.parse(requests.get(request_predictions).content, attr_prefix = '')

        

        ## Main Block for returning predictions from api call ## 
        ## Currently need a fix for returning bad results from api (No Busses arriving at stop, stop id / route combination does not exist, etc) ##

        if 'direction' in predictions_dict['body']['predictions']:

            if isinstance(predictions_dict['body']['predictions']['direction'], dict) == True:

                title_a = predictions_dict['body']['predictions']['direction']['title']

                if isinstance(predictions_dict['body']['predictions']['direction']['prediction'], list) == True:

                    preds_provided = [(title_a, int(i['seconds'])) for i in predictions_dict['body']['predictions']['direction']['prediction']]

                    preds_provided.sort(key = lambda y: y[1])

                elif isinstance(predictions_dict['body']['predictions']['direction']['prediction'], dict) == True:

                    preds_provided = [(title_a, int(predictions_dict['body']['predictions']['direction']['prediction']['seconds']))]

            elif isinstance(predictions_dict['body']['predictions']['direction'], list) == True:

                preds_provided = []
                
                for i in predictions_dict['body']['predictions']['direction']:

                    if isinstance(i['prediction'], list) == True:

                        for j in i['prediction']:

                            preds_provided.append((i['title'], int(j['seconds'])))
                                     
                    else:

                        preds_provided.append((i['title'], int(i['prediction']['seconds'])))

                preds_provided.sort(key = lambda y: y[1])

            now_time = datetime.now().strftime('%m/%d/%Y, %H:%M:%S')

            accordion_items = []

            counter = 0
            max_len = len(preds_provided)

            while counter < 3:

                mins = preds_provided[counter][1] // 60

                leftover_secs = preds_provided[counter][1] % 60

                message = ''

                if mins > 0 :
                    message = f'This vehicle is arriving in {mins} Minutes and {leftover_secs} Seconds'

                else:
                    message = f'This vehicle is arriving in {leftover_secs} Seconds'
                
                accordion_items.append(dbc.AccordionItem(
                    id=f'prediction-{counter}', children = [
                        html.P(message)
                    ], title = f'{preds_provided[counter][0]} - {preds_provided[counter][1]} seconds'
                ))

                counter += 1

                if counter == max_len:

                    break

            div_children = [html.H6(f'Predictions last updated: {now_time}'), dbc.Accordion(id = 'predictions-accordion', children = accordion_items, flush = True)]

            return div_children

        else:

            now_time = datetime.now().strftime('%m/%d/%Y, %H:%M:%S')

            return [[dbc.Accordion(id = 'predictions-accordion', children = [now_time], flush = True)]]

    else:
        return dash.no_update



## This callback does the periodic refresh for the vehicle locations
## This callback waits 15 seconds, and returns the main - graph figure
@app.callback([Output('main-graph', 'figure'), Output('info-cards-group', 'children')],
        [Input('timing-component', 'n_intervals'),Input('reset-store', 'data'), State('service-alerts-store', 'data')])
def update_metrics(n, reset_store, sas):
    if reset_store == "0":
        updated_epoch = int(time.time())

        # Request for Vehicles
        vlr = requests.get(f'https://webservices.umoiq.com/service/publicXMLFeed?command=vehicleLocations&a=ttc&t={updated_epoch}')

        # Locations transformation
        vl = xmltodict.parse(vlr.content, attr_prefix='')

        vlDF = pd.DataFrame.from_dict(vl['body']['vehicle'])

        vlDF['lat'] = vlDF['lat'].astype(float)

        vlDF['lon'] = vlDF['lon'].astype(float)

        vlDF['routeTitle'] = vlDF['dirTag'].map(bus_direction_tag_title_dict)


        layout_int = go.Layout(mapbox_style="carto-positron", hovermode='closest', uirevision = True, showlegend = True, autosize=True, margin = {'r': 0, 't': 0, 'b': 0, 'l': 0 },
        legend = {'orientation': 'h', 'xanchor': 'left', 'yanchor': 'bottom', "y": 1.02, "x": 0}, mapbox = {'center': {'lat': 43.6532, 'lon': -79.3832}, 'zoom': 12, 'bearing' : 344})


        data_int = go.Scattermapbox(uirevision = True, lat = vlDF['lat'], lon = vlDF['lon'], mode = 'markers', 
        marker = go.scattermapbox.Marker(size = 8, opacity = 0.75, color = 'red'), name='TTC Vehicle Locations',
        customdata=np.stack((vlDF['routeTag'], vlDF['routeTitle'], vlDF['speedKmHr']), axis=-1),
        hovertemplate = '<b>Main Route: </b>%{customdata[0]}' + '<br><b>Route Direction:</b> %{customdata[1]}' + '<br><b>Current Speed: </b> %{customdata[2]} km/h')

        ## Section to return Card Information ## 

        len_vlDF = len(vlDF.index)

        active_vehicles_sentence = f'{len_vlDF} Vehicles'

        service_alerts_num = sas

        cardgroup_children = [
                    dbc.Card(id = 'current-vehicles-card', color = 'success', children = [
                        dbc.CardBody([
                            html.H5('Current TTC Vehicles', style = {'color':'white'}),
                            html.H3(active_vehicles_sentence, style = {'color':'white'}),
                            html.P('Displaying the current number of TTC vehicles', style = {'color':'white'})
                    ])]),
                    dbc.Card(id = 'current-alerts-card', color = 'warning', children = [
                        dbc.CardBody([
                            html.H5('Current TTC Alerts', style = {'color':'white'}),
                            html.H3(f'{service_alerts_num} Alerts', style = {'color':'white'}),
                            dbc.Button(id = 'service-alerts-toggle', children='Current Alerts Details', color = 'primary', outline=True)
                        ])
                    ]),
                    dbc.Card(id = 'historical-trends-card', color = 'info', children = [
                        dbc.CardBody([
                            html.H5('Historical TTC Performance Trends', style = {'color': 'white'}),
                            html.P('Click the link below to view historical TTC performace trends for previous years', style = {'color': 'white'}),
                            dbc.CardLink('Link to Historical TTC Trends', href = '#', style = {'color': 'white'})
                        ])
                    ])
                ]
        
        ## Card Information Section End ##

        
        return [go.Figure(data = [data_int], layout = layout_int), cardgroup_children]
    
    else:
        updated_epoch = int(time.time())

        ## Returning Stop locations in a different color, smaller as well
        request_route_config = f'https://webservices.umoiq.com/service/publicXMLFeed?command=routeConfig&a=ttc&r={reset_store}'


        ## Dictionary for holding the stops on the route
        stops_route_dict = xmltodict.parse(requests.get(request_route_config).content, attr_prefix = '')
        
        stops_route_df = pd.DataFrame.from_dict(stops_route_dict['body']['route']['stop'])

        stops_route_df['lat'] = stops_route_df['lat'].astype(float)

        stops_route_df['lon'] = stops_route_df['lon'].astype(float)

        stops_smb = go.Scattermapbox(lat = stops_route_df['lat'], lon = stops_route_df['lon'], mode = 'markers', text = stops_route_df['title'], uirevision = True,
        customdata=np.stack((stops_route_df['title'], stops_route_df['stopId']), axis=-1),
        marker = go.scattermapbox.Marker(size = 5, opacity = 0.75, color = 'red'), name='TTC Stops',
        hovertemplate = '<b>%{customdata[0]}</b>' + '<br><b>Stop ID:</b> %{customdata[1]}')

        ## Returning Bus Locations

        vlr = requests.get(f'https://webservices.umoiq.com/service/publicXMLFeed?command=vehicleLocations&a=ttc&t={updated_epoch}&r={reset_store}')

        # Locations transformation
        vl = xmltodict.parse(vlr.content, attr_prefix='')
        

        if isinstance(vl['body']['vehicle'], list):

            vlDF = pd.DataFrame.from_dict(vl['body']['vehicle'], orient='columns')
        
        else:
            vlDF = pd.DataFrame.from_dict([vl['body']['vehicle']], orient='columns')

            #print(vlDF.head(5))

        vlDF['lat'] = vlDF['lat'].astype(float)

        vlDF['lon'] = vlDF['lon'].astype(float)

        vlDF['routeTitle'] = vlDF['dirTag'].map(bus_direction_tag_title_dict)

        vehicle_smb = go.Scattermapbox(lat = vlDF['lat'], lon = vlDF['lon'], mode = 'markers', 
        marker = go.scattermapbox.Marker(size = 10, opacity = 0.75, color = '#0078d7'), name='TTC Vehicle Locations', uirevision = True,
        customdata=np.stack((vlDF['routeTag'], vlDF['routeTitle'], vlDF['speedKmHr']), axis=-1),
        hovertemplate = '<b>Main Route: </b>%{customdata[0]}' + '<br><b>Route Direction:</b> %{customdata[1]}' + '<br><b>Current Speed: </b> %{customdata[2]} km/h')



        # Layout generation with auto zoom depending on the stops
        maxlon, minlon = max(stops_route_df['lon']), min(stops_route_df['lon'])
        maxlat, minlat = max(stops_route_df['lat']), min(stops_route_df['lat'])
        
        center = {
        'lat': round((maxlat + minlat) / 2, 6),
        'lon': round((maxlon + minlon) / 2, 6)
        }

        max_bound = max(abs(maxlat-minlat), abs(maxlon-minlon)) * 111
        zoom = 14 - np.log(max_bound)

        layout_int = go.Layout(mapbox_style="carto-positron", hovermode='closest', showlegend = True, uirevision = True, autosize=True, margin = {'r': 0, 't': 0, 'b': 0, 'l': 0 },
        legend = {'orientation': 'h', 'xanchor': 'left', 'yanchor': 'bottom', "y": 1.02, "x": 0}, mapbox = {'center': center, 'zoom': zoom, 'bearing' : 344})


        ## Section to return Card Information ## 

        len_vlDF = len(vlDF.index)

        active_vehicles_sentence = f'{len_vlDF} Vehicles'

        service_alerts_num = sas

        cardgroup_children = [
                    dbc.Card(id = 'current-vehicles-card', color = 'success', children = [
                        dbc.CardBody([
                            html.H5(f'Current TTC Vehicles: Line {reset_store}', style = {'color':'white'}),
                            html.H3(active_vehicles_sentence, style = {'color':'white'}),
                            html.P(f'Displaying the current number of TTC vehicles on line {reset_store}', style = {'color':'white'})
                    ])]),
                    dbc.Card(id = 'current-alerts-card', color = 'warning', children = [
                        dbc.CardBody([
                            html.H5('Current TTC Alerts', style = {'color':'white'}),
                            html.H3(f'{service_alerts_num} Alerts', style = {'color':'white'}),
                            dbc.Button(id = 'service-alerts-toggle', children='Current Alerts Details', color = 'primary', outline=True)
                        ])
                    ]),
                    dbc.Card(id = 'historical-trends-card', color = 'info', children = [
                        dbc.CardBody([
                            html.H5('Historical TTC Performance Trends', style = {'color': 'white'}),
                            html.P('Click the link below to view historical TTC performace trends for previous years', style = {'color': 'white'}),
                            dbc.CardLink('Link to Historical TTC Trends', href = '#', style = {'color': 'white'})
                        ])
                    ])
                ] 

        return [go.Figure(data = [stops_smb, vehicle_smb], layout = layout_int), cardgroup_children]


@app.callback([Output('service-alerts-store', 'data'), Output('current-alerts-card', 'children'), Output('alerts-offcanvas-div', 'children')], Input('service_alerts_timer', 'n_intervals'))
def dynamic_service_alerts():
    url_service_alerts = 'https://www.ttc.ca/service-alerts'

    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options, executable_path=r'C:\\Users\\Bushman\\geckodriver.exe')
    driver.get(url_service_alerts)

    results = driver.find_elements(By.CLASS_NAME, "ServiceAlerts_ListAlerts__2BUmu")

    results_list_split = results[0].text.split('\n')

    ## Function loops through above list to split line and route number into separate stuff

    result_return = []
    result_inner_list = []
    counter = 0

    for i in results_list_split:
        print(i)
        print(i[0].isdigit())
        if i[0].isdigit() == True:
            counter = 1
            result_inner_list.append(i)

        elif i[0].isdigit() == False:
            counter = 0
            result_inner_list.append(i)
            result_return.append(result_inner_list)
        
            result_inner_list = []

    service_alerts_num = len(result_return)

    # Loop through result return list to create accordion items
    
    accordion_items = []
    
    if len(result_return) > 0:
        for lst in result_return:

            if len(lst) == 2: 

                accordion_items.append(dbc.AccordionItem(children = [
                    dbc.Row(children=[
                        dbc.Col(width = '20%', children=[html.H5(f'{str(lst[0])}')]),
                        dbc.Col(width = '80%', children=[html.P(f'{str(lst[1])}')])
                        ])
                    ])
                )

            elif len(lst) == 1:

                accordion_items.append(dbc.AccordionItem(children = [
                    html.P(f'{str(lst[0])}')
                ]))

    return [service_alerts_num, [dbc.CardBody([html.H5('Current TTC Alerts', style = {'color':'white'}), html.H3(f'{service_alerts_num} Alerts', style = {'color':'white'}), dbc.Button(id = 'service-alerts-toggle', children='Current Alerts Details', color = 'primary', outline=True)])], html.Div(id = 'alerts-offcanvas-div', children = [dbc.Offcanvas(id='service-alerts-offcanvas', title = 'Current Service Delays', placement = 'end', is_open = False, children = [dbc.Accordion(children = accordion_items)])])]


@app.callback(Output("service-alerts-offcanvas", "is_open"), Input("service-alerts-toggle", "n_clicks"), State("service-alerts-offcanvas", "is_open"))
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=True)