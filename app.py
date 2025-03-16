import os
import base64
import json
import io
from io import StringIO
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
        "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap",
        "/assets/custom.css",          # Load our custom CSS with typing animation
        "/assets/datasharing-theme.css", # Load our DataSharingAssist theme
        "/assets/journey-flow.css"      # Load our journey flow styling
    ],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.title = "DataSharingAssist - Smart Data Sharing & Privacy Solution"
server = app.server

# Add auto-scrolling JavaScript to head
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script src="/assets/auto-scroll.js"></script>
        <script>
            document.addEventListener("DOMContentLoaded", function() {
                window.dashExtensions.autoScroll();
            });
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

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
                                        # html.H4(
                                        #     "Data Upload",
                                        #     className="mb-2 d-flex align-items-center",
                                        #     style={
                                        #         "fontFamily": "'Roboto', sans-serif",
                                        #         "color": "var(--neutral-800)",
                                        #         "paddingBottom": "5px",
                                        #         "fontWeight": "500",
                                        #         "borderBottom": "1px solid var(--neutral-300)",
                                        #     }
                                        # ),
                                        # User Journey mini-flow
                                        html.Div(
                                            [
                                                # Heading removed as requested
                                                # Steps with connecting lines
                                                html.Div(
                                                    [
                                                        # Step 1 - Upload
                                                        html.Div(
                                                            [
                                                                html.Div(
                                                                    "1",
                                                                    className="step-number active",
                                                                    id="step-1"
                                                                ),
                                                                html.Div(
                                                                    [
                                                                        html.Div("Upload Dataset", className="step-title active"),
                                                                        html.Div("Start here", className="step-description")
                                                                    ],
                                                                    className="step-text"
                                                                )
                                                            ],
                                                            className="journey-step"
                                                        ),
                                                        # Connector
                                                        html.Div(className="step-connector", id="connector-1"),
                                                        # Step 2 - Review Analysis
                                                        html.Div(
                                                            [
                                                                html.Div(
                                                                    "2",
                                                                    className="step-number inactive",
                                                                    id="step-2"
                                                                ),
                                                                html.Div(
                                                                    [
                                                                        html.Div("Review Analysis", className="step-title inactive"),
                                                                        html.Div("Privacy & quality scores", className="step-description")
                                                                    ],
                                                                    className="step-text"
                                                                )
                                                            ],
                                                            className="journey-step"
                                                        ),
                                                        # Connector
                                                        html.Div(className="step-connector", id="connector-2"),
                                                        # Step 3 - Chat
                                                        html.Div(
                                                            [
                                                                html.Div(
                                                                    "3",
                                                                    className="step-number inactive",
                                                                    id="step-3"
                                                                ),
                                                                html.Div(
                                                                    [
                                                                        html.Div("Chat with Assistant", className="step-title inactive"),
                                                                        html.Div("Get personalized guidance", className="step-description")
                                                                    ],
                                                                    className="step-text"
                                                                )
                                                            ],
                                                            className="journey-step"
                                                        ),
                                                    ],
                                                    className="d-flex justify-content-between align-items-center my-3"
                                                )
                                            ],
                                            className="journey-container"
                                        ),
                                        create_upload_component(),
                                        html.Div(id="upload-info-container")
                                    ],
                                    className="p-3 mb-3",
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
                    className="mt-1",
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
                                                            "Data Analysis",
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
                                                # User guidance message - shows when no dataset is loaded
                                                html.Div(
                                                    [
                                                        dbc.Alert(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        DashIconify(
                                                                            icon="mdi:lightbulb-on",
                                                                            width=36,
                                                                            height=36,
                                                                            className="me-3",
                                                                            color="#fb8500"  # Orange/amber for contrast
                                                                        ),
                                                                        html.Div(
                                                                            [
                                                                                html.H5("Start by uploading your dataset", className="alert-heading mb-1", style={"color": "#3a0ca3"}),
                                                                                html.P(
                                                                                    "Use the upload button above to analyze your dataset. Privacy and quality analyses will run automatically after upload.",
                                                                                    className="mb-0 small"
                                                                                )
                                                                            ],
                                                                            className="d-flex flex-column"
                                                                        )
                                                                    ],
                                                                    className="d-flex align-items-center"
                                                                )
                                                            ],
                                                            color="light",
                                                            className="border mb-4",
                                                            style={"border-left": "4px solid #fb8500 !important"},
                                                            id="upload-guidance-message"
                                                        )
                                                    ],
                                                    id="guidance-container"
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
                                                "transition": "all var(--transition-normal)",
                                                "height": "calc(100% - 1rem)"  # Subtract margin to align properly
                                            }
                                        )
                                    ],
                                    md=7,
                                    className="mb-4",
                                    style={"height": "100%"}
                                ),
                                
                                # Right Column - Chatbot
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.H4(
                                                            "Data Sharing Assistant", 
                                                            className="mb-2 privacy-recommendation-title",
                                                            style={"color": "#3a0ca3"}
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.Span(
                                                                            [
                                                                                html.Strong("Note: ", style={"color": "#92400e"}),
                                                                                "For the prototype, we limited the knowledge base to publicly available information to ensure accessibility on SEED and due to the use of the commercial OpenAI API. As a result, it does not include restricted content such as IM8 guidelines and other internal policies. Testing was conducted using sample public datasets."
                                                                            ]
                                                                        )
                                                                    ],
                                                                    className="p-2 mb-3 small",
                                                                    style={
                                                                        "backgroundColor": "#fff7ed", 
                                                                        "borderLeft": "4px solid #f59e0b",
                                                                        "borderRadius": "4px"
                                                                    }
                                                                ),
                                                                html.Span("DataSharingAssist helps you to make data-driven decision on privacy risks, improve data quality and give you recommendations enhanced with WOG privacy polcies and tools")
                                                            ],
                                                            className="text-muted mb-3 small d-flex flex-column"
                                                        )
                                                    ],
                                                    className="mb-2"
                                                ),
                                                create_chatbot_component(),
                                            ],
                                            className="p-4 chatbot-panel",
                                            style={
                                                "borderRadius": "0",
                                                "boxShadow": "none",
                                                "backgroundColor": "#FFFFFF",
                                                "border": "none",
                                                "position": "relative",
                                                "transition": "all var(--transition-normal)",
                                                "height": "calc(100% - 1rem)",  # Match height with left panel
                                                "overflowY": "hidden",  # Prevent content from overflowing
                                                "display": "flex",
                                                "flexDirection": "column"
                                            }
                                        )
                                    ],
                                    md=5,
                                    className="mb-4",
                                    style={"height": "100%"}
                                ),
                            ],
                            className="equal-height-row",
                            style={"minHeight": "600px"}
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
                                            height="100px",
                                            className="mb-2"
                                        ),
                                        html.P(
                                            "Smart Privacy for a Digital Singapore",
                                            className="text-muted small mb-1",
                                            style={"fontWeight": "500"}
                                        ),
                                        html.P(
                                            "© 2025 DataSharingAssist",
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
            className="py-2",
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
        
        # Enhanced data info with custom green theme that complements purple
        file_info = html.Div([
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("✓", 
                                    className="me-2", 
                                    style={
                                        "color": "white",
                                        "fontWeight": "bold",
                                        "backgroundColor": "#10b981",
                                        "borderRadius": "50%",
                                        "width": "22px",
                                        "height": "22px",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center",
                                        "fontSize": "14px"
                                    }),
                            html.Span("File uploaded successfully!",
                                    style={"fontWeight": "500", "color": "#064e3b"})
                        ],
                        className="d-flex align-items-center"
                    ),
                    html.Div(
                        [
                            html.Span(f"{filename}", className="me-2 small", style={"fontWeight": "500", "color": "#065f46"}),
                            html.Span(f"• {df.shape[0]} rows", className="me-2 small", style={"color": "#047857"}),
                            html.Span(f"• {df.shape[1]} columns", className="small", style={"color": "#047857"}),
                        ],
                        className="d-flex align-items-center mt-1"
                    ),
                    html.Hr(className="my-2", style={"borderColor": "#a7f3d0", "opacity": "0.5"}),
                    # Navigation guidance to improve user journey with purple accent
                    html.Div(
                        [
                            DashIconify(
                                icon="mdi:arrow-down-thin-circle-outline",
                                width=20,
                                height=20,
                                className="me-2",
                                color="#3a0ca3"
                            ),
                            html.Span(
                                "Your privacy and quality analysis is now running automatically below",
                                style={"fontWeight": "500", "color": "#3a0ca3"}
                            )
                        ],
                        className="d-flex align-items-center mt-1"
                    )
                ],
                className="mb-3 py-3 px-3",
                style={
                    "backgroundColor": "#ecfdf5",
                    "border": "1px solid #a7f3d0",
                    "borderLeft": "4px solid #10b981",
                    "borderRadius": "4px",
                    "boxShadow": "0 1px 3px rgba(0, 0, 0, 0.05)"
                }
            )
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

