import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from sklearn.ensemble import IsolationForest


def analyze_data_quality(df, custom_constraints=None):
    """Perform data quality analysis on the dataset using the six dimensions and custom constraints."""
    # Calculate data quality metrics for each dimension
    completeness_metrics = calculate_completeness(df)
    accuracy_metrics = calculate_accuracy(df)
    validity_metrics = calculate_validity(df)
    uniqueness_metrics = calculate_uniqueness(df)
    integrity_metrics = calculate_integrity(df)
    consistency_metrics = calculate_consistency(df)
    
    # Apply custom constraints if provided
    custom_constraints_results = {}
    if custom_constraints:
        custom_constraints_results = apply_custom_constraints(df, custom_constraints)
    
    # Legacy metrics for backward compatibility
    missing_values = calculate_missing_values(df)
    outliers = calculate_outliers(df)
    data_types = calculate_data_types(df)
    
    # Calculate overall data quality score (weighted average of dimension scores)
    dimension_weights = {
        "completeness": 0.25,
        "accuracy": 0.2,
        "validity": 0.15,
        "uniqueness": 0.15,
        "integrity": 0.1,
        "consistency": 0.15
    }
    
    overall_quality_score = (
        dimension_weights["completeness"] * completeness_metrics["overall_score"] +
        dimension_weights["accuracy"] * accuracy_metrics["overall_score"] +
        dimension_weights["validity"] * validity_metrics["overall_score"] +
        dimension_weights["uniqueness"] * uniqueness_metrics["overall_score"] +
        dimension_weights["integrity"] * integrity_metrics["overall_score"] +
        dimension_weights["consistency"] * consistency_metrics["overall_score"]
    )
    
    quality_results = {
        "overall_quality_score": overall_quality_score,
        "dimensions": {
            "completeness": completeness_metrics,
            "accuracy": accuracy_metrics,
            "validity": validity_metrics,
            "uniqueness": uniqueness_metrics,
            "integrity": integrity_metrics,
            "consistency": consistency_metrics
        },
        "custom_constraints": custom_constraints_results,
        # Legacy fields for backward compatibility
        "missing_score": completeness_metrics["overall_score"],
        "outlier_score": accuracy_metrics["overall_score"],
        "consistency_score": consistency_metrics["overall_score"],
        "completeness": {
            "completeness_score": completeness_metrics["overall_score"],
            "total_cells": completeness_metrics["total_cells"],
            "non_missing_cells": completeness_metrics["non_missing_cells"],
            "missing_cells": completeness_metrics["missing_cells"]
        },
        "column_details": {
            "missing_values": missing_values,
            "outliers": outliers,
            "data_types": data_types,
            "consistency": {col: details["case_consistency_score"] for col, details in consistency_metrics["column_details"].items()}
        }
    }
    
    # Create visualizations
    visualizations = create_quality_visualizations(quality_results, df)
    
    return quality_results, visualizations

# Add these functions to data_quality_analyzer.py

def calculate_completeness(df):
    """
    Calculate completeness metrics for each column in the dataset.
    
    Completeness: Is your data complete, with no missing values or gaps?
    """
    column_completeness = {}
    
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_percentage = missing_count / len(df) if len(df) > 0 else 0
        completeness_score = 1 - missing_percentage
        
        column_completeness[col] = {
            "missing_count": int(missing_count),
            "missing_percentage": float(missing_percentage),
            "completeness_score": float(completeness_score)
        }
    
    # Calculate overall completeness
    total_cells = df.size
    non_missing_cells = total_cells - df.isna().sum().sum()
    overall_completeness_score = non_missing_cells / total_cells if total_cells > 0 else 1.0
    
    return {
        "overall_score": float(overall_completeness_score),
        "total_cells": int(total_cells),
        "non_missing_cells": int(non_missing_cells),
        "missing_cells": int(total_cells - non_missing_cells),
        "column_details": column_completeness
    }

