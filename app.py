import requests
import base64
import io
import json
import os
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, State, dash_table
from dash.exceptions import PreventUpdate

from worker import queue

BASE_URL = "http://localhost:8000"


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server


# App layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='redirect'),
    html.Div(id='page-content'),
    dcc.Store(id='jwt-store', storage_type='local'),   
])

# Homepage layout
basic = html.Div([
    dbc.Container([
        dbc.Col([
            dbc.Row(html.H2("Predicting survival of patients with liver cirrhosis", style={"font-size" : "35px", "color" : "#474747"}), style={"float":"left"}),
            dbc.Col(html.A("see task on Kaggle", href='https://www.kaggle.com/datasets/joebeachcapital/cirrhosis-patient-survival-prediction/', target='_blank', style={"font-size": "30px", "float":"left", "margin-left":"10px"})),
            dbc.Col(dbc.Button("Sign Up", href="/signup", color="primary"), style={"float":"right", "padding-left":"30px", "padding-top":".1%"}),
            dbc.Col(dbc.Button("Log In", href="/login", color="primary"), style={"float":"right", "padding-top":".1%"}),
        ], style={"margin-top" : "5%"}),
        dbc.Row([
            dbc.Col(html.H3('', style={"font-size" : "25px"}), style={"margin-top" : "3%"}, width=11)
        ]),
        
        dbc.Col([
            dbc.Row([
                dbc.Col(html.H4('A few words about cirrhosis', style={"color" : "#EA6237", "font-size" : "30px"}), width=8),
                dbc.Col(html.P('Liver cirrhosis is a serious condition caused by long-term liver damage and the formation of extensive scar tissue. This often occurs due to conditions such as hepatitis or chronic alcohol use.', style={"font-size" : "20px", "color" : "#677278"}), width=10)
            ]),
            dbc.Row([
                dbc.Col(html.H4('Description of the dataset', style={"color" : "#EA6237", "font-size" : "30px"}), width=8),
                dbc.Col(html.P('The study includes information about patients, including their gender, age and other attributes - 17 attributes in total. Additional attributes include data on D-penicillamine medication use and treatment outcome. Total entries - 418. This dataset is based on research conducted by the Mayo Clinic between 1974 and 1984.', style={"font-size" : "20px", "color" : "#677278"}), width=10)
            ]),
            ], style={"margin-top" : "5%"}),
        
        dbc.Col([
            dbc.Row([
                dbc.Col(html.H4('Our service offers several models', style={"color" : "#474747", "font-size" : "30px"}), width=8),
                dbc.Col([
                    html.Span(html.B('Catboost'), style={"font-size": "23px", "color": "#D13838"}),
                    html.Span(' ~ 80% correct predictions', style={"font-size": "20px", "color" : "#677278"})
                ], width=8),
                dbc.Col([
                    html.Span(html.B('Random Forest'), style={"font-size": "23px", "color": "#7FC481"}),
                    html.Span(' ~ 78% correct predictions', style={"font-size": "20px", "color" : "#677278"})
                ], width=8),
                dbc.Col([
                    html.Span(html.B('Logistic Regression'), style={"font-size": "23px", "color": "#4CA4EA"}),
                    html.Span(' ~ 76% correct predictions', style={"font-size": "20px", "color" : "#677278"})
                ], width=8),
            ]),
            ], style={"margin-top" : "3%"}),
        
        dbc.Row(
            dbc.Col(
                dbc.Button(html.B("Main page"), href="/main", color="primary", style={"width" : "150px", "height" : "45px", "font-size":"20px", "text-align" : "center"})), style={"float":"left", "margin-top" : "3%", "margin-bottom" : "3%"}
            )
    ]),
])