# Update quality-column-names-store when column data is available
@app.callback(
    Output("quality-column-names-store", "data"),
    Input("column-names-store", "data"),
    prevent_initial_call=True
)
def update_quality_column_names(column_names):
    """Update the quality column names store when the main column names store changes."""
    if column_names is None:
        raise PreventUpdate
    # Simply pass the column names to the quality store
    return column_names

# Show/hide guidance message based on dataset availability
@app.callback(
    Output("guidance-container", "style"),
    Input("dataset-store", "data"),
)
def toggle_guidance_message(dataset_json):
    """Hide guidance message when dataset is loaded."""
    if dataset_json is None:
        # Show guidance when no dataset
        return {"display": "block"}
    else:
        # Hide guidance when dataset is loaded
        return {"display": "none"}

# Update journey steps based on user progress
@app.callback(
    [Output("step-1", "className"),
     Output("step-2", "className"),
     Output("step-3", "className"),
     Output("connector-1", "className"),
     Output("connector-2", "className")],
    [Input("dataset-store", "data"),
     Input("privacy-scores-store", "data"),
     Input("data-quality-scores-store", "data"),
     Input("chat-messages", "children")]
)
def update_journey_progress(dataset, privacy_scores, quality_scores, chat_messages):
    """Update the journey steps based on user progress."""
    # Initialize with default classes
    step1_class = "step-number inactive"
    step2_class = "step-number inactive"
    step3_class = "step-number inactive"
    connector1_class = "step-connector"
    connector2_class = "step-connector"
    
    # Step 1: Always starts as active or completed
    if dataset is None:
        # User hasn't uploaded a dataset yet
        step1_class = "step-number active"
    else:
        # Dataset uploaded
        step1_class = "step-number completed"
        connector1_class = "step-connector active"
        # Move to step 2
        step2_class = "step-number active"
    
    # Step 2: Analysis completed?
    if privacy_scores is not None and quality_scores is not None:
        # Both analyses completed
        step2_class = "step-number completed"
        connector2_class = "step-connector active"
        # Move to step 3
        step3_class = "step-number active"
    
    # Step 3: Chat started?
    if chat_messages and len(chat_messages) > 2:  # More than welcome message
        step3_class = "step-number completed"
    
    return step1_class, step2_class, step3_class, connector1_class, connector2_class

