import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import re
import math
from typing import Dict, List, Any, Tuple, Optional

# Helper function for tooltips
def get_risk_level_recommendations(risk_level):
    """Return a list of recommendations based on the risk level."""
    if risk_level == "High Risk":
        return [
            html.Li("Apply data masking or tokenization to personally identifiable information", className="small"),
            html.Li("Consider aggregating or generalizing sensitive fields", className="small"),
            html.Li("Remove unique identifiers or replace with category values", className="small"),
            html.Li("Implement k-anonymity to prevent re-identification", className="small"),
            html.Li("Obtain explicit consent before sharing this dataset", className="small"),
        ]
    elif risk_level == "Medium Risk":
        return [
            html.Li("Review and transform high-risk fields to reduce identifiability", className="small"),
            html.Li("Consider data generalization techniques (e.g., age ranges instead of exact ages)", className="small"),
            html.Li("Document privacy measures taken for data sharing compliance", className="small"),
            html.Li("Implement access controls when sharing this dataset", className="small"),
        ]
    else:  # Low Risk
        return [
            html.Li("Document the privacy-preserving measures already in place", className="small"),
            html.Li("Maintain current anonymization levels in future updates", className="small"),
            html.Li("Consider periodic re-assessment if data structure changes", className="small"),
        ]

# Import the new privacy metrics module
from utils.privacy_metrics import (
    analyze_dataset_privacy,
    calculate_privacy_factor,
    calculate_shannon_entropy,
    calculate_hartley_measure,
    calculate_cumulative_privacy_factor
)

# Regular expressions for detecting sensitive data patterns
PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b',
    "credit_card": r'\b(?:\d{4}[- ]?){3}\d{4}\b',
    "singapore_nric": r'\b[STFG]\d{7}[A-Z]\b',
    "address": r'\b\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b',
    "date_of_birth": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
    "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
}

def uniqueness_score(column):
    """Calculate the uniqueness score for a column.
    A higher uniqueness score indicates higher re-identification risk."""
    if column.nunique() == 0:
        return 0
    return min(1.0, column.nunique() / len(column))

def count_pattern_matches(column, pattern):
    """Count the number of pattern matches in a column."""
    if pd.api.types.is_numeric_dtype(column):
        column = column.astype(str)
    
    matches = column.str.contains(pattern, regex=True, na=False)
    return matches.sum()

def calculate_privacy_risk(df):
    """Calculate privacy risk scores for each column in the dataframe."""
    column_scores = {}
    
    for col in df.columns:
        # Skip columns with too many missing values
        if df[col].isna().mean() > 0.5:
            column_scores[col] = {
                "privacy_risk_score": 0,
                "uniqueness_score": 0,
                "sensitive_data_score": 0,
                "sensitivity_type": "None",
                "samples": [],
            }
            continue
        
        uniqueness = uniqueness_score(df[col])
        
        # Check for sensitive data patterns
        sensitive_count = 0
        sensitivity_type = "None"
        
        for pattern_name, pattern in PATTERNS.items():
            if pd.api.types.is_string_dtype(df[col]):
                matches = count_pattern_matches(df[col], pattern)
                if matches > 0:
                    sensitive_count += matches
                    if sensitivity_type == "None":
                        sensitivity_type = pattern_name
                    else:
                        sensitivity_type += f", {pattern_name}"
        
        sensitive_data_score = min(1.0, sensitive_count / (len(df) or 1))
        
        # Calculate the overall privacy risk score (weighted average)
        privacy_risk_score = 0.7 * uniqueness + 0.3 * sensitive_data_score
        
        # Get some sample values (up to 5)
        samples = df[col].dropna().sample(min(5, len(df))).tolist() if len(df) > 0 else []
        
        column_scores[col] = {
            "privacy_risk_score": privacy_risk_score,
            "uniqueness_score": uniqueness,
            "sensitive_data_score": sensitive_data_score,
            "sensitivity_type": sensitivity_type,
            "samples": samples,
        }
    
    return column_scores

def analyze_privacy_risks(df):
    """Perform privacy risk analysis on the dataset."""
    # Calculate traditional privacy risk scores
    column_scores = calculate_privacy_risk(df)
    
    # Calculate information theory-based privacy metrics
    entropy_metrics = analyze_dataset_privacy(df)
    
    # Merge traditional and entropy-based metrics
    for col in column_scores:
        if col in entropy_metrics["column_metrics"]:
            column_scores[col]["privacy_factor"] = entropy_metrics["column_metrics"][col]["privacy_factor"]
            column_scores[col]["shannon_entropy"] = entropy_metrics["column_metrics"][col]["shannon_entropy"]
            column_scores[col]["hartley_measure"] = entropy_metrics["column_metrics"][col]["hartley_measure"]
    
    # Calculate overall dataset privacy risk score
    high_risk_columns = [col for col, scores in column_scores.items() if scores["privacy_risk_score"] > 0.7]
    medium_risk_columns = [col for col, scores in column_scores.items() if 0.3 < scores["privacy_risk_score"] <= 0.7]
    
    overall_risk = {
        "overall_privacy_score": sum([scores["privacy_risk_score"] for scores in column_scores.values()]) / len(column_scores) if column_scores else 0,
        "overall_privacy_factor": entropy_metrics["overall_privacy_factor"],
        "avg_shannon_entropy": entropy_metrics["avg_shannon_entropy"],
        "avg_hartley_measure": entropy_metrics["avg_hartley_measure"],
        "high_risk_columns": high_risk_columns,
        "medium_risk_columns": medium_risk_columns,
        "low_risk_columns": [col for col, scores in column_scores.items() if scores["privacy_risk_score"] <= 0.3],
        "total_columns": len(column_scores),
        "column_scores": column_scores,
    }
    
    # Create visualizations
    visualizations = create_privacy_visualizations(column_scores, overall_risk)
    
    return overall_risk, visualizations

def create_privacy_visualizations(column_scores, overall_risk):
    """Create visualizations for privacy risk analysis with separate simple and technical views."""
    
    # Create both simple and technical visualizations
    simple_view = create_simple_privacy_view(column_scores, overall_risk)
    technical_view = create_technical_privacy_view(column_scores, overall_risk)
    
    # Return both views in containers for the appropriate tabs
    return html.Div(
        [
            # Simple view for non-technical users
            html.Div(simple_view, id="simple-privacy-results"),
            
            # Technical view for advanced users
            html.Div(technical_view, id="technical-privacy-results"),
        ]
    )

