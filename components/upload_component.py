import dash_bootstrap_components as dbc
from dash import html, dcc

def create_upload_component():
    """Create the file upload component."""
    return html.Div(
        [
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    [
                        html.Div("Drag and Drop or Select a CSV File", 
                                className="upload-text", 
                                style={"fontSize": "0.9rem", "marginBottom": "2px"}),
                        # html.Div("Supported formats: CSV, Excel", 
                        #         className="upload-hint small text-muted", 
                        #         style={"fontSize": "0.75rem"}),
                    ],
                    className="upload-area d-flex flex-column align-items-center justify-content-center",
                    style={"padding": "8px 0"},
                ),
                style={
                    "width": "100%",
                    "height": "60px",  # Reduced height
                    "borderRadius": "8px",
                    "cursor": "pointer",
                    "backgroundColor": "#F8FAFC",
                    "border": "1px solid #E2E8F0",
                },
                multiple=False,
                accept=".csv, .xls, .xlsx",
            ),
            html.Div(id="upload-status"),
            html.Div(id="upload-info-container", className="mt-2"),  # Reduced margin
        ],
        className="mb-2",  # Reduced margin
    )