# Automatically trigger analyses when dataset is uploaded
@app.callback(
    Output("run-privacy-analysis-btn", "n_clicks"),
    Output("run-quality-analysis-btn", "n_clicks"),
    Input("dataset-store", "data"),
    prevent_initial_call=True
)
def auto_trigger_analyses(dataset_json):
    """Automatically trigger both analyses when a dataset is uploaded."""
    if dataset_json is None:
        raise PreventUpdate
    # Return non-zero values to simulate button clicks
    return 1, 1

# Enable/disable report buttons based on analysis completion
@app.callback(
    Output("privacy-generate-report-btn", "disabled"),
    Output("quality-generate-report-btn", "disabled"),
    [Input("privacy-scores-store", "data"),
     Input("data-quality-scores-store", "data")],
    prevent_initial_call=True
)
def manage_report_buttons(privacy_data, quality_data):
    """Enable report buttons only when both analyses are completed."""
    # Consider analyses complete if data exists in both stores
    both_analyses_complete = privacy_data is not None and quality_data is not None
    
    # Both buttons have same state - enabled only when both analyses complete
    return not both_analyses_complete, not both_analyses_complete

# Run privacy analysis when a dataset is loaded
@app.callback(
    Output("privacy-scores-store", "data"),
    Output("privacy-results-container", "children"),
    Input("dataset-store", "data"),
    Input("run-privacy-analysis-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_privacy_analysis(json_data, n_clicks):
    print("=== PRIVACY ANALYSIS CALLBACK TRIGGERED ===")
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    if json_data is None:
        raise PreventUpdate
    
    # Parse the JSON data back to a dataframe
    from io import StringIO
    df = pd.read_json(StringIO(json_data), orient='split')
    
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
    
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    if json_data is None:
        print("Preventing update due to None inputs")
        raise PreventUpdate
    
    try:
        # Parse the JSON data back to a dataframe
        from io import StringIO
        df = pd.read_json(StringIO(json_data), orient='split')
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
    df = pd.read_json(StringIO(dataset_data), orient='split')
    
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
    df = pd.read_json(StringIO(dataset_data), orient='split')
    
    # Generate the report
    return generate_report(df, privacy_results, quality_results, report_format)

# Process chat messages
@app.callback(
    Output("chat-messages", "children"),
    Output("chat-history-store", "data"),
    Output("user-input", "value", allow_duplicate="initial_duplicate"),  # Clear the input field after sending
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
            dbc.Row(
                [
                    # Message content column
                    dbc.Col(
                        html.Div(
                            user_input,
                            className="user-message-text"
                        ),
                        className="text-end"
                    ),
                    # User avatar column (using user.png image)
                    dbc.Col(
                        html.Div(
                            html.Img(
                                src="/assets/user.png",
                                className="user-avatar",
                                style={
                                    "width": "32px",
                                    "height": "32px",
                                    "borderRadius": "50%",
                                    "objectFit": "cover",
                                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                                }
                            ),
                            style={"paddingLeft": "8px"}
                        ),
                        width="auto",
                        className="d-flex align-items-start pt-1"
                    )
                ],
                className="g-0"
            )
        ],
        className="user-message mb-3 d-flex justify-content-end"
    )
    
    # Add user message to display
    updated_messages = current_messages + [user_message_component]
    
    # Add improved typing indicator with animation
    typing_indicator = html.Div(
        [
            html.Div(
                [
                    DashIconify(icon="material-symbols:support-agent", width=24, color="#0066CC"),
                ],
                className="d-flex align-items-center me-2"
            ),
            html.Div(
                [
                    html.Div(className="typing-dot"),
                    html.Div(className="typing-dot"),
                    html.Div(className="typing-dot"),
                ],
                className="typing-indicator me-2"
            ),
            html.Div("AI thinking...", style={"fontSize": "0.85rem", "color": "rgba(0,0,0,0.7)"})
        ],
        className="chat-loading-container mb-3 d-flex align-items-center"
    )
    updated_messages = updated_messages + [typing_indicator]
    
    # Auto-scrolling is now handled through CSS and a small script in the header
    # This avoids the duplicate callback issue
    
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

# Register the custom constraints toggle callback
@app.callback(
    Output("custom-constraints-content", "is_open"),
    [Input("custom-constraints-button", "n_clicks")],
    [State("custom-constraints-content", "is_open")],
    prevent_initial_call=True
)
def toggle_custom_constraints(n_clicks, is_open):
    """Toggle the collapse state of the custom constraints section."""
    if n_clicks:
        return not is_open
    return is_open

# Register the constraint management callback
@app.callback(
    Output("custom-constraints-container", "children"),
    Output("constraints-store", "data"),
    [Input("add-constraint-btn", "n_clicks"),
     Input({"type": "remove-constraint", "index": ALL}, "n_clicks"),
     Input("quality-column-names-store", "data")],
    [State("custom-constraints-container", "children"),
     State("constraints-store", "data"),
     State({"type": "constraint-column", "index": ALL}, "value"),
     State({"type": "constraint-type", "index": ALL}, "value"),
     State({"type": "constraint-value", "index": ALL}, "value")],
    prevent_initial_call=True
)
def manage_constraints_callback(add_clicks, remove_clicks, column_names, current_rows, stored_constraints, columns, types, values):
    """Add or remove constraint rows and update the constraints store."""
    from components.data_quality import create_constraint_row
    import json
    
    # Initialize constraints if empty
    if not stored_constraints:
        stored_constraints = []
        
    # Get trigger info
    ctx_triggered = dash.callback_context.triggered[0]
    triggered_id = ctx_triggered["prop_id"].split(".")[0]
    
    # Add a new constraint
    if triggered_id == "add-constraint-btn":
        next_index = len(current_rows)
        current_rows.append(create_constraint_row(next_index, column_names))
    
    # If column names were updated, recreate all constraint rows with the new column options
    elif triggered_id == "quality-column-names-store":
        # Keep existing values if possible
        updated_rows = []
        for i, row in enumerate(current_rows):
            # Create a new row with the updated column options
            new_row = create_constraint_row(i, column_names)
            updated_rows.append(new_row)
        
        current_rows = updated_rows
    
    # Remove a constraint
    elif "remove-constraint" in triggered_id:
        # Parse the index from the triggered ID
        remove_index = json.loads(triggered_id)["index"]
        current_rows = [row for row in current_rows if json.loads(row["id"])["index"] != remove_index]
    
    # Update the stored constraints based on current values
    updated_constraints = []
    for i, (column, constraint_type, value) in enumerate(zip(columns, types, values)):
        if column:  # Only add if column is specified
            updated_constraints.append({
                "column": column,
                "type": constraint_type,
                "value": value,
            })
    
    return current_rows, updated_constraints


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

# Toggle the entropy metrics details section
@app.callback(
    Output("entropy-collapse", "is_open"),
    Input("entropy-toggle-btn", "n_clicks"),
    State("entropy-collapse", "is_open"),
)
def toggle_entropy_section(n_clicks, is_open):
    """Toggle the entropy metrics section when the button is clicked."""
    if n_clicks:
        return not is_open
    return is_open

# Toggle between simple and technical privacy views
@app.callback(
    [
        Output("view-toggle-container", "style"),
        Output("simple-privacy-container", "style"),
        Output("technical-privacy-container", "style"),
        Output("simple-view-btn", "active"),
        Output("technical-view-btn", "active"),
        Output("simple-view-btn", "outline"),
        Output("technical-view-btn", "outline"),
        Output("simple-view-btn", "style"),
        Output("technical-view-btn", "style"),
    ],
    [
        Input("privacy-scores-store", "data"),
        Input("simple-view-btn", "n_clicks"),
        Input("technical-view-btn", "n_clicks")
    ],
    [
        State("simple-view-btn", "active"),
        State("simple-view-btn", "style"),
        State("technical-view-btn", "style"),
    ]
)
def toggle_privacy_views(privacy_data, simple_clicks, tech_clicks, simple_active, simple_style, tech_style):
    """Toggle between simple and technical views of privacy analysis."""
    ctx = dash.callback_context
    toggle_visible = {"display": "block"}
    toggle_hidden = {"display": "none"}
    
    # Default styles for buttons
    active_simple_style = {
        "borderTopRightRadius": 0,
        "borderBottomRightRadius": 0,
        "backgroundColor": "#4361ee",
        "borderColor": "#4361ee"
    }
    inactive_simple_style = {
        "borderTopRightRadius": 0,
        "borderBottomRightRadius": 0,
        "borderColor": "#4361ee",
        "color": "#4361ee"
    }
    active_tech_style = {
        "borderTopLeftRadius": 0,
        "borderBottomLeftRadius": 0,
        "backgroundColor": "#4361ee",
        "borderColor": "#4361ee"
    }
    inactive_tech_style = {
        "borderTopLeftRadius": 0,
        "borderBottomLeftRadius": 0,
        "borderColor": "#4361ee",
        "color": "#4361ee"
    }
    
    # If no privacy data, hide everything
    if not privacy_data:
        return toggle_hidden, toggle_hidden, toggle_hidden, True, False, False, True, active_simple_style, inactive_tech_style
    
    # Show toggle container when there's privacy data
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    
    # Default to simple view
    if triggered_id != "technical-view-btn" and triggered_id != "simple-view-btn":
        return toggle_visible, toggle_visible, toggle_hidden, True, False, False, True, active_simple_style, inactive_tech_style
    
    # Handle button clicks to switch views
    if triggered_id == "technical-view-btn":
        return toggle_visible, toggle_hidden, toggle_visible, False, True, True, False, inactive_simple_style, active_tech_style
    else:  # simple-view-btn clicked
        return toggle_visible, toggle_visible, toggle_hidden, True, False, False, True, active_simple_style, inactive_tech_style

# Privacy visualization helper functions
def get_privacy_factors_chart(column_names, privacy_factors):
    """Create a privacy factors bar chart with the application's design theme."""
    # Sort data for better visualization
    sorted_data = sorted(zip(column_names, privacy_factors), key=lambda x: x[1], reverse=True)
    sorted_column_names, sorted_privacy_factors = zip(*sorted_data) if sorted_data else ([], [])
    
    # Create the chart with the application's purple color theme
    fig = px.bar(
        x=sorted_column_names, 
        y=sorted_privacy_factors,
        labels={
            "x": "", 
            "y": "Privacy Factor",
        },
        color_discrete_sequence=["#4361ee"],
        text=[f"{s:.2f}" for s in sorted_privacy_factors] if sorted_privacy_factors else [],
    )
    
    # Apply clean, minimal styling
    fig.update_layout(
        xaxis_tickangle=-30,
        margin=dict(l=20, r=10, t=10, b=40),  # Tight margins
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Roboto", size=11, color="#555b6e"),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
            range=[0, max(sorted_privacy_factors) * 1.1 if sorted_privacy_factors else 1],
        ),
    )
    
    # Improve text positioning and hover info
    fig.update_traces(
        marker=dict(line=dict(width=0)),
        textposition="outside",
        textfont=dict(size=10, color="#4b5563"),
        hovertemplate="<b>%{x}</b><br>Privacy Factor: <b>%{y:.2f}</b><extra></extra>"
    )
    
    return fig

