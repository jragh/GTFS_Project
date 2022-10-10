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

## Loading in the Route Config information for the routes
## This will need to be handled better in the future, for daily / weekly updating of the file
## Lookup anywhere in the file that is loading in the bus realtime locations, use a left join on the tag
bus_direction_tag_title = pd.read_csv('C:\\Users\\Bushman\\Documents\\directionDFCSV.csv')

bus_direction_tag_title_dict = {bus_direction_tag_title.loc[i, 'tag']: ' '.join(str(bus_direction_tag_title.loc[i, 'title']).split(' ')[3:]) for i, j in bus_direction_tag_title.iterrows()}
external_stylesheets = ['dbc.themes.FLATLY'] 

## Need to specify the stylesheet by the URL, in the future will store the CSS as a file on a cloud system or something
app = dash.Dash(__name__, external_stylesheets=['https://cdn.jsdelivr.net/npm/bootswatch@5.1.3/dist/flatly/bootstrap.min.css'])

app.layout = dbc.Container(fluid = True, children = [
    dbc.Row(id = 'main-row', class_name="g-0", style = {"height" : "100vh"}, children = [
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
        dbc.Col(id = 'map-area', align = "end", width = 9, style ={"height": "100vh"}, children = [
            html.Div(id = 'map-div', style ={"height": "100%"}, children = [dcc.Graph(style = {'height': "100vh"}, id='main-graph')])
            ])
        ]), 
    ], style = {'height': "100vh"}, class_name="g-0")

## Try to replace the div as opposed to just the map component
## This section of code resets the div when the reset button is clicked
@app.callback([Output('line-selection', 'value')], Input('reset-map-button', 'n_clicks'), prevent_initial_call=True)
def dropdown_menu_reset(n_clicks):
    if n_clicks:
        return [""]


@app.callback([Output('map-div', 'children'), Output('description-paragraph', 'children'), Output('reset-store', 'data'), Output('stop-selection-div', 'children'), Output('parent-stop-predictions-div', 'children')],Input('reset-map-button', 'n_clicks'), Input('select-line-button', 'n_clicks'), State('line-selection', 'value'), prevent_initial_call=True)
def update_graph(n_clicks, n_clicks2, state1):
    triggered_id = ctx.triggered_id
    print(triggered_id)
    if triggered_id == 'reset-map-button':
        return map_reset(n_clicks)
    if triggered_id == 'select-line-button':
        return line_selection_zoom(state1)


