import pandas as pd     #(version 1.0.0)

import dash             #(version 1.9.1) pip install dash==1.9.1
from dash import dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import requests
import plotly.graph_objs as go
from datetime import datetime, timedelta
from math import cos, sin, pi  # Import cos, sin, and pi functions
import warnings

# Add this line to filter out FutureWarnings
warnings.filterwarnings("ignore", category=FutureWarning)


#-------------------------------------------------------------------------------

#{'id': '0FD2SCPF8QQ0VTGWBV2MKPJ4QB', 'value': 'Off', 'feed_id': 2609145, 
#'feed_key': 'm1state', 'created_at': '2023-09-09T04:51:07Z', 'created_epoch': 1694235067, 'expiration': '2023-10-09T04:51:07Z'}
categories=["value","feed_key","created_at","expiration"]
def api_call():
    
    # Define your Adafruit IO username and API key
    username = "clgretailautomation"
    api_key = "aio_emTC43BQVgPTVKSNAGmaTNRxutSy"

    # Define the feed name you want to access
    feed_name = "m1state"  # Replace with your actual feed name

    # Create the URL for the Adafruit IO API
    url = f"https://io.adafruit.com/api/v2/{username}/feeds/{feed_name}/data"

    # Set up the headers with your API key for authentication
    headers = {
        "X-AIO-Key": api_key,
        
    }

    response = requests.get(url, headers=headers)
    json_data = response.json()
    df = pd.DataFrame(json_data)
    #print (df[categories])
    #print (df[:20])
    print("updated")
    
    # Convert UTC to IST (Indian Standard Time)
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Asia/Kolkata')

    df['created_at'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

    df['expiration'] = pd.to_datetime(df['expiration']).dt.tz_convert('Asia/Kolkata')

    df['expiration'] = df['expiration'].dt.strftime('%Y-%m-%d %H:%M:%S')

    df = df[categories]
    # Print the updated DataFrame
    #print(df)





    # Convert 'created_at' to datetime format
    df['created_at'] = pd.to_datetime(df['created_at'])

    # Sort the DataFrame by 'created_at'
    df = df.sort_values(by='created_at')

    # Define the frequency (in minutes)
    f = 5  # minute interval to fill previous state
    frequency = pd.Timedelta(minutes=f)

    # Create a new DataFrame to store the filled data
    filled_data = []

    # Get the current date and time as a Pandas Timestamp object
    current_datetime = pd.Timestamp(datetime.now())

    # Iterate through the DataFrame and fill in the missing data up to the current date
    previous_row = None

    for index, row in df.iterrows():
        if previous_row is not None:
            time_diff = row['created_at'] - previous_row['created_at']
            minutes_diff = time_diff.total_seconds() / 60
            if minutes_diff > f:
                # Add rows with intermediate timestamps and the previous 'value'
                for i in range(f, int(minutes_diff), f):
                    new_time = previous_row['created_at'] + pd.Timedelta(minutes=i)
                    #print("new_time", new_time)
                    
                    filled_data.append({'value': previous_row['value'], 'created_at': new_time})
        filled_data.append({'value': row['value'], 'created_at': row['created_at']})
        previous_row = row

    # Continue filling intermediate timestamps up to the current date and time
    while filled_data[-1]['created_at'] < current_datetime:
        last_row = filled_data[-1]
        new_time = last_row['created_at'] + pd.Timedelta(minutes=f)
        filled_data.append({'value': last_row['value'], 'created_at': new_time})

    # Create a new DataFrame with the filled data
    filled_df = pd.DataFrame(filled_data)

    # Reset the index of the filled DataFrame
    filled_df = filled_df.reset_index(drop=True)

    # Print the filled DataFrame
    # print(filled_df.head(60))

    # Save the filled DataFrame to a CSV file
    #filled_df.to_csv('filled_df.csv', index=False)


    # Convert 'created_at' column to datetime
    filled_df['created_at'] = pd.to_datetime(filled_df['created_at'])
    return filled_df

filled_df = api_call()

# Function to determine the current shift based on the current time
def get_current_shift():
    current_time = datetime.now()
    if 6 <= current_time.hour < 14:
        return 'Shift 1 (6 am to 2 pm)'
    elif 14 <= current_time.hour < 22:
        return 'Shift 2 (2 pm to 10 pm)'
    else:
        return 'Shift 3 (10 pm to 6 am next day)'

app = dash.Dash(__name__)

# Define CSS styles to reduce the size of components
app.layout = html.Div(style={'max-width': '1000px','background-color': '#171b26','margin': 'auto', 'textAlign': 'center',
                            'font-family': 'YourCustomFont, sans-serif','height': '400px'}, children=[
    html.H1('CLG RETAIL SHIFT DASHBOARD', style={'font-size': '34px', 'color':'#ff6666'}),  # Title line moved here
    
    dcc.DatePickerSingle(
        id='date-picker-single',
        date=filled_df['created_at'].max().date(),  # Default to the latest date
        display_format='YYYY-MM-DD',
        style={'width': '100%','margin-bottom': '20px'},  # Adjust the width as needed
    ),

    dcc.Dropdown(
        id='shift-selector',
        options=[
            {'label': 'Shift 1 (6 am to 2 pm)', 'value': 'Shift 1 (6 am to 2 pm)'},
            {'label': 'Shift 2 (2 pm to 10 pm)', 'value': 'Shift 2 (2 pm to 10 pm)'},
            {'label': 'Shift 3 (10 pm to 6 am next day)', 'value': 'Shift 3 (10 pm to 6 am next day)'}
        ],
        value=get_current_shift(),  # Default to the current shift
        style={
        'width': '100%',  # Adjust the width as needed
        'background-color': '#171b26',  # Set background color
        'border': '1px solid #2b2e37' , # Set border color and width
         'color': '#2b2e37',     

    },
        
    ),

    html.Div(id='current-state-container', style={'display': 'flex', 'align-items': 'center',}),
    
    dcc.Graph(id='shift-chart'),  # Container for the shift chart (remains here)
    
    dcc.Interval(
        id='interval-component',
        interval=5*60*1000,  # Interval is in milliseconds (5 minutes)
        n_intervals=0
    ),
])

# Function to calculate state durations as you provided
def calculate_state_duration(df, shift_start, shift_end):
    # Initialize states and state durations
    states = ['Off', 'No Load', 'On Load']
    state_durations = {state: 0 for state in states}
    
    # Initialize state and start time
    current_state = None
    state_start_time = None
    
    # Iterate through the DataFrame
    for index, row in df.iterrows():
        if (shift_start == 6 or shift_start == 14) and shift_start <= row['created_at'].hour < shift_end:
            if current_state is None:
                current_state = row['value']        
                state_start_time = row['created_at']
            elif row['value'] != current_state:
                state_durations[current_state] += (row['created_at'] - state_start_time).total_seconds()
                current_state = row['value']
                state_start_time = row['created_at']
        else:
            if current_state is None:
                current_state = row['value']        
                state_start_time = row['created_at']
            elif row['value'] != current_state:
                state_durations[current_state] += (row['created_at'] - state_start_time).total_seconds()
                current_state = row['value']
                state_start_time = row['created_at']

    # Add the final state duration
    if current_state is not None:
        state_durations[current_state] += (df.iloc[-1]['created_at'] - state_start_time).total_seconds()
    
    # Convert durations to hours
    state_durations = {state: duration / 3600 for state, duration in state_durations.items()}
    
    return state_durations

def get_current_state(selected_date, selected_shift):
    #global filled_df
    current_state = filled_df.iloc[-1]['value']
    return current_state

# Function to determine the color for the current state
def get_current_state_color(current_state):
    # Define colors for different states
    state_colors = {
        'Off': '#d779ee',
        'No Load': '#e2361c',
        'On Load': '#40e0d0'
    }

    # Get the color for the current state
    return state_colors.get(current_state, 'gray')  # Default to gray if state is not recognized

# Callback to update the shift chart and current state indicator
@app.callback(
    [Output('shift-chart', 'figure'),
     Output('current-state-container', 'children')],
    [Input('date-picker-single', 'date'),
     Input('shift-selector', 'value'),
     Input('interval-component', 'n_intervals')]  # Added input for the interval component
)
def update_shift_chart(selected_date, selected_shift, n_intervals):  # Added n_intervals
    global filled_df
    filled_df = api_call()
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
    # Filter DataFrame based on the selected date
    next_day = selected_date + pd.DateOffset(days=1)
    filtered_df = filled_df[(filled_df['created_at'].dt.date == selected_date) |
                           (filled_df['created_at'].dt.date == next_day.date())]
    
    # Define the shift time ranges
    shift_ranges = {
        'Shift 1 (6 am to 2 pm)': (6, 14),   # 6 am to 2 pm
        'Shift 2 (2 pm to 10 pm)': (14, 22),  # 2 pm to 10 pm
        'Shift 3 (10 pm to 6 am next day)': (22, 30)  # 10 pm to 6 am next day
    }

    # Determine the selected shift's start and end times
    shift_start, shift_end = shift_ranges[selected_shift]

    # Filter DataFrame for the selected shift
    if selected_shift == 'Shift 3 (10 pm to 6 am next day)':
        if selected_date != datetime.now().date():
            
            # For Shift 3 on a selected date (not today), consider data from the selected date until 6 am next day
            shift_df = filtered_df[((filtered_df['created_at'].dt.hour >= shift_start) &
                                    (filtered_df['created_at'].dt.date == selected_date) |
                                    (filtered_df['created_at'].dt.hour < 6 )&
                                    (filtered_df['created_at'].dt.date == next_day.date()) &
                                    (filtered_df['created_at'].dt.hour < shift_end))]
        else:
            # For Shift 3 on today's date, consider data from 22:00 to 23:59
            prev_day = selected_date + pd.DateOffset(days=-1)
            shift_df = filled_df[((filled_df['created_at'].dt.hour >= shift_start) 
                                  & (filled_df['created_at'].dt.date == prev_day.date())) |
                                 ((filled_df['created_at'].dt.hour < 6) &
                                  (filled_df['created_at'].dt.date == selected_date))]
    elif(selected_shift == 'Shift 1 (6 am to 2 pm)' or selected_shift == 'Shift 2 (2 pm to 10 pm)'):
        shift_df = filtered_df[
                ((filtered_df['created_at'].dt.hour >= shift_start) &
                (filtered_df['created_at'].dt.hour < shift_end)&(filtered_df['created_at'].dt.date == selected_date))]
    
    # Calculate state durations using the calculate_state_duration function
    state_durations = calculate_state_duration(shift_df, shift_start, shift_end)

    # Define custom colors for each state
    colors = ['#d779ee', '#e2361c', '#40e0d0']  # Orange for Off, Red for No Load, Green for On Load

    # Create a donut chart
    labels = list(state_durations.keys())
    values = list(state_durations.values())

    # Calculate percentages
    total_duration = sum(values)
    percentages = []
    if (total_duration != 0):
        percentages = [(value / total_duration) * 100 for value in values]

    # Create text labels with time in hours, minutes, and percentages
    text_labels = [f"{int(value)} hr {int((value % 1) * 60)} min "
                   for value, percent in zip(values, percentages)]
    #text_labels = [i for i in text_labels if (i!='0 hr 0 min ' )]
    #print("text_labels",text_labels)

    # Create outer labels for text placement
    outer_labels = [f'{label}: {text}' for label, text in zip(labels, text_labels)]

    # Calculate label positions
    label_positions = [(0.9 * cos((percent + sum(percentages[:i])) * pi / 180),
                        0.9 * sin((percent + sum(percentages[:i])) * pi / 180))
                       for i, percent in enumerate(percentages)]

    # Create a donut chart with a shadow effect
    trace = go.Pie(
        labels=outer_labels,
        values=values,
        hole=0.5,
        marker=dict(
            colors=colors,
            line=dict(color='rgba(255, 120, 120, 0.3)', width=4)  # Add shadow effect here
        ),
        text=text_labels,
        hoverinfo='text+percent',
        textposition='outside',
        outsidetextfont=dict(color='yellow', size=14),
        pull=[0.04, 0.04, 0.04],
    )

    layout = go.Layout(
        title={'text':f'{selected_shift} on {selected_date}','font': {'color': '#ff6666', 'size':20,},'y': 0.98},
        paper_bgcolor='#171b26',
        legend={'title': {'text': 'State Indicator'}, 'font': {'color': '#ff6666','size':12}}  # Set the legend text color here
    )

    # Get the current state based on real-time data
    current_state = get_current_state(filled_df, selected_shift)
    
    # Get the color for the current state
    current_state_color = get_current_state_color(current_state)

    # Update the current state indicator with color and size
    current_state_indicator_style = {
        'background-color': current_state_color,  # Set the background color based on the current state
        'color': '#fff',  # Text color
        'border': '2px solid #000',  # Border color and width
        'border-radius': '15px',  # Border radius for curved corners
        'padding': '10px 10px',  # Padding inside the button
        'font-size': '18px',  # Font size
        'text-align': 'center',
        'box-shadow': '4px 4px 8px rgba(255, 102, 102, 0.2)',  # Box shadow for 3D effect
        'margin-top': '10px',
        'cursor': 'default',  # Remove cursor pointer
        'width': '70px',  # Set width
        'height': '70px',  # Set height
        'margin-left': '10px',
    }

    current_state_container = html.Div([
        html.Button(current_state, id='current-state-button', style=current_state_indicator_style),
        html.Span('', style={'font-size': '18px', 'margin-left': '10px'}),
    ], style={'display': 'flex', 'justify-content': 'center','align-items': 'center'})

    figure = {'data': [trace], 'layout': layout}

    return figure, current_state_container

if __name__ == '__main__':
    app.run_server(debug=True)