def get_shannon_entropy_chart(column_names, shannon_entropy):
    """Create a shannon entropy bar chart with the application's design theme."""
    # Sort data for better visualization
    sorted_data = sorted(zip(column_names, shannon_entropy), key=lambda x: x[1], reverse=True)
    sorted_column_names, sorted_entropy = zip(*sorted_data) if sorted_data else ([], [])
    
    # Create the chart with the application's green color theme
    fig = px.bar(
        x=sorted_column_names, 
        y=sorted_entropy,
        labels={
            "x": "", 
            "y": "Shannon Entropy (bits)", 
        },
        color_discrete_sequence=["#10b981"],  # Green from the theme
        text=[f"{s:.2f}" for s in sorted_entropy] if sorted_entropy else [],
    )
    
    # Apply clean, minimal styling
    fig.update_layout(
        xaxis_tickangle=-30,
        margin=dict(l=20, r=10, t=10, b=40),  # Tight margins
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Roboto", size=11, color="#555b6e"),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
        ),
    )
    
    # Improve text positioning and hover info
    fig.update_traces(
        marker=dict(line=dict(width=0)),
        textposition="outside",
        textfont=dict(size=10, color="#4b5563"),
        hovertemplate="<b>%{x}</b><br>Shannon Entropy: <b>%{y:.2f}</b> bits<extra></extra>"
    )
    
    return fig