def create_technical_privacy_view(column_scores, overall_risk):
    """Create detailed technical privacy visualizations for advanced users."""
    # Extract data for visualizations
    column_names = list(column_scores.keys())
    privacy_scores = [scores["privacy_risk_score"] for scores in column_scores.values()]
    privacy_factors = [scores.get("privacy_factor", 0) for scores in column_scores.values()]
    shannon_entropy = [scores.get("shannon_entropy", 0) for scores in column_scores.values()]
    hartley_measure = [scores.get("hartley_measure", 0) for scores in column_scores.values()]
    
    # Create technical view with entropy metrics card at the top
    return html.Div(
        [
            html.Div(
                [
                    html.P(
                        "Technical metrics provide insights into data anonymization quality using information theory concepts.",
                        className="text-muted small mb-3",
                    ),
                    
                    # Technical metrics summary cards - privacy factor and shannon entropy
                    dbc.Row(
                        [
                            # Privacy Factor card
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.Div(
                                                    [
                                                        html.H6(
                                                            "Privacy Factor",
                                                            className="mb-1",
                                                            style={"fontWeight": "500", "fontSize": "0.9rem", "color": "#3a0ca3"}
                                                        ),
                                                        html.Span(
                                                            DashIconify(
                                                                icon="mdi:information-outline",
                                                                width=14,
                                                                height=14,
                                                                style={"cursor": "help", "color": "#6b7280"}
                                                            ),
                                                            id="tech-privacy-factor-info",
                                                        ),
                                                        dbc.Tooltip(
                                                            "The Privacy Factor measures identifiability. Values closer to 1 indicate better anonymization, while values closer to 0 suggest high re-identification risk.",
                                                            target="tech-privacy-factor-info",
                                                            placement="top"
                                                        )
                                                    ],
                                                    className="d-flex justify-content-between align-items-center"
                                                ),
                                                html.Div(
                                                    f"{overall_risk['overall_privacy_factor']:.3f}",
                                                    style={"fontSize": "1.5rem", "fontWeight": "500", "color": "#4361ee", "textAlign": "center", "marginTop": "8px"}
                                                ),
                                                # Progress bar
                                                html.Div(
                                                    style={
                                                        "height": "6px",
                                                        "backgroundColor": "#e5e7eb",
                                                        "borderRadius": "3px",
                                                        "margin": "8px 0"
                                                    },
                                                    children=[
                                                        html.Div(
                                                            style={
                                                                "width": f"{overall_risk['overall_privacy_factor'] * 100}%",
                                                                "height": "100%",
                                                                "background": "linear-gradient(90deg, #4361ee 0%, #3a0ca3 100%)",
                                                                "borderRadius": "3px"
                                                            }
                                                        )
                                                    ]
                                                ),
                                                html.Div(
                                                    [
                                                        html.Div("Re-identification Risk", style={"fontSize": "0.7rem", "color": "#6b7280"}),
                                                        html.Div("Privacy Protection", style={"fontSize": "0.7rem", "color": "#6b7280"})
                                                    ],
                                                    className="d-flex justify-content-between"
                                                )
                                            ]
                                        )
                                    ],
                                    className="h-100 shadow-sm",
                                    style={"border": "none"}
                                ),
                                md=6
                            ),
                            
                            # Shannon Entropy card
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.Div(
                                                    [
                                                        html.H6(
                                                            "Shannon Entropy",
                                                            className="mb-1",
                                                            style={"fontWeight": "500", "fontSize": "0.9rem", "color": "#10b981"}
                                                        ),
                                                        html.Span(
                                                            DashIconify(
                                                                icon="mdi:information-outline",
                                                                width=14,
                                                                height=14,
                                                                style={"cursor": "help", "color": "#6b7280"}
                                                            ),
                                                            id="tech-shannon-info",
                                                        ),
                                                        dbc.Tooltip(
                                                            "Shannon Entropy quantifies data randomness in bits. Higher values indicate more diverse and unpredictable data, which generally provides better privacy.",
                                                            target="tech-shannon-info",
                                                            placement="top"
                                                        )
                                                    ],
                                                    className="d-flex justify-content-between align-items-center"
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            f"{overall_risk['avg_shannon_entropy']:.3f}",
                                                            style={"fontSize": "1.5rem", "fontWeight": "500", "color": "#10b981"}
                                                        ),
                                                        html.Span(" bits", style={"fontSize": "0.8rem", "color": "#6b7280"})
                                                    ],
                                                    className="text-center mt-2 mb-2"
                                                ),
                                                html.Div(
                                                    [
                                                        DashIconify(icon="mdi:arrow-up", width=14, height=14, color="#10b981"),
                                                        html.Span("Higher values indicate better privacy", className="ms-1 small", style={"color": "#6b7280"})
                                                    ],
                                                    className="d-flex justify-content-center align-items-center mt-2",
                                                    style={"fontSize": "0.75rem"}
                                                )
                                            ]
                                        )
                                    ],
                                    className="h-100 shadow-sm",
                                    style={"border": "none"}
                                ),
                                md=6
                            )
                        ],
                        className="mb-4"
                    ),
                    
                    # Column Risk Scores with sorted data
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                "Privacy Risk by Column", 
                                                className="mb-1",
                                                style={"fontWeight": "500", "fontSize": "0.9rem", "color": "#3a0ca3"}
                                            ),
                                            dbc.Tooltip(
                                                "Each column is assigned a risk score based on its content and uniqueness. Higher scores indicate greater privacy risk.",
                                                target="column-risk-heading",
                                                placement="top"
                                            ),
                                            html.Span(
                                                DashIconify(
                                                    icon="mdi:information-outline",
                                                    width=14,
                                                    height=14,
                                                    style={"cursor": "help", "color": "#6b7280"}
                                                ),
                                                id="column-risk-heading",
                                            ),
                                        ],
                                        className="d-flex align-items-center mb-2 justify-content-between"
                                    ),
                                    
                                    # Use the existing sorted bar chart
                                    dcc.Graph(
                                        figure=get_column_risk_chart(column_names, privacy_scores),
                                        config={"displayModeBar": False},
                                        style={"height": "270px"}
                                    )
                                ]
                            )
                        ],
                        className="mb-4 shadow-sm",
                        style={"border": "none"}
                    ),
                    
                    # Toggle for advanced entropy metrics
                    dbc.Button(
                        [
                            "Advanced Entropy Metrics",
                            DashIconify(icon="mdi:chevron-down", width=16, height=16, className="ms-1")
                        ],
                        id="entropy-toggle-btn",
                        color="link",
                        className="mb-3 p-0",
                        style={"color": "#3a0ca3", "textDecoration": "none"}
                    ),
                    
                    # Collapsible advanced metrics section
                    dbc.Collapse(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            # Column-level metrics in tabs
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(
                                                        [],
                                                        label="Privacy Factors",
                                                        tab_id="tab-privacy-factors",
                                                    ),
                                                    dbc.Tab(
                                                        [],
                                                        label="Shannon Entropy",
                                                        tab_id="tab-shannon",
                                                    ),
                                                    dbc.Tab(
                                                        [],
                                                        label="Hartley Measure",
                                                        tab_id="tab-hartley",
                                                    ),
                                                ],
                                                id="privacy-metric-tabs",
                                                active_tab="tab-privacy-factors",
                                            ),
                                            # Tab content container that will be populated by the callback
                                            html.Div(id="tab-content-privacy-metrics", className="pt-3")
                                        ]
                                    )
                                ],
                                className="shadow-sm",
                                style={"border": "none"}
                            )
                        ],
                        id="entropy-collapse",
                        is_open=False
                    )
                ],
                className="pt-2"
            ),
        ]
    )

# Helper functions for technical charts
def get_column_risk_chart(column_names, privacy_scores):
    """Create a column risk bar chart with improved aesthetics."""
    # Sort data for better visualization
    sorted_data = sorted(zip(column_names, privacy_scores), key=lambda x: x[1], reverse=True)
    sorted_column_names, sorted_privacy_scores = zip(*sorted_data)
    
    # Create risk categories after sorting
    sorted_risk_categories = []
    for score in sorted_privacy_scores:
        if score > 0.7:
            sorted_risk_categories.append("High Risk")
        elif score > 0.3:
            sorted_risk_categories.append("Medium Risk")
        else:
            sorted_risk_categories.append("Low Risk")
    
    # Enhanced color palette matching the application theme
    risk_colors = {
        "High Risk": "#EF4444",    # Red
        "Medium Risk": "#F59E0B", # Amber
        "Low Risk": "#10B981",    # Green that matches theme
    }
    
    # Create the bar chart
    fig = px.bar(
        x=sorted_column_names, 
        y=sorted_privacy_scores,
        color=sorted_risk_categories,
        color_discrete_map=risk_colors,
        labels={
            "x": "", 
            "y": "Risk Score", 
            "color": ""
        },
        text=[f"{s:.2f}" for s in sorted_privacy_scores],
    )
    
    # Clean, modern styling
    fig.update_layout(
        xaxis_tickangle=-30,
        margin=dict(l=30, r=20, t=20, b=50),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="center", 
            x=0.5,
            title=None,
            font=dict(size=11),
            borderwidth=0
        ),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Roboto", size=11, color="#555b6e"),
        xaxis=dict(
            showgrid=False,
            linecolor="#e5e7eb",
            linewidth=1,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
            gridwidth=1,
            linecolor="#e5e7eb",
            linewidth=1,
            range=[0, max(sorted_privacy_scores) * 1.2],
            tickfont=dict(size=10),
            title=dict(font=dict(size=12))
        ),
    )
    
    # Improve bar appearance and hover information
    fig.update_traces(
        marker=dict(line=dict(width=0)),
        textposition="outside",
        textfont=dict(size=10, color="#4b5563"),
        hovertemplate="<b>%{x}</b><br>Risk Score: <b>%{y:.2f}</b><br>Classification: <b>%{marker.color}</b><extra></extra>"
    )
    
    return fig

