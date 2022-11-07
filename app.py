
from dash import Dash, html, dcc,dash_table as dt
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_daq as daq
import config
import utils
from typing import List
import pandas as pd
from multielo.multielo import MultiElo
from multielo.player_tracker import Tracker, Player

import argparse

# determine if the script was run with any arguments
parser = argparse.ArgumentParser()
parser.add_argument("--debug", "-d", "--DEBUG", "-D", action="store_const", const=True,
                    help="Run in debug mode")
args, _ = parser.parse_known_args()
DEBUG = True if args.debug else False

app = Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)

app.title = "Aoullim Elo Dashboard"
server = app.server
app_color = {"graph_bg": "#082255", "graph_line": "#007ACE"}

app.config["suppress_callback_exceptions"] = True

# Get data
match_data = utils.load_match_data_from_gsheet(group="AOULLIM")
player_df = utils.load_player_data_from_gsheet(group="AOULLIM")

app.layout = html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.A(
                            html.Img(
                                className="logo",
                                src=app.get_asset_url("aoullim-logo.png"),
                            ),
                            href="https://www.instagram.com/aoullim_tennis/",
                        ),
                        html.H2("AOULLIM - TENNIS RANKING AND LEADERBOARD"),
                        html.P(
                            """View elo rating and rank by event and match types"""
                        ),
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                    dcc.Dropdown(
                                        id="group-filter",
                                        options=[
                                            {"label": 'Aoullim', "value": 'AOULLIM'},
                                            {"label": 'iGo', "value": 'IGO'},
                                        ],
                                        value="AOULLIM",
                                        placeholder="Select tennis group",
                                        style={"border": "0px solid black"},
                                )
                            ],
                        ),
                        # Change to side-by-side for mobile layout
                        html.Div(
                            className="row",
                            children=[
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        # Dropdown for locations on map
                                        dcc.Dropdown(
                                            id="match-type-filter",
                                            options=[
                                                {"label": 'Singles', "value": 'S'},
                                                {"label": 'Doubles', "value": 'D'},
                                            ],
                                            value="D",
                                            placeholder="Select match type",
                                        )
                                    ],
                                ),
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        # Dropdown to select times
                                        dcc.Dropdown(
                                            id="event-type-filter",
                                            options=[
                                                {"label": event_type, "value": event_type}
                                                for event_type in match_data.event.unique()
                                                ]+[{"label": "All", "value": "All"}],
                                            value="All",
                                            placeholder="Select event type",
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                # Column for app graphs and plots
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dbc.Card(
                            html.Div(
                                dbc.Col(id="elo-ranking-table"),
                                style={"maxHeight": "600px", "overflow": "scroll"},
                            ),
                            body=True,
                        ),
                        dcc.Graph(id="elo-ranking-chart"),
                    ]
                    ),
                ],
            ),
        ],
    )

@app.callback(
    [Output("elo-ranking-chart", "figure"),
     Output("elo-ranking-table", "children"),],
    [Input("match-type-filter", "value"),
        Input("event-type-filter", "value"),
        Input("group-filter", "value")])
def get_rating_chart(match_type, event, group):
    match_type = re.sub("^\s+|\s+$", "", match_type, flags=re.UNICODE)
    event = re.sub("^\s+|\s+$", "", event, flags=re.UNICODE)
    group = re.sub("^\s+|\s+$", "", group, flags=re.UNICODE)    
    
    # Get updated data on callback
    match_data = utils.load_match_data_from_gsheet(group)
    player_df = utils.load_player_data_from_gsheet(group)
    
    if match_type == 'S':
        player_df['initial_elo'] = player_df.initial_elo_singles
    elif match_type == 'D':
        player_df['initial_elo'] = player_df.initial_elo_doubles
        
    players = [Player(player_id=x, rating=float(y)) for x,y in zip(player_df.player_id.str.replace(' ',''),
                                                                   player_df.initial_elo)]
    data = utils.prep_results_history_for_dash(match_data, event=event, match_type=match_type)
    data = data[['date','winners', 'losers']]
    
    current_tracker = Tracker(players=players)
    current_tracker.process_data(data)
    
    current_ratings = utils.prep_current_ratings_for_dash(
        tracker=current_tracker,
        results_history=data,
        min_games=1,
        event=event
    )
    
    current_fig = utils.plot_tracker_history(
    tracker=current_tracker,
    title='Elo Rating Chart',
    equal_time_steps=False,
    min_games=1)


    return current_fig, utils.display_current_ratings_table(current_ratings)

if __name__ == '__main__':
    
    app.run_server(debug=DEBUG)