def get_hartley_measure_chart(column_names, hartley_measure):
    """Create a hartley measure bar chart with the application's design theme."""
    # Sort data for better visualization
    sorted_data = sorted(zip(column_names, hartley_measure), key=lambda x: x[1], reverse=True)
    sorted_column_names, sorted_hartley = zip(*sorted_data) if sorted_data else ([], [])
    
    # Create the chart with the application's purple color theme (darker shade)
    fig = px.bar(
        x=sorted_column_names, 
        y=sorted_hartley,
        labels={
            "x": "", 
            "y": "Hartley Measure (dits)", 
        },
        color_discrete_sequence=["#3a0ca3"],  # Darker purple from the theme
        text=[f"{s:.2f}" for s in sorted_hartley] if sorted_hartley else [],
    )
    
    # Apply clean, minimal styling
    fig.update_layout(
        xaxis_tickangle=-30,
        margin=dict(l=20, r=10, t=10, b=40),  # Tight margins
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Roboto", size=11, color="#555b6e"),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
        ),
    )
    
    # Improve text positioning and hover info
    fig.update_traces(
        marker=dict(line=dict(width=0)),
        textposition="outside",
        textfont=dict(size=10, color="#4b5563"),
        hovertemplate="<b>%{x}</b><br>Hartley Measure: <b>%{y:.2f}</b> dits<extra></extra>"
    )
    
    return fig