def get_privacy_factors_chart(column_names, privacy_factors):
    """Create a privacy factors bar chart."""
    # Sort data
    sorted_data = sorted(zip(column_names, privacy_factors), key=lambda x: x[1], reverse=True)
    sorted_column_names, sorted_privacy_factors = zip(*sorted_data)
    
    # Create the chart
    fig = px.bar(
        x=sorted_column_names, 
        y=sorted_privacy_factors,
        labels={
            "x": "", 
            "y": "Privacy Factor", 
        },
        color_discrete_sequence=["#4361ee"],
    )
    
    # Clean styling
    fig.update_layout(
        xaxis_tickangle=-30,
        margin=dict(l=30, r=20, t=20, b=50),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Roboto", size=11, color="#555b6e"),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
            range=[0, max(sorted_privacy_factors) * 1.2],
        ),
    )
    
    return fig

def get_shannon_entropy_chart(column_names, shannon_entropy):
    """Create a shannon entropy bar chart."""
    # Sort data
    sorted_data = sorted(zip(column_names, shannon_entropy), key=lambda x: x[1], reverse=True)
    sorted_column_names, sorted_entropy = zip(*sorted_data)
    
    # Create the chart
    fig = px.bar(
        x=sorted_column_names, 
        y=sorted_entropy,
        labels={
            "x": "", 
            "y": "Shannon Entropy (bits)", 
        },
        color_discrete_sequence=["#10b981"],
    )
    
    # Clean styling
    fig.update_layout(
        xaxis_tickangle=-30,
        margin=dict(l=30, r=20, t=20, b=50),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Roboto", size=11, color="#555b6e"),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
        ),
    )
    
    return fig

def get_hartley_measure_chart(column_names, hartley_measure):
    """Create a hartley measure bar chart."""
    # Sort data
    sorted_data = sorted(zip(column_names, hartley_measure), key=lambda x: x[1], reverse=True)
    sorted_column_names, sorted_hartley = zip(*sorted_data)
    
    # Create the chart
    fig = px.bar(
        x=sorted_column_names, 
        y=sorted_hartley,
        labels={
            "x": "", 
            "y": "Hartley Measure (dits)", 
        },
        color_discrete_sequence=["#3a0ca3"],
    )
    
    # Clean styling
    fig.update_layout(
        xaxis_tickangle=-30,
        margin=dict(l=30, r=20, t=20, b=50),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Roboto", size=11, color="#555b6e"),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
        ),
    )
    
    return fig

