import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

def calculate_assist_player(df_):
    """
    Calculate the assist player for each shot event in the given dataframe.

    Parameters:
    - df_ (pandas.DataFrame): The input dataframe containing shot event data.

    Returns:
    - df_2 (pandas.DataFrame): The modified dataframe with an additional column 'AssisterName' representing the name of the player who assisted the shot.

    Notes:
    - The function assumes that the input dataframe has the following columns: 'name', 'seconds_elapsed', 'AC'.
    - The function calculates the assist player based on the following conditions:
        - If the seconds_elapsed of the current row is equal to the seconds_elapsed of the next row and the AC (action code) is not 'ASS', then the AssisterName is set to the name of the next row.
        - If the seconds_elapsed of the current row is not equal to the seconds_elapsed of the next row or the AC is 'ASS', then the AssisterName is set to the name of the current row.
    - The function removes rows where the AssisterName is null and renames the 'name' column to 'ShooterName' in the resulting dataframe.
    """

    df_['AssisterName'] = df_['name']

    # Conditions
    conditions = [
        (df_['seconds_elapsed'] == df_['seconds_elapsed'].shift(-1)) & (df_['AC'] != 'ASS'),
        (df_['AC'].shift(1) == 'ASS') & (df_['AC'] == 'FT') & (df_['seconds_elapsed'] == df_['seconds_elapsed'].shift(1)),
        (df_['seconds_elapsed'] != df_['seconds_elapsed'].shift(-1)) | (df_['AC'] == 'ASS')
    ]

    # Choices
    choices = [
        df_['name'].shift(-1),
        df_['name'].shift(1), # The assist player name for free throws should be the same as the player name with AC 'ASS'
        df_['name']
    ]

    # Apply the conditions and choices
    df_['AssisterName'] = np.select(conditions, choices, default=df_['AssisterName'])

    # Remove unnecessary rows
    df_2 = df_.drop(df_[df_['AssisterName'].isnull()].index)
    df_2.rename(columns={'name':'ShooterName'}, inplace=True)
    return df_2


def successful_offense(df, rsc, nationality):
    """
    Calculate the successful offense statistics for a given dataframe.

    Parameters:
    - df (pandas.DataFrame): The input dataframe containing offense event data.
    - rsc (str): The specific RSC (Referee Signal Code) to filter the dataframe.
    - nationality (str): The specific nationality to filter the dataframe.

    Returns:
    - df_ (pandas.DataFrame): The modified dataframe containing offense event data for the specified RSC and nationality.
    - df_2 (pandas.DataFrame): The modified dataframe with an additional column 'AssisterName' representing the name of the player who assisted the shot, for successful shots only.

    Notes:
    - The function assumes that the input dataframe has the following columns: 'rsc', 'Nationality', 'Action', 'AC', 'name', 'zoneBasic', 'distanceShot', 'zoneRange', 'seconds_elapsed'.
    - The function filters the dataframe based on the specified RSC and nationality.
    - The function selects rows where the 'Action' column contains the keywords 'made', 'missed', or 'Assist'.
    - The function assigns the 'ShotOutcome' column based on the presence of the keywords 'made' or 'missed' in the 'Action' column.
    - The function assigns the 'ShotValue' column based on the 'ShotOutcome' and 'AC' columns.
    - The function selects specific columns and resets the index of the resulting dataframe.
    - The function calls the 'calculate_assist_player' function to calculate the assist player for successful shots only.
    - The function returns two dataframes: the modified dataframe with offense event data and the modified dataframe with assist player information for successful shots only.
    """
    df_canada = df[(df.rsc==rsc)&(df.Nationality==nationality)]


    searchfor = ['made', 'missed', 'Assist']
    s = df_canada['Action'].str.contains('|'.join(searchfor))
    df_ = df_canada.loc[s]

    df_['ShotOutcome'] = ''
    df_.loc[df_.Action.str.contains('made'), 'ShotOutcome'] = 'made'
    df_.loc[df_.Action.str.contains('missed'), 'ShotOutcome'] = 'missed'

    df_['ShotValue'] = 0
    df_.loc[(df_['ShotOutcome']=='made')&(df_['AC'] =='FT'), 'ShotValue'] = 1
    df_.loc[(df_['ShotOutcome']=='made')&(df_['AC'] == 'P2'), 'ShotValue'] = 2
    df_.loc[(df_['ShotOutcome']=='made')&(df_['AC'] == 'P3'), 'ShotValue'] = 3

    
    df_ = df_[['Nationality','name', 'AC', 'Action', 'ShotValue', 'ShotOutcome','zoneBasic','distanceShot','zoneRange', 'seconds_elapsed']].reset_index(drop=True)
    df_2 = calculate_assist_player(df_)
    df_2 = df_2.loc[df_['ShotOutcome']=='made']
    return df_,df_2