# Sign up layout
signup_page = html.Div([
    dbc.Container([
        dbc.Col([
            dbc.Col(html.H2("Signup Page"), style={"float":"left"}),
            dbc.Col(dbc.Button("Back to start", href="/"), style={"float":"right", "padding-top":".1%"})
        ], style={"margin-top" : "5%"}),        
        html.Br(),        
        html.Br(),
        dbc.Col([
            dbc.Col(
                dbc.Form([
                    dbc.Label("Username"),
                    dbc.Input(id='signup-username', placeholder="Enter username"),
                    html.Br(),
                    dbc.Label("Password"),
                    dbc.Input(id='signup-password', placeholder="Enter password", type="password"),
                    html.Br(),
                    dbc.Label("Confirm Password"),
                    dbc.Input(id='signup-confirm-password', placeholder="Confirm password", type="password"),
                    html.Br(),
                    dbc.Button("Signup", id="signup-button", color="success")
                ], style={"font-size" : "20px", "color" : "#474747", "margin-top" : "3%"}),
                width=6
            )
        ]),
        
        html.Div(id='signup-output')
    ]),
])


# Log in Layout
login_page = html.Div([
    dbc.Container([
        dbc.Col([
            dbc.Col(html.H2("Login Page"), style={"float":"left"}),
            dbc.Col(dbc.Button("Back to start", href="/"), style={"float":"right", "padding-top":".1%"})
        ], style={"margin-top" : "5%"}),
        html.Br(),        
        html.Br(),        
        dbc.Col([
            dbc.Col(
                dbc.Form([
                    dbc.Label("Username"),
                    dbc.Input(id='login-username', placeholder="Enter username"),
                    html.Br(),
                    dbc.Label("Password"),
                    dbc.Input(id='login-password', placeholder="Enter password", type="password"),
                    html.Br(),
                    dbc.Button("Login", id="login-button", color="primary"),
                ], style={"font-size" : "20px", "color" : "#474747", "margin-top" : "3%"}),
                width=6
            )
        ]),
        
        html.Div(id='login-output')
    ]),
])

# Basic homepage layout
main_page = html.Div([
    dbc.Container([
        dbc.Col([
            dbc.Row(html.H2("Main Page"), style={"float":"left"}),
            dbc.Col(dbc.Button("Back to start", href="/", color="primary"), style={"float":"right", "padding-top":".1%"}),
        ], style={"margin-top" : "5%"}),
        dbc.Col([
            dbc.Col(html.Div(id='main-page-content'), width=12)
        ]),
    ])
])

# Functions
def get_bill_balance(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/get-bill-balance", headers=headers)
    return response.json().get('balance', 'Unable to fetch balance')

def buy_coins(token, amount):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/buy-coins", json={"amount": amount}, headers=headers)
    return response.json()

def upload_data(token, file_stream, file_name):
    headers = {"Authorization": f"Bearer {token}"}
    files = {'file': (file_name, file_stream)}
    response = requests.post(f"{BASE_URL}/upload-data", headers=headers, files=files)
    return response

def choose_model(token, data_id, model_type):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "data_id": data_id,
        "model_type": model_type
    }
    response = requests.post(f"{BASE_URL}/choose-model", json=payload, headers=headers)
    return response


def run_model(token, data_id, model_name, model_path, model_cost):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "data_id": data_id,
        "model_name": model_name,
        "model_path": model_path,
        "model_cost": model_cost
    }
    response = requests.post(f"{BASE_URL}/run-model", json=payload, headers=headers)
    return response.json()

# Sample dataframe that appears on the main page 
current_dir = os.path.dirname(os.path.abspath('cirrhosis.csv'))
base_dir = os.path.dirname(current_dir)
file_path = os.path.join(base_dir, 'web-ml-service', 'models', 'data', 'cirrhosis.csv')

# Set absolute path
df = pd.read_csv(file_path).drop(columns=['Status', 'ID']).head()


# Sign up callback
@app.callback(
    Output('signup-output', 'children'),
    Input('signup-button', 'n_clicks'),
    [State('signup-username', 'value'),
     State('signup-password', 'value'),
     State('signup-confirm-password', 'value')],
    prevent_initial_call=True)
