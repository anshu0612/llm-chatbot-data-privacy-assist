import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, dash_table, ALL, MATCH
import dash
from dash_iconify import DashIconify
import json

def create_data_quality_tab():
    """Create the data quality assessment tab content with six dimensions and custom constraints."""
    return html.Div(
        [
            html.Div(
                [
                    html.P(
                        "This tab evaluates the quality of your dataset across six key dimensions: Completeness, Accuracy, Validity, Uniqueness, Integrity, and Consistency.",
                        className="text-muted",
                    ),
                    
                    # Add dimension descriptions
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.H6("Completeness", className="mb-1"),
                                    html.P("Is your data complete, with no missing values or gaps?", className="small text-muted"),
                                ], className="dimension-card p-2 mb-2")
                            ], width=6),
                            dbc.Col([
                                html.Div([
                                    html.H6("Accuracy", className="mb-1"),
                                    html.P("Does your data correctly reflect reality and is it free of errors?", className="small text-muted"),
                                ], className="dimension-card p-2 mb-2")
                            ], width=6),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.H6("Validity", className="mb-1"),
                                    html.P("Does your data conform to specified formats, ranges, and definitions?", className="small text-muted"),
                                ], className="dimension-card p-2 mb-2")
                            ], width=6),
                            dbc.Col([
                                html.Div([
                                    html.H6("Uniqueness", className="mb-1"),
                                    html.P("Is your data free from unintended duplicates?", className="small text-muted"),
                                ], className="dimension-card p-2 mb-2")
                            ], width=6),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.H6("Integrity", className="mb-1"),
                                    html.P("Can your data be consistently traced and connected across your agency?", className="small text-muted"),
                                ], className="dimension-card p-2 mb-2")
                            ], width=6),
                            dbc.Col([
                                html.Div([
                                    html.H6("Consistency", className="mb-1"),
                                    html.P("Is your data stable and coherent across different systems and time periods?", className="small text-muted"),
                                ], className="dimension-card p-2 mb-2")
                            ], width=6),
                        ]),
                    ], className="mb-3 mt-3"),
                    
                    # Custom Quality Constraints Section
                    dbc.Card([
                        dbc.CardHeader(
                            dbc.Button(
                                "Custom Quality Constraints",
                                id="custom-constraints-button",
                                color="link",
                                className="text-decoration-none w-100 text-start",
                            )
                        ),
                        dbc.Collapse(
                            dbc.CardBody([
                                html.P(
                                    "Define custom constraints to validate your data quality. These constraints will be checked during quality analysis.",
                                    className="text-muted mb-3",
                                ),
                                dbc.Row([
                                    dbc.Col([
                                        html.Div(id="custom-constraints-container", children=[]),
                                        dbc.Button(
                                            "Add Constraint",
                                            id="add-constraint-btn",
                                            color="secondary",
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
                    ], className="mb-3"),
                    
                    dbc.Button(
                        "Run Quality Analysis",
                        id="run-quality-analysis-btn",
                        color="primary",
                        className="mt-3 run-analysis-btn",
                    ),
                ],
                className="mb-4",
            ),
            
            html.Div(id="quality-results-container"),
            
            html.Div(
                [
                    html.H5("Generate Report", className="mb-3"),
                    html.P("Export the data quality analysis results as a report.", className="text-muted"),
                    dbc.RadioItems(
                        options=[
                            {"label": "PDF Report", "value": "pdf"},
                            {"label": "JSON Data", "value": "json"},
                        ],
                        value="pdf",
                        id="quality-report-format-radio",
                        inline=True,
                        className="mb-3",
                    ),
                    dbc.Button(
                        "Generate Report",
                        id="quality-generate-report-btn",
                        color="primary",
                        className="generate-report-btn",
                    ),
                    dcc.Download(id="quality-download-report"),
                ],
                className="mt-4 pt-3 border-top",
            ),
        ],
        className="p-3",
    )


def create_constraint_row(index, columns=None):
    """Create a row for a custom constraint."""
    # Create column options for dropdown
    column_options = []
    if columns is not None:
        column_options = [{'label': col, 'value': col} for col in columns]
    
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Column", html_for=f"constraint-column-{index}"),
                            dbc.Select(
                                id={"type": "constraint-column", "index": index},
                                options=column_options,
                                placeholder="Select column",
                            ),
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Constraint Type", html_for=f"constraint-type-{index}"),
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
                            ),
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Value", html_for=f"constraint-value-{index}"),
                            dbc.Input(
                                id={"type": "constraint-value", "index": index},
                                type="text",
                                placeholder="Enter constraint value if needed",
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label(" ", html_for=f"constraint-remove-{index}"),
                            dbc.Button(
                                "✕",
                                id={"type": "remove-constraint", "index": index},
                                color="danger",
                                outline=True,
                                size="sm",
                                className="w-100",
                            ),
                        ],
                        width=2,
                    ),
                ],
                className="mb-2 align-items-end",
            ),
        ],
        id={"type": "constraint-row", "index": index},
        className="constraint-row mb-3",
    )


@callback(
    Output("custom-constraints-container", "children"),
    Output("constraints-store", "data"),
    [Input("add-constraint-btn", "n_clicks"),
     Input({"type": "remove-constraint", "index": dash.ALL}, "n_clicks"),
     Input("quality-column-names-store", "data")],
    [State("custom-constraints-container", "children"),
     State("constraints-store", "data"),
     State({"type": "constraint-column", "index": dash.ALL}, "value"),
     State({"type": "constraint-type", "index": dash.ALL}, "value"),
     State({"type": "constraint-value", "index": dash.ALL}, "value")],
    prevent_initial_call=True
)
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


@callback(
    Output("custom-constraints-content", "is_open"),
    [Input("custom-constraints-button", "n_clicks")],
    [State("custom-constraints-content", "is_open")],
)
def toggle_custom_constraints(n_clicks, is_open):
    """Toggle the collapse state of the custom constraints section."""
    if n_clicks:
        return not is_open
    return is_open
