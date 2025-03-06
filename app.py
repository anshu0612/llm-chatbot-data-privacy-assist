import os
import base64
import json
import io
import dash
from dash import dcc, html, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import numpy as np
import time
from dash.exceptions import PreventUpdate
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.title = "Data Privacy Assist 2 - Data-driven Privacy Guidance"
server = app.server

# Import components and utils
try:
    from components import (
        create_navbar,
        create_upload_component,
        create_privacy_assessment_tab,
        create_data_quality_tab,
        create_chatbot_component,
        process_chat_message,
        create_knowledge_manager_component
    )
    from utils import analyze_privacy_risks, analyze_data_quality, generate_report
except ImportError as e:
    print(f"Error importing components or utils: {e}")
    # Fallback to direct imports
    from components.upload_component import create_upload_component
    from components.privacy_assessment import create_privacy_assessment_tab
    from components.data_quality import create_data_quality_tab
    from components.chatbot_component import create_chatbot_component, process_chat_message
    from components.navbar import create_navbar
    from components.knowledge_manager import create_knowledge_manager_component
    from utils.privacy_analyzer import analyze_privacy_risks
    from utils.data_quality_analyzer import analyze_data_quality
    from utils.report_generator import generate_report

# Create the app layout
app.layout = html.Div(
    [
        dcc.Store(id="dataset-store", storage_type="memory"),
        dcc.Store(id="privacy-scores-store", storage_type="memory"),
        dcc.Store(id="data-quality-scores-store", storage_type="memory"),
        dcc.Store(id="chat-history-store", data=[], storage_type="memory"),
        dcc.Store(id="column-names-store", storage_type="memory"),
        dcc.Store(id="constraints-store", data=None, storage_type="memory"),
        
        create_navbar(),
        
        # Privacy eye element has been removed
        
        # Privacy toast has been removed
        
        dbc.Container(
            [
                # Data Upload Section (Always visible)
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H4(
                                            "Data Upload",
                                            className="mb-3 d-flex align-items-center",
                                            style={
                                                "fontFamily": "'Roboto', sans-serif",
                                                "color": "var(--neutral-800)",
                                                "paddingBottom": "10px",
                                                "fontWeight": "500",
                                                "borderBottom": "1px solid var(--neutral-300)",
                                            }
                                        ),
                                        html.P("Upload your dataset to begin privacy and quality assessment", className="text-muted mb-3"),
                                        create_upload_component(),
                                        html.Div(id="upload-info-container")
                                    ],
                                    className="p-4 mb-4",
                                    style={
                                        "backgroundColor": "var(--surface)",
                                        "border": "1px solid var(--neutral-300)",
                                        "borderRadius": "8px",
                                        "boxShadow": "var(--shadow-sm)",
                                    }
                                )
                            ],
                            width=12,
                        )
                    ],
                    className="mt-4",
                ),

                # Analysis Panels (Shown after data upload)
                html.Div(
                    id="analysis-content",
                    style={"display": "block"},
                    children=[
                        dbc.Row(
                            [
                                # Left Column - Privacy & Data Quality Analysis
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.H4(
                                                            [
                                                                "Data Analysis", 
                                                                html.Span(
                                                                    className="status-indicator active",
                                                                    id="privacy-status",
                                                                    title="Privacy Monitor Status"
                                                                )
                                                            ],
                                                            className="mb-3 d-flex align-items-center",
                                                            style={
                                                                "fontFamily": "'Roboto', sans-serif",
                                                                "color": "var(--neutral-800)",
                                                                "borderBottom": "1px solid var(--neutral-300)",
                                                                "paddingBottom": "10px",
                                                                "fontWeight": "500"
                                                            }
                                                        ),
                                                    ],
                                                    className="d-flex flex-column"
                                                ),
                                                html.Div(
                                                    [
                                                        # Tabs navigation
                                                        dbc.Tabs(
                                                            [
                                                                dbc.Tab(
                                                                    children=None,
                                                                    label="Privacy Risk Assessment",
                                                                    tab_id="tab-privacy",
                                                                    activeTabClassName="fw-bold",
                                                                    label_style={"color": "#0066CC", "background-color": "#F9F9F9", "border": "1px solid #C2E2FF", "border-radius": "0.5rem 0.5rem 0 0"},
                                                                    active_label_style={"color": "#1A8BFF", "background-color": "#FFFFFF", "border-bottom": "2px solid #1A8BFF", "font-weight": "600"},
                                                                ),
                                                                dbc.Tab(
                                                                    children=None,
                                                                    label="Data Quality Assessment",
                                                                    tab_id="tab-quality",
                                                                    activeTabClassName="fw-bold",
                                                                    label_style={"color": "#0066CC", "background-color": "#F9F9F9", "border": "1px solid #C2E2FF", "border-radius": "0.5rem 0.5rem 0 0"},
                                                                    active_label_style={"color": "#1A8BFF", "background-color": "#FFFFFF", "border-bottom": "2px solid #1A8BFF", "font-weight": "600"},
                                                                ),
                                                            ],
                                                            id="tabs",
                                                            active_tab="tab-privacy",
                                                            className="mt-4",
                                                        ),
                                                        
                                                        # Tab content - separate from the tabs
                                                        html.Div(
                                                            [
                                                                html.Div(
                                                                    create_privacy_assessment_tab(),
                                                                    id="privacy-tab-content",
                                                                    style={"display": "block"}
                                                                ),
                                                                html.Div(
                                                                    create_data_quality_tab(),
                                                                    id="quality-tab-content",
                                                                    style={"display": "none"}
                                                                ),
                                                            ],
                                                            className="p-4",
                                                            id="tab-content",
                                                            style={"background-color": "#FFFFFF", "border": "1px solid #C2E2FF", "border-top": "none", "border-radius": "0 0 0.5rem 0.5rem"}
                                                        ),
                                                    ],
                                                    className="tabs-container",
                                                    style={"background-color": "#FFFFFF"}
                                                ),
                                            ],
                                            className="data-analysis-card p-4 mb-4",
                                            style={
                                                "backgroundColor": "#FFFFFF",
                                                "border": "1px solid #C2E2FF",
                                                "borderRadius": "0.5rem",
                                                "boxShadow": "var(--shadow-md)",
                                                "position": "relative",
                                                "transition": "all var(--transition-normal)"
                                            }
                                        )
                                    ],
                                    md=7,
                                    className="mb-4"
                                ),
                                
                                # Right Column - Chatbot
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.H4(
                                                            "Privacy Recommendations", 
                                                            className="mb-2 privacy-recommendation-title"
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.Span("AI assistant powered by Singapore Public Sector Privacy Policies"),
                                                                html.Span(
                                                                    "ACTIVE",
                                                                    className="ms-2 badge bg-primary",
                                                                    style={
                                                                        "backgroundColor": "var(--primary) !important",
                                                                        "fontSize": "10px",
                                                                        "fontWeight": "500",
                                                                        "paddingTop": "3px",
                                                                        "paddingBottom": "3px"
                                                                    }
                                                                )
                                                            ],
                                                            className="text-muted mb-3 small d-flex align-items-center"
                                                        )
                                                    ],
                                                    className="mb-2"
                                                ),
                                                create_chatbot_component(),
                                            ],
                                            className="p-4 chatbot-panel",
                                            style={
                                                "backgroundColor": "#FFFFFF",
                                                "border": "none", 
                                                "borderRadius": "4px",
                                                "boxShadow": "var(--shadow)",
                                                "position": "relative",
                                                "transition": "all var(--transition-normal)"
                                            }
                                        )
                                    ],
                                    md=5,
                                    className="mb-4"
                                ),
                            ]
                        )
                    ]
                ),
                

                
                # Modern footer with interactive elements
                html.Div(
                    [
                        html.Hr(style={"borderTop": "1px solid #e0e0e0", "opacity": 0.6}),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Img(
                                            src="/assets/logo.png", 
                                            height="40px",
                                            className="mb-2"
                                        ),
                                        html.P(
                                            "Smart Privacy for a Digital Singapore",
                                            className="text-muted small mb-1",
                                            style={"fontWeight": "500"}
                                        ),
                                        html.P(
                                            " 2025 Data Privacy Assist",
                                            className="text-muted small mb-0"
                                        ),
                                    ],
                                    className="text-center", 
                                    style={"width": "50%", "margin": "0 auto"}
                                ),
                                html.Div(
                                    [
                                        dbc.Button(
                                            [
                                                DashIconify(
                                                    icon="mdi:help-circle-outline", 
                                                    width=16,
                                                    className="me-1"
                                                ), 
                                                "Help"
                                            ],
                                            color="link",
                                            size="sm",
                                            className="me-2 text-muted"
                                        ),
                                        dbc.Button(
                                            [
                                                DashIconify(
                                                    icon="mdi:shield-check-outline", 
                                                    width=16,
                                                    className="me-1"
                                                ), 
                                                "Privacy Policy"
                                            ],
                                            color="link",
                                            size="sm",
                                            className="me-2 text-muted"
                                        ),
                                        dbc.Button(
                                            [
                                                DashIconify(
                                                    icon="mdi:information-outline", 
                                                    width=16,
                                                    className="me-1"
                                                ), 
                                                "About"
                                            ],
                                            color="link",
                                            size="sm",
                                            className="text-muted"
                                        ),
                                    ],
                                    className="d-flex justify-content-center mt-2"
                                )
                            ],
                        ),
                    ],
                    className="mt-4 mb-2 footer"
                )
            ],
            fluid=True,
            className="py-4",
        ),
    ],
    className="min-vh-100",
    style={"position": "relative"}
)

