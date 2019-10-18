#!/usr/bin/env python
# coding: utf-8

# In[1]:


import re

import dash
import dash_core_components as dcc
from dash.exceptions import PreventUpdate
import dash_html_components as html
from dash.dependencies import Input, Output, State
import matplotlib
from matplotlib import cm
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.figure_factory as ff


# dev
pd.set_option('display.max_rows', 500)


# In[3]:


# read initial data
df = pd.read_csv('https://davidschneiderprojects.s3.amazonaws.com/NFL/2018_data.csv'
                 ,index_col=False
                 ,low_memory=False)
df.drop('Unnamed: 0', axis=1, inplace=True)


# In[4]:


# global dash attributes
app = dash.Dash(__name__)
app.title = "NFL Plotting with Dash"


# In[5]:


# make a green->yellow->red colormap for plotly/dash
grrd_cmap = matplotlib.cm.get_cmap('RdYlGn').reversed()
grrd_rgb = []
norm = matplotlib.colors.Normalize(vmin=0, vmax=255)
for i in range(0, 255):
    k = matplotlib.colors.colorConverter.to_rgb(grrd_cmap(norm(i)))
    grrd_rgb.append(k)
def matplotlib_to_plotly(cmap, pl_entries):
    h = 1.0/(pl_entries-1)
    pl_colorscale = []
    for k in range(pl_entries):
        C = list(map(np.uint8, np.array(cmap(k*h)[:3])*255))
        pl_colorscale.append([k*h, 'rgb'+str((C[0], C[1], C[2]))])
    return pl_colorscale
grrd = matplotlib_to_plotly(grrd_cmap, 255)


# In[6]:


team_abbrevs = {'ARI': 'Arizona Cardinals'
               ,'ATL': 'Atlanta Falcons'
               ,'BAL': 'Baltimore Ravens'
               ,'BUF': 'Buffalo Bills'
               ,'CAR': 'Carolina Panthers'
               ,'CHI': 'Chicago Bears'
               ,'CIN': 'Cincinnati Bengals'
               ,'CLE': 'Cleveland Browns'
               ,'DAL': 'Dallas Cowboys'
               ,'DEN': 'Denver Broncos'
               ,'DET': 'Detroit Lions'
               ,'GB': 'Green Bay Packers'
               ,'HOU': 'Houston Texans'
               ,'IND': 'Indianapolis Colts'
               ,'JAX': 'Jacksonville Jaguars'
               ,'KC': 'Kansas City Chiefs'
               ,'LA': 'Los Angeles Rams'
               ,'LAC': 'Los Angeles Chargers'
               ,'MIA': 'Miami Dolphins'
               ,'MIN': 'Minnesota Vikings'
               ,'NE': 'New England Patriots'
               ,'NO': 'New Orleans Saints'
               ,'NYG': 'New York Giants'
               ,'NYJ': 'New York Jets'
               ,'OAK': 'Oakland Raiders'
               ,'PHI': 'Philadelphia Eagles'
               ,'PIT': 'Pittsburgh Steelers'
               ,'SEA': 'Seattle Seahawks'
               ,'SF': 'San Francisco 49ers'
               ,'TB': 'Tampa Bay Buccaneers'
               ,'TEN': 'Tennessee Titans'
               ,'WAS': 'Washington Redskins'}
team_name_abbrevs = {'ARI': 'Cardinals'
               ,'ATL': 'Falcons'
               ,'BAL': 'Ravens'
               ,'BUF': 'Bills'
               ,'CAR': 'Panthers'
               ,'CHI': 'Bears'
               ,'CIN': 'Bengals'
               ,'CLE': 'Browns'
               ,'DAL': 'Cowboys'
               ,'DEN': 'Broncos'
               ,'DET': 'Lions'
               ,'GB': 'Packers'
               ,'HOU': 'Texans'
               ,'IND': 'Colts'
               ,'JAX': 'Jaguars'
               ,'KC': 'Chiefs'
               ,'LA': 'Rams'
               ,'LAC': 'Chargers'
               ,'MIA': 'Dolphins'
               ,'MIN': 'Vikings'
               ,'NE': 'Patriots'
               ,'NO': 'Saints'
               ,'NYG': 'Giants'
               ,'NYJ': 'Jets'
               ,'OAK': 'Raiders'
               ,'PHI': 'Eagles'
               ,'PIT': 'Steelers'
               ,'SEA': 'Seahawks'
               ,'SF': '49ers'
               ,'TB': 'Buccaneers'
               ,'TEN': 'Titans'
               ,'WAS': 'Redskins'}