def create_offense(df2):
    """
    Create an edgelist summarizing all the possible connections between shooters and assisters.

    Parameters:
    - df2 (pandas.DataFrame): The input dataframe containing offense event data.

    Returns:
    - offense_summary (pandas.DataFrame): The dataframe summarizing the connections between shooters and assisters, sorted by the total shot value in descending order.

    Notes:
    - The function assumes that the input dataframe has the following columns: 'ShooterName', 'AssisterName', 'ShotValue'.
    - The function selects only the necessary columns ('ShooterName', 'AssisterName', 'ShotValue') from the input dataframe.
    - The function groups the data by 'ShooterName' and 'AssisterName' and calculates the sum of 'ShotValue' for each unique combination.
    - The function returns a dataframe with unique edges, where each row represents a connection between a shooter and an assister, along with the total shot value for that connection.
    - The resulting dataframe is sorted in descending order based on the total shot value.
    """
    ### 1. Let's take only the 3 values for the graph:
    offense_summary = df2[['ShooterName','AssisterName','ShotValue']]

    ### 2. Create a dataframe with unique edges
    offense_summary = offense_summary.groupby(['ShooterName','AssisterName'])['ShotValue'].sum()

    ### 3. Let's Sort this 
    offense_summary = pd.DataFrame(offense_summary).reset_index().sort_values(by='ShotValue', ascending=False).reset_index(drop=True)
    
    return offense_summary


def create_graph(offense_summary):
    """
    Create a directed graph using NetworkX based on the given offense_summary dataframe.

    Parameters:
    - offense_summary (pandas.DataFrame): The input dataframe summarizing the connections between shooters and assisters, along with the total shot value for each connection.

    Returns:
    - G (networkx.DiGraph): The directed graph representing the connections between shooters and assisters.

    Notes:
    - The function assumes that the offense_summary dataframe has the following columns: 'ShooterName', 'AssisterName', 'ShotValue'.
    - The function uses the nx.from_pandas_edgelist() function from the NetworkX library to create a directed graph.
    - The 'AssisterName' column is used as the source nodes, the 'ShooterName' column is used as the target nodes, and the 'ShotValue' column is used as the edge attribute.
    - The resulting graph G is a directed graph, where each edge represents a connection between an assister and a shooter, and the edge attribute represents the total shot value for that connection.
    """
    ### Create the graph using NetworkX
    G = nx.from_pandas_edgelist(offense_summary,
                            source='AssisterName', 
                            target='ShooterName',
                            edge_attr=['ShotValue'],
                            create_using=nx.DiGraph())

    return G




def create_individual_offense(offense_summary):
    """
    Create a summarized edgelist of Individual Offense.

    Parameters:
    - offense_summary (pandas.DataFrame): The input dataframe summarizing the connections between shooters and assisters, along with the total shot value for each connection.

    Returns:
    - individual_offense (pandas.DataFrame): The dataframe summarizing the individual offense for each shooter, where each row represents a shooter and their total shot value.

    Notes:
    - The function assumes that the offense_summary dataframe has the following columns: 'ShooterName', 'AssisterName', 'ShotValue'.
    - The function selects only the necessary columns ('ShooterName', 'ShotValue') from the offense_summary dataframe.
    - The function filters the dataframe to include only rows where the 'ShooterName' is equal to the 'AssisterName', indicating that the shooter assisted their own shot.
    - The resulting dataframe individual_offense contains the shooter's name and their total shot value, and is sorted in ascending order based on the shooter's name.
    """
    individual_offense = (offense_summary[['ShooterName','ShotValue']]
                    .loc[(offense_summary['ShooterName']==offense_summary['AssisterName'])]
                    .reset_index(drop=True))
    
    return individual_offense