def calculate_accuracy(df):
    """
    Calculate accuracy metrics for each column in the dataset.
    
    Accuracy: Does your data correctly reflect reality and is it free of errors?
    
    Note: True accuracy requires domain knowledge and reference data.
    This implementation uses outlier detection as a proxy for accuracy.
    """
    column_accuracy = {}
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            # Use isolation forest to detect outliers as a proxy for accuracy
            try:
                clf = IsolationForest(contamination=0.1, random_state=42)
                column_data = df[col].fillna(df[col].median()).values.reshape(-1, 1)
                outlier_predictions = clf.fit_predict(column_data)
                outlier_count = (outlier_predictions == -1).sum()
                outlier_percentage = outlier_count / len(df) if len(df) > 0 else 0
                accuracy_score = 1 - outlier_percentage
                
                column_accuracy[col] = {
                    "outlier_count": int(outlier_count),
                    "outlier_percentage": float(outlier_percentage),
                    "accuracy_score": float(accuracy_score)
                }
            except Exception as e:
                column_accuracy[col] = {
                    "outlier_count": 0,
                    "outlier_percentage": 0,
                    "accuracy_score": 1.0
                }
        else:
            column_accuracy[col] = {
                "outlier_count": 0,
                "outlier_percentage": 0,
                "accuracy_score": 1.0
            }
    
    # Calculate overall accuracy score (average of column scores)
    overall_accuracy_score = sum([v["accuracy_score"] for v in column_accuracy.values()]) / len(column_accuracy) if column_accuracy else 1.0
    
    return {
        "overall_score": float(overall_accuracy_score),
        "column_details": column_accuracy
    }

def calculate_validity(df):
    """
    Calculate validity metrics for each column in the dataset.
    
    Validity: Does your data conform to specified formats, ranges, and definitions?
    """
    column_validity = {}
    
    for col in df.columns:
        # Initialize validity score
        validity_score = 1.0
        invalid_count = 0
        
        # Check validity based on data type
        if pd.api.types.is_numeric_dtype(df[col]):
            # For numeric columns, check for infinity and NaN values
            non_finite_count = (~np.isfinite(df[col].dropna())).sum()
            invalid_count = non_finite_count
            
            if len(df[col].dropna()) > 0:
                validity_score = 1 - (non_finite_count / len(df[col].dropna()))
            
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            # For datetime columns, all non-null values are considered valid
            # (pandas already converted them to datetime)
            validity_score = 1.0
            
        elif pd.api.types.is_string_dtype(df[col]):
            # For string columns, check for empty strings
            empty_string_count = (df[col].fillna('') == '').sum()
            invalid_count = empty_string_count
            
            if len(df) > 0:
                validity_score = 1 - (empty_string_count / len(df))
        
        column_validity[col] = {
            "invalid_count": int(invalid_count),
            "validity_score": float(validity_score)
        }
    
    # Calculate overall validity score (average of column scores)
    overall_validity_score = sum([v["validity_score"] for v in column_validity.values()]) / len(column_validity) if column_validity else 1.0
    
    return {
        "overall_score": float(overall_validity_score),
        "column_details": column_validity
    }

def calculate_uniqueness(df):
    """
    Calculate uniqueness metrics for each column in the dataset.
    
    Uniqueness: Is your data free from unintended duplicates?
    """
    column_uniqueness = {}
    
    for col in df.columns:
        # Count duplicate values
        value_counts = df[col].value_counts()
        duplicate_values = value_counts[value_counts > 1].sum() - len(value_counts[value_counts > 1])
        total_values = len(df[col].dropna())
        
        # Calculate uniqueness score
        uniqueness_score = 1.0
        if total_values > 0:
            uniqueness_score = 1 - (duplicate_values / total_values)
        
        column_uniqueness[col] = {
            "duplicate_count": int(duplicate_values),
            "unique_percentage": float(df[col].nunique() / total_values if total_values > 0 else 1.0),
            "uniqueness_score": float(uniqueness_score)
        }
    
    # Check for duplicate rows
    duplicate_rows_count = df.duplicated().sum()
    row_uniqueness_score = 1 - (duplicate_rows_count / len(df) if len(df) > 0 else 0)
    
    # Calculate overall uniqueness score (average of column scores + row uniqueness)
    column_scores_sum = sum([v["uniqueness_score"] for v in column_uniqueness.values()])
    overall_uniqueness_score = (column_scores_sum + row_uniqueness_score) / (len(column_uniqueness) + 1) if column_uniqueness else 1.0
    
    return {
        "overall_score": float(overall_uniqueness_score),
        "duplicate_rows": int(duplicate_rows_count),
        "row_uniqueness_score": float(row_uniqueness_score),
        "column_details": column_uniqueness
    }

