import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, dash_table, ALL, MATCH
import dash
from dash_iconify import DashIconify
import json

def create_data_quality_tab():
    """Create the data quality assessment tab content with improved visual design."""
    return html.Div(
        [
            html.Div(
                [
                    # Introduction section with friendly explanation
                    html.Div([
                        html.Div(
                            [
                                DashIconify(
                                    icon="mdi:database-check",
                                    width=28,
                                    height=28,
                                    className="me-2",
                                    color="#4361ee"
                                ),
                                html.H4("Data Quality Assessment", style={"fontWeight": "500", "color": "#3a0ca3"})
                            ],
                            className="d-flex align-items-center mb-2"
                        ),
                        html.P(
                            "Understanding your data quality is essential for making reliable decisions. We help you identify and address quality issues across multiple dimensions.",
                            className="mb-3",
                        ),
                        html.Div(
                            [
                                html.Span("✓", className="me-2", style={"color": "#10b981", "fontWeight": "bold"}),
                                "Measures data completeness, accuracy, and validity"
                            ],
                            className="d-flex align-items-center small mb-1"
                        ),
                        html.Div(
                            [
                                html.Span("✓", className="me-2", style={"color": "#10b981", "fontWeight": "bold"}),
                                "Identifies issues that could impact analysis results"
                            ],
                            className="d-flex align-items-center small mb-1"
                        ),
                        html.Div(
                            [
                                html.Span("✓", className="me-2", style={"color": "#10b981", "fontWeight": "bold"}),
                                "Provides visualization of quality metrics"
                            ],
                            className="d-flex align-items-center small mb-1"
                        ),
                    ],
                    className="bg-light p-3 rounded mb-4 border-start border-3",
                    style={"borderColor": "#4361ee"}),
                    
                    # Dimension cards with improved visual design
                    html.Div([
                        html.H5("Quality Dimensions", className="mb-3", style={"color": "#3a0ca3", "fontWeight": "500"}),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            DashIconify(
                                                icon="mdi:checkbox-marked-circle-outline",
                                                width=20,
                                                height=20,
                                                className="me-2",
                                                color="#4361ee"
                                            ),
                                            html.H6(
                                                "Completeness", 
                                                className="mb-0 d-inline", 
                                                style={"color": "#3a0ca3", "fontWeight": "500"}
                                            ),
                                            html.Span(
                                                DashIconify(
                                                    icon="mdi:information-outline",
                                                    width=16,
                                                    height=16,
                                                    style={"cursor": "help", "color": "#6b7280"},
                                                    className="ms-2"
                                                ),
                                                id="completeness-info",
                                            ),
                                        ], className="d-flex align-items-center mb-2"),
                                        dbc.Tooltip(
                                            "Completeness measures the presence of required data. Higher completeness scores indicate fewer missing values.",
                                            target="completeness-info",
                                            placement="top"
                                        ),
                                        html.P(
                                            "Measures whether your dataset has all the necessary values without missing data.",
                                            className="small text-muted mb-0"
                                        ),
                                    ])
                                ], className="h-100 shadow-sm", style={"border": "none"})
                            ], md=6, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            DashIconify(
                                                icon="mdi:target",
                                                width=20,
                                                height=20,
                                                className="me-2",
                                                color="#4361ee"
                                            ),
                                            html.H6(
                                                "Accuracy", 
                                                className="mb-0 d-inline", 
                                                style={"color": "#3a0ca3", "fontWeight": "500"}
                                            ),
                                            html.Span(
                                                DashIconify(
                                                    icon="mdi:information-outline",
                                                    width=16,
                                                    height=16,
                                                    style={"cursor": "help", "color": "#6b7280"},
                                                    className="ms-2"
                                                ),
                                                id="accuracy-info",
                                            ),
                                        ], className="d-flex align-items-center mb-2"),
                                        dbc.Tooltip(
                                            "Accuracy evaluates how well data represents the real-world values it aims to model. Higher accuracy scores indicate data closely matching reality.",
                                            target="accuracy-info",
                                            placement="top"
                                        ),
                                        html.P(
                                            "Evaluates whether data values correctly represent reality without errors.",
                                            className="small text-muted mb-0"
                                        ),
                                    ])
                                ], className="h-100 shadow-sm", style={"border": "none"})
                            ], md=6, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            DashIconify(
                                                icon="mdi:check-decagram-outline",
                                                width=20,
                                                height=20,
                                                className="me-2",
                                                color="#10b981"
                                            ),
                                            html.H6(
                                                "Validity", 
                                                className="mb-0 d-inline", 
                                                style={"color": "#3a0ca3", "fontWeight": "500"}
                                            ),
                                            html.Span(
                                                DashIconify(
                                                    icon="mdi:information-outline",
                                                    width=16,
                                                    height=16,
                                                    style={"cursor": "help", "color": "#6b7280"},
                                                    className="ms-2"
                                                ),
                                                id="validity-info",
                                            ),
                                        ], className="d-flex align-items-center mb-2"),
                                        dbc.Tooltip(
                                            "Validity checks if data conforms to required formats, ranges, and rules. A higher validity score means more data points meet expected criteria.",
                                            target="validity-info",
                                            placement="top"
                                        ),
                                        html.P(
                                            "Assesses if data values follow expected formats and business rules.",
                                            className="small text-muted mb-0"
                                        ),
                                    ])
                                ], className="h-100 shadow-sm", style={"border": "none"})
                            ], md=6, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            DashIconify(
                                                icon="mdi:fingerprint",
                                                width=20,
                                                height=20,
                                                className="me-2",
                                                color="#10b981"
                                            ),
                                            html.H6(
                                                "Uniqueness", 
                                                className="mb-0 d-inline", 
                                                style={"color": "#3a0ca3", "fontWeight": "500"}
                                            ),
                                            html.Span(
                                                DashIconify(
                                                    icon="mdi:information-outline",
                                                    width=16,
                                                    height=16,
                                                    style={"cursor": "help", "color": "#6b7280"},
                                                    className="ms-2"
                                                ),
                                                id="uniqueness-info",
                                            ),
                                        ], className="d-flex align-items-center mb-2"),
                                        dbc.Tooltip(
                                            "Uniqueness identifies unintended duplicate records. A higher uniqueness score indicates fewer problematic duplicates in your dataset.",
                                            target="uniqueness-info",
                                            placement="top"
                                        ),
                                        html.P(
                                            "Verifies data is free from unintended duplicates that could skew analysis.",
                                            className="small text-muted mb-0"
                                        ),
                                    ])
                                ], className="h-100 shadow-sm", style={"border": "none"})
                            ], md=6, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            DashIconify(
                                                icon="mdi:link",
                                                width=20,
                                                height=20,
                                                className="me-2",
                                                color="#4361ee"
                                            ),
                                            html.H6(
                                                "Integrity", 
                                                className="mb-0 d-inline", 
                                                style={"color": "#3a0ca3", "fontWeight": "500"}
                                            ),
                                            html.Span(
                                                DashIconify(
                                                    icon="mdi:information-outline",
                                                    width=16,
                                                    height=16,
                                                    style={"cursor": "help", "color": "#6b7280"},
                                                    className="ms-2"
                                                ),
                                                id="integrity-info",
                                            ),
                                        ], className="d-flex align-items-center mb-2"),
                                        dbc.Tooltip(
                                            "Integrity examines whether data maintains logical connections between related fields and tables. Higher integrity scores indicate better relationship maintenance.",
                                            target="integrity-info",
                                            placement="top"
                                        ),
                                        html.P(
                                            "Ensures data maintains consistent relationships and referential integrity.",
                                            className="small text-muted mb-0"
                                        ),
                                    ])
                                ], className="h-100 shadow-sm", style={"border": "none"})
                            ], md=6, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            DashIconify(
                                                icon="mdi:balance",
                                                width=20,
                                                height=20,
                                                className="me-2",
                                                color="#4361ee"
                                            ),
                                            html.H6(
                                                "Consistency", 
                                                className="mb-0 d-inline", 
                                                style={"color": "#3a0ca3", "fontWeight": "500"}
                                            ),
                                            html.Span(
                                                DashIconify(
                                                    icon="mdi:information-outline",
                                                    width=16,
                                                    height=16,
                                                    style={"cursor": "help", "color": "#6b7280"},
                                                    className="ms-2"
                                                ),
                                                id="consistency-info",
                                            ),
                                        ], className="d-flex align-items-center mb-2"),
                                        dbc.Tooltip(
                                            "Consistency measures how uniform data values are across your dataset. Higher consistency scores indicate fewer contradictions or variations in representation.",
                                            target="consistency-info",
                                            placement="top"
                                        ),
                                        html.P(
                                            "Evaluates if data is uniform and coherent across different systems and time periods.",
                                            className="small text-muted mb-0"
                                        ),
                                    ])
                                ], className="h-100 shadow-sm", style={"border": "none"})
                            ], md=6, className="mb-3"),
                        ]),
                    ], className="mb-4"),
                    
                    # Custom Quality Constraints Section
                    dbc.Card([
                        dbc.CardHeader(
                            html.Div(
                                [
                                    DashIconify(
                                        icon="mdi:tune-vertical",
                                        width=20,
                                        height=20,
                                        className="me-2",
                                        color="#4361ee"
                                    ),
                                    html.H6(
                                        "Custom Quality Constraints",
                                        className="mb-0 d-inline",
                                        style={"fontWeight": "500"}
                                    ),
                                    dbc.Button(
                                        DashIconify(
                                            icon="mdi:chevron-down",
                                            width=20,
                                            height=20,
                                        ),
                                        id="custom-constraints-button",
                                        color="link",
                                        className="float-end p-0",
                                        style={"color": "#3a0ca3"},
                                    )
                                ],
                                className="d-flex align-items-center justify-content-between"
                            ),
                            style={"backgroundColor": "#f8f9fa", "border": "none"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody([
                                html.Div(
                                    [
                                        DashIconify(
                                            icon="mdi:lightbulb-outline",
                                            width=18,
                                            height=18,
                                            color="#10b981",
                                            className="me-2 flex-shrink-0"
                                        ),
                                        html.P(
                                            "Custom constraints let you define specific quality rules for your data. These rules are checked during quality analysis and help you identify issues unique to your business context.",
                                            className="small mb-3",
                                        )
                                    ],
                                    className="d-flex align-items-start p-2 mb-3",
                                    style={
                                        "backgroundColor": "#ecfdf5",
                                        "borderRadius": "4px",
                                        "border": "1px solid rgba(16, 185, 129, 0.2)",
                                    }
                                ),
                                dbc.Row([
                                    dbc.Col([
                                        html.Div(id="custom-constraints-container", children=[]),
                                        dbc.Button(
                                            [
                                                DashIconify(
                                                    icon="mdi:plus",
                                                    width=16,
                                                    height=16,
                                                    className="me-1"
                                                ),
                                                "Add Constraint"
                                            ],
                                            id="add-constraint-btn",
                                            style={
                                                "background": "linear-gradient(90deg, #4361ee 0%, #3a0ca3 100%)",
                                                "border": "none"
                                            },
                                            size="sm",
                                            className="mt-2",
                                        ),
                                    ])
                                ]),
                                # Store for constraints and column names
                                dcc.Store(id="constraints-store", data=[]),
                                dcc.Store(id="quality-column-names-store", data=[])
                            ]),
                            id="custom-constraints-content",
                        ),
                    ], className="mb-3 shadow-sm", style={"border": "none"}),
                    
                    # Hidden button for callback triggering (not visible to users)
                    html.Div(
                        dbc.Button(
                            "Run Quality Analysis",
                            id="run-quality-analysis-btn",
                            style={"display": "none"}
                        ),
                        style={"display": "none"}
                    ),
                ],
                className="mb-4",
            ),
            
            # Results container with loading state
            dbc.Spinner(
                html.Div(id="quality-results-container", className="mb-4"),
                color="#4361ee",
                size="lg",
                fullscreen=False,
                spinner_style={"width": "3rem", "height": "3rem"}
            ),
            
            # Report generation section with cleaner design
            html.Div(
                [
                    html.Div(
                        [
                            DashIconify(
                                icon="mdi:file-document-outline",
                                width=20,
                                height=20,
                                className="me-2",
                                color="#3a0ca3"
                            ),
                            html.H5("Export Data Report", className="mb-0", style={"fontWeight": "500"})
                        ],
                        className="d-flex align-items-center mb-3"
                    ),
                    html.P("Share data quality insights with stakeholders or compliance teams.", className="text-muted small mb-3"),
                    dbc.RadioItems(
                        options=[
                            {"label": "PDF Report", "value": "pdf"},
                            {"label": "HTML Report", "value": "html"},
                            {"label": "JSON Data", "value": "json"},
                        ],
                        value="pdf",
                        id="quality-report-format-radio",
                        inline=True,
                        className="mb-3",
                    ),
                    dbc.Button(
                        [
                            DashIconify(
                                icon="mdi:download-outline",
                                width=18,
                                height=18,
                                className="me-2"
                            ),
                            "Download Report"
                        ],
                        id="quality-generate-report-btn",
                        style={
                            "background": "linear-gradient(90deg, #4361ee 0%, #3a0ca3 100%)",
                            "border": "none"
                        },
                        className="generate-report-btn",
                        disabled=True,  # Disabled by default
                    ),
                    dcc.Download(id="quality-download-report"),
                ],
                className="mt-4 pt-3 border-top",
            ),
        ],
        className="p-3",
    )