def create_assisted_offense(offense_summary):
    
    """
    Create a summarized edgelist of Assisted Offense.

    Parameters:
    - offense_summary (pandas.DataFrame): The input dataframe summarizing the connections between shooters and assisters, along with the total shot value for each connection.

    Returns:
    - assisted_offense (pandas.DataFrame): The dataframe summarizing the assisted offense, where each row represents a connection between a shooter and an assister, along with the total shot value for that connection.

    Notes:
    - The function assumes that the offense_summary dataframe has the following columns: 'ShooterName', 'AssisterName', 'ShotValue'.
    - The function selects only the necessary columns ('ShooterName', 'AssisterName', 'ShotValue') from the offense_summary dataframe.
    - The function filters the dataframe to include only rows where the 'ShooterName' is not equal to the 'AssisterName', indicating that the shooter was assisted by another player.
    - The resulting dataframe assisted_offense contains the shooter's name, the assister's name, and the total shot value for that connection.
    """

    assisted_offense = (offense_summary[['ShooterName','AssisterName','ShotValue']]
                    .loc[(offense_summary['ShooterName']!=offense_summary['AssisterName'])]
                    .reset_index(drop=True))
    
    return assisted_offense




def draw_networkgraph(df2, ax):
    """
    This code snippet defines a function called draw_networkgraph. 

    The draw_networkgraph function takes two parameters: df2, which is a pandas DataFrame, and ax, which is a matplotlib Axes object. 

    The function first calls three other functions: create_offense, create_individual_offense, and create_graph. These functions are assumed to be defined elsewhere.

    The draw_networkgraph function then performs the following steps:

    1. Calculates the size of the nodes based on the amount of scoring each player creates by themselves without the help of an assist.
    2. Calculates the width of the edges based on the amount of points created by an assist between two players.
    3. Defines the position of the nodes in the graph using a circular layout.
    4. Draws the nodes using the nx.draw_networkx_nodes function from the NetworkX library.
    5. Draws the edges using the nx.draw_networkx_edges function from the NetworkX library.
    6. Draws the labels using the nx.draw_networkx_labels function from the NetworkX library.
    7. Sets the title of the plot.
    8. Sets the margins and axis properties.
    9. Returns the resulting plot.

    The purpose of this code snippet is to create a network graph visualization of the connections between players in a basketball offense, where the size of the nodes represents the individual scoring ability of each player and the width of the edges represents the amount of points created by an assist between two players.
    """
    offense_summary = create_offense(df2)
    individual_offense = create_individual_offense(offense_summary)    
    G = create_graph(offense_summary)
    
    ###### DRAWING NODES #######
    '''
    The size of the nodes will be proportional to 
    the amount of scoring they create by themselves
    without the help of an assist
    '''

    individual_offense = (offense_summary[['ShooterName','ShotValue']]
                        .loc[(offense_summary['ShooterName']==offense_summary['AssisterName'])]
                        .reset_index(drop=True))

    a = dict(zip(individual_offense['ShooterName'],individual_offense['ShotValue']))
    for k, v in a.items():
        a[k] = float(v)

    players_solo_score = dict.fromkeys(G.nodes(), 0)
    players_solo_score.update(a)

    for k, v in players_solo_score.items():
        players_solo_score[k] = float(v)

    nodesize = np.array(list(players_solo_score.values()))
    nodesize = nodesize/np.sum(nodesize)
    nodesize = [i*10000 for i in nodesize]

    ###### DRAWING EDGES #######
    '''
    The width of the edges will be proportional to the amount
    of points created by an assist between two players.
    '''
    #EdgeList
    non_assisted = [(u, v) for (u, v, d) in G.edges(data=True) if u != v]

    #EdgeSize
    edgesize = [(d) for (u, v, d) in G.edges(data=True) if u != v]
    edgesize = np.array([value['ShotValue'] for value in edgesize])
    edgesize = edgesize/np.sum(edgesize)*100


    ###### DRAWING GRAPH #######

    # Position of the Nodes in the Graph (Circular)
    pos = nx.circular_layout(G)


    # Drawing Nodes
    nx.draw_networkx_nodes(G, pos, 
                        node_size=nodesize, 
                        node_color='green',
                        alpha=0.5)


    # Drawing Edges
    nx.draw_networkx_edges(G, pos, 
                        edgelist=non_assisted, 
                        width=edgesize, 
                        alpha=0.2, 
                        arrows=True,
                        arrowstyle='-',
                        arrowsize=20,
                        edge_color="black")

    # Dreawing Labels
    label_options = {"ec": "k", "fc": "green", "alpha": 0.01}
    nx.draw_networkx_labels(G, pos, 
                            font_size=7, font_family="sans-serif", font_color='black',
                            verticalalignment='bottom',
                            horizontalalignment = 'center',
                            bbox=label_options
                            )

    ax.set_title(
        "Network of Points between players",
        loc='center',
        fontsize=12,
        weight='bold',
        color='gray',
        wrap=True
            )

    ax = plt.gca()
    ax.margins(0.08)
    plt.axis("off")
    plt.tight_layout()
    # return ax    