def map_reset(n_clicks):

    layout_int = go.Layout(title = 'Test Scattermapbox Map', mapbox_style="carto-positron", hovermode='closest', showlegend = True,
    mapbox = {'center': {'lat': 43.6532, 'lon': -79.3832}, 'zoom': 12, 'bearing' : 344})

    updated_epoch = int(time.time())

    # Request for Vehicles
    vlr = requests.get(f'https://webservices.umoiq.com/service/publicXMLFeed?command=vehicleLocations&a=ttc&t={updated_epoch}')

    # Locations transformation
    vl = xmltodict.parse(vlr.content, attr_prefix='')

    vlDF = pd.DataFrame.from_dict(vl['body']['vehicle'])

    vlDF['lat'] = vlDF['lat'].astype(float)

    vlDF['lon'] = vlDF['lon'].astype(float)

    vlDF['routeTitle'] = vlDF['dirTag'].map(bus_direction_tag_title_dict)

    data_int = go.Scattermapbox(uirevision = True, lat = vlDF['lat'], lon = vlDF['lon'], mode = 'markers', 
    marker = go.scattermapbox.Marker(size = 8, opacity = 0.75, color = 'orange'), name='TTC Vehicle Locations',
    customdata=np.stack((vlDF['routeTag'], vlDF['routeTitle'], vlDF['speedKmHr']), axis=-1),
    hovertemplate = '<b>Main Route: </b>%{customdata[0]}' + '<br><b>Route Direction:</b> %{customdata[1]}' + '<br><b>Current Speed: </b> %{customdata[2]} km/h')

    ## Callback 

    return [[dcc.Graph(id='main-graph', style = {'height': "100vh"}, figure = go.Figure(data = [data_int], layout = layout_int))], ['Feel free to select a TTC Bus Route to view line details at a closer glance. Or just view all the currently running vehicles on the network!'], "0", [], [html.Div(id='stop-predictions-div', children = [])]]


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



        # Layout generation with auto zoom depending on the stops
        maxlon, minlon = max(stops_route_df['lon']), min(stops_route_df['lon'])
        maxlat, minlat = max(stops_route_df['lat']), min(stops_route_df['lat'])
        
        center = {
        'lat': round((maxlat + minlat) / 2, 6),
        'lon': round((maxlon + minlon) / 2, 6)
        }

        max_bound = max(abs(maxlat-minlat), abs(maxlon-minlon)) * 111
        zoom = 14 - np.log(max_bound)

        layout_int = go.Layout(title = 'Test Scattermapbox Map', mapbox_style="carto-positron", hovermode='closest', showlegend = True, uirevision = True,
        mapbox = {'center': center, 'zoom': zoom, 'bearing' : 344})

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


        return [[dcc.Graph(id='main-graph', style = {'height': "100vh"}, figure = go.Figure(data = [stops_smb, vehicle_smb], layout = layout_int))], [f"You have selected line {value_route}!"], value_route, stops_children, [html.Div(id='stop-predictions-div', children = [])]]

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

                preds_provided = [(i['title'], int(j['seconds'])) for i in predictions_dict['body']['predictions']['direction'] for j in i['prediction']]

                preds_provided.sort(key = lambda y: y[1])

            header = html.H4('Stop Arrival Predictions')
            subheader = html.H6(f'Showing Next Arrival Predictions for {stop_value}')

            accordion_items = []
        
            ## While loop to return only 3 at most predictions ##
            counter = 0
            max_len = len(preds_provided)

            while counter < 3:

                accordion_items.append(dbc.AccordionItem(
                    id=f'prediction-{counter}', children = [
                        html.P(f'This is Prediction {counter}')
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

                preds_provided = [(i['title'], int(j['seconds'])) for i in predictions_dict['body']['predictions']['direction'] for j in i['prediction']]

                preds_provided.sort(key = lambda y: y[1])

            now_time = datetime.now().strftime('%m/%d/%Y, %H:%M:%S')

            accordion_items = []

            counter = 0
            max_len = len(preds_provided)

            while counter < 3:
                
                accordion_items.append(dbc.AccordionItem(
                    id=f'prediction-{counter}', children = [
                        html.P(f'This is Prediction {counter}')
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
@app.callback(Output('main-graph', 'figure'),
        [Input('timing-component', 'n_intervals'),Input('reset-store', 'data')])
def update_metrics(n, reset_store):
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


        layout_int = go.Layout(title = 'Test Scattermapbox Map', mapbox_style="carto-positron", hovermode='closest', uirevision = True, showlegend = True,
        mapbox = {'center': {'lat': 43.6532, 'lon': -79.3832}, 'zoom': 12, 'bearing' : 344})


        data_int = go.Scattermapbox(uirevision = True, lat = vlDF['lat'], lon = vlDF['lon'], mode = 'markers', 
        marker = go.scattermapbox.Marker(size = 8, opacity = 0.75, color = 'red'), name='TTC Vehicle Locations',
        customdata=np.stack((vlDF['routeTag'], vlDF['routeTitle'], vlDF['speedKmHr']), axis=-1),
        hovertemplate = '<b>Main Route: </b>%{customdata[0]}' + '<br><b>Route Direction:</b> %{customdata[1]}' + '<br><b>Current Speed: </b> %{customdata[2]} km/h')

        
        return go.Figure(data = [data_int], layout = layout_int)
    
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

        layout_int = go.Layout(title = 'Test Scattermapbox Map', mapbox_style="carto-positron", hovermode='closest', showlegend = True, uirevision = True,
        mapbox = {'center': center, 'zoom': zoom, 'bearing' : 344})

        return go.Figure(data = [stops_smb, vehicle_smb], layout = layout_int)



if __name__ == '__main__':
    app.run_server(debug=True)