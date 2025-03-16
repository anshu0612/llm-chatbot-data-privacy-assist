import dash_bootstrap_components as dbc
from dash import html
from dash_iconify import DashIconify

def create_navbar():
    """Create the navigation bar component with a Google Material Design theme."""
    return dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(
                                # Modern logo using the logo.png image
                                html.Div(
                                    [
                                        html.Img(
                                            src="/assets/logo.png",
                                            height=50,
                                            className="me-2 navbar-logo",
                                            style={
                                                "backgroundColor": "transparent",
                                                "borderRadius": "4px"
                                            }
                                        ),
                                    ],
                                    className="d-flex align-items-center navbar-logo-container",
                                    style={"backgroundColor": "transparent"}
                                ),
                                width="auto",
                                className="me-2"
                            ),
                            dbc.Col(
                                html.Div([
                                    dbc.NavbarBrand(
                                        "DataSharingAssist", 
                                        className="ms-1 nav-brand",
                                        style={
                                            "color": "white",
                                            "fontWeight": "600",
                                            "letterSpacing": "0.5px",
                                            "fontSize": "1.4rem",
                                            "textShadow": "0 2px 4px rgba(0,0,0,0.1)"
                                        },
                                    ),
                                    html.Div(
                                        "Data-obsessed, AI assessed. Making Data Sharing Stress-Free to Foster Openness and Progress",
                                        className="ms-2",
                                        style={
                                            "color": "rgba(255,255,255,0.9)",
                                            "fontSize": "0.82rem",
                                            "letterSpacing": "0.2px",
                                            "fontWeight": "400",
                                            "marginTop": "1px",
                                            "background": "linear-gradient(90deg, rgba(255,255,255,0.95), rgba(255,255,255,0.8))",
                                            "WebkitBackgroundClip": "text",
                                            "WebkitTextFillColor": "transparent"
                                        }
                                    )
                                ], className="d-flex flex-column")
                            ),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="/",
                    style={"textDecoration": "none"},
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                dbc.Collapse(
                    dbc.Nav(
                        [
                            # Spacer that pushes the following items to the right
                            dbc.NavItem(className="me-auto"),
                        
                            # Right-side navbar buttons with icons
                            html.Div([
                                # Guide button
                                dbc.Button(
                                    DashIconify(
                                        icon="mdi:book-open-variant",
                                        width=20,
                                        height=20,
                                        color="white"
                                    ),
                                    color="link",
                                    className="nav-icon-button mx-1",
                                    id="guide-button",
                                    style={
                                        "backgroundColor": "rgba(255,255,255,0.1)", 
                                        "borderRadius": "6px",
                                        "border": "none",
                                        "padding": "6px",
                                        "transition": "all 0.2s ease"
                                    }
                                ),
                                # Notifications button with badge
                                dbc.Button(
                                    [
                                        DashIconify(
                                            icon="mdi:bell-outline",
                                            width=20,
                                            height=20,
                                            color="white"
                                        ),
                                        html.Span(
                                            "3",
                                            className="position-absolute top-0 start-100 translate-middle badge rounded-pill",
                                            style={
                                                "backgroundColor": "#fb8500",
                                                "fontSize": "0.6rem",
                                                "transform": "translate(-50%, -25%)"
                                            }
                                        )
                                    ],
                                    color="link",
                                    className="nav-icon-button mx-1 position-relative",
                                    id="notifications-button",
                                    style={
                                        "backgroundColor": "rgba(255,255,255,0.1)", 
                                        "borderRadius": "6px",
                                        "border": "none",
                                        "padding": "6px",
                                        "transition": "all 0.2s ease"
                                    }
                                ),
                                # Collaboration button
                                dbc.Button(
                                    DashIconify(
                                        icon="mdi:account-group-outline",
                                        width=20,
                                        height=20,
                                        color="white"
                                    ),
                                    color="link",
                                    className="nav-icon-button mx-1",
                                    id="collab-button",
                                    style={
                                        "backgroundColor": "rgba(255,255,255,0.1)", 
                                        "borderRadius": "6px",
                                        "border": "none",
                                        "padding": "6px",
                                        "transition": "all 0.2s ease"
                                    }
                                ),
                                # Divider
                                html.Div(
                                    className="mx-2",
                                    style={
                                        "width": "1px",
                                        "height": "24px",
                                        "backgroundColor": "rgba(255,255,255,0.2)"
                                    }
                                ),
                                # User profile button
                                dbc.Button(
                                    [
                                        html.Div(
                                            "A",
                                            style={
                                                "backgroundColor": "#4361ee",
                                                "color": "white",
                                                "width": "28px",
                                                "height": "28px",
                                                "borderRadius": "50%",
                                                "display": "flex",
                                                "alignItems": "center",
                                                "justifyContent": "center",
                                                "fontSize": "0.75rem",
                                                "fontWeight": "500",
                                                "marginRight": "8px"
                                            }
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    "Anshu",
                                                    style={"color": "white", "fontSize": "0.85rem", "fontWeight": "500", "lineHeight": "1.1"}
                                                ),
                                                html.Div(
                                                    "singh_anshu@tech.gov.sg",
                                                    style={"color": "rgba(255,255,255,0.7)", "fontSize": "0.7rem", "lineHeight": "1.1"}
                                                )
                                            ],
                                            className="d-none d-md-block"
                                        )
                                    ],
                                    color="link",
                                    className="d-flex align-items-center nav-user-button",
                                    id="user-button",
                                    style={
                                        "backgroundColor": "rgba(255,255,255,0.1)", 
                                        "borderRadius": "6px",
                                        "border": "none",
                                        "padding": "4px 12px 4px 4px",
                                        "transition": "all 0.2s ease"
                                    }
                                )
                            ], className="d-flex align-items-center"),
                        ],
                        className="ms-auto d-flex align-items-center",
                        navbar=True,
                    ),
                    id="navbar-collapse",
                    navbar=True,
                ),
            ],
            fluid=True,
        ),
        dark=True,
        className="mb-4 py-2 modern-navbar",
        style={
            "background": "linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%)",
            "boxShadow": "0 2px 10px rgba(58, 12, 163, 0.2)"
        }
    )