def draw_adjancecy_matrix(df2, fig, ax):
    """
    This code snippet defines a function called draw_adjancecy_matrix.

    The draw_adjancecy_matrix function takes three parameters: df2, which is a pandas DataFrame, fig, which is a matplotlib Figure object, and ax, which is a matplotlib Axes object.

    The function performs the following steps:

    1. Calls the create_offense function to create a dataframe summarizing the connections between shooters and assisters, along with the total shot value for each connection.
    2. Calls the create_graph function to create a directed graph representing the connections between shooters and assisters.
    3. Calculates the adjacency matrix of the graph using the nx.adjacency_matrix function from the NetworkX library, with the 'ShotValue' attribute as the weight.
    4. Converts the adjacency matrix to a dense matrix.
    5. Retrieves the list of assisters and scorers from the graph.
    6. Creates a heatmap of the adjacency matrix using the ax.imshow function from the matplotlib library.
    7. Sets the tick labels for the x-axis and y-axis using the ax.set_xticks and ax.set_yticks functions, respectively.
    8. Rotates the tick labels on the x-axis by 45 degrees and aligns them to the right.
    9. Creates text annotations for each cell in the heatmap using nested for loops.
    10. Sets the title of the plot using the ax.set_title function.
    11. Adjusts the layout of the plot using the fig.tight_layout function.

    The purpose of this code snippet is to visualize the distribution of points between shooters and assisters in a basketball offense using a heatmap.
    """

    offense_summary = create_offense(df2)
    # individual_offense = create_individual_offense(offense_summary)    
    G = create_graph(offense_summary)
    
    A = nx.adjacency_matrix(G,weight='ShotValue',)
    matrix = A.todense()
    assiters = list(G.nodes())
    scorers = list(G.nodes())

    # fig, ax = plt.subplots()
    im = ax.imshow(matrix, cmap='Greens')

    # Show all ticks and label them with the respective list entries
    ax.set_xticks(np.arange(len(assiters)), labels=assiters)
    ax.set_yticks(np.arange(len(scorers)), labels=scorers)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
            rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(len(scorers)):
        for j in range(len(assiters)):
            text = ax.text(j, i, matrix[i, j],
                        ha="center", va="center", color="black")

    ax.set_title(
           "Points Distributed by Scorer and Assister",
            loc='center',
            fontsize=12,
            weight='bold',
            color='gray',
            wrap=True
                )

    fig.tight_layout()
    # return plt.show()