# Now define the simple view for non-technical users
def create_simple_privacy_view(column_scores, overall_risk):
    """Create simplified privacy visualizations for non-technical users focusing on clarity and actionability."""
    # Extract data for visualizations
    column_names = list(column_scores.keys())
    privacy_scores = [scores["privacy_risk_score"] for scores in column_scores.values()]
    
    # Get risk counts and levels
    high_risk_count = len(overall_risk["high_risk_columns"])
    medium_risk_count = len(overall_risk["medium_risk_columns"])
    low_risk_count = len(overall_risk["low_risk_columns"])
    total_columns = high_risk_count + medium_risk_count + low_risk_count
    
    # Determine overall risk level and color
    risk_level = "Low Risk"
    risk_color = "#10B981"  # Green
    risk_bg_color = "#ecfdf5"  # Light mint green
    risk_description = "Your data appears to have good privacy protection."
    risk_action = "Continue with your current anonymization approach."
    risk_icon = "mdi:shield-check"
    
    if overall_risk["overall_privacy_score"] > 0.7:
        risk_level = "High Risk"
        risk_color = "#EF4444"  # Red
        risk_bg_color = "#FEF2F2"  # Light red
        risk_description = "Your data contains sensitive information that needs protection."
        risk_action = "Apply masking or anonymization to high-risk fields before sharing."
        risk_icon = "mdi:shield-alert"
    elif overall_risk["overall_privacy_score"] > 0.3:
        risk_level = "Medium Risk"
        risk_color = "#F59E0B"  # Amber
        risk_bg_color = "#FFFBEB"  # Light amber
        risk_description = "Your data has some privacy concerns to address."
        risk_action = "Review medium-risk fields and consider privacy-enhancing techniques."
        risk_icon = "mdi:shield-half-full"
    
    return html.Div(
        [
            # User-friendly overview card
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            # Risk score overview
                            dbc.Row(
                                [
                                    # Left: Score card
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    # Risk level with icon
                                                    html.Div(
                                                        [
                                                            DashIconify(
                                                                icon=risk_icon,
                                                                width=24,
                                                                height=24,
                                                                color=risk_color,
                                                                className="me-2"
                                                            ),
                                                            html.H5(
                                                                risk_level,
                                                                style={"color": risk_color, "margin": "0", "fontWeight": "500"}
                                                            )
                                                        ],
                                                        className="d-flex align-items-center mb-2"
                                                    ),
                                                    # Large score
                                                    html.Div(
                                                        f"{overall_risk['overall_privacy_score']:.2f}",
                                                        style={
                                                            "fontSize": "2.5rem",
                                                            "fontWeight": "500",
                                                            "color": risk_color,
                                                            "lineHeight": "1",
                                                            "marginBottom": "8px"
                                                        }
                                                    ),
                                                    # Risk scale
                                                    html.Div(
                                                        style={
                                                            "height": "8px",
                                                            "backgroundColor": "#e5e7eb",
                                                            "borderRadius": "4px",
                                                            "marginBottom": "8px",
                                                            "width": "100%",
                                                            "position": "relative",
                                                            "overflow": "hidden"
                                                        },
                                                        children=[
                                                            # Green segment
                                                            html.Div(style={
                                                                "position": "absolute",
                                                                "left": "0%",
                                                                "width": "30%",
                                                                "height": "100%",
                                                                "backgroundColor": "#10b981",
                                                                "opacity": "0.7",
                                                                "borderRadius": "4px 0 0 4px"
                                                            }),
                                                            # Yellow segment
                                                            html.Div(style={
                                                                "position": "absolute",
                                                                "left": "30%",
                                                                "width": "40%",
                                                                "height": "100%",
                                                                "backgroundColor": "#f59e0b",
                                                                "opacity": "0.7"
                                                            }),
                                                            # Red segment
                                                            html.Div(style={
                                                                "position": "absolute",
                                                                "left": "70%",
                                                                "width": "30%",
                                                                "height": "100%",
                                                                "backgroundColor": "#ef4444",
                                                                "opacity": "0.7",
                                                                "borderRadius": "0 4px 4px 0"
                                                            }),
                                                            # Indicator
                                                            html.Div(style={
                                                                "position": "absolute",
                                                                "left": f"{overall_risk['overall_privacy_score'] * 100}%",
                                                                "transform": "translateX(-50%)",
                                                                "width": "12px",
                                                                "height": "12px",
                                                                "borderRadius": "50%",
                                                                "backgroundColor": risk_color,
                                                                "top": "-2px",
                                                                "border": "2px solid white"
                                                            })
                                                        ]
                                                    ),
                                                    # Scale labels
                                                    html.Div(
                                                        [
                                                            html.Span("Low", style={"fontSize": "10px", "color": "#10b981"}),
                                                            html.Span("Medium", style={"fontSize": "10px", "color": "#f59e0b"}),
                                                            html.Span("High", style={"fontSize": "10px", "color": "#ef4444"}),
                                                        ],
                                                        className="d-flex justify-content-between",
                                                        style={"fontSize": "0.7rem"}
                                                    )
                                                ],
                                                className="mb-3"
                                            )
                                        ],
                                        md=5,
                                    ),
                                    
                                    # Right: Description and actions
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    # Description
                                                    html.P(
                                                        risk_description,
                                                        className="mb-2",
                                                        style={"fontSize": "0.95rem"}
                                                    ),
                                                    # Recommended action
                                                    html.Div(
                                                        [
                                                            DashIconify(
                                                                icon="mdi:lightbulb-outline",
                                                                width=16,
                                                                height=16,
                                                                color="#10b981",
                                                                className="me-2 flex-shrink-0"
                                                            ),
                                                            html.P(
                                                                ["Recommendation: ", html.Strong(risk_action)],
                                                                className="small mb-0",
                                                            )
                                                        ],
                                                        className="d-flex align-items-start p-2 mb-3",
                                                        style={
                                                            "backgroundColor": "#ecfdf5",
                                                            "borderRadius": "4px",
                                                            "border": "1px solid rgba(16, 185, 129, 0.2)",
                                                        }
                                                    ),
                                                    # Key statistics
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    f"{high_risk_count} High Risk",
                                                                ],
                                                                className="badge bg-danger me-2"
                                                            ),
                                                            html.Div(
                                                                [
                                                                    f"{medium_risk_count} Medium Risk",
                                                                ],
                                                                className="badge bg-warning me-2"
                                                            ),
                                                            html.Div(
                                                                [
                                                                    f"{low_risk_count} Low Risk",
                                                                ],
                                                                className="badge bg-success me-2"
                                                            ),
                                                        ],
                                                        className="d-flex flex-wrap"
                                                    )
                                                ]
                                            )
                                        ],
                                        md=7
                                    )
                                ]
                            )
                        ]
                    )
                ],
                className="mb-4 shadow-sm",
                style={"border": "none"}
            ),
            
            # High risk fields section - only shown if there are high risk fields
            html.Div(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.Div(
                                    [
                                        DashIconify(
                                            icon="mdi:alert-circle",
                                            width=16,
                                            height=16,
                                            color="#ef4444",
                                            className="me-2"
                                        ),
                                        html.H6("High Risk Fields", className="mb-0", style={"fontWeight": "500"})
                                    ],
                                    className="d-flex align-items-center"
                                ),
                                style={"backgroundColor": "#FEF2F2", "color": "#b91c1c"}
                            ),
                            dbc.CardBody(
                                [
                                    html.P(
                                        "These fields contain sensitive information that could identify individuals. Consider anonymizing, masking, or omitting them when sharing data.",
                                        className="small mb-3"
                                    ),
                                    html.Div(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.Div(
                                                            [
                                                                DashIconify(
                                                                    icon="mdi:database-alert",
                                                                    width=16,
                                                                    height=16,
                                                                    color="#ef4444",
                                                                    className="me-2"
                                                                ),
                                                                html.Strong(col)
                                                            ],
                                                            className="d-flex align-items-center mb-1 p-1"
                                                        ),
                                                        md=4
                                                    )
                                                    for col in overall_risk["high_risk_columns"]
                                                ],
                                                className="g-2"
                                            )
                                            if overall_risk["high_risk_columns"] else
                                            html.Div("No high risk fields detected.", className="text-muted small")
                                        ],
                                    )
                                ]
                            )
                        ],
                        className="mb-3 shadow-sm",
                        style={"border": "none"}
                    )
                ] if high_risk_count > 0 else []
            ),
            
            # Column distribution simple chart
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.H6(
                                        "Privacy Risk Distribution",
                                        className="mb-0",
                                        style={"fontWeight": "500"}
                                    ),
                                    html.Span(
                                        DashIconify(
                                            icon="mdi:information-outline",
                                            width=14,
                                            height=14,
                                            style={"cursor": "help", "color": "#6b7280"}
                                        ),
                                        id="simple-dist-info",
                                    ),
                                    dbc.Tooltip(
                                        "This shows how privacy risk is distributed across your dataset fields. Each column is evaluated based on sensitivity and uniqueness of data.",
                                        target="simple-dist-info",
                                        placement="top"
                                    )
                                ],
                                className="d-flex justify-content-between align-items-center mb-3"
                            ),
                            
                            # Simple horizontal stacked bar
                            html.Div(
                                [
                                    # Distribution percents
                                    html.Div(
                                        [
                                            html.Div(
                                                style={
                                                    "height": "16px",
                                                    "display": "flex",
                                                    "width": "100%",
                                                    "borderRadius": "8px",
                                                    "overflow": "hidden"
                                                },
                                                children=[
                                                    # Low risk segment
                                                    html.Div(
                                                        style={
                                                            "width": f"{low_risk_count / total_columns * 100 if total_columns else 0}%",
                                                            "backgroundColor": "#10b981",
                                                            "height": "100%",
                                                            "display": "flex",
                                                            "alignItems": "center",
                                                            "justifyContent": "center"
                                                        },
                                                        children=[
                                                            html.Span(
                                                                f"{low_risk_count}" if low_risk_count / total_columns > 0.1 else "",
                                                                style={"color": "white", "fontSize": "0.7rem", "fontWeight": "bold"}
                                                            )
                                                        ] if low_risk_count > 0 else []
                                                    ),
                                                    # Medium risk segment
                                                    html.Div(
                                                        style={
                                                            "width": f"{medium_risk_count / total_columns * 100 if total_columns else 0}%",
                                                            "backgroundColor": "#f59e0b",
                                                            "height": "100%",
                                                            "display": "flex",
                                                            "alignItems": "center",
                                                            "justifyContent": "center"
                                                        },
                                                        children=[
                                                            html.Span(
                                                                f"{medium_risk_count}" if medium_risk_count / total_columns > 0.1 else "",
                                                                style={"color": "white", "fontSize": "0.7rem", "fontWeight": "bold"}
                                                            )
                                                        ] if medium_risk_count > 0 else []
                                                    ),
                                                    # High risk segment
                                                    html.Div(
                                                        style={
                                                            "width": f"{high_risk_count / total_columns * 100 if total_columns else 0}%",
                                                            "backgroundColor": "#ef4444",
                                                            "height": "100%",
                                                            "display": "flex",
                                                            "alignItems": "center",
                                                            "justifyContent": "center"
                                                        },
                                                        children=[
                                                            html.Span(
                                                                f"{high_risk_count}" if high_risk_count / total_columns > 0.1 else "",
                                                                style={"color": "white", "fontSize": "0.7rem", "fontWeight": "bold"}
                                                            )
                                                        ] if high_risk_count > 0 else []
                                                    )
                                                ]
                                            ),
                                            
                                            # Labels
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                style={
                                                                    "height": "10px",
                                                                    "width": "10px",
                                                                    "borderRadius": "2px",
                                                                    "backgroundColor": "#10b981",
                                                                    "marginRight": "4px"
                                                                }
                                                            ),
                                                            html.Span(f"Low Risk ({low_risk_count})", style={"fontSize": "0.8rem"})
                                                        ],
                                                        className="d-flex align-items-center"
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                style={
                                                                    "height": "10px",
                                                                    "width": "10px",
                                                                    "borderRadius": "2px",
                                                                    "backgroundColor": "#f59e0b",
                                                                    "marginRight": "4px"
                                                                }
                                                            ),
                                                            html.Span(f"Medium Risk ({medium_risk_count})", style={"fontSize": "0.8rem"})
                                                        ],
                                                        className="d-flex align-items-center"
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                style={
                                                                    "height": "10px",
                                                                    "width": "10px",
                                                                    "borderRadius": "2px",
                                                                    "backgroundColor": "#ef4444",
                                                                    "marginRight": "4px"
                                                                }
                                                            ),
                                                            html.Span(f"High Risk ({high_risk_count})", style={"fontSize": "0.8rem"})
                                                        ],
                                                        className="d-flex align-items-center"
                                                    )
                                                ],
                                                className="d-flex justify-content-between mt-2"
                                            ),
                                            
                                            # Total fields
                                            html.Div(
                                                [
                                                    html.Strong(f"{total_columns}", style={"color": "#3a0ca3"}),
                                                    " total fields analyzed"
                                                ],
                                                className="text-center small text-muted mt-2"
                                            )
                                        ],
                                        className="px-3 py-2"
                                    )
                                ]
                            )
                        ]
                    )
                ],
                className="shadow-sm",
                style={"border": "none"}
            )
        ],
        className="simple-view"
    )

