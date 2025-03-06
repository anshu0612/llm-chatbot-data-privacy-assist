import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
import re
import math
from typing import Dict, List, Any, Tuple, Optional

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
    """Create visualizations for privacy risk analysis."""
    # Create a bar chart of privacy risk scores
    column_names = list(column_scores.keys())
    privacy_scores = [scores["privacy_risk_score"] for scores in column_scores.values()]
    privacy_factors = [scores.get("privacy_factor", 0) for scores in column_scores.values()]
    shannon_entropy = [scores.get("shannon_entropy", 0) for scores in column_scores.values()]
    hartley_measure = [scores.get("hartley_measure", 0) for scores in column_scores.values()]
    
    risk_categories = []
    for score in privacy_scores:
        if score > 0.7:
            risk_categories.append("High Risk")
        elif score > 0.3:
            risk_categories.append("Medium Risk")
        else:
            risk_categories.append("Low Risk")
    
    risk_colors = {
        "High Risk": "#FF4136",
        "Medium Risk": "#FF851B",
        "Low Risk": "#2ECC40",
    }
    
    # Create the privacy risk score bar chart
    fig_privacy_scores = px.bar(
        x=column_names, 
        y=privacy_scores,
        color=risk_categories,
        color_discrete_map=risk_colors,
        labels={"x": "Column", "y": "Privacy Risk Score", "color": "Risk Level"},
        title="Column Privacy Risk Scores",
        height=250,  # Reduced height
    )
    fig_privacy_scores.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=50, r=20, t=40, b=80),  # Compact margins
        title_font_size=14,  # Smaller title
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)  # Horizontal legend on top
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
    
    # Create a pie chart for risk distribution
    risk_distribution = {
        "High Risk": len(overall_risk["high_risk_columns"]),
        "Medium Risk": len(overall_risk["medium_risk_columns"]),
        "Low Risk": len(overall_risk["low_risk_columns"]),
    }
    
    fig_risk_distribution = px.pie(
        values=list(risk_distribution.values()),
        names=list(risk_distribution.keys()),
        color=list(risk_distribution.keys()),
        color_discrete_map=risk_colors,
        title="Column Risk Distribution",
        hole=0.4,
    )
    fig_risk_distribution.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),  # Very compact margins
        title_font_size=14,  # Smaller title
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)  # Horizontal legend below
    )
    
    # Create a gauge chart for overall privacy risk
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall_risk["overall_privacy_score"],
        title={"text": "Overall Privacy Risk Score", "font": {"size": 14}},
        number={"font": {"size": 24}},  # Smaller number size
        gauge={
            "axis": {"range": [0, 1], "tickwidth": 1, "tickcolor": "darkblue", "tickfont": {"size": 10}},
            "bar": {"color": "darkblue"},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 0.3], "color": "#2ECC40"},
                {"range": [0.3, 0.7], "color": "#FF851B"},
                {"range": [0.7, 1], "color": "#FF4136"},
            ],
        }
    ))
    fig_gauge.update_layout(
        height=200,  # Reduced height
        margin=dict(l=10, r=10, t=30, b=10)  # Very compact margins
    )
    
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
    
    # Create the high-risk columns table
    high_risk_table = None
    if overall_risk["high_risk_columns"]:
        high_risk_data = []
        for col in overall_risk["high_risk_columns"]:
            high_risk_data.append(
                {
                    "Column": col,
                    "Risk Score": f"{column_scores[col]['privacy_risk_score']:.2f}",
                    "Sensitivity Type": column_scores[col]["sensitivity_type"],
                    "Sample Values": ", ".join([str(s) for s in column_scores[col]["samples"][:3]]),
                }
            )
        
        high_risk_table = dbc.Table.from_dataframe(
            pd.DataFrame(high_risk_data),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="mt-3",
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
                                            html.Div(
                                                [
                                                    dcc.Graph(figure=fig_gauge, config={"displayModeBar": False}),
                                                ],
                                                className="d-flex justify-content-center"
                                            ),
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
                                            html.H5("Column Risk Distribution", className="card-title"),
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
                                            html.P(
                                                f"Found {len(overall_risk['high_risk_columns'])} high-risk columns that may contain sensitive information.",
                                                className="text-danger small",
                                            ) if overall_risk["high_risk_columns"] else html.P("No high-risk columns found.", className="text-success small"),
                                            high_risk_table if high_risk_table is not None else html.Div(),
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
            
            html.Div(
                [
                    html.H5("Information Entropy Metrics", className="mb-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H5("Cumulative Privacy Factor", className="card-title"),
                                                    html.Div(
                                                        [
                                                            dcc.Graph(figure=fig_privacy_factor_gauge, config={"displayModeBar": False}),
                                                        ],
                                                        className="d-flex justify-content-center"
                                                    ),
                                                    html.P(
                                                        "The Cumulative Privacy Factor measures overall dataset anonymity. Values close to 1 indicate better privacy, while values close to 0 indicate higher re-identification risk.",
                                                        className="text-muted mt-2", style={"fontSize": "0.85rem"}
                                                    )
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
                                                    html.H5("Information Entropy Measures", className="card-title"),
                                                    html.Div(
                                                        [
                                                            dbc.Row([
                                                                dbc.Col([
                                                                    html.Div(
                                                                        [
                                                                            html.Span(f"{overall_risk['avg_shannon_entropy']:.2f}", 
                                                                                    style={"fontSize": "2rem", "fontWeight": "bold", "color": "#0066CC"}),
                                                                            html.Span(" bits", style={"fontSize": "1rem", "color": "#666"})
                                                                        ],
                                                                        className="text-center mb-1"
                                                                    ),
                                                                    html.Div("Shannon Entropy", className="text-center small text-muted")
                                                                ], md=6),
                                                                dbc.Col([
                                                                    html.Div(
                                                                        [
                                                                            html.Span(f"{overall_risk['avg_hartley_measure']:.2f}", 
                                                                                    style={"fontSize": "2rem", "fontWeight": "bold", "color": "#0066CC"}),
                                                                            html.Span(" dits", style={"fontSize": "1rem", "color": "#666"})
                                                                        ],
                                                                        className="text-center mb-1"
                                                                    ),
                                                                    html.Div("Hartley Measure", className="text-center small text-muted")
                                                                ], md=6),
                                                            ]),
                                                        ],
                                                        className="d-flex justify-content-center my-3"
                                                    ),
                                                    html.P(
                                                        "These entropy measures quantify information unpredictability. Shannon entropy uses log base 2 (bits), while Hartley measure uses log base 10 (decimal digits). Higher values indicate better privacy protection.",
                                                        className="text-muted mt-2", style={"fontSize": "0.85rem"}
                                                    )
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
                                ]
                            ),
                        ],
                        className="mb-4 shadow-sm",
                    ),
                ],
                className="mt-4",
            ),
            
            # More compact summary section
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5("Privacy Risk Summary", className="card-title"),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Strong(f"{overall_risk['overall_privacy_score']:.2f}", className="text-primary", style={"fontSize": "1.1rem"}),
                                            " Privacy Risk Score"
                                        ],
                                        className="d-inline-block me-3"
                                    ),
                                    html.Div(
                                        [
                                            html.Strong(f"{overall_risk['overall_privacy_factor']:.4f}", className="text-primary", style={"fontSize": "1.1rem"}),
                                            " Privacy Factor"
                                        ],
                                        className="d-inline-block"
                                    ),
                                ],
                                className="mb-2"
                            ),
                            html.P(
                                [
                                    f"Dataset contains {len(overall_risk['high_risk_columns'])} high-risk, {len(overall_risk['medium_risk_columns'])} medium-risk, and {len(overall_risk['low_risk_columns'])} low-risk columns. ",
                                    f"If all columns are shared, there is a {(1-overall_risk['overall_privacy_factor'])*100:.1f}% chance of individual identification."
                                ],
                                className="small text-muted mb-2"
                            ),
                            html.P(
                                [
                                    "Recommendation: ",
                                    "Apply anonymization or pseudonymization to high-risk columns before sharing this dataset."
                                    if overall_risk["high_risk_columns"] else 
                                    "Review medium-risk columns and consider privacy-enhancing techniques where appropriate."
                                ],
                                className="small mb-0 fw-bold"
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm bg-light",
            ),
        ],
        className="privacy-results",
    )