def create_constraint_row(index, columns=None):
    """Create a row for a custom constraint with improved styling."""
    # Create column options for dropdown
    column_options = []
    if columns is not None:
        column_options = [{'label': col, 'value': col} for col in columns]
    
    return html.Div(
        [
            dbc.Card(
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Column", 
                                        html_for=f"constraint-column-{index}",
                                        style={"color": "#4361ee", "fontWeight": "500", "fontSize": "0.85rem"}
                                    ),
                                    dbc.Select(
                                        id={"type": "constraint-column", "index": index},
                                        options=column_options,
                                        placeholder="Select column",
                                        style={"borderColor": "#e5e7eb", "borderRadius": "0.375rem"}
                                    ),
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Constraint Type", 
                                        html_for=f"constraint-type-{index}",
                                        style={"color": "#4361ee", "fontWeight": "500", "fontSize": "0.85rem"}
                                    ),
                                    dbc.Select(
                                        id={"type": "constraint-type", "index": index},
                                        options=[
                                            {"label": "Not Null", "value": "not_null"},
                                            {"label": "Unique", "value": "unique"},
                                            {"label": "Min Value", "value": "min_value"},
                                            {"label": "Max Value", "value": "max_value"},
                                            {"label": "Regex Pattern", "value": "regex"},
                                            {"label": "Value In List", "value": "value_in_list"},
                                            {"label": "Date Format", "value": "date_format"},
                                        ],
                                        value="not_null",
                                        style={"borderColor": "#e5e7eb", "borderRadius": "0.375rem"}
                                    ),
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Value", 
                                        html_for=f"constraint-value-{index}",
                                        style={"color": "#4361ee", "fontWeight": "500", "fontSize": "0.85rem"}
                                    ),
                                    dbc.Input(
                                        id={"type": "constraint-value", "index": index},
                                        type="text",
                                        placeholder="Enter constraint value if needed",
                                        style={"borderColor": "#e5e7eb", "borderRadius": "0.375rem"}
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label(" ", html_for=f"constraint-remove-{index}", style={"color": "transparent"}),
                                    dbc.Button(
                                        DashIconify(
                                            icon="mdi:close", 
                                            width=18, 
                                            height=18,
                                            color="#ef4444"
                                        ),
                                        id={"type": "remove-constraint", "index": index},
                                        color="link",
                                        size="sm",
                                        className="px-2",
                                        style={
                                            "backgroundColor": "rgba(239, 68, 68, 0.1)", 
                                            "borderRadius": "50%", 
                                            "height": "32px", 
                                            "width": "32px", 
                                            "padding": "0",
                                            "display": "flex",
                                            "alignItems": "center",
                                            "justifyContent": "center",
                                            "border": "none"
                                        }
                                    ),
                                ],
                                width=2,
                            ),
                        ],
                        className="align-items-end",
                    )
                ),
                className="mb-2 shadow-sm",
                style={"border": "none", "borderLeft": "3px solid #4361ee", "borderRadius": "0.375rem"}
            ),
        ],
        id={"type": "constraint-row", "index": index},
        className="constraint-row mb-3",
    )


# This callback needs to be registered with the app instance to work correctly
def manage_constraints(add_clicks, remove_clicks, column_names, current_rows, stored_constraints, columns, types, values):
    """Add or remove constraint rows and update the constraints store."""
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Initialize constraints if empty
    if not stored_constraints:
        stored_constraints = []
    
    # Add a new constraint
    if triggered_id == "add-constraint-btn":
        next_index = len(current_rows)
        current_rows.append(create_constraint_row(next_index, column_names))
    
    # If column names were updated, recreate all constraint rows with the new column options
    elif triggered_id == "quality-column-names-store":
        # Keep existing values if possible
        updated_rows = []
        for i, row in enumerate(current_rows):
            # Get the current values for this row if they exist
            current_column = columns[i] if i < len(columns) else None
            current_type = types[i] if i < len(types) else None
            current_value = values[i] if i < len(values) else None
            
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


# This callback needs to be registered with the app instance to work correctly
# We'll redefine this in app.py to ensure it's connected to the right application
def toggle_custom_constraints(n_clicks, is_open):
    """Toggle the collapse state of the custom constraints section."""
    if n_clicks:
        return not is_open
    return is_open