# Handle tab content in the privacy metrics tabs
@app.callback(
    Output("tab-content-privacy-metrics", "children"),
    Input("privacy-metric-tabs", "active_tab"),
    State("privacy-scores-store", "data")
)
def render_privacy_tab_content(active_tab, privacy_data):
    """Render the appropriate content for the selected privacy metrics tab."""
    if not privacy_data or not active_tab:
        return []
    
    # Handle data safely with proper error management
    try:
        # Check if data is properly structured
        if isinstance(privacy_data, str):
            import json
            privacy_data = json.loads(privacy_data)
            
        # Get data from the store - safely with error handling
        if "column_scores" not in privacy_data:
            # Fallback if data structure is different
            return html.Div("No privacy metrics data available", className="text-muted my-3")
            
        column_scores = privacy_data["column_scores"]
        column_names = list(column_scores.keys())
        
        if active_tab == "tab-privacy-factors":
            privacy_factors = [scores.get("privacy_factor", 0) for scores in column_scores.values()]
            return [
                dcc.Graph(
                    figure=get_privacy_factors_chart(column_names, privacy_factors),
                    config={"displayModeBar": False},
                    style={"height": "250px"}
                ),
                html.P(
                    "Privacy Factor measures how difficult it is to identify an individual from a specific field. Values closer to 1 indicate better privacy.",
                    className="text-muted mt-1", 
                    style={"fontSize": "0.8rem"}
                )
            ]
        
        elif active_tab == "tab-shannon":
            shannon_entropy = [scores.get("shannon_entropy", 0) for scores in column_scores.values()]
            return [
                dcc.Graph(
                    figure=get_shannon_entropy_chart(column_names, shannon_entropy),
                    config={"displayModeBar": False},
                    style={"height": "250px"}
                ),
                html.P(
                    "Shannon Entropy measures unpredictability in bits. Higher entropy values indicate more diverse distributions of values.",
                    className="text-muted mt-1", 
                    style={"fontSize": "0.8rem"}
                )
            ]
        
        elif active_tab == "tab-hartley":
            hartley_measure = [scores.get("hartley_measure", 0) for scores in column_scores.values()]
            return [
                dcc.Graph(
                    figure=get_hartley_measure_chart(column_names, hartley_measure),
                    config={"displayModeBar": False},
                    style={"height": "250px"}
                ),
                html.P(
                    "Hartley Measure (H₀) uses log base 10 to quantify information content. Higher values indicate better privacy.",
                    className="text-muted mt-1", 
                    style={"fontSize": "0.8rem"}
                )
            ]
            
        return []
    except Exception as e:
        # Provide a user-friendly error message
        return html.Div([
            html.P("Unable to display privacy metrics", className="text-danger"),
            html.P(str(e), className="small text-muted")
        ], className="p-3")
    
    return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the DataSharingAssist application')
    parser.add_argument('-p', '--port', type=int, default=3000, help='Port to run the app on')
    args = parser.parse_args()
    
    app.run_server(debug=True, port=args.port)