def calculate_integrity(df):
    """
    Calculate integrity metrics for the dataset.
    
    Integrity: Can your data be consistently traced and connected across your agency?
    
    Note: Full integrity assessment requires knowledge of relationships between tables.
    This implementation focuses on potential foreign key columns and referential integrity.
    """
    # Identify potential ID columns (columns with unique values that might be foreign keys)
    potential_id_columns = []
    column_integrity = {}
    
    for col in df.columns:
        # Check if column name contains 'id', 'key', 'code' or similar
        is_potential_id = any(id_term in col.lower() for id_term in ['id', 'key', 'code', 'num', 'uuid'])
        
        # Check if column has high cardinality (many unique values)
        unique_count = df[col].nunique()
        total_count = len(df[col].dropna())
        unique_ratio = unique_count / total_count if total_count > 0 else 0
        
        # Calculate integrity score based on null values in potential ID columns
        null_count = df[col].isna().sum()
        integrity_score = 1 - (null_count / len(df) if len(df) > 0 else 0)
        
        if is_potential_id or unique_ratio > 0.9:
            potential_id_columns.append(col)
        
        column_integrity[col] = {
            "is_potential_id": is_potential_id,
            "unique_ratio": float(unique_ratio),
            "null_count": int(null_count),
            "integrity_score": float(integrity_score)
        }
    
    # Calculate overall integrity score
    # Higher weight for potential ID columns
    if potential_id_columns:
        id_scores_sum = sum([column_integrity[col]["integrity_score"] for col in potential_id_columns])
        id_score = id_scores_sum / len(potential_id_columns)
        other_columns = [col for col in df.columns if col not in potential_id_columns]
        
        if other_columns:
            other_scores_sum = sum([column_integrity[col]["integrity_score"] for col in other_columns])
            other_score = other_scores_sum / len(other_columns)
            overall_integrity_score = (id_score * 0.7) + (other_score * 0.3)
        else:
            overall_integrity_score = id_score
    else:
        # If no potential ID columns, use average of all columns
        overall_integrity_score = sum([v["integrity_score"] for v in column_integrity.values()]) / len(column_integrity) if column_integrity else 1.0
    
    return {
        "overall_score": float(overall_integrity_score),
        "potential_id_columns": potential_id_columns,
        "column_details": column_integrity
    }

def calculate_consistency(df):
    """
    Calculate consistency metrics for the dataset.
    
    Consistency: Is your data stable and coherent across different systems and time periods?
    """
    column_consistency = {}
    
    for col in df.columns:
        # Initialize consistency metrics
        case_consistency_score = 1.0
        format_consistency_score = 1.0
        
        # Check for case consistency in string columns
        if pd.api.types.is_string_dtype(df[col]):
            lowercase_count = df[col].dropna().str.islower().sum()
            uppercase_count = df[col].dropna().str.isupper().sum()
            mixed_case_count = len(df[col].dropna()) - lowercase_count - uppercase_count
            
            if len(df[col].dropna()) > 0:
                case_consistency_score = max(lowercase_count, uppercase_count, mixed_case_count) / len(df[col].dropna())
            
            column_consistency[col] = {
                "case_consistency_score": float(case_consistency_score),
                "lowercase_count": int(lowercase_count),
                "uppercase_count": int(uppercase_count),
                "mixed_case_count": int(mixed_case_count),
                "format_consistency_score": float(format_consistency_score)
            }
        
        # Check for format consistency in numeric columns
        elif pd.api.types.is_numeric_dtype(df[col]):
            # Check if values follow a consistent pattern (e.g., all integers vs. mix of integers and floats)
            non_null_values = df[col].dropna()
            integer_count = 0
            float_count = 0
            
            if len(non_null_values) > 0:
                integer_count = (non_null_values % 1 == 0).sum()
                float_count = len(non_null_values) - integer_count
                format_consistency_score = max(integer_count, float_count) / len(non_null_values)
            
            column_consistency[col] = {
                "case_consistency_score": float(case_consistency_score),
                "format_consistency_score": float(format_consistency_score),
                "integer_count": int(integer_count),
                "float_count": int(float_count)
            }
        
        # For other data types
        else:
            column_consistency[col] = {
                "case_consistency_score": float(case_consistency_score),
                "format_consistency_score": float(format_consistency_score)
            }
    
    # Calculate overall consistency score (average of case and format consistency)
    case_scores = [v["case_consistency_score"] for v in column_consistency.values()]
    format_scores = [v["format_consistency_score"] for v in column_consistency.values()]
    
    overall_consistency_score = (sum(case_scores) + sum(format_scores)) / (2 * len(column_consistency)) if column_consistency else 1.0
    
    return {
        "overall_score": float(overall_consistency_score),
        "column_details": column_consistency
    }



def calculate_missing_values(df):
    """Calculate missing value metrics for each column."""
    missing_values = {}
    
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_percentage = missing_count / len(df) if len(df) > 0 else 0
        
        missing_values[col] = {
            "missing_count": int(missing_count),
            "missing_percentage": float(missing_percentage),
        }
    
    return missing_values

