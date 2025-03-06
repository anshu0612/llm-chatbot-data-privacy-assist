"""
Privacy metrics module based on information theory for the Data Privacy Assist application.
Implements Shannon entropy and other privacy measures to quantify data privacy risk.
"""

import pandas as pd
import numpy as np
import math
import logging
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_privacy_factor(column: pd.Series) -> float:
    """
    Calculate the Privacy Factor (probability of uniquely identifying an individual) for a column.
    
    Args:
        column: The pandas Series to analyze
        
    Returns:
        float: Privacy Factor between 0 and 1, where higher values indicate better privacy
    """
    # Handle empty or null column
    if column.empty or column.isna().all():
        return 1.0
    
    # For numeric or datetime data, convert to string for counting
    if pd.api.types.is_numeric_dtype(column) or pd.api.types.is_datetime64_dtype(column):
        column = column.astype(str)
    
    # Count occurrences of each value
    value_counts = column.value_counts()
    total_values = len(column)
    
    # Calculate the probability of identifying an individual for each value
    # For each value, the probability of identification is 1/frequency
    # Privacy Factor = 1 - probability of identification
    privacy_factors = []
    
    for frequency in value_counts:
        identification_probability = 1 / frequency
        privacy_factor = 1 - identification_probability
        privacy_factors.append(privacy_factor)
    
    # Return the average privacy factor across all values
    return sum(privacy_factors) / len(privacy_factors) if privacy_factors else 1.0

def calculate_shannon_entropy(column: pd.Series) -> float:
    """
    Calculate the Shannon Entropy for a column.
    
    Shannon Entropy measures the unpredictability or surprise of values in a dataset.
    Higher entropy means better privacy (more unpredictable values).
    
    Args:
        column: The pandas Series to analyze
        
    Returns:
        float: Shannon Entropy value
    """
    # Handle empty or null column
    if column.empty or column.isna().all():
        return 0.0
    
    # For numeric or datetime data, convert to string for counting
    if pd.api.types.is_numeric_dtype(column) or pd.api.types.is_datetime64_dtype(column):
        column = column.astype(str)
    
    # Count occurrences of each value
    value_counts = column.value_counts()
    total_values = len(column)
    
    # Calculate Shannon Entropy: -Σ p(x) log₂ p(x)
    entropy = 0
    for frequency in value_counts:
        probability = frequency / total_values
        # Avoid log(0) which is undefined
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy

def calculate_hartley_measure(column: pd.Series, log_base: float = 10) -> float:
    """
    Calculate the Hartley Measure for a column.
    
    The Hartley measure is defined as log_base(N), where N is the number of unique values.
    This represents the number of digits (in the specified base) needed to represent
    all possible values in the column.
    
    Args:
        column: The pandas Series to analyze
        log_base: The base of the logarithm to use (default is 10)
        
    Returns:
        float: Hartley Measure value
    """
    # Handle empty or null column
    if column.empty or column.isna().all():
        return 0.0
    
    # Count the number of unique non-null values
    unique_values_count = column.dropna().nunique()
    
    # Handle case where there are no unique values
    if unique_values_count <= 1:
        return 0.0
    
    # Calculate Hartley Measure: log_base(N)
    hartley_measure = math.log(unique_values_count, log_base)
    
    return hartley_measure

def calculate_column_metrics(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Calculate privacy metrics for each column in the dataframe.
    
    Args:
        df: The pandas DataFrame to analyze
        
    Returns:
        dict: Dictionary of column metrics
    """
    column_metrics = {}
    
    for col in df.columns:
        # Skip columns with too many missing values
        if df[col].isna().mean() > 0.5:
            column_metrics[col] = {
                "privacy_factor": 1.0,
                "shannon_entropy": 0.0,
                "hartley_measure": 0.0,
                "examples": []
            }
            continue
        
        # Calculate privacy metrics
        privacy_factor = calculate_privacy_factor(df[col])
        shannon_entropy = calculate_shannon_entropy(df[col])
        hartley_measure = calculate_hartley_measure(df[col])
        
        # Get some sample values (up to 5)
        samples = df[col].dropna().sample(min(5, len(df))).tolist() if len(df) > 0 else []
        
        column_metrics[col] = {
            "privacy_factor": privacy_factor,
            "shannon_entropy": shannon_entropy,
            "hartley_measure": hartley_measure,
            "examples": samples
        }
    
    return column_metrics

def calculate_cumulative_privacy_factor(column_metrics: Dict[str, Dict[str, Any]], 
                                       selected_columns: Optional[List[str]] = None) -> float:
    """
    Calculate the cumulative privacy factor for the entire dataset or selected columns.
    
    Args:
        column_metrics: Dictionary of column metrics
        selected_columns: Optional list of columns to consider (defaults to all)
        
    Returns:
        float: Cumulative privacy factor between 0 and 1
    """
    if selected_columns is None:
        selected_columns = list(column_metrics.keys())
    
    # Filter to ensure we only use columns that exist in column_metrics
    valid_columns = [col for col in selected_columns if col in column_metrics]
    
    if not valid_columns:
        return 1.0
    
    # Calculate the cumulative product of privacy factors
    cumulative_factor = 1.0
    for col in valid_columns:
        cumulative_factor *= column_metrics[col]["privacy_factor"]
    
    return cumulative_factor

def format_privacy_metrics(column_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format the privacy metrics for display.
    
    Args:
        column_metrics: Dictionary of column metrics
        
    Returns:
        dict: Formatted metrics for display
    """
    # Calculate overall metrics
    overall_privacy_factor = calculate_cumulative_privacy_factor(column_metrics)
    
    # Calculate average metrics
    avg_privacy_factor = sum(col["privacy_factor"] for col in column_metrics.values()) / len(column_metrics) if column_metrics else 0
    avg_shannon_entropy = sum(col["shannon_entropy"] for col in column_metrics.values()) / len(column_metrics) if column_metrics else 0
    avg_hartley_measure = sum(col["hartley_measure"] for col in column_metrics.values()) / len(column_metrics) if column_metrics else 0
    
    # Determine high, medium, and low risk columns based on privacy factor
    high_risk_columns = [col for col, metrics in column_metrics.items() if metrics["privacy_factor"] < 0.3]
    medium_risk_columns = [col for col, metrics in column_metrics.items() if 0.3 <= metrics["privacy_factor"] < 0.7]
    low_risk_columns = [col for col, metrics in column_metrics.items() if metrics["privacy_factor"] >= 0.7]
    
    return {
        "overall_privacy_factor": overall_privacy_factor,
        "avg_privacy_factor": avg_privacy_factor,
        "avg_shannon_entropy": avg_shannon_entropy,
        "avg_hartley_measure": avg_hartley_measure,
        "high_risk_columns": high_risk_columns,
        "medium_risk_columns": medium_risk_columns,
        "low_risk_columns": low_risk_columns,
        "column_metrics": column_metrics
    }

def analyze_dataset_privacy(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze privacy of a dataset using information theory-based metrics.
    
    Args:
        df: The pandas DataFrame to analyze
        
    Returns:
        dict: Complete privacy analysis results
    """
    try:
        # Calculate column-level metrics
        column_metrics = calculate_column_metrics(df)
        
        # Format results for display
        results = format_privacy_metrics(column_metrics)
        
        logger.info(f"Completed privacy metrics analysis on dataset with {len(df.columns)} columns")
        
        return results
    
    except Exception as e:
        logger.error(f"Error analyzing dataset privacy: {e}")
        return {
            "error": str(e),
            "overall_privacy_factor": 0,
            "column_metrics": {}
        }
