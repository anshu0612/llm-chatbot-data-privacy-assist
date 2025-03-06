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
                                            height=36,
                                            className="me-2 navbar-logo"
                                        ),
                                    ],
                                    className="d-flex align-items-center navbar-logo-container"
                                ),
                                width="auto",
                                className="me-2"
                            ),
                            dbc.Col(
                                html.Div([
                                    dbc.NavbarBrand(
                                        "Data Privacy Assist", 
                                        className="ms-1 nav-brand fw-semibold",
                                        style={"color": "white"},
                                    ),
                                    html.Div(
                                        "Data-driven Privacy Guidance, Trusted Decisions.",
                                        className="ms-2 small",
                                        style={"color": "rgba(255,255,255,0.8)", "font-style": "italic", "font-size": "0.8rem"}
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
                    dbc.Row(
                        dbc.Col(
                            dbc.Nav(
                        [
                            # Commented out navigation buttons
                            html.Div([
                                # Privacy Check button
                                # dbc.NavItem(
                                #     dbc.NavLink(
                                #         [
                                #             DashIconify(
                                #                 icon="carbon:chart-evaluation",
                                #                 width=20,
                                #                 height=20,
                                #                 className="me-2"
                                #             ),
                                #             "Privacy Check",
                                #         ],
                                #         href="#privacy-check",
                                #         className="nav-link-modern",
                                #     )
                                # ),
                                # Guidelines button
                                # dbc.NavItem(
                                #     dbc.NavLink(
                                #         [
                                #             DashIconify(
                                #                 icon="carbon:policy",
                                #                 width=20,
                                #                 height=20,
                                #                 className="me-2"
                                #             ),
                                #             "Guidelines",
                                #         ],
                                #         href="#guidelines",
                                #         className="nav-link-modern",
                                #     )
                                # ),
                            ], className="d-flex align-items-center"),
                            # Help button (commented out)
                            # dbc.NavItem(
                            #     dbc.Button(
                            #         [
                            #             DashIconify(
                            #                 icon="carbon:help",
                            #                 width=18,
                            #                 height=18,
                            #                 className="me-2"
                            #             ),
                            #             "Help",
                            #         ],
                            #         color="light",
                            #         className="nav-help-button ms-3",
                            #         id="help-button",
                            #         outline=True
                            #     )
                            # ),
                        ],
                        className="ms-auto d-flex align-items-center",
                        navbar=True,
                        ),
                        width="auto",
                        className="ms-auto",
                        ),
                    ),
                    id="navbar-collapse",
                    navbar=True,
                ),
            ],
            fluid=True,
        ),
        color="primary",
        dark=True,
        className="mb-4 py-2 modern-navbar",
        style={"boxShadow": "0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 2px 6px 2px rgba(60, 64, 67, 0.15)", "backgroundColor": "var(--google-blue) !important"}
    )