def calculate_outliers(df):
    """Calculate outlier metrics for each numerical column."""
    outliers = {}
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            # Use isolation forest to detect outliers
            try:
                clf = IsolationForest(contamination=0.1, random_state=42)
                column_data = df[col].fillna(df[col].median()).values.reshape(-1, 1)
                outlier_predictions = clf.fit_predict(column_data)
                outlier_count = (outlier_predictions == -1).sum()
                outlier_percentage = outlier_count / len(df) if len(df) > 0 else 0
                
                outliers[col] = {
                    "outlier_count": int(outlier_count),
                    "outlier_percentage": float(outlier_percentage),
                }
            except Exception as e:
                # If outlier detection fails, set to 0
                outliers[col] = {
                    "outlier_count": 0,
                    "outlier_percentage": 0,
                }
        else:
            outliers[col] = {
                "outlier_count": 0,
                "outlier_percentage": 0,
            }
    
    return outliers

def calculate_data_types(df):
    """Calculate data type information for each column."""
    data_types = {}
    
    for col in df.columns:
        dtype = df[col].dtype
        
        if pd.api.types.is_numeric_dtype(df[col]):
            if (df[col].dropna() % 1 == 0).all():
                inferred_type = "integer"
            else:
                inferred_type = "float"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            inferred_type = "datetime"
        elif pd.api.types.is_bool_dtype(df[col]):
            inferred_type = "boolean"
        else:
            inferred_type = "string"
        
        unique_values = df[col].nunique()
        unique_percentage = unique_values / len(df) if len(df) > 0 else 0
        
        data_types[col] = {
            "dtype": str(dtype),
            "inferred_type": inferred_type,
            "unique_values": int(unique_values),
            "unique_percentage": float(unique_percentage),
        }
    
    return data_types

# This is the old calculate_consistency function which is now replaced by the new implementation above
def calculate_consistency_old(df):
    """Calculate consistency metrics for the dataset."""
    consistency = {}
    
    # Check for consistency in string columns (e.g., case consistency)
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            # Check for case consistency
            lowercase_count = df[col].dropna().str.islower().sum()
            uppercase_count = df[col].dropna().str.isupper().sum()
            mixed_case_count = len(df[col].dropna()) - lowercase_count - uppercase_count
            
            if len(df[col].dropna()) > 0:
                case_consistency_score = max(lowercase_count, uppercase_count) / len(df[col].dropna())
            else:
                case_consistency_score = 1.0
            
            consistency[col] = {
                "case_consistency_score": float(case_consistency_score),
                "lowercase_count": int(lowercase_count),
                "uppercase_count": int(uppercase_count),
                "mixed_case_count": int(mixed_case_count),
            }
        else:
            consistency[col] = {
                "case_consistency_score": 1.0,
                "lowercase_count": 0,
                "uppercase_count": 0,
                "mixed_case_count": 0,
            }
    
    return consistency

# This is the old calculate_completeness function which is now replaced by the new implementation above
def calculate_completeness_old(df):
    """Calculate overall completeness of the dataset."""
    total_cells = df.size
    non_missing_cells = total_cells - df.isna().sum().sum()
    
    completeness_score = non_missing_cells / total_cells if total_cells > 0 else 1.0
    
    return {
        "completeness_score": float(completeness_score),
        "overall_score": float(completeness_score),  # Added for compatibility with new code
        "total_cells": int(total_cells),
        "non_missing_cells": int(non_missing_cells),
        "missing_cells": int(total_cells - non_missing_cells),
    }

# Old analyze_data_quality function has been replaced by the new implementation above

# Update references to the old calculate_completeness function
def analyze_data_quality_old(df):
    """Perform data quality analysis on the dataset."""
    # Calculate data quality metrics
    missing_values = calculate_missing_values(df)
    outliers = calculate_outliers(df)
    data_types = calculate_data_types(df)
    consistency_old = calculate_consistency_old(df)  # Use the old implementation for backward compatibility
    consistency_metrics = calculate_consistency(df)  # Use the new implementation
    completeness = calculate_completeness(df)  # Use the new implementation
    
    # Calculate overall data quality score
    missing_score = 1 - sum([v["missing_percentage"] for v in missing_values.values()]) / len(missing_values) if missing_values else 1.0
    outlier_score = 1 - sum([v["outlier_percentage"] for v in outliers.values()]) / len(outliers) if outliers else 1.0
    consistency_score = consistency_metrics["overall_score"]  # Use the overall_score from the new implementation
    
    overall_quality_score = (0.5 * missing_score + 0.3 * outlier_score + 0.2 * consistency_score)
    
    quality_results = {
        "overall_quality_score": overall_quality_score,
        "missing_score": missing_score,
        "outlier_score": outlier_score,
        "consistency_score": consistency_score,
        "completeness": completeness,
        "column_details": {
            "missing_values": missing_values,
            "outliers": outliers,
            "data_types": data_types,
            "consistency": consistency_old,  # Use the old format for backward compatibility
        },
    }
    
    # Create visualizations
    visualizations = create_quality_visualizations(quality_results, df)
    
    return quality_results, visualizations