def create_offense_summary(df_2):
    """
    Create a summary of offense statistics based on the given dataframe.

    Parameters:
    - df_2 (pandas.DataFrame): The input dataframe containing offense event data.

    Returns:
    - offense_extract (pandas.DataFrame): The dataframe summarizing the offense statistics, including total points, points from 3-pointers, points from 2-pointers, points from free throws, and average shot distance.

    Notes:
    - The function assumes that the input dataframe has the following columns: 'ShooterName', 'AssisterName', 'ShotValue', 'distanceShot'.
    - The function calculates the total points, points from 3-pointers, points from 2-pointers, points from free throws, and average shot distance for the offense.
    - The function creates a new dataframe offense_extract with the specified columns and adds the calculated statistics as a row.
    - The function calculates the offense statistics for three categories: total offense, assisted offense, and solo offense.
    - The offense statistics for each category are calculated by filtering the dataframe based on the 'ShooterName' and 'AssisterName' columns.
    - The resulting offense_extract dataframe contains the offense statistics for each category and is returned as the output.
    """
    extract_columns = ['Type of Play',
                       'Total Points',
                       '3 Points',
                       '2 Points',
                       'Free Throw',
                       'Avg. Shot Distance (feet)']

    offense_extract = pd.DataFrame(columns=extract_columns)
    
    a = df_2[['ShooterName','AssisterName','ShotValue','distanceShot']]
    x = a

    total_points = x['ShotValue'].sum()
    total_points_3p = x.loc[(x['ShotValue']==3)]['ShotValue'].sum()
    total_points_2p = x.loc[(x['ShotValue']==2)]['ShotValue'].sum()
    total_points_1p = x.loc[(x['ShotValue']==1)]['ShotValue'].sum()
    total_points_dist = round(x.loc[(x['ShotValue']!=1)]['distanceShot'].mean(),2)
    offensive_vector = ['Total',total_points, total_points_3p, total_points_2p , total_points_1p, total_points_dist]
    offense_extract.loc[len(offense_extract)] = offensive_vector

    x = a.loc[(a['ShooterName'] ==a['AssisterName'])]
    assisted_points = x['ShotValue'].sum()
    assisted_points_3p = x.loc[(x['ShotValue']==3)]['ShotValue'].sum()
    assisted_points_2p = x.loc[(x['ShotValue']==2)]['ShotValue'].sum()
    assisted_points_1p = x.loc[(x['ShotValue']==1)]['ShotValue'].sum()
    assisted_points_dist = round(x.loc[(x['ShotValue']!=1)]['distanceShot'].mean(),2)
    offensive_vector = ['Assisted',assisted_points, assisted_points_3p, assisted_points_2p , assisted_points_1p, assisted_points_dist]
    offense_extract.loc[len(offense_extract)] = offensive_vector

    x = a.loc[(a['ShooterName'] !=a['AssisterName'])]
    solo_points = x['ShotValue'].sum()
    solo_points_3p = x.loc[(x['ShotValue']==3)]['ShotValue'].sum()
    solo_points_2p = x.loc[(x['ShotValue']==2)]['ShotValue'].sum()
    solo_points_1p = x.loc[(x['ShotValue']==1)]['ShotValue'].sum()
    solo_points_dist = round(x.loc[(x['ShotValue']!=1)]['distanceShot'].mean(),2)
    offensive_vector = ['Solo',solo_points, solo_points_3p, solo_points_2p , solo_points_1p, solo_points_dist]
    offense_extract.loc[len(offense_extract)] = offensive_vector
      
    return offense_extract




def draw_game_summary(df, ax):
    """
    This code snippet defines a function called draw_game_summary.

    The draw_game_summary function takes two parameters: df, which is a pandas DataFrame, and ax, which is a matplotlib Axes object.

    The function performs the following steps:

    1. Sets the limits for the y-axis and x-axis of the plot.
    2. Removes all the spines from the plot.
    3. Calls the create_offense_summary function to create a summary of the offense data.
    4. Iterates over each row of the offense summary and plots the text on the plot.
    5. Adds a title to the plot.
    6. Adds multiple lines below each row of the offense summary.

    The purpose of this code snippet is to draw a game summary plot that displays the points split by assisted and solo play.
    """
    # making the structure
    # fig, ax = plt.subplots(figsize=(10,4))

    rows = 3 # number of rows that we want
    cols = 6 # number of columns that we want


    ax.set_ylim(-0.5, rows) #  y limits
    ax.set_xlim(0, cols) #  X limits
    ax.axis('off') # removing all the spines
    
    offense_extract = create_offense_summary(df)
    matrix = offense_extract

    # iterating over each row of the dataframe and plot the text
    # df_working is a DataFrame object with our fake data
    for row in matrix.iloc[:,:].iterrows(): # this will return the row as a tupple
            
            # row[0] will be the index of the row
            # row[1] will be the actual data as a Series
            x_position = 0.5
            for i in matrix.columns:
                    ax.text(x=x_position,  
                            y=row[0], 
                            s=row[1][i], 
                            va="center", 
                            ha="center", 
                            size=10)
                    ax.text(x_position, 
                            rows-0.5, str(i), 
                            weight='bold', 
                            ha='center', 
                            size=10,
                            color='green',
                            alpha=0.5,
                            wrap=True)._get_wrap_line_width = lambda : 100
                    x_position+=1


    # Adding title
    ax.set_title(
            'Points Splitted by Assisted and Solo Play',
            loc='center',
            fontsize=12,
            weight='bold',
            color='gray',
            wrap=True
    )

    # adds main line belowthe headers
    # ax.plot([.25,cols-.2], [rows-1.5, rows-1.5],ls="-",lw=1,c="black")

    # adds multiple lines below each row
    for row in matrix.iterrows():
            ax.plot(
            [.25, cols-.2],
            [row[0] -.5, row[0] - .5],
            ls=':',
            lw='.5',
            c='grey'
            )
    # return ax
            




