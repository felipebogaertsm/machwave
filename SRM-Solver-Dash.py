import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html

from functions.ib_functions import *
from functions.propellant import *
from functions.structural_functions import *
from functions.functions import *

app = dash.Dash()

exec(open('SRM-Solver.py').read())

app.layout = html.Div(['Graphs',
                       dcc.Graph(id='pressure',
                                 figure={'data': [
                                     go.Scatter(
                                         x=t,
                                         y=P0 * 1e-6,
                                         mode='lines',
                                         marker={
                                             'color': '#008141'
                                         }
                                     )],
                                     'layout': go.Layout(title='Chamber Pressure Plot')}
                                 ),
                       dcc.Graph(id='thrust',
                                 figure={'data': [
                                     go.Scatter(
                                         x=t,
                                         y=F,
                                         mode='lines',
                                         marker={
                                             'color': '#6a006a'
                                         }
                                     )],
                                     'layout': go.Layout(title='Thrust Plot')}
                                 )],
                      style={'color': 'black', 'border': '10px blue solid'})

if __name__ == '__main__':
    app.run_server()
