import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

CUSTOM_ORDER = ['10-9', '9-8', '8-7', '7-6', '6-5', '5-4', '4-3', '3-2', '2-1', '1-0']


def plot_heatmap_seaborn(time_percentages_df1, time_percentages_df2, time_percentages_df3, time_percentages_df4):
    """Plot the heatmaps using seaborn

    Args:
        time_percentages_df1 (pandas DataFrame): DataFrame with the time percentages for the first quarter
        time_percentages_df2 (pandas DataFrame): DataFrame with the time percentages for the second quarter
        time_percentages_df3 (pandas DataFrame): DataFrame with the time percentages for the third quarter
        time_percentages_df4 (pandas DataFrame): DataFrame with the time percentages for the fourth quarter
    """
    # Assuming df is your DataFrame and 'range' is the column you want to reorder

    # Create the heatmaps using seaborn
    fig, axs = plt.subplots(1, 4, figsize=(20, 10))

    sns.heatmap(time_percentages_df1[CUSTOM_ORDER], ax=axs[0], cmap='Blues', cbar=False, yticklabels=True)
    axs[0].set_title('Q1 Minutes')

    sns.heatmap(time_percentages_df2[CUSTOM_ORDER], ax=axs[1], cmap='Blues', cbar=False, yticklabels=False)
    axs[1].set_title('Q2 Minutes')
    axs[1].set(ylabel='')

    sns.heatmap(time_percentages_df3[CUSTOM_ORDER], ax=axs[2], cmap='Blues', cbar=False, yticklabels=False)
    axs[2].set_title('Q3 Minutes')
    axs[2].set(ylabel='')

    sns.heatmap(time_percentages_df4[CUSTOM_ORDER], ax=axs[3], cmap='Blues', yticklabels=False)
    axs[3].set_title('Q4 Minutes')
    axs[3].set(ylabel='')

    plt.suptitle('Time Percentages Heatmap')
    plt.tight_layout()
    plt.show()


def plot_plusminus_heatmap_seaborn(heatmap_plus_minus):
    fig, axs = plt.subplots(1, 4, figsize=(20, 5))

    # Create heatmaps for each quarter
    for i, quarter in enumerate([1, 2, 3, 4]):
        # Filter data for the quarter
        data = heatmap_plus_minus[heatmap_plus_minus.quarter == quarter].copy()
        data['plusminus_inverse'] = -1.0*data['plusminus']
        
        # Create a pivot table for the heatmap
        pivot = data.pivot(index='quarter', columns='minute', values='plusminus_inverse')
        
        # Sort the minute column in descending order
        pivot.sort_index(axis=1, ascending=False, inplace=True)
        
        # Create the heatmap
        sns.heatmap(pivot, ax=axs[i], cmap='RdYlGn', center=0, cbar=False)
        
        # Set the title
        axs[i].set_title(f'Q{quarter}')
        
        # Hide y labels and ticks
        axs[i].set_yticks([])
        axs[i].set_ylabel('')

    plt.tight_layout()
    plt.show()



def plot_game_diff_seaborn(all_pbp_no_end_q):
    fig, axs = plt.subplots(1, 4, figsize=(20, 5), sharey=True)

    # Create bar plots for each quarter
    max_abs_value = np.max(np.abs(all_pbp_no_end_q['+/-']))

    for i, quarter in enumerate([1, 2, 3, 4]):
        # Filter data for the quarter
        data = all_pbp_no_end_q[all_pbp_no_end_q.quarter == quarter].reset_index()
        
        # Create the bar plot
        axs[i].bar(data.index, data['+/-'], color=data['+/-'].apply(lambda x: 'green' if x > 0 else 'darkred'))
        
        # Set the title
        axs[i].set_title(f'Q{quarter}')
        
        # Hide x labels and ticks
        axs[i].set_xticks([])
        axs[i].set_xlabel('')
        # Set y-axis limits to be symmetrical around 0
        axs[i].set_ylim([-max_abs_value, max_abs_value])

    # Set the y axis label for the first plot
    axs[0].set_ylabel('Score Differential')

    plt.tight_layout()
    plt.show()



