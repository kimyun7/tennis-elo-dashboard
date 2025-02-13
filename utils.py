
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import plotly.express as px
from multielo.multielo import MultiElo
from multielo.player_tracker import Tracker, Player
from plotly.graph_objs import Figure
from typing import List, Union
import gspread
from gspread.spreadsheet import Spreadsheet
from gspread.worksheet import Worksheet
import config


def get_dash_theme(style: str) -> List[str]:
    try:
        return [getattr(dbc.themes, style)]
    except AttributeError:
        raise AttributeError(f"could not find theme named '{style}'")

def load_match_data_from_gsheet(group: str) -> pd.DataFrame:
    gc = gspread.service_account(filename=config.GSHEETS_CREDENTIALS_FILE)
    spreadsheet = gc.open_by_key(config.GROUPS[group]['SPREADSHEET_ID'])
    data_sheet = get_worksheet_by_id(spreadsheet, config.GROUPS[group]['DATA_SHEET_ID'])
    df = worksheet_to_dataframe(data_sheet)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    # df.rename(columns={'date':'Date'}, inplace=True)
    df.sort_values("date", inplace=True)
    return df

def load_player_data_from_gsheet(group: str):
    gc = gspread.service_account(filename=config.GSHEETS_CREDENTIALS_FILE)
    spreadsheet = gc.open_by_key(config.GROUPS[group]['SPREADSHEET_ID'])
    data_sheet = get_worksheet_by_id(spreadsheet, config.GROUPS[group]['PLAYER_SHEET_ID'])
    df = worksheet_to_dataframe(data_sheet)
    return df

def get_worksheet_by_id(spreadsheet: Spreadsheet, worksheet_id: str) -> Worksheet:
    try:
        return [w for w in spreadsheet.worksheets() 
        if w.id == worksheet_id][0]
    except IndexError:
        raise gspread.WorksheetNotFound(f"worksheet ID {worksheet_id} does not exist")


def get_worksheet_by_name(spreadsheet: Spreadsheet, worksheet_name: str) -> Worksheet:
    return spreadsheet.worksheet(worksheet_name)


def worksheet_to_dataframe(worksheet: Worksheet, headers: bool = True) -> pd.DataFrame:
    data = worksheet.get_all_values()
    if headers:
        columns = data[0]
        data = data[1:]
    else:
        columns = [f"col{i}" for i in range(len(data[0]))]

    #data = [['date', '1st', '2nd', '3rd', '4th'], ['2022-03-21', ['Satya','Ram'], 'Bala', 'Ramesh', 'Sriram'], ['2022-03-21', 'Sceenu', 'Ramesh', 'Satya', 'Sriram'], ['2022-03-28', 'Satya', 'Alfred', '_Sub_', 'Bala'], ['2022-03-28', 'Ram', 'Satya', '_Sub_', 'Sceenu']]
    df = pd.DataFrame(data, columns=columns)
    df = replace_null_string_with_nan(df)
    return df