def signup(n_clicks, username, password, confirm_password):
    if n_clicks:
        if password != confirm_password:
            return "Passwords do not match. Please try again."
        try:
            response = requests.post(f"{BASE_URL}/signup", json={"username": username, "password": password})
            if response.status_code == 200:
                return "Signup successful. Redirecting to login...", dcc.Location(pathname="/login", id="login-output")
            elif response.status_code == 400:
                return "Signup unsuccessful. This username already exists"
        except requests.RequestException as e:
            return f"Signup failed: {str(e)}"

# Login callback
@app.callback(
    [Output('login-output', 'children'),
     Output('jwt-store', 'data'),
     Output('redirect', 'children')],
    [Input('login-button', 'n_clicks')],
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True)
def login(n_clicks, username, password):
    if n_clicks:
        try:
            response = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
            response.raise_for_status()
            data = response.json()
            access_token = data.get("access_token", "No access token provided")
            return "Logged in successfully! Redirecting...", {"token": access_token}, dcc.Location(pathname='/main', id='location')
        except:
            return "Wrong username or password", {}, None
    raise PreventUpdate


# Update the main page if we've got a user's JWT token 
@app.callback(
    Output('main-page-content', 'children'),
    Input('jwt-store', 'data')
)
def update_main_page(jwt_data):
    jwt_token = jwt_data.get("token") if jwt_data else None
    if jwt_token:
        balance = get_bill_balance(jwt_token)
        return html.Div([
            dcc.Store(id='upload-status-store'),
            dcc.Store(id='choose-model-output-data'),
            dcc.Store(id='job-id-store', storage_type='session'),


            dbc.Col([
                html.Br(),
                html.H4(f"Your Bill balance: {balance} coins", style={"margin":"50px 0 20px 0"}),
                # Bill field
                dbc.Row(html.Div(html.H4("Buy Coins"))),
                dbc.Row([
                    dbc.Col(html.Div([
                        dbc.Input(id='buy-coins-amount', type="number", placeholder="Enter amount"),
                    ]), width=6),
                    dbc.Col(html.Div([
                        html.A(dbc.Button('Buy', id="buy-coins-button", color="success"), href='/main'),
                        html.Div(id='buy-coins-output')
                    ]), width=6),
                ]),
                
                
                # Demonstrate the sample of uploading dataframe
                dbc.Row([
                    html.Div([
                        html.H4("Upload Data for ML Model", style={"margin":"0px 0px 25px 0px"}),
                        html.H5("Sample of uploading data:"),
                        ], style={"margin":"35px 0px 5px 0px"}),
                    ]),
                
                # Display sample dataframe
                dbc.Row([
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name": i, "id": i} for i in df.columns],
                        data=df.to_dict('records'),
                        
                        # Style the dataframe
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'fontFamily': 'Arial, sans-serif',
                            'fontSize': '12px',
                        },

                        style_header={
                            'backgroundColor': 'lightgrey',
                            'fontWeight': 'bold',
                            'border': '1px solid black'
                        },

                        style_data={
                            'backgroundColor': 'white',
                            'border': '1px solid grey'
                        },
                    ),
                    dbc.Row([
                        html.Div(
                           html.I("Please note that the loaded csv file must contain the following columns: N_Days, Drug, Age, Sex, Ascites, Hepatomegaly, Spiders, Edema, Bilirubin, Cholesterol, Albumin, Copper, Alk_Phos, SGOT, Tryglicerides, Platelets, Prothrombin, Stage"), style={"margin":"20px 0px 10px 0px"}),
                    ]),
                    
                    # Upload Data for ML Model
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div(['Drag and Drop or Select Files  ', html.A('(.csv)')]),
                        style={
                            'width': '100%', 'height': '60px', 'lineHeight': '60px',
                            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                            'textAlign': 'center', 'margin': '10px'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-data-output')]),
                
                # Model selection
                dbc.Row([
                    dbc.Row(html.Div(
                        html.H4("Select Model", style={"margin":"20px 0px 20px 0px"}),
                    )),
                    dbc.Col(html.Div([
                        dcc.Dropdown(
                            id='model-dropdown',
                            options=[
                                {'label': 'Catboost (30 coins)', 'value': 'CatBoost'},
                                {'label': 'Logistic Regression (10 coins)', 'value': 'Logistic Regression'},
                                {'label': 'Random Forest (20 coins)', 'value': 'Random Forest'}
                            ],
                            placeholder="Select a model"
                        ),
                    ]), width=6),
                    dbc.Col(html.Div([
                        dbc.Button("Choose Model", id="choose-model-button", color="primary"),
                        html.Div(id='choose-model-output')
                    ]))
                ]),
                
                # Run model
                dbc.Row([
                    dbc.Col(html.Div([
                        dbc.Button("Run Model", id="run-model-button", color="warning"),
                        html.Div(id='run-model-output'),
                        html.Div(id='output'),
                        html.Div(id='timer'),
                    ]), style={'margin': '20px 0px 20px 0px'}),
                ]),
                
                html.A(id='download-link', children='Download Results', href='', style={'display': 'none'}),
                
                dbc.Col([
                    html.P(html.B('Interpretation of results'), style={"font-size": "20px", "color": "#677278"}),
                    html.Span('0 — means censored; ', style={"font-size": "15px", "color" : "#677278"}),
                    html.Span('1 — means censored due to liver tx; ', style={"font-size": "15px", "color" : "#677278"}),
                    html.Span('2 — means death', style={"font-size": "15px", "color" : "#677278"})
                ], id="description", style={"display" : "none", "margin-top" : '20px'}, width=8)
            ], style={"margin-bottom":"3%"}),
            
        ])
    else:
        return dbc.Col([html.Br(),html.Br(), html.H4("You need to log in to access this page.", style={"margin-top" : "20px"})])


# Buy coins callback
@app.callback(
    Output('buy-coins-output', 'children'),
    Input('buy-coins-button', 'n_clicks'),
    [State('jwt-store', 'data'), 
     State('buy-coins-amount', 'value')],
    prevent_initial_call=True)
def handle_buy_coins(n_clicks, jwt_data, amount):
    jwt_token = jwt_data.get("token") if jwt_data else None
    if jwt_token and amount:
        response = buy_coins(jwt_token, amount)
        return f"Response: {response}"
    return "Please enter a valid amount and ensure you're logged in."


# Upload data callback
@app.callback(
    [Output('upload-data-output', 'children'), 
     Output('upload-status-store', 'data')],
    Input('upload-data', 'contents'),
    [State('upload-data', 'filename'),
     State('jwt-store', 'data')],
    prevent_initial_call=True)
def handle_upload(contents, filename, jwt_data):
    jwt_token = jwt_data.get("token") if jwt_data else None
    if jwt_token and contents:
        if not filename.endswith('.csv'):
            return "We support only a CSV file.", {}
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        response = upload_data(jwt_token, io.BytesIO(decoded), filename)
        if response.status_code == 200:
            return "File uploaded successfully.", json.dumps(response.json())
        elif response.status_code == 400:
            return f"{response.json()['detail']}", {}
        else:
            return "Upload failed.", {}
    
    return "Please upload a file and ensure you're logged in."


# Model selection callback
@app.callback(
    [Output('choose-model-output', 'children'), 
     Output('choose-model-output-data', 'data')],
    Input('choose-model-button', 'n_clicks'),
    [State('jwt-store', 'data'),
     State('upload-status-store', 'data'),
     State('model-dropdown', 'value')],
    prevent_initial_call=True)
def handle_model_choice(n_clicks, jwt_data, upload_output, model_type):
    jwt_token = jwt_data.get("token") if jwt_data else None
    upload_data = json.loads(upload_output) if upload_output else {}
    data_id = upload_data.get('data_id')
    if jwt_token and data_id and model_type:
        response = choose_model(jwt_token, data_id, model_type)
        if response.status_code == 200:
            response = response.json()
            return f"You choose the model: {json.dumps(response['name'])}, that cost is {json.dumps(response['cost'])} coins", json.dumps(response)
        elif response.status_code == 403:
            return f"Model selection failed: {response.json()['detail']}", {}
        else:
            return f"Model selection failed: {response.json()['detail']}", {}
            
    return "First you need to load the data", {}


# Add workers

@app.callback(
    Output('interval-component', 'disabled'),
    Input('run-model-button', 'n_clicks'),
    prevent_initial_call=True)
def enable_interval(n_clicks):
    return False  # Enable the interval component

@app.callback(
    [Output('run-model-output', 'children'), 
     Output('job-id-store', 'data'), Output('timer', 'children')],   
    Input('run-model-button', 'n_clicks'),
    [State('jwt-store', 'data'),
     State('upload-status-store', 'data'),
     State('choose-model-output-data', 'data')],
    prevent_initial_call=True)
def handle_run_model(n_clicks, jwt_data, upload_output, model_output):
    jwt_token = jwt_data.get("token") if jwt_data else None
    upload_data = json.loads(upload_output) if upload_output else {}
    model_data = json.loads(model_output) if model_output else {}
    
    data_id = upload_data.get('data_id')
    model_name = model_data.get('name')
    model_path = model_data.get('file_path')
    model_cost = model_data.get('cost')
    
    if jwt_token and data_id and model_name and model_path is not None and model_cost is not None:
        try: 
            job = queue.enqueue('app.run_model', 
                                jwt_token, data_id, model_name, model_path, model_cost)
            return html.P("Model execution started", style={"margin-top":"20px", "font-size" : "20px"}), job.id, dcc.Interval(
                                                                                                                        id='interval-component',                                                                                                      interval=5*1000,
                                                                                                                        n_intervals=0),
        except Exception as e:
            return f"Error: {str(e)}", " ", dcc.Interval(
                                                    id='interval-component',
                                                    interval=5*1000,  
                                                    n_intervals=0)
            
    return "Please complete all steps before running the model.", " ", dcc.Interval(
                                                                            id='interval-component',
                                                                            interval=1000000,  
                                                                            n_intervals=0)

@app.callback(
    [Output('output', 'children'), 
     Output('download-link', 'href'), 
     Output('download-link', 'style'), 
     Output('description', 'style')],
    Input('interval-component', 'n_intervals'),
    Input('timer', 'children'),
    State('job-id-store', 'data'),
    prevent_initial_call=True)
def fetch_result(n_intervals, timer, job_id_data):
    if job_id_data:
        job_id = job_id_data
        job = queue.fetch_job(job_id)
        try:
            if job.is_finished:
                download_url = f"{BASE_URL}/{job.result['file_path']}"
                return html.P("Model successfully executed", style={"margin-top":"20px", "font-size" : "20px"}), download_url, {'display': 'block', 'color': 'blue'}, {'display': 'block'} 
            elif job.is_failed:
                return "Model execution failed. There maybe a problem with the dataset", "", {'display': 'none', 'color': 'blue'}, {'display': 'none'} 
        except:
            return "", "", {'display': 'none', 'color': 'blue'}, {'display': 'none'} 
    return html.P("Waiting for result...", style={"margin-top":"20px", "font-size" : "18px"}), "", {'display': 'none', 'color': 'blue'}, {'display': 'none'} 


# Manager callback
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return basic
    elif pathname == '/signup':
        return signup_page
    elif pathname == '/login':
        return login_page
    elif pathname == '/main':
        return main_page
    else:
        return basic


if __name__ == '__main__':
    app.run_server(debug=True)
    