def apply_custom_constraints(df, constraints):
    """Apply custom constraints to the dataset and return the results."""
    results = {
        "constraints": [],
        "overall_score": 1.0,
        "pass_count": 0,
        "fail_count": 0,
        "total_count": len(constraints) if constraints else 0
    }
    
    if not constraints:
        return results
    
    for constraint in constraints:
        column = constraint.get("column")
        constraint_type = constraint.get("type")
        value = constraint.get("value")
        
        # Skip if column doesn't exist
        if column not in df.columns:
            results["constraints"].append({
                "column": column,
                "type": constraint_type,
                "value": value,
                "passed": False,
                "error": "Column not found in dataset",
                "pass_rate": 0.0
            })
            results["fail_count"] += 1
            continue
        
        # Apply the constraint based on its type
        if constraint_type == "not_null":
            non_null_count = df[column].count()
            total_count = len(df)
            pass_rate = non_null_count / total_count if total_count > 0 else 1.0
            passed = pass_rate == 1.0
            error = f"{total_count - non_null_count} null values found" if not passed else ""
        
        elif constraint_type == "unique":
            unique_count = df[column].nunique()
            total_count = df[column].count()
            pass_rate = 1.0 if unique_count == total_count else 0.0
            passed = pass_rate == 1.0
            error = f"{total_count - unique_count} duplicate values found" if not passed else ""
        
        elif constraint_type == "min_value":
            try:
                min_value = float(value) if value else 0
                if pd.api.types.is_numeric_dtype(df[column]):
                    valid_count = (df[column] >= min_value).sum()
                    total_count = df[column].count()
                    pass_rate = valid_count / total_count if total_count > 0 else 1.0
                    passed = pass_rate == 1.0
                    error = f"{total_count - valid_count} values below minimum" if not passed else ""
                else:
                    passed = False
                    pass_rate = 0.0
                    error = "Column is not numeric"
            except ValueError:
                passed = False
                pass_rate = 0.0
                error = "Invalid minimum value"
        
        elif constraint_type == "max_value":
            try:
                max_value = float(value) if value else 0
                if pd.api.types.is_numeric_dtype(df[column]):
                    valid_count = (df[column] <= max_value).sum()
                    total_count = df[column].count()
                    pass_rate = valid_count / total_count if total_count > 0 else 1.0
                    passed = pass_rate == 1.0
                    error = f"{total_count - valid_count} values above maximum" if not passed else ""
                else:
                    passed = False
                    pass_rate = 0.0
                    error = "Column is not numeric"
            except ValueError:
                passed = False
                pass_rate = 0.0
                error = "Invalid maximum value"
        
        elif constraint_type == "regex":
            if not value:
                passed = False
                pass_rate = 0.0
                error = "No regex pattern provided"
            else:
                try:
                    import re
                    pattern = re.compile(value)
                    if pd.api.types.is_string_dtype(df[column]):
                        # Apply regex to non-null values
                        valid_mask = df[column].notna() & df[column].astype(str).str.match(pattern)
                        valid_count = valid_mask.sum()
                        total_count = df[column].count()
                        pass_rate = valid_count / total_count if total_count > 0 else 1.0
                        passed = pass_rate == 1.0
                        error = f"{total_count - valid_count} values don't match pattern" if not passed else ""
                    else:
                        passed = False
                        pass_rate = 0.0
                        error = "Column is not string type"
                except re.error:
                    passed = False
                    pass_rate = 0.0
                    error = "Invalid regex pattern"
        
        elif constraint_type == "value_in_list":
            if not value:
                passed = False
                pass_rate = 0.0
                error = "No list of values provided"
            else:
                try:
                    # Parse comma-separated list
                    allowed_values = [v.strip() for v in value.split(',')]
                    # Convert to appropriate type if column is numeric
                    if pd.api.types.is_numeric_dtype(df[column]):
                        allowed_values = [float(v) for v in allowed_values]
                    
                    valid_count = df[column].isin(allowed_values).sum()
                    total_count = df[column].count()
                    pass_rate = valid_count / total_count if total_count > 0 else 1.0
                    passed = pass_rate == 1.0
                    error = f"{total_count - valid_count} values not in allowed list" if not passed else ""
                except ValueError:
                    passed = False
                    pass_rate = 0.0
                    error = "Invalid list format or type mismatch"
        
        elif constraint_type == "date_format":
            if not value:
                value = "%Y-%m-%d"  # Default format
            
            if pd.api.types.is_datetime64_any_dtype(df[column]):
                # If already datetime, all values are valid
                passed = True
                pass_rate = 1.0
                error = ""
            else:
                try:
                    # Try to parse as datetime with the given format
                    valid_count = 0
                    total_count = df[column].count()
                    
                    for val in df[column].dropna():
                        try:
                            pd.to_datetime(val, format=value)
                            valid_count += 1
                        except:
                            pass
                    
                    pass_rate = valid_count / total_count if total_count > 0 else 1.0
                    passed = pass_rate == 1.0
                    error = f"{total_count - valid_count} values don't match date format" if not passed else ""
                except:
                    passed = False
                    pass_rate = 0.0
                    error = "Invalid date format"
        
        else:  # Unknown constraint type
            passed = False
            pass_rate = 0.0
            error = "Unknown constraint type"
        
        # Add result to the constraints list
        results["constraints"].append({
            "column": column,
            "type": constraint_type,
            "value": value,
            "passed": passed,
            "error": error,
            "pass_rate": float(pass_rate)
        })
        
        if passed:
            results["pass_count"] += 1
        else:
            results["fail_count"] += 1
    
    # Calculate overall score
    results["overall_score"] = results["pass_count"] / results["total_count"] if results["total_count"] > 0 else 1.0
    
    return results