# File upload callback
@app.callback(
    Output("dataset-store", "data"),
    Output("upload-status", "children"),
    Output("upload-info-container", "children"),
    Output("column-names-store", "data"),
    Output("analysis-content", "style"),  # Add output for the analysis content visibility
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
    prevent_initial_call=True
)
def update_output(contents, filename, last_modified):
    print("=== UPLOAD CALLBACK TRIGGERED ===")
    print(f"Contents type: {type(contents)}")
    print(f"Filename: {filename}")
    if contents is None:
        raise PreventUpdate
    
    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        
        if filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None, dbc.Alert("Only CSV and Excel files are supported.", color="danger"), None, [], {"display": "none"}
        
        # Basic data info
        file_info = html.Div([
            dbc.Alert("File uploaded successfully! You can now proceed with analysis.", color="success", className="mb-3"),
            html.Div([
                html.P(f"Filename: {filename}", className="mb-1"),
                html.P(f"Last modified: {datetime.fromtimestamp(last_modified/1000).strftime('%Y-%m-%d %H:%M:%S')}", className="mb-1"),
                html.P(f"Number of rows: {df.shape[0]}", className="mb-1"),
                html.P(f"Number of columns: {df.shape[1]}", className="mb-1"),
            ], className="small")
        ])
        
        # Return the dataframe as JSON, update UI, and show analysis panels
        return df.to_json(date_format='iso', orient='split'), \
               None, \
               file_info, \
               df.columns.tolist(), \
               {"display": "block"}  # Make analysis panels visible
    
    except Exception as e:
        print(f"Error processing file: {e}")
        return None, dbc.Alert(f"Error processing file: {str(e)}", color="danger"), None, [], {"display": "none"}