# Remove duplicate code
def categorize_risk_score(score):
    """Return the risk category based on the score."""
    if score > 0.7:
        return "High Risk"
    elif score > 0.3:
        return "Medium Risk"
    else:
        return "Low Risk"
    
    # Use a color scheme that's more aligned with the application theme
    risk_colors = {
        "High Risk": "#EF4444",    # Red
        "Medium Risk": "#F59E0B", # Amber
        "Low Risk": "#10B981",    # Green
    }
    
    # Create a beautifully styled privacy risk score bar chart
    # Sort data for better visualization
    sorted_data = sorted(zip(column_names, privacy_scores, risk_categories), key=lambda x: x[1], reverse=True)
    sorted_column_names, sorted_privacy_scores, sorted_risk_categories = zip(*sorted_data)
    
    # Enhanced color palette that matches the application theme
    enhanced_risk_colors = {
        "High Risk": "#EF4444",    # Red
        "Medium Risk": "#F59E0B", # Amber
        "Low Risk": "#10B981",    # Green that matches theme
    }
    
    fig_privacy_scores = px.bar(
        x=sorted_column_names, 
        y=sorted_privacy_scores,
        color=sorted_risk_categories,
        color_discrete_map=enhanced_risk_colors,
        labels={
            "x": "", 
            "y": "Risk Score", 
            "color": ""
        },
        title=None,
        height=300,
        text=[f"{s:.2f}" for s in sorted_privacy_scores],
    )
    
    # Clean, modern styling for the chart
    fig_privacy_scores.update_layout(
        xaxis_tickangle=-30,
        margin=dict(l=30, r=20, t=20, b=50),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="center", 
            x=0.5,
            title=None,
            font=dict(size=11),
            borderwidth=0
        ),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#ffffff",
        font=dict(family="Roboto", size=11, color="#555b6e"),
        xaxis=dict(
            showgrid=False,
            linecolor="#e5e7eb",
            linewidth=1,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
            gridwidth=1,
            linecolor="#e5e7eb",
            linewidth=1,
            range=[0, max(sorted_privacy_scores) * 1.2],
            tickfont=dict(size=10),
            title=dict(font=dict(size=12))
        ),
        hoverlabel=dict(font=dict(family="Roboto", size=11)),
    )
    
    # Improve bar appearance and hover information
    fig_privacy_scores.update_traces(
        marker=dict(line=dict(width=0)),
        textposition="outside",
        textfont=dict(size=10, color="#4b5563"),
        hovertemplate="<b>%{x}</b><br>Risk Score: <b>%{y:.2f}</b><br>Classification: <b>%{marker.color}</b><extra></extra>"
    )
    
    # Create the privacy factor bar chart
    fig_privacy_factors = px.bar(
        x=column_names, 
        y=privacy_factors,
        labels={"x": "Column", "y": "Privacy Factor"},
        title="Column Privacy Factors (Higher is Better)",
        height=250,  # Reduced height
        color=privacy_factors,
        color_continuous_scale=["#FF4136", "#FF851B", "#2ECC40"],
        range_color=[0, 1]
    )
    fig_privacy_factors.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=50, r=20, t=40, b=80),  # Compact margins
        title_font_size=14,  # Smaller title
        coloraxis_colorbar=dict(len=0.6, thickness=10)  # Smaller colorbar
    )
    
    # Create the Shannon entropy bar chart
    fig_shannon = px.bar(
        x=column_names, 
        y=shannon_entropy,
        labels={"x": "Column", "y": "Shannon Entropy (bits)"},
        title="Column Shannon Entropy (Higher is Better)",
        height=250,  # Reduced height
        color=shannon_entropy,
        color_continuous_scale=["#FF4136", "#FF851B", "#2ECC40"],
    )
    fig_shannon.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=50, r=20, t=40, b=80),  # Compact margins
        title_font_size=14,  # Smaller title
        coloraxis_colorbar=dict(len=0.6, thickness=10)  # Smaller colorbar
    )
    
    # Create the Hartley measure bar chart
    fig_hartley = px.bar(
        x=column_names, 
        y=hartley_measure,
        labels={"x": "Column", "y": "Hartley Measure (dits)"},
        title="Column Hartley Measure (Higher is Better)",
        height=250,  # Reduced height
        color=hartley_measure,
        color_continuous_scale=["#FF4136", "#FF851B", "#2ECC40"],
    )
    fig_hartley.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=50, r=20, t=40, b=80),  # Compact margins
        title_font_size=14,  # Smaller title
        coloraxis_colorbar=dict(len=0.6, thickness=10)  # Smaller colorbar
    )
    
    # Create a compact, space-efficient column risk distribution visualization
    risk_distribution = {
        "High Risk": len(overall_risk["high_risk_columns"]),
        "Medium Risk": len(overall_risk["medium_risk_columns"]),
        "Low Risk": len(overall_risk["low_risk_columns"]),
    }
    
    # Calculate total for percentages
    total_columns = sum(risk_distribution.values())
    
    # Create a horizontal stacked bar chart - much more space efficient
    fig_risk_distribution = go.Figure()
    
    # Calculate positions for bar segments
    x_positions = [0]
    percentages = []
    colors = []
    labels = []
    hover_texts = []
    
    for i, (key, value) in enumerate(risk_distribution.items()):
        if total_columns > 0:
            percentage = value / total_columns * 100
            percentages.append(percentage)
            x_positions.append(x_positions[-1] + percentage)
            colors.append(risk_colors[key])
            labels.append(key)
            hover_texts.append(f"{key}: {value} fields ({percentage:.1f}%)")
    
    # Add the bar segments
    for i in range(len(percentages)):
        fig_risk_distribution.add_trace(go.Bar(
            x=[percentages[i]],
            y=["Fields"],
            orientation='h',
            marker=dict(
                color=colors[i],
                line=dict(width=1, color="#ffffff")
            ),
            text=f"{percentages[i]:.1f}%" if percentages[i] > 7 else "",  # Only show text if enough space
            textposition="inside",
            textfont=dict(color="white", size=10),
            hoverinfo="text",
            hovertext=hover_texts[i],
            showlegend=True,
            name=labels[i],
            legendgroup=labels[i]
        ))
    
    # Add count indicators on top of the bar for clearer reading
    for i, (key, value) in enumerate(risk_distribution.items()):
        if value > 0 and total_columns > 0:
            position = x_positions[i] + (percentages[i] / 2)
            if percentages[i] < 7:  # If too small for inside text, put it above
                fig_risk_distribution.add_annotation(
                    x=position,
                    y=1.1,  # Just above the bar
                    text=f"{value}",
                    showarrow=False,
                    font=dict(size=10, color=colors[i]),
                    xanchor="center"
                )
    
    # Extremely minimal layout to save space
    fig_risk_distribution.update_layout(
        height=70,  # Super compact height
        margin=dict(l=0, r=0, t=10, b=20),  # Minimal margins
        barmode='stack',
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.8,  # Positioned below the bar
            xanchor="center",
            x=0.5,
            font=dict(size=10),
            itemwidth=30,
            traceorder="normal"
        ),
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0, 100]  # Fix range to percentages
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False
        ),
        uniformtext=dict(mode="hide", minsize=10),
        hoverlabel=dict(font=dict(size=11))
    )
    
    # Add a highly compact total fields indicator
    fig_risk_distribution.add_annotation(
        x=-0.5,  # Left side of the bar
        y=0,
        text=f"<b>{total_columns}</b> fields",
        showarrow=False,
        font=dict(size=11, color="#555b6e"),
        xanchor="right",
        xshift=-5
    )
    
    # Create a minimalist score card instead of a gauge chart
    risk_level = "Low Risk"
    risk_color = risk_colors["Low Risk"]
    risk_description = "Your data has minimal privacy concerns."
    risk_icon = "mdi:shield-check"  # Icon for low risk
    risk_bg_color = "rgba(16, 185, 129, 0.1)"  # Light green background
    
    if overall_risk["overall_privacy_score"] > 0.7:
        risk_level = "High Risk"
        risk_color = risk_colors["High Risk"]
        risk_description = "Your data contains sensitive information that needs protection."
        risk_icon = "mdi:shield-alert"
        risk_bg_color = "rgba(239, 68, 68, 0.1)"  # Light red background
    elif overall_risk["overall_privacy_score"] > 0.3:
        risk_level = "Medium Risk"
        risk_color = risk_colors["Medium Risk"]
        risk_description = "Your data has some privacy concerns to address."
        risk_icon = "mdi:shield-half-full"
        risk_bg_color = "rgba(245, 158, 11, 0.1)"  # Light amber background
    
    # Create HTML components for a clean card layout instead of a gauge
    fig_gauge = html.Div([
        html.Div([
            # Score and level in a row
            html.Div([
                # Left side - large score
                html.Div([
                    # Score with tooltip
                    html.Div([
                        html.Div(
                            f"{overall_risk['overall_privacy_score']:.2f}",
                            style={
                                "fontSize": "36px",
                                "fontWeight": "500",
                                "color": risk_color,
                                "lineHeight": "1"
                            }
                        ),
                        dbc.Tooltip(
                            [
                                html.P(
                                    "The Overall Privacy Risk Score is calculated as the weighted average of individual column risk scores.",
                                    className="mb-2 small",
                                ),
                                html.P(
                                    "Factors that affect this score:",
                                    className="mb-1 small fw-bold",
                                ),
                                html.Ul([
                                    html.Li("Presence of personally identifiable information (PII)", className="small"),
                                    html.Li("Uniqueness and identifiability of data fields", className="small"),
                                    html.Li("Distribution and entropy of values", className="small"),
                                    html.Li("Potential for re-identification through data combination", className="small"),
                                ], className="ps-3 mb-0"),
                                html.P(
                                    ["Score ranges: ", 
                                     html.Span("0.0-0.3 (Low Risk)", style={"color": "#10b981"}), ", ",
                                     html.Span("0.3-0.7 (Medium Risk)", style={"color": "#f59e0b"}), ", ",
                                     html.Span("0.7-1.0 (High Risk)", style={"color": "#ef4444"})],
                                    className="mt-2 small",
                                )
                            ],
                            target=f"risk-score-value",
                            placement="bottom",
                            style={"maxWidth": "350px"}
                        ),
                        html.Div(
                            "Risk Score",
                            id="risk-score-value",
                            style={
                                "fontSize": "12px",
                                "color": "#6b7280",
                                "marginTop": "2px",
                                "textDecoration": "underline dotted",
                                "textDecorationThickness": "1px",
                                "cursor": "help"
                            }
                        )
                    ])
                ], style={"marginRight": "24px"}),
                
                # Right side - risk level with icon
                html.Div([
                    html.Div([
                        DashIconify(
                            icon=risk_icon,
                            width=22,
                            height=22,
                            color=risk_color,
                            style={"marginRight": "8px"}
                        ),
                        html.Span(
                            risk_level,
                            style={
                                "fontSize": "16px",
                                "fontWeight": "500",
                                "color": risk_color
                            }
                        )
                    ], style={"display": "flex", "alignItems": "center"}),
                    
                    # Description with info icon and tooltip
                    html.Div(
                        [
                            html.Div(
                                risk_description,
                                style={
                                    "fontSize": "12px",
                                    "color": "#6b7280",
                                    "marginTop": "4px",
                                    "maxWidth": "180px",
                                    "display": "inline"
                                }
                            ),
                            html.Span(
                                DashIconify(
                                    icon="mdi:information-outline",
                                    width=14,
                                    height=14,
                                    style={"marginLeft": "6px", "verticalAlign": "middle", "color": "#6b7280"}
                                ),
                                id="risk-description-info",
                                style={"cursor": "help"}
                            ),
                            dbc.Tooltip(
                                [
                                    html.P(
                                        "Recommendations based on this risk level:",
                                        className="mb-2 small fw-bold",
                                    ),
                                    html.Ul(
                                        get_risk_level_recommendations(risk_level),
                                        className="ps-3 mb-0 small"
                                    )
                                ],
                                target="risk-description-info",
                                placement="bottom",
                                style={"maxWidth": "300px"}
                            )
                        ],
                        style={"display": "flex", "alignItems": "flex-start"}
                    )
                ])
            ], style={
                "display": "flex",
                "alignItems": "flex-start",
                "justifyContent": "flex-start",
                "marginBottom": "16px"
            }),
            
            # Risk scale bar
            html.Div([
                # Scale background
                html.Div(style={
                    "height": "6px",
                    "width": "100%",
                    "backgroundColor": "#e5e7eb",
                    "borderRadius": "3px",
                    "position": "relative",
                    "overflow": "hidden"
                }, children=[
                    # Green segment
                    html.Div(style={
                        "position": "absolute",
                        "left": "0%",
                        "width": "30%",
                        "height": "100%",
                        "backgroundColor": "#10b981",
                        "opacity": "0.2",
                        "borderRadius": "3px 0 0 3px"
                    }),
                    # Amber segment
                    html.Div(style={
                        "position": "absolute",
                        "left": "30%",
                        "width": "40%",
                        "height": "100%",
                        "backgroundColor": "#f59e0b",
                        "opacity": "0.2"
                    }),
                    # Red segment
                    html.Div(style={
                        "position": "absolute",
                        "left": "70%",
                        "width": "30%",
                        "height": "100%",
                        "backgroundColor": "#ef4444",
                        "opacity": "0.2",
                        "borderRadius": "0 3px 3px 0"
                    }),
                    # Indicator
                    html.Div(style={
                        "position": "absolute",
                        "left": f"{overall_risk['overall_privacy_score'] * 100}%",
                        "transform": "translateX(-50%)",
                        "width": "10px",
                        "height": "10px",
                        "borderRadius": "50%",
                        "backgroundColor": risk_color,
                        "top": "-2px"
                    })
                ]),
                
                # Scale labels with tooltip
                html.Div([
                    html.Div(["Low ", 
                             DashIconify(icon="mdi:information-outline", width=12, height=12, style={"cursor": "help"})],
                             id="risk-scale-info",
                             style={"fontSize": "10px", "color": "#6b7280", "display": "flex", "alignItems": "center"}),
                    html.Div("Medium", style={"fontSize": "10px", "color": "#6b7280"}),
                    html.Div("High", style={"fontSize": "10px", "color": "#6b7280"}),
                    dbc.Tooltip(
                        [
                            html.P(
                                "The privacy risk scale represents how sensitive your data is and how easily individuals could be identified.",
                                className="mb-2 small",
                            ),
                            html.P([
                                html.Span("Low Risk (0.0-0.3): ", className="fw-bold", style={"color": "#10b981"}),
                                "Data is sufficiently anonymized with minimal re-identification risk."
                            ], className="mb-1 small"),
                            html.P([
                                html.Span("Medium Risk (0.3-0.7): ", className="fw-bold", style={"color": "#f59e0b"}),
                                "Some identifiable information exists, requiring additional privacy measures."
                            ], className="mb-1 small"),
                            html.P([
                                html.Span("High Risk (0.7-1.0): ", className="fw-bold", style={"color": "#ef4444"}),
                                "Contains sensitive PII or high re-identification potential."
                            ], className="mb-0 small")
                        ],
                        target="risk-scale-info",
                        placement="top",
                        style={"maxWidth": "350px"}
                    )
                ], style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "marginTop": "6px"
                })
            ], style={"marginBottom": "8px"})
        ], style={
            "padding": "16px",
            "backgroundColor": "white",
            "borderRadius": "8px",
            "height": "140px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center"
        })
    ], style={"height": "150px", "marginBottom": "16px"})
    
    # Create a gauge chart for the overall privacy factor
    fig_privacy_factor_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall_risk["overall_privacy_factor"],
        title={"text": "Cumulative Privacy Factor", "font": {"size": 14}},
        number={"suffix": "", "valueformat": ".4f", "font": {"size": 24}},  # Smaller number size
        gauge={
            "axis": {"range": [0, 1], "tickwidth": 1, "tickcolor": "darkblue", "tickfont": {"size": 10}},
            "bar": {"color": "darkblue"},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 0.3], "color": "#FF4136"},  # Low privacy factor = high risk
                {"range": [0.3, 0.7], "color": "#FF851B"},
                {"range": [0.7, 1], "color": "#2ECC40"},  # High privacy factor = low risk
            ],
        }
    ))
    fig_privacy_factor_gauge.update_layout(
        height=200,  # Reduced height
        margin=dict(l=10, r=10, t=30, b=10)  # Very compact margins
    )
    
    # Create a more user-friendly high-risk columns display
    high_risk_cards = []
    recommendations = []
    
    if overall_risk["high_risk_columns"]:
        for col in overall_risk["high_risk_columns"]:
            # Get recommendation based on sensitivity type
            sensitivity_type = column_scores[col]["sensitivity_type"]
            recommendation = ""
            action_items = []
            
            if sensitivity_type == "PII":
                recommendation = "Contains personally identifiable information (PII) that could identify individuals."
                action_items = [
                    "Consider removing this field entirely if not essential",
                    "Apply anonymization techniques like masking or tokenization",
                    "Replace with category values instead of specific identifiers"
                ]
            elif sensitivity_type == "Quasi-identifier":
                recommendation = "May not directly identify individuals but could be combined with other data for re-identification."
                action_items = [
                    "Apply generalization (reduce precision of values)",
                    "Use data binning to group values into ranges",
                    "Consider k-anonymity techniques to protect against linkage attacks"
                ]
            elif sensitivity_type == "Sensitive":
                recommendation = "Contains potentially sensitive personal information."
                action_items = [
                    "Consider differential privacy techniques",
                    "Aggregate values when possible",
                    "Obtain appropriate consent for sharing this data"
                ]
            
            # Add to recommendations list for overall guidance
            if col not in [r["column"] for r in recommendations]:
                recommendations.append({
                    "column": col,
                    "sensitivity_type": sensitivity_type,
                    "recommendation": recommendation,
                    "action_items": action_items
                })
            
            # Create a card for each high-risk column
            sample_values = [str(s) for s in column_scores[col]["samples"][:3]]
            if len(sample_values) > 0:
                sample_display = ", ".join(sample_values)
                if len(sample_display) > 50:
                    sample_display = sample_display[:47] + "..."
            else:
                sample_display = "None available"
                
            high_risk_cards.append(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.Div(
                                    [
                                        html.Strong(col, className="me-1"),
                                        dbc.Badge(
                                            sensitivity_type,
                                            color="danger",
                                            className="ms-1",
                                            style={"fontSize": "0.7rem"}
                                        ),
                                    ],
                                    className="d-flex justify-content-between align-items-center"
                                )
                            ],
                            style={"padding": "0.5rem 1rem", "backgroundColor": "rgba(239, 68, 68, 0.1)"}
                        ),
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Div("Risk Score:", className="small text-muted"),
                                        html.Div(
                                            f"{column_scores[col]['privacy_risk_score']:.2f}",
                                            className="ms-auto",
                                            style={"fontWeight": "500", "color": risk_colors['High Risk']}
                                        )
                                    ],
                                    className="d-flex justify-content-between align-items-center mb-1"
                                ),
                                html.Div(
                                    [
                                        html.Div("Sample Values:", className="small text-muted"),
                                        html.Div(
                                            sample_display,
                                            className="ms-2 small fst-italic",
                                            style={"maxWidth": "60%", "textOverflow": "ellipsis", "whiteSpace": "nowrap"}
                                        )
                                    ],
                                    className="d-flex align-items-center mt-2"
                                ),
                                html.Hr(className="my-2", style={"opacity": "0.15"}),
                                html.P(recommendation, className="small mb-0")
                            ],
                            className="py-2"
                        )
                    ],
                    className="mb-3 shadow-sm risk-card",
                    style={"borderLeft": f"3px solid {risk_colors['High Risk']}"}
                )
            )
    
    # Combine all visualizations
    return html.Div(
        [
            html.H4("Privacy Risk Analysis Results", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5("Overall Privacy Risk", className="card-title"),
                                            # Directly include the HTML component instead of using dcc.Graph
                                            fig_gauge,
                                        ]
                                    ),
                                ],
                                className="mb-4 shadow-sm",
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div([
                                                html.H5("Column Risk Distribution", className="card-title me-2"),
                                                html.Span(
                                                    DashIconify(
                                                        icon="mdi:information-outline",
                                                        width=16,
                                                        height=16,
                                                        style={"color": "#6b7280", "cursor": "help"}
                                                    ),
                                                    id="dist-info"
                                                ),
                                                dbc.Tooltip(
                                                    [
                                                        html.P(
                                                            "This chart shows the distribution of privacy risk levels across all data fields in your dataset.",
                                                            className="mb-2 small",
                                                        ),
                                                        html.P(
                                                            "Each column is evaluated based on:",
                                                            className="mb-1 small fw-bold",
                                                        ),
                                                        html.Ul([
                                                            html.Li("Sensitivity of the information", className="small"),
                                                            html.Li("Uniqueness of values", className="small"),
                                                            html.Li("Potential to identify individuals", className="small"),
                                                            html.Li("Statistical properties like entropy", className="small"),
                                                        ], className="ps-3 mb-1 small"),
                                                        html.P(
                                                            "Fields containing names, IDs, or unique identifiers typically have higher risk scores.",
                                                            className="mb-0 small",
                                                        )
                                                    ],
                                                    target="dist-info",
                                                    placement="top",
                                                    style={"maxWidth": "350px"}
                                                )
                                            ], className="d-flex align-items-center mb-2"),
                                            dcc.Graph(figure=fig_risk_distribution, config={"displayModeBar": False}),
                                        ]
                                    ),
                                ],
                                className="mb-4 shadow-sm",
                            ),
                        ],
                        md=6,
                    ),
                ]
            ),
            
            # Combine the top row cards with the high risk columns section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5("High Risk Columns", className="card-title"),
                                            html.Div([
                                                html.Div([
                                                    DashIconify(
                                                        icon="mdi:shield-alert", 
                                                        width=16, 
                                                        height=16, 
                                                        color="#EF4444" if overall_risk["high_risk_columns"] else "#10b981"
                                                    ),
                                                    html.Span(
                                                        f"Found {len(overall_risk['high_risk_columns'])} high-risk columns that may contain sensitive information." if overall_risk["high_risk_columns"] else "No high-risk columns found. Your data appears well-anonymized.",
                                                        className="ms-2 small",
                                                        style={"fontWeight": "500", "color": "#EF4444" if overall_risk["high_risk_columns"] else "#10b981"}
                                                    ),
                                                ], className="d-flex align-items-center mb-3"),
                                            ]),
                                            html.Div(
                                                high_risk_cards if high_risk_cards else html.Div(), 
                                                style={"maxHeight": "350px", "overflowY": "auto"}
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-4 shadow-sm h-100",
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5("Column Risk Scores", className="card-title"),
                                            dcc.Graph(figure=fig_privacy_scores, config={"displayModeBar": False}),
                                        ]
                                    ),
                                ],
                                className="mb-4 shadow-sm h-100",
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="equal-height-cards",
            ),
            
            # Remove the separate high risk columns section as it's now in the row above
            html.Hr(style={"margin": "1rem 0"}),
            
            # Technical metrics in a clean, collapsible card
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        DashIconify(
                                            icon="mdi:shield-lock-outline", 
                                            width=18, 
                                            height=18, 
                                            color="#4361ee",
                                            className="me-2"
                                        ),
                                        html.H6("Privacy Metrics", className="mb-0 d-inline")
                                    ],
                                    className="d-flex align-items-center"
                                ),
                                dbc.Button(
                                    [
                                        "View Technical Details",
                                        DashIconify(
                                            icon="mdi:chevron-down", 
                                            width=16, 
                                            height=16, 
                                            className="ms-1"
                                        )
                                    ],
                                    id="entropy-toggle-btn",
                                    color="link",
                                    size="sm",
                                    style={"color": "#4361ee", "textDecoration": "none", "padding": "0"},
                                )
                            ],
                            className="d-flex justify-content-between align-items-center"
                        ),
                        style={
                            "backgroundColor": "white", 
                            "border": "none", 
                            "borderBottom": "1px solid rgba(0,0,0,0.05)"
                        }
                    ),
                    dbc.Collapse(
                        [
                            dbc.CardBody(
                                [
                                    # Educational explanation
                                    html.Div(
                                        [
                                            DashIconify(
                                                icon="mdi:lightbulb-outline", 
                                                width=16, 
                                                height=16, 
                                                color="#10b981",
                                                className="me-2 flex-shrink-0"
                                            ),
                                            html.P(
                                                "Privacy metrics help quantify how well anonymized your data is. Higher values indicate better privacy protection.",
                                                className="small mb-0",
                                            )
                                        ],
                                        className="d-flex align-items-start p-2 mb-3",
                                        style={
                                            "backgroundColor": "#ecfdf5", 
                                            "borderRadius": "4px"
                                        }
                                    ),
                                    
                                    # Two key metrics in cards
                                    dbc.Row(
                                        [
                                            # Privacy Factor
                                            dbc.Col(
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                # Header with info icon
                                                                html.Div(
                                                                    [
                                                                        html.H6(
                                                                            "Privacy Factor",
                                                                            className="mb-0",
                                                                            style={
                                                                                "fontSize": "0.875rem", 
                                                                                "color": "#3a0ca3", 
                                                                                "fontWeight": "500"
                                                                            }
                                                                        ),
                                                                        html.Span(
                                                                            DashIconify(
                                                                                icon="mdi:information-outline",
                                                                                width=14,
                                                                                height=14,
                                                                                style={"cursor": "help"}
                                                                            ),
                                                                            id="privacy-factor-info"
                                                                        ),
                                                                        dbc.Tooltip(
                                                                            "The Privacy Factor measures how difficult it is to identify individuals in your dataset. Values closer to 1 indicate better anonymization and privacy protection.",
                                                                            target="privacy-factor-info",
                                                                            placement="top"
                                                                        )
                                                                    ],
                                                                    className="d-flex justify-content-between align-items-center mb-2"
                                                                ),
                                                                
                                                                # Value with visual indicator
                                                                html.Div(
                                                                    f"{overall_risk['overall_privacy_factor']:.2f}",
                                                                    style={
                                                                        "fontSize": "2rem",
                                                                        "fontWeight": "500",
                                                                        "color": "#4361ee",
                                                                        "textAlign": "center"
                                                                    }
                                                                ),
                                                                
                                                                # Progress bar
                                                                html.Div(
                                                                    style={
                                                                        "height": "8px",
                                                                        "backgroundColor": "#e5e7eb",
                                                                        "borderRadius": "4px",
                                                                        "margin": "8px 0"
                                                                    },
                                                                    children=[
                                                                        html.Div(
                                                                            style={
                                                                                "width": f"{overall_risk['overall_privacy_factor'] * 100}%",
                                                                                "height": "100%",
                                                                                "backgroundColor": "#4361ee",
                                                                                "borderRadius": "4px",
                                                                                "background": "linear-gradient(90deg, #4361ee 0%, #3a0ca3 100%)"
                                                                            }
                                                                        )
                                                                    ]
                                                                ),
                                                                
                                                                # Scale indicators
                                                                html.Div(
                                                                    [
                                                                        html.Div("Low Privacy", style={"fontSize": "0.7rem", "color": "#6b7280"}),
                                                                        html.Div("High Privacy", style={"fontSize": "0.7rem", "color": "#6b7280"})
                                                                    ],
                                                                    className="d-flex justify-content-between"
                                                                )
                                                            ]
                                                        )
                                                    ],
                                                    className="h-100 shadow-sm",
                                                    style={"border": "none"}
                                                ),
                                                md=6
                                            ),
                                            
                                            # Shannon Entropy
                                            dbc.Col(
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                # Header with info icon
                                                                html.Div(
                                                                    [
                                                                        html.H6(
                                                                            "Shannon Entropy",
                                                                            className="mb-0",
                                                                            style={
                                                                                "fontSize": "0.875rem", 
                                                                                "color": "#10b981", 
                                                                                "fontWeight": "500"
                                                                            }
                                                                        ),
                                                                        html.Span(
                                                                            DashIconify(
                                                                                icon="mdi:information-outline",
                                                                                width=14,
                                                                                height=14,
                                                                                style={"cursor": "help"}
                                                                            ),
                                                                            id="shannon-entropy-info"
                                                                        ),
                                                                        dbc.Tooltip(
                                                                            "Shannon Entropy measures information randomness in bits. Higher values indicate more diverse data where individual records are harder to predict, offering better privacy.",
                                                                            target="shannon-entropy-info",
                                                                            placement="top"
                                                                        )
                                                                    ],
                                                                    className="d-flex justify-content-between align-items-center mb-2"
                                                                ),
                                                                
                                                                # Value with unit
                                                                html.Div(
                                                                    [
                                                                        html.Span(
                                                                            f"{overall_risk['avg_shannon_entropy']:.2f}",
                                                                            style={
                                                                                "fontSize": "2rem",
                                                                                "fontWeight": "500",
                                                                                "color": "#10b981"
                                                                            }
                                                                        ),
                                                                        html.Span(
                                                                            " bits",
                                                                            style={
                                                                                "fontSize": "0.8rem",
                                                                                "color": "#6b7280",
                                                                                "marginLeft": "4px"
                                                                            }
                                                                        )
                                                                    ],
                                                                    style={"textAlign": "center"}
                                                                ),
                                                                
                                                                # Simple visual indicator
                                                                html.Div(
                                                                    [
                                                                        DashIconify(icon="mdi:arrow-up", width=14, height=14, color="#10b981"),
                                                                        html.Span("Higher is better for privacy", className="ms-1 small", style={"color": "#6b7280"})
                                                                    ],
                                                                    className="d-flex justify-content-center align-items-center mt-3",
                                                                    style={"fontSize": "0.75rem"}
                                                                )
                                                            ]
                                                        )
                                                    ],
                                                    className="h-100 shadow-sm",
                                                    style={"border": "none"}
                                                ),
                                                md=6
                                            )
                                        ],
                                        className="mb-3"
                                    )
                                ]
                            )
                        ],
                        id="entropy-collapse",
                        is_open=False
                    )
                ],
                className="mb-4 border-0"
            ),
            
            # Combine all column-level metrics into tabs to save vertical space
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5("Column-Level Privacy Metrics", className="card-title"),
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        [
                                            dcc.Graph(figure=fig_privacy_factors, config={"displayModeBar": False}),
                                            html.P(
                                                "Privacy Factor measures how difficult it is to identify an individual from a specific field. Values closer to 1 indicate better privacy.",
                                                className="text-muted mt-1", style={"fontSize": "0.8rem"}
                                            )
                                        ],
                                        label="Privacy Factors",
                                        tab_id="tab-privacy-factors",
                                    ),
                                    dbc.Tab(
                                        [
                                            dcc.Graph(figure=fig_shannon, config={"displayModeBar": False}),
                                            html.P(
                                                "Shannon Entropy measures unpredictability in bits. Higher entropy values indicate more diverse distributions of values.",
                                                className="text-muted mt-1", style={"fontSize": "0.8rem"}
                                            )
                                        ],
                                        label="Shannon Entropy",
                                        tab_id="tab-shannon",
                                    ),
                                    dbc.Tab(
                                        [
                                            dcc.Graph(figure=fig_hartley, config={"displayModeBar": False}),
                                            html.P(
                                                "Hartley Measure (H₀) uses log base 10 to quantify information content. Higher values indicate better privacy.",
                                                className="text-muted mt-1", style={"fontSize": "0.8rem"}
                                            )
                                        ],
                                        label="Hartley Measure",
                                        tab_id="tab-hartley",
                                    ),
                                ],
                                id="privacy-metric-tabs",
                                active_tab="tab-privacy-factors",
                            )
                        ],
                        className="mb-4 shadow-sm",
                    ),
                ],
                className="mt-4",
            ),
            

        ],
        className="privacy-results",
    )