# In[7]:


# styling
forestgreen = '#012800'
green = '#024e00'
lightgray = '#cfcfcf'
white = '#fff'
colors = {'background': forestgreen
          ,'text': lightgray
         }


# In[8]:


# dataframes for different graph options
## penalty dataframe
df_pen = df[[col for col in df.columns if re.search("(penalty)|(game\_date)", col) or col in ('posteam', 'defteam')]]
df_pen['penalty_side'] = np.where(df['posteam']==df['penalty_team'], 'Offensive', 'Defensive')
df_pen = df_pen[df_pen['penalty']==1.0].drop(['penalty_player_id'
                                             ,'penalty'
                                             ,'posteam'
                                             ,'defteam']
                                            ,axis=1)
df_pen['penalty_type'].replace(to_replace=np.nan, value='Not Recorded', inplace=True)
df_pen = df_pen.sort_values(['game_date'
                             ,'penalty_team'
                             ,'penalty_player_name'
                             ,'penalty_yards'])
df_pen = df_pen.reset_index(drop=True)


# In[9]:


### penalty breakouts
pen_by_type = df_pen.groupby(['penalty_team', 'penalty_side', 'penalty_type'], as_index=False).sum().sort_values(['penalty_yards'])
penalty_types = pen_by_type.drop_duplicates(subset=['penalty_side', 'penalty_type'])[['penalty_side','penalty_type']].sort_values(['penalty_side','penalty_type'])
penalty_types = penalty_types.reset_index(drop=True)
#pen_by_team_game = df_pen.groupby(['penalty_team', 'game_date'], as_index=False).sum()
pen_by_player = df_pen.groupby(['penalty_player_name'], as_index=False).sum()


# In[10]:


#TODO:
#radio button: total yds, num penalties, yds per penalty
#update list of penalty types if off/def selected
#separate graph for player vs team view
#slider for week range


# In[22]:


# penalty graph
app.layout = html.Div([
    html.Div(id='page-content', children=[
        html.H1(children="2018 NFL Play Breakdown")
    ])
    ,dcc.Graph(id='graph_pen_by_team')
    ,html.Div([
        dcc.Dropdown(id='team_dropdown'
                      ,options=[{'label': team_name_abbrevs[team], 'value': team} for team in pen_by_type['penalty_team'].unique()]
                      ,value=[team for team in pen_by_type['penalty_team'].unique()]
                      ,multi=True
                      ,style={'background-color': forestgreen
                              ,'color': forestgreen}
                      ,placeholder="Filter by team(s)" )
        ,dcc.RadioItems(
                id='penalty-side-radio'
                ,options=[{'label': i, 'value': i} for i in
                         ['All', 'Offensive', 'Defensive']]
                ,value='All'
                ,style={'background-color': forestgreen
                        ,'color': lightgray}
                ,inputStyle={'padding': '20px'}
                ,labelStyle={'display': 'inline-block'
                             ,'margin': '15px 20px'
                             ,'width': '20vw'} )
        ,dcc.Dropdown(id='penalty-type-dropdown'
                      ,options=[{'label': ptype, 'value': ptype} for ptype in penalty_types['penalty_type'].unique()]
                      ,value=['All']
                      ,multi=True
                      ,style={'background-color': forestgreen
                              ,'color': forestgreen}
                      ,placeholder="Type of penalty" )
        ,dcc.Dropdown(id='highlighted-team-dropdown'
                      ,options=[{'label': team_name_abbrevs[team], 'value': team} for team in pen_by_type['penalty_team'].unique()]
                      ,value=''
                      ,multi=False
                      ,style={'background-color': forestgreen
                              ,'color': forestgreen}
                      ,placeholder="Highlight Team" )
    ])
])

@app.callback(
    dash.dependencies.Output('graph_pen_by_team', 'figure')
    ,[dash.dependencies.Input('team_dropdown', 'value')
      ,dash.dependencies.Input('penalty-side-radio', 'value')
      ,dash.dependencies.Input('penalty-type-dropdown', 'value') 
      ,dash.dependencies.Input('highlighted-team-dropdown', 'value') ] )