def all_plots_game(time_percentages_df1, time_percentages_df2, time_percentages_df3, time_percentages_df4, heatmap_plus_minus, all_pbp_no_end_q, teams, scores):
    fig = plt.figure(figsize=(20, 20))

    gs = gridspec.GridSpec(3, 4, height_ratios=[1, 0.05, 0.3]) 

    # Create heatmaps for time percentages
    time_percentages_dfs = [time_percentages_df1, time_percentages_df2, time_percentages_df3, time_percentages_df4]
    for i, df in enumerate(time_percentages_dfs):
        ax = plt.subplot(gs[0, i])
        if i == 3:
            sns.heatmap(df[CUSTOM_ORDER], ax=ax, cmap='Blues', cbar=True, yticklabels=False)
        elif i == 0:
            sns.heatmap(df[CUSTOM_ORDER], ax=ax, cmap='Blues', cbar=False, yticklabels=True)
        else:
            sns.heatmap(df[CUSTOM_ORDER], ax=ax, cmap='Blues', cbar=False, yticklabels=False)
        ax.set_title(f'Q{i+1} Minutes')
        if i != 0:
            ax.set(ylabel='')

    # Create heatmaps for each quarter
    for i, quarter in enumerate([1, 2, 3, 4]):
        # Filter data for the quarter
        data = heatmap_plus_minus[heatmap_plus_minus.quarter == quarter].copy()
        data.loc[:, 'plusminus_inverse'] = -1.0*data['plusminus']
        
        # Create a pivot table for the heatmap
        pivot = data.pivot(index='quarter', columns='minute', values='plusminus_inverse')
        
        # Sort the minute column in descending order
        pivot.sort_index(axis=1, ascending=False, inplace=True)
        
        # Create the heatmap
        ax = plt.subplot(gs[1, i])
        sns.heatmap(pivot, ax=ax, cmap='RdYlGn_r', center=0, cbar=False)
        
        # Set the title
        ax.set_title(f'Q{quarter} Plus/Minus')
        
        # Hide y labels and ticks
        ax.set_yticks([])
        ax.set_ylabel('')

    # Create bar plots for each quarter
    max_abs_value = np.max(np.abs(all_pbp_no_end_q['+/-']))
    for i, quarter in enumerate([1, 2, 3, 4]):
        # Filter data for the quarter
        if scores is None:
            data_plot = all_pbp_no_end_q[all_pbp_no_end_q.quarter == quarter].sort_values(by=['quarter', 'minute', 'level_2'], ascending=[True, False, True]).reset_index(drop=True)
        else:
            data_plot = all_pbp_no_end_q[all_pbp_no_end_q.quarter == quarter].reset_index()
        
        # Create the bar plot
        ax = plt.subplot(gs[2, i])
        ax.bar(data_plot.index, data_plot['+/-'], color=data_plot['+/-'].apply(lambda x: 'green' if x > 0 else 'darkred'))
        
        # Set the title
        ax.set_title(f'Q{quarter} Score Differential')
        
        # Hide x labels and ticks
        ax.set_xticks([])
        ax.set_xlabel('')
        if i!=0:
            ax.set_yticks([])
            ax.set_ylabel('')

        # Set y-axis limits to be symmetrical around 0
        ax.set_ylim([-max_abs_value, max_abs_value])
        if i==0:
            ax.set_ylabel('Score Differential')

    if scores is None:
        plt.suptitle(f"Average Rotation Strategy for {teams}", fontsize=20, y=1.001) 
    else:
        plt.suptitle(f'Game Analysis of {teams[0]} ({scores[0]}) vs {teams[1]} ({scores[1]})', fontsize=20, y=1.05)    
    plt.tight_layout()
    plt.show()