# Run privacy analysis when a dataset is loaded
@app.callback(
    Output("privacy-scores-store", "data"),
    Output("privacy-results-container", "children"),
    Input("dataset-store", "data"),
    Input("run-privacy-analysis-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_privacy_analysis(json_data, n_clicks):
    print("hererere")
    if json_data is None:
        raise PreventUpdate
    
    # Parse the JSON data back to a dataframe
    df = pd.read_json(json_data, orient='split')
    
    # Run the privacy analysis
    privacy_results, visualizations = analyze_privacy_risks(df)
    
    # Return the results
    return json.dumps(privacy_results), visualizations

# Run data quality analysis when a dataset is loaded
@app.callback(
    Output("data-quality-scores-store", "data"),
    Output("quality-results-container", "children"),
    Input("dataset-store", "data"),
    Input("run-quality-analysis-btn", "n_clicks"),
    State("constraints-store", "data"),
    prevent_initial_call=True,
)
def run_data_quality_analysis(json_data, n_clicks, constraints_data=None):
    print("=== DATA QUALITY ANALYSIS CALLBACK TRIGGERED ===")
    print(f"n_clicks: {n_clicks}")
    print(f"json_data is None: {json_data is None}")
    print(f"constraints_data: {constraints_data}")
    
    if json_data is None or n_clicks is None:
        print("Preventing update due to None inputs")
        raise PreventUpdate
    
    try:
        # Parse the JSON data back to a dataframe
        df = pd.read_json(json_data, orient='split')
        print(f"DataFrame shape: {df.shape}")
        
        # Run the data quality analysis with custom constraints
        print("Running data quality analysis...")
        quality_results, visualizations = analyze_data_quality(df, constraints_data)
        print("Analysis complete!")
        
        # Return the results
        return json.dumps(quality_results), visualizations
    except Exception as e:
        print(f"Error in data quality analysis: {e}")
        import traceback
        traceback.print_exc()
        # Return empty results in case of error
        return json.dumps({"error": str(e)}), html.Div(dbc.Alert(f"Error processing data quality: {str(e)}", color="danger"))

# Generate PDF or JSON reports for privacy assessment
@app.callback(
    Output("privacy-download-report", "data"),
    Input("privacy-generate-report-btn", "n_clicks"),
    State("privacy-report-format-radio", "value"),
    State("privacy-scores-store", "data"),
    State("data-quality-scores-store", "data"),
    State("dataset-store", "data"),
    prevent_initial_call=True,
)
def generate_privacy_report_callback(n_clicks, report_format, privacy_data, quality_data, dataset_data):
    if n_clicks is None or not all([privacy_data, quality_data, dataset_data]):
        raise PreventUpdate
    
    # Parse the data
    privacy_results = json.loads(privacy_data)
    quality_results = json.loads(quality_data)
    df = pd.read_json(dataset_data, orient='split')
    
    # Generate the report
    return generate_report(df, privacy_results, quality_results, report_format)

# Generate PDF or JSON reports for data quality assessment
@app.callback(
    Output("quality-download-report", "data"),
    Input("quality-generate-report-btn", "n_clicks"),
    State("quality-report-format-radio", "value"),
    State("privacy-scores-store", "data"),
    State("data-quality-scores-store", "data"),
    State("dataset-store", "data"),
    prevent_initial_call=True,
)
def generate_quality_report_callback(n_clicks, report_format, privacy_data, quality_data, dataset_data):
    if n_clicks is None or not all([privacy_data, quality_data, dataset_data]):
        raise PreventUpdate
    
    # Parse the data
    privacy_results = json.loads(privacy_data)
    quality_results = json.loads(quality_data)
    df = pd.read_json(dataset_data, orient='split')
    
    # Generate the report
    return generate_report(df, privacy_results, quality_results, report_format)

# Process chat messages
@app.callback(
    Output("chat-messages", "children"),
    Output("chat-history-store", "data"),
    Output("user-input", "value"),  # Clear the input field after sending
    [Input("send-button", "n_clicks"), Input("user-input", "n_submit")],  # Trigger on button click or Enter key
    State("user-input", "value"),
    State("chat-messages", "children"),
    State("chat-history-store", "data"),
    State("privacy-scores-store", "data"),
    State("data-quality-scores-store", "data"),
    prevent_initial_call=True,
)
def process_message(n_clicks, n_submit, user_input, current_messages, chat_history, privacy_data, quality_data):
    if (n_clicks is None and n_submit is None) or not user_input:
        raise PreventUpdate
    
    # Format user message for display
    user_message_component = html.Div(
        [
            html.Div(
                user_input,
                className="user-message-text"
            )
        ],
        className="user-message mb-3 d-flex justify-content-end"
    )
    
    # Add user message to display
    updated_messages = current_messages + [user_message_component]
    
    # Add typing indicator
    typing_indicator = html.Div(
        dbc.Spinner(size="sm", color="primary"),
        className="bot-message-typing mb-3"
    )
    updated_messages = updated_messages + [typing_indicator]
    
    # Process the message through the chatbot
    privacy_context = json.loads(privacy_data) if privacy_data else {}
    quality_context = json.loads(quality_data) if quality_data else {}
    
    # Add the user message to history
    new_history = chat_history + [{"role": "user", "content": user_input}]
    
    # Get bot response (now returns a dict with id, content, timestamp, feedback)
    bot_response_data = process_chat_message(user_input, new_history, privacy_context, quality_context)
    
    # Add bot response to history
    new_history = new_history + [{"role": "assistant", "content": bot_response_data["content"]}]
    
    # Create bot message component using the helper function from chatbot_component
    from components.chatbot_component import create_bot_message
    bot_message_component = create_bot_message(bot_response_data)
    
    # Update messages (replace typing indicator with actual response)
    updated_messages = updated_messages[:-1] + [bot_message_component]
    
    # Return empty string as third value to clear the input field
    return updated_messages, new_history, ""

# Tab switching callback
@app.callback(
    Output("privacy-tab-content", "style"),
    Output("quality-tab-content", "style"),
    Input("tabs", "active_tab"),
)
def switch_tab(active_tab):
    if active_tab == "tab-privacy":
        return {"display": "block"}, {"display": "none"}
    elif active_tab == "tab-quality":
        return {"display": "none"}, {"display": "block"}
    # Default case
    return {"display": "block"}, {"display": "none"}


@app.callback(
    Output("dimensions-collapse-content", "is_open"),
    [Input("dimensions-collapse-button", "n_clicks")],
    [State("dimensions-collapse-content", "is_open")],
    prevent_initial_call=True
)
def toggle_dimensions_collapse(n_clicks, is_open):
    """Toggle the collapse state of the dimensions details."""
    if n_clicks:
        return not is_open
    return is_open


@app.callback(
    Output("column-collapse-content", "is_open"),
    [Input("column-collapse-button", "n_clicks")],
    [State("column-collapse-content", "is_open")],
    prevent_initial_call=True
)
def toggle_column_collapse(n_clicks, is_open):
    """Toggle the collapse state of the column-level details."""
    if n_clicks:
        return not is_open
    return is_open


@app.callback(
    Output("constraints-collapse-content", "is_open"),
    [Input("constraints-collapse-button", "n_clicks")],
    [State("constraints-collapse-content", "is_open")],
    prevent_initial_call=True
)
def toggle_constraints_collapse(n_clicks, is_open):
    """Toggle the collapse state of the custom constraints results."""
    if n_clicks:
        return not is_open
    return is_open

# Privacy eye animation callback has been removed

# Privacy status indicator callback - activated when data is loaded
@app.callback(
    Output("privacy-status", "className"),
    Input("dataset-store", "data"),
    prevent_initial_call=True
)
def update_privacy_status(data):
    if data is None:
        return "status-indicator"
    return "status-indicator active"

# The callback for the data quality details collapse was removed as the components don't exist

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the Data Privacy Assist application')
    parser.add_argument('-p', '--port', type=int, default=9000, help='Port to run the app on')
    args = parser.parse_args()
    
    app.run_server(debug=True, port=args.port)