def replace_null_string_with_nan(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace("", np.nan)


def get_dash_theme(style: str) -> List[str]:
    try:
        return [getattr(dbc.themes, style)]
    except AttributeError:
        raise AttributeError(f"could not find theme named '{style}'")


def prep_results_history_for_dash(
        data: pd.DataFrame, match_type=None, event=None) -> pd.DataFrame:
    
    results_history = data.copy()
    results_history = results_history.dropna(how="all", axis=1)  # drop columns if all NaN
    results_history = results_history.rename(columns={"date": "date"})
    
        
    if event and event != 'All':
        results_history = results_history[results_history.event == event]
    if match_type:
        results_history = results_history[results_history.match_type == match_type]
    
    if not len(results_history):
        return pd.DataFrame(columns=['date','winners','losers'])
    
    results_history['score_team_1'] = results_history['score_team_1'].astype(int)
    results_history['score_team_2'] = results_history['score_team_2'].astype(int)
    results_history['winning_team'] = results_history[['score_team_1','score_team_2']].idxmax(axis=1)
    
    if match_type == 'D':
        results_history['losers'] = results_history.apply(
                lambda x: (x['team_1_1'], x['team_1_2']) 
                if x['winning_team'] != 'score_team_1' 
                else (x['team_2_1'], x['team_2_2']), axis=1)
        results_history['winners'] = results_history.apply(
                lambda x: (x['team_1_1'], x['team_1_2']) 
                if x['winning_team'] == 'score_team_1' 
                else (x['team_2_1'], x['team_2_2']), axis=1)
    else:
        results_history['losers'] = results_history.apply(
                lambda x: (x['team_1_1'])
                if x['winning_team'] != 'score_team_1' 
                else x['team_2_1'], axis=1)
        results_history['winners'] = results_history.apply(
                lambda x: (x['team_1_1'])
                if x['winning_team'] == 'score_team_1' 
                else x['team_2_1'], axis=1)
        
    return results_history


def prep_current_ratings_for_dash(
        tracker: Tracker,
        results_history: pd.DataFrame,
        min_games: int = 0,
        event: str = None
) -> pd.DataFrame:
    current_ratings = tracker.get_current_ratings()
    current_ratings["rating"] = current_ratings["rating"].round(2)
    win_df = get_wins_from_history(results_history)
    current_ratings = (
        remove_dummy_player(df=current_ratings)
        .merge(win_df, on="player_id", how="left")
        .fillna({"n_wins": 0})
        .rename(columns={
            "rank": "Rank",
            "player_id": "Name",
            "n_games": "Games Played",
            "n_wins": "Wins",
            "rating": "Elo Rating",
        })
    )
    # only include players who have played min_games, then re-rank
    current_ratings = current_ratings[current_ratings["Games Played"] >= min_games]
    current_ratings["Rank"] = range(1, current_ratings.shape[0] + 1)
    current_ratings['Win Percentage'] = current_ratings['Wins'] / current_ratings['Games Played'] * 100
    current_ratings['Event'] = event
    col_order = ["Rank", "Name", "Games Played", "Wins", "Win Percentage", "Elo Rating", "Event"]
    return current_ratings[col_order]


def get_wins_from_history(data: pd.DataFrame) -> pd.DataFrame():
    if isinstance(data.winners.values[0], str):
        return pd.DataFrame(
        pd.Series([x for x in data.winners], 
                  name='Winner').to_frame().Winner.value_counts()).reset_index().rename(
        columns={'index':'player_id', 'Winner': 'n_wins'})
    else:
        return pd.DataFrame(
            pd.Series(list(sum([x for x in data.winners], ())), 
                      name='Winner').to_frame().Winner.value_counts()).reset_index().rename(
            columns={'index':'player_id', 'Winner': 'n_wins'})


def plot_tracker_history(
        tracker: Tracker,
        title: str = None,
        equal_time_steps: bool = False,
        min_games: int = 0,
) -> Figure:
    """
    Create an interactive plot with the rating history of each player in the Tracker.

    :param tracker: tracker with Elo history for all players
    :param title: title for the plot
    :param equal_time_steps: if True, space the x-axis equally; otherwise use the
    provided timestamps
    :param min_games: minimum number of games player must have played to be included

    :return: a plot generated using plotly.express.line
    """
    history_df = tracker.get_history_df()
    history_df = remove_dummy_player(df=history_df)

    # filter out players who haven't played min_games
    include_players = [player.id for player in tracker.players
                       if player.count_games() >= min_games]
    history_df = history_df[history_df["player_id"].isin(include_players)]

    if equal_time_steps:
        date_df = history_df[["date"]].drop_duplicates().sort_values("date").reset_index(drop=True)
        date_df["game number"] = date_df.index + 1
        history_df = history_df.merge(date_df, on="Date", how="inner")
        x_col = "game number"
    else:
        x_col = "date"

    history_df = history_df.sort_values(["player_id", x_col]).reset_index(drop=True)

    # return history_df
    fig = px.line(
        history_df,
        x=x_col,
        y="rating",
        color="player_id",
        color_discrete_sequence=px.colors.qualitative.Plotly + px.colors.qualitative.Set2,
    )
    fig.update_traces(mode="lines+markers")
    fig.update_layout(
        plot_bgcolor="#323130",
        paper_bgcolor="#323130",
        font_color="white",
        yaxis_title="Elo rating",
        title=title,
        title_x=0.5,
        legend=dict(title="<b>Player</b>", y=0.5),
        # dashed line at average rating
        shapes=[dict(
            type="line",
            yref="y",
            y0=tracker.initial_player_rating,
            y1=tracker.initial_player_rating,
            xref="paper",
            x0=0,
            x1=1,
            opacity=0.5,
            line=dict(dash="dash", width=1.5),
        )]
    )
    return fig

def display_current_ratings_table(
    current_ratings: pd.DataFrame,
    striped: bool = True,
    bordered: bool = True,
    hover: bool = False,
    **kwargs
) -> dbc.Table:
    table = dbc.Table.from_dataframe(
        current_ratings,
        striped=striped,
        bordered=bordered,
        hover=hover,
        **kwargs
    )
    return table


def display_game_results_table(
        results_history: pd.DataFrame,
        hover: bool = True,
        **kwargs
) -> dbc.Table:
    return dbc.Table.from_dataframe(results_history, hover=hover, **kwargs)


def get_tracker(
    k_value: float,
    d_value: float,
    score_function_base: float,
    initial_rating: float,
    data_to_process: pd.DataFrame = None,
) -> Tracker:
    elo_rater = MultiElo(
        k_value=k_value,
        d_value=d_value,
        score_function_base=score_function_base,
    )
    tracker = Tracker(elo_rater=elo_rater, initial_rating=initial_rating)
    if data_to_process is not None:
        tracker.process_data(data_to_process)
    return tracker


def load_json_data(json_data) -> pd.DataFrame:
    return pd.read_json(json_data, convert_dates=False)


def remove_dummy_player(
    df: pd.DataFrame,
) -> pd.DataFrame:
    dummy_player_id = config.DUMMY_PLAYER_NAME
    if dummy_player_id is None:
        return df
    df = df[df["player_id"] != dummy_player_id]
    return df