def create_constraints_results_table(constraints_results):
    """Create a table showing the results of custom constraints."""
    if not constraints_results or not constraints_results.get("constraints"):
        return html.P("No constraints results available.", className="text-muted")
    
    # Create table data
    table_data = []
    for constraint in constraints_results.get("constraints", []):
        table_data.append({
            "Column": constraint.get("column", ""),
            "Constraint Type": constraint.get("type", "").replace("_", " ").title(),
            "Value": constraint.get("value", ""),
            "Status": "✓ Passed" if constraint.get("passed", False) else "✗ Failed",
            "Pass Rate": f"{constraint.get('pass_rate', 0.0) * 100:.1f}%",
            "Error": constraint.get("error", "")
        })
    
    # Create the table
    constraints_table = dbc.Table.from_dataframe(
        pd.DataFrame(table_data),
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mt-3",
    )
    
    return constraints_table


def create_column_quality_table(quality_results, df):
    """Create a detailed table showing quality metrics for each column."""
    # Create data quality details table
    quality_table_data = []
    
    # Check if we're using the new data structure with dimensions
    if "dimensions" in quality_results:
        for col in df.columns:
            # Get metrics from each dimension
            completeness_score = quality_results["dimensions"]["completeness"]["column_details"][col]["completeness_score"]
            missing_percentage = quality_results["dimensions"]["completeness"]["column_details"][col]["missing_percentage"] * 100
            
            # Get accuracy score if it's a numeric column
            accuracy_score = quality_results["dimensions"]["accuracy"]["column_details"].get(col, {}).get("accuracy_score", "N/A")
            if accuracy_score != "N/A":
                accuracy_score = f"{accuracy_score:.2f}"
            
            # Get validity score
            validity_score = quality_results["dimensions"]["validity"]["column_details"].get(col, {}).get("validity_score", 1.0)
            
            # Get uniqueness metrics
            uniqueness_score = quality_results["dimensions"]["uniqueness"]["column_details"].get(col, {}).get("uniqueness_score", 1.0)
            unique_percentage = quality_results["dimensions"]["uniqueness"]["column_details"].get(col, {}).get("unique_percentage", 0) * 100
            
            # Get integrity metrics
            integrity_score = quality_results["dimensions"]["integrity"]["column_details"].get(col, {}).get("integrity_score", 1.0)
            is_potential_id = quality_results["dimensions"]["integrity"]["column_details"].get(col, {}).get("is_potential_id", False)
            
            # Get consistency metrics
            consistency_score = quality_results["dimensions"]["consistency"]["column_details"].get(col, {}).get("case_consistency_score", 1.0)
            
            # Get data type
            data_type = quality_results["column_details"]["data_types"][col]["inferred_type"]
            
            quality_table_data.append({
                "Column": col,
                "Data Type": data_type,
                "Completeness": f"{completeness_score:.2f}",
                "Missing (%)": f"{missing_percentage:.1f}%",
                "Accuracy": accuracy_score,
                "Validity": f"{validity_score:.2f}",
                "Uniqueness": f"{uniqueness_score:.2f}",
                "Unique (%)": f"{unique_percentage:.1f}%",
                "Integrity": f"{integrity_score:.2f}" + (" (ID)" if is_potential_id else ""),
                "Consistency": f"{consistency_score:.2f}",
            })
    else:
        # For backward compatibility with old data structure
        for col in df.columns:
            quality_table_data.append({
                "Column": col,
                "Data Type": quality_results["column_details"]["data_types"][col]["inferred_type"],
                "Missing (%)": f"{quality_results['column_details']['missing_values'][col]['missing_percentage'] * 100:.1f}%",
                "Unique Values": quality_results["column_details"]["data_types"][col]["unique_values"],
                "Outliers (%)": f"{quality_results['column_details']['outliers'][col]['outlier_percentage'] * 100:.1f}%" if quality_results["column_details"]["data_types"][col]["inferred_type"] in ["integer", "float"] else "N/A",
                "Consistency": f"{quality_results['column_details']['consistency'][col]:.2f}",
            })
    
    # Create the table
    quality_table = dbc.Table.from_dataframe(
        pd.DataFrame(quality_table_data),
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mt-3",
    )
    
    return quality_table