def draw_dashboard(df2, nationality, rsc, save=False, show=True):
    """
    Draws a dashboard of visualizations for analyzing a basketball game from a network perspective.

    Parameters:
    - df2 (pandas.DataFrame): The input dataframe containing offense event data.

    Returns:
    - None

    The draw_dashboard function creates a dashboard of visualizations for analyzing a basketball game from a network perspective. It takes an input dataframe, df2, which should contain offense event data.

    The function first creates a figure with a size of 12x8 inches. It then divides the figure into a grid of 10 rows and 6 columns using the add_gridspec function from the matplotlib library.

    Next, the function adds three subplots to the figure:

    1. Subplot 1 (ax0): This subplot displays a game summary using the draw_game_summary function. The draw_game_summary function takes the input dataframe, df2, and an Axes object, ax0, and plots a table showing the points split by assisted and solo play.
    2. Subplot 2 (ax1): This subplot displays a network graph using the draw_networkgraph function. The draw_networkgraph function takes the input dataframe, df2, and an Axes object, ax1, and plots a network graph showing the connections between players in the offense.
    3. Subplot 3 (ax2): This subplot displays an adjacency matrix using the draw_adjancecy_matrix function. The draw_adjancecy_matrix function takes the input dataframe, df2, a Figure object, fig, and an Axes object, ax2, and plots a heatmap showing the distribution of points between shooters and assisters.

    After adding the subplots, the function adds lines between the subplots using the add_artist function from the matplotlib library.

    Finally, the function sets the title of the figure and displays the figure using the show function from the matplotlib library.

    Note: The draw_game_summary, draw_networkgraph, and draw_adjancecy_matrix functions are assumed to be defined elsewhere.

    The purpose of this function is to provide a convenient way to visualize and analyze a basketball game from a network perspective, allowing for insights into the connections between players and the distribution of points between shooters and assisters.
    """
    fig = plt.figure("Degree of a random graph", figsize=(12, 8))

    axgrid = fig.add_gridspec(10, 6)

    ax0 = fig.add_subplot(axgrid[1:4, :])
    draw_game_summary(df2, ax0)

    ax1 = fig.add_subplot(axgrid[4:, :4])
    draw_networkgraph(df2, ax1)

    ax2 = fig.add_subplot(axgrid[4:, 4:])
    draw_adjancecy_matrix(df2, fig, ax2)

    # Add lines between subplots
    fig.add_artist(plt.Line2D((0.00, 1), (0.65, 0.65), color='gray', linewidth=0.5, linestyle=':'))
    fig.add_artist(plt.Line2D((0.6, 0.6), (0.65, 0), color='gray', linewidth=0.5, linestyle=':'))
    # fig.add_artist(plt.Line2D((0.05, 0.95), (0.82, 0.82), color='black', linewidth=1))
    fig.suptitle(str(f'Analysis of {nationality} Game ({rsc}) - Network Perspective '), fontsize=16,  weight='bold',color='black')
    if save:
         plt.savefig(f'{nationality}_{rsc}.png')
    if show:
         plt.show()
