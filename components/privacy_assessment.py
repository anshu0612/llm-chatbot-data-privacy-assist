import dash_bootstrap_components as dbc
from dash import html, dcc
from dash_iconify import DashIconify

def create_privacy_assessment_tab():
    """Create the privacy assessment tab content with segmented views for technical and non-technical users."""
    return html.Div(
        [
            html.Div(
                [
                    # Introduction with friendly explanation
                    html.Div([
                        html.Div(
                            [
                                DashIconify(
                                    icon="mdi:shield-lock-outline",
                                    width=28,
                                    height=28,
                                    className="me-2",
                                    color="#4361ee"
                                ),
                                html.H4("Privacy Risk Assessment", style={"fontWeight": "500", "color": "#3a0ca3"})
                            ],
                            className="d-flex align-items-center mb-2"
                        ),
                        html.P(
                            "We understand sharing data can be concerning. Our privacy assessment helps you understand what sensitive information exists in your dataset and provides clear guidance on sharing it safely.",
                            className="mb-2",
                        ),
                        html.Div(
                            [
                                html.Span("✓", className="me-2", style={"color": "#10b981", "fontWeight": "bold"}),
                                "Detects sensitive fields and privacy vulnerabilities",
                            ],
                            className="d-flex align-items-center small mb-1"
                        ),
                        html.Div(
                            [
                                html.Span("✓", className="me-2", style={"color": "#10b981", "fontWeight": "bold"}),
                                "Calculates re-identification risk with simple and technical views",
                            ],
                            className="d-flex align-items-center small mb-1"
                        ),
                        html.Div(
                            [
                                html.Span("✓", className="me-2", style={"color": "#10b981", "fontWeight": "bold"}),
                                "Suggests specific actions tailored to your data",
                            ],
                            className="d-flex align-items-center small mb-1"
                        ),
                    ],
                    className="bg-light p-3 rounded mb-4 border-start border-3",
                    style={"borderColor": "#4361ee"}),
                    
                    # Hidden button for callback triggering only
                    html.Div(
                        dbc.Button(
                            "Run Privacy Analysis",
                            id="run-privacy-analysis-btn",
                            style={"display": "none"}
                        ), 
                        style={"display": "none"}
                    ),
                ],
                className="mb-2",
            ),
            
            # Results Container with segmented views
            html.Div(
                [
                    # Results will be loaded here, but with view mode toggle
                    html.Div(
                        [
                            # View mode toggle (to be shown after analysis runs)
                            html.Div(
                                [
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                [
                                                    DashIconify(
                                                        icon="mdi:account-outline", 
                                                        width=16, 
                                                        height=16, 
                                                        className="me-1"
                                                    ),
                                                    "Simple View"
                                                ],
                                                id="simple-view-btn",
                                                color="primary",
                                                outline=False,
                                                active=True,
                                                style={
                                                    "borderTopRightRadius": 0,
                                                    "borderBottomRightRadius": 0,
                                                    "backgroundColor": "#4361ee",
                                                    "borderColor": "#4361ee"
                                                }
                                            ),
                                            dbc.Button(
                                                [
                                                    DashIconify(
                                                        icon="mdi:tools", 
                                                        width=16, 
                                                        height=16, 
                                                        className="me-1"
                                                    ),
                                                    "Technical View"
                                                ],
                                                id="technical-view-btn",
                                                color="primary",
                                                outline=True,
                                                active=False,
                                                style={
                                                    "borderTopLeftRadius": 0,
                                                    "borderBottomLeftRadius": 0,
                                                    "borderColor": "#4361ee",
                                                    "color": "#4361ee"
                                                }
                                            ),
                                        ],
                                        id="view-mode-toggle",
                                        className="mb-3"
                                    ),
                                ],
                                id="view-toggle-container",
                                style={"display": "none"}
                            ),
                            
                            # Non-technical view container
                            html.Div(
                                id="simple-privacy-container",
                                className="simple-view-container"
                            ),
                            
                            # Technical view container (initially hidden)
                            html.Div(
                                id="technical-privacy-container",
                                className="technical-view-container",
                                style={"display": "none"}
                            )
                        ]
                    )
                ],
                id="privacy-results-container"
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
                    html.P("Share this report with stakeholders or compliance teams.", className="text-muted small mb-3"),
                    dbc.RadioItems(
                        options=[
                            {"label": "PDF Report", "value": "pdf"},
                            {"label": "HTML Report", "value": "html"},
                            {"label": "JSON Data", "value": "json"},
                        ],
                        value="pdf",
                        id="privacy-report-format-radio",
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
                        id="privacy-generate-report-btn",
                        color="primary",
                        className="generate-report-btn",
                        disabled=True,  # Disabled by default
                        style={"backgroundColor": "#4361ee", "borderColor": "#4361ee"}
                    ),
                    dcc.Download(id="privacy-download-report"),
                ],
                className="mt-4 pt-3 border-top",
            ),
        ],
        className="p-3",
    )