def create_quality_visualizations(quality_results, df):
    """Create visualizations for data quality analysis based on the six dimensions."""
    # Create a radar chart for the six dimensions
    dimensions = ["Completeness", "Accuracy", "Validity", "Uniqueness", "Integrity", "Consistency"]
    
    # Check if we're using the new data structure with dimensions
    if "dimensions" in quality_results:
        dimension_scores = [
            quality_results["dimensions"]["completeness"]["overall_score"],
            quality_results["dimensions"]["accuracy"]["overall_score"],
            quality_results["dimensions"]["validity"]["overall_score"],
            quality_results["dimensions"]["uniqueness"]["overall_score"],
            quality_results["dimensions"]["integrity"]["overall_score"],
            quality_results["dimensions"]["consistency"]["overall_score"]
        ]
    else:
        # For backward compatibility with old data structure
        dimension_scores = [
            quality_results["completeness"]["completeness_score"],
            quality_results["outlier_score"],  # Use outlier score as a proxy for accuracy
            1.0,  # Default validity score
            1.0,  # Default uniqueness score
            1.0,  # Default integrity score
            quality_results["consistency_score"]  # Use consistency score
        ]
    
    # Create radar chart for dimensions
    fig_dimensions = go.Figure()
    fig_dimensions.add_trace(go.Scatterpolar(
        r=dimension_scores,
        theta=dimensions,
        fill='toself',
        name='Data Quality Dimensions',
        line_color='rgba(27, 158, 119, 0.8)',
        fillcolor='rgba(27, 158, 119, 0.3)'
    ))
    fig_dimensions.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=False,
        title="Data Quality Dimensions",
        title_font_size=14,
        height=300,
        margin=dict(l=40, r=40, t=40, b=30)
    )
    
    # Continue with the rest of your visualizations...
    # (Include your existing visualizations here)
    
    # Add the dimensions radar chart to your visualization layout
    return html.Div(
        [
            html.H4("Data Quality Analysis Results", className="mb-4"),
            
            # Add the dimensions radar chart
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5("Data Quality Dimensions", className="card-title"),
                            dcc.Graph(figure=fig_dimensions, config={"displayModeBar": False}),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm",
            ),
            
            # Continue with your existing visualization layout...
            # (Include your existing layout here)
            
            # Add dimension details with computation information
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Button(
                            "Data Quality Dimensions Details",
                            id="dimensions-collapse-button",
                            color="link",
                            className="text-decoration-none w-100 text-start",
                        )
                    ),
                    dbc.Collapse(
                        dbc.CardBody([
                            html.Div([
                                # Check if we're using the new data structure with dimensions
                                html.Div([
                                    html.H6("Completeness", className="mt-3"),
                                    html.P("Is your data complete, with no missing values or gaps?"),
                                    html.P(f"Score: {quality_results['dimensions']['completeness']['overall_score']:.2f}" if 'dimensions' in quality_results else f"Score: {quality_results['completeness']['completeness_score']:.2f}"),
                                    html.P(f"Missing cells: {quality_results['dimensions']['completeness']['missing_cells'] if 'dimensions' in quality_results else quality_results['completeness']['missing_cells']} out of {quality_results['dimensions']['completeness']['total_cells'] if 'dimensions' in quality_results else quality_results['completeness']['total_cells']}"),
                                    html.P("Computation: Ratio of non-missing values to total values. Higher is better.", className="small text-muted"),
                                    
                                    html.H6("Accuracy", className="mt-3"),
                                    html.P("Does your data correctly reflect reality and is it free of errors?"),
                                    html.P(f"Score: {quality_results['dimensions']['accuracy']['overall_score']:.2f}" if 'dimensions' in quality_results else f"Score: {quality_results['outlier_score']:.2f}"),
                                    html.P("Computation: Uses Isolation Forest algorithm to detect outliers as a proxy for accuracy. Higher score means fewer outliers.", className="small text-muted"),
                                    
                                    html.H6("Validity", className="mt-3"),
                                    html.P("Does your data conform to specified formats, ranges, and definitions?"),
                                    html.P(f"Score: {quality_results['dimensions']['validity']['overall_score']:.2f}" if 'dimensions' in quality_results else "Score: 1.00 (Not calculated in this version)"),
                                    html.P("Computation: Checks for invalid values based on data types (e.g., non-finite numbers, empty strings). Higher score means more valid data.", className="small text-muted"),
                                    
                                    html.H6("Uniqueness", className="mt-3"),
                                    html.P("Is your data free from unintended duplicates?"),
                                    html.P(f"Score: {quality_results['dimensions']['uniqueness']['overall_score']:.2f}" if 'dimensions' in quality_results else "Score: 1.00 (Not calculated in this version)"),
                                    html.P(f"Duplicate rows: {quality_results['dimensions']['uniqueness']['duplicate_rows']}" if 'dimensions' in quality_results else ""),
                                    html.P("Computation: Analyzes duplicate values in columns and duplicate rows. Higher score means fewer duplicates.", className="small text-muted"),
                                    
                                    html.H6("Integrity", className="mt-3"),
                                    html.P("Can your data be consistently traced and connected across your agency?"),
                                    html.P(f"Score: {quality_results['dimensions']['integrity']['overall_score']:.2f}" if 'dimensions' in quality_results else "Score: 1.00 (Not calculated in this version)"),
                                    html.P(f"Potential ID columns: {', '.join(quality_results['dimensions']['integrity']['potential_id_columns']) if 'dimensions' in quality_results and quality_results['dimensions']['integrity']['potential_id_columns'] else 'None detected'}"),
                                    html.P("Computation: Identifies potential ID columns and checks for null values. Higher weight given to ID columns. Higher score means better referential integrity.", className="small text-muted"),
                                    
                                    html.H6("Consistency", className="mt-3"),
                                    html.P("Is your data stable and coherent across different systems and time periods?"),
                                    html.P(f"Score: {quality_results['dimensions']['consistency']['overall_score']:.2f}" if 'dimensions' in quality_results else f"Score: {quality_results['consistency_score']:.2f}"),
                                    html.P("Computation: Checks for case consistency in strings and format consistency in numbers. Higher score means more consistent formatting.", className="small text-muted"),
                                ]),
                            ]),
                        ]),
                        id="dimensions-collapse-content",
                    ),
                ],
                className="mb-4 shadow-sm",
            ),
            
            # Add column-level evaluation table
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Button(
                            "Column-Level Quality Details",
                            id="column-collapse-button",
                            color="link",
                            className="text-decoration-none w-100 text-start",
                        )
                    ),
                    dbc.Collapse(
                        dbc.CardBody([
                            html.Div([
                                # Create data quality details table
                                html.P("This table shows detailed quality metrics for each column in your dataset:", className="mb-3"),
                                create_column_quality_table(quality_results, df)
                            ]),
                        ]),
                        id="column-collapse-content",
                    ),
                ],
                className="mb-4 shadow-sm",
            ),
            
            # Add custom constraints results if available
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Button(
                            "Custom Constraints Results",
                            id="constraints-collapse-button",
                            color="link",
                            className="text-decoration-none w-100 text-start",
                        )
                    ),
                    dbc.Collapse(
                        dbc.CardBody([
                            html.Div([
                                # Show custom constraints results if available
                                html.Div([
                                    html.H6("Custom Constraints Results", className="mb-3"),
                                    html.P(f"Overall Constraints Score: {quality_results.get('custom_constraints', {}).get('overall_score', 1.0):.2f}", className="mb-2"),
                                    html.P([
                                        f"Passed: {quality_results.get('custom_constraints', {}).get('pass_count', 0)}/{quality_results.get('custom_constraints', {}).get('total_count', 0)} constraints",
                                    ], className="mb-3"),
                                    
                                    # Create constraints results table
                                    create_constraints_results_table(quality_results.get('custom_constraints', {}))
                                ]) if quality_results.get('custom_constraints', {}).get('total_count', 0) > 0 else 
                                html.P("No custom constraints defined. Add constraints in the Custom Quality Constraints section above.", className="text-muted")
                            ]),
                        ]),
                        id="constraints-collapse-content",
                    ),
                ],
                className="mb-4 shadow-sm",
            ) if "custom_constraints" in quality_results else html.Div(),
        ],
        className="quality-results",
    )

    
# Old create_quality_visualizations function has been completely replaced by the new implementation above
