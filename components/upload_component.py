import dash_bootstrap_components as dbc
from dash import html, dcc
from dash_iconify import DashIconify

def create_upload_component():
    """Create the file upload component."""
    return html.Div(
        [
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    [
                        html.Div([
                            DashIconify(
                                icon="mdi:cloud-upload-outline",
                                width=24,
                                height=24,
                                color="#4361ee",
                                className="me-2"
                            ),
                            "Drag and Drop or Select a CSV File"
                        ], 
                        className="upload-text d-flex align-items-center justify-content-center", 
                        style={
                            "fontSize": "0.95rem", 
                            "fontWeight": "500",
                            "color": "#3a0ca3",
                        }),
                        html.Div("Supported formats: CSV", 
                              className="upload-hint small text-muted", 
                              style={"fontSize": "0.75rem", "marginTop": "4px"}),
                    ],
                    className="upload-area d-flex flex-column align-items-center justify-content-center",
                    style={"padding": "10px 0"},
                ),
                style={
                    "width": "100%",
                    "height": "90px",
                    "borderRadius": "10px",
                    "cursor": "pointer",
                    "background": "linear-gradient(145deg, #f8f9ff 0%, #f0f4ff 100%)",
                    "border": "1px dashed rgba(67, 97, 238, 0.4)",
                    "boxShadow": "0 2px 6px rgba(67, 97, 238, 0.05)",
                    "transition": "all 0.2s ease",
                    "hoverBorderColor": "#3a0ca3",
                    "hoverBoxShadow": "0 4px 12px rgba(67, 97, 238, 0.1)",
                },
                multiple=False,
                accept=".csv, .xls, .xlsx",
            ),
            html.Div(id="upload-status"),
            html.Div(id="upload-info-container", className="mt-2"),  # Reduced margin
        ],
        className="mb-2",  # Reduced margin
    )