def team_penalty_figure(team_values, side_value, type_values, highlighted_teams_values):
    traces = []
    title = "<b>Penalty Dashboard</b>"
    # type
    if 'All' not in type_values:
        filtered_df = pen_by_type[pen_by_type['penalty_type'].isin(type_values)]
    else:
        filtered_df = pen_by_type
    # side
    if side_value == 'All':
        pass
    elif side_value in (['Offensive','Defensive']):
        filtered_df = filtered_df[filtered_df['penalty_side']==side_value]
        title += f'- {side_value}'
    else:
        raise ValueError
    layout = {#'margin': dict(l = 50, r = 50, b = 50, t = 50, pad = 4),
        'plot_bgcolor': colors['text']
         ,'paper_bgcolor': colors['text']
         ,'title': title
         ,'titlefont':dict(size=24, color='#565656', family='Arial, sans-serif')
         ,'yaxis':dict(title='Number of Yards<br>', showgrid=False)
         ,'xaxis':dict(title='Team', showgrid=False, font=dict(size=100))
         ,'showlegend': False}
    # team
    if len(team_values)>0:
        filtered_df = filtered_df[filtered_df['penalty_team'].isin(team_values)]
        filtered_df = filtered_df.groupby(['penalty_team'], as_index=False).sum()
        filtered_df = filtered_df.sort_values(['penalty_yards'])
        traces.append(go.Bar(x=filtered_df['penalty_team']
                        ,y=filtered_df['penalty_yards']
                        ,name='Selected Teams'
                        ,marker={'color': filtered_df['penalty_yards']
                                ,'colorscale': grrd}))
    else:
        filtered_df = filtered_df.groupby(['penalty_type'], as_index=False).sum()
        filtered_df = filtered_df.sort_values(['penalty_yards'])
        layout['xaxis']['title']='Type of Penalty'
        layout['xaxis']['automargin']=True
        traces.append(go.Bar(x=filtered_df['penalty_type']
                ,y=filtered_df['penalty_yards']
                ,name='Selected Types'
                ,marker={'color': filtered_df['penalty_yards']
                        ,'colorscale': grrd}))
    # not optimal
    if highlighted_teams_values:
        title += f'- {highlighted_teams_values} {team_name_abbrevs[highlighted_teams_values]}'
        layout['title'] = title
        if highlighted_teams_values not in team_values:
            raise PreventUpdate 
        layout['barmode'] = 'stack'
        highlight = filtered_df[filtered_df['penalty_team']==highlighted_teams_values]['penalty_yards'].iloc[0]
        traces_new = []
        ilh, ill, ils = [], [], []
        for index, value in enumerate(traces[0]['y']):
            if value == highlight:
                ils.append(index)
            elif value < highlight:
                ilh.append(index)
            else:
                ill.append(index)
        xl = [x for i, x in enumerate(traces[0]['x']) if i in ilh]
        yl = [y for i, y in enumerate(traces[0]['y']) if y < highlight]
        traces_new.append(go.Bar(x=xl
                ,y=yl
                ,name=''
                ,marker={'color': 'gray'}))
        xs = [x for i, x in enumerate(traces[0]['x']) if i in ils]
        ys = [y for i, y in enumerate(traces[0]['y']) if y == highlight]
        traces_new.append(go.Bar(x=xs
                ,y=ys
                ,name='Selected Team'
                ,marker={'color': '#ffdb58'})) 
        traces_new.append(go.Bar(x=filtered_df[filtered_df['penalty_yards']<highlight]['penalty_team']
                            ,y=highlight-filtered_df[filtered_df['penalty_yards']<highlight]['penalty_yards']
                            ,name=''
                            ,marker={'color':'green'}))
        # higher than selected team
        xl = [x for i, x in enumerate(traces[0]['x']) if i in ill]
        yl = [y for i, y in enumerate(traces[0]['y']) if y > highlight]
        ## colored part
        traces_new.append(go.Bar(x=xl
                            ,y=yl
                            ,name=''
                            ,marker={'color': 'gray'}))
        ## black part
        traces_new.append(go.Bar(x=filtered_df[filtered_df['penalty_yards']>highlight]['penalty_team']
                            ,y=(highlight-filtered_df[filtered_df['penalty_yards']>highlight]['penalty_yards'])
                            ,name=''
                            ,marker={'color':'red'}))
        return {'data': traces_new
               ,'layout': layout}
    
    return {'data': traces
        ,'layout': layout}


# In[12]:


if __name__ == '__main__':
    app.run_server(debug=True)

