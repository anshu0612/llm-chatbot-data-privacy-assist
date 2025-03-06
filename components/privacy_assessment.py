import dash_bootstrap_components as dbc
from dash import html, dcc
from dash_iconify import DashIconify

def create_privacy_assessment_tab():
    """Create the privacy assessment tab content."""
    return html.Div(
        [
            html.Div(
                [
                    html.P(
                        "This tab analyzes privacy risks in your dataset by identifying potentially sensitive information and evaluating data anonymization levels.",
                        className="text-muted",
                    ),
                    dbc.Button(
                        "Run Privacy Analysis",
                        id="run-privacy-analysis-btn",
                        color="primary",
                        className="mt-3 run-analysis-btn",
                    ),
                ],
                className="mb-4",
            ),
            
            html.Div(id="privacy-results-container"),
            
            html.Div(
                [
                    html.H5("Generate Report", className="mb-3"),
                    html.P("Export the privacy analysis results as a report.", className="text-muted"),
                    dbc.RadioItems(
                        options=[
                            {"label": "PDF Report", "value": "pdf"},
                            {"label": "JSON Data", "value": "json"},
                        ],
                        value="pdf",
                        id="privacy-report-format-radio",
                        inline=True,
                        className="mb-3",
                    ),
                    dbc.Button(
                        "Generate Report",
                        id="privacy-generate-report-btn",
                        color="primary",
                        className="generate-report-btn",
                    ),
                    dcc.Download(id="privacy-download-report"),
                ],
                className="mt-4 pt-3 border-top",
            ),
        ],
        className="p-3",
    )
