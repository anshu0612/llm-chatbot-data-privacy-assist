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
