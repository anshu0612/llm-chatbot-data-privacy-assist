import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import base64
import io
from datetime import datetime
import pdfkit
from dash import dcc, html
import dash_bootstrap_components as dbc

def generate_json_report(df, privacy_results, quality_results):
    """Generate a JSON report containing privacy and data quality analysis results."""
    # Combine all results
    report = {
        "report_type": "Data Privacy and Quality Analysis",
        "timestamp": datetime.now().isoformat(),
        "dataset": {
            "name": "Uploaded Dataset",
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": list(df.columns),
        },
        "privacy_analysis": privacy_results,
        "quality_analysis": quality_results,
    }
    
    # Create a download component
    content_string = json.dumps(report, indent=2)
    content_base64 = base64.b64encode(content_string.encode()).decode()
    
    return dict(
        content=content_base64,
        filename="data_privacy_report.json",
        type="application/json",
        base64=True,
    )

def generate_pdf_report(df, privacy_results, quality_results):
    """Generate a PDF report containing privacy and data quality analysis results."""
    try:
        # Create HTML content for the PDF
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Data Privacy and Quality Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 20px;
                    color: #333;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                }}
                .section {{
                    margin-bottom: 30px;
                }}
                h1 {{
                    color: #2c3e50;
                }}
                h2 {{
                    color: #3498db;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 5px;
                }}
                h3 {{
                    color: #2980b9;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                table, th, td {{
                    border: 1px solid #ddd;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .risk-high {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                .risk-medium {{
                    color: #f39c12;
                    font-weight: bold;
                }}
                .risk-low {{
                    color: #27ae60;
                    font-weight: bold;
                }}
                .score-container {{
                    text-align: center;
                    margin: 20px 0;
                }}
                .score-box {{
                    display: inline-block;
                    width: 150px;
                    height: 150px;
                    margin: 0 15px;
                    border-radius: 50%;
                    text-align: center;
                    line-height: 150px;
                    font-size: 36px;
                    font-weight: bold;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Data Privacy and Quality Report</h1>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="section">
                    <h2>Dataset Overview</h2>
                    <p>This report provides an analysis of the uploaded dataset:</p>
                    <table>
                        <tr><th>Number of Rows</th><td>{len(df)}</td></tr>
                        <tr><th>Number of Columns</th><td>{len(df.columns)}</td></tr>
                        <tr><th>Column Names</th><td>{', '.join(df.columns)}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>Privacy Risk Assessment</h2>
                    
                    <div class="score-container">
                        <div class="score-box" style="background-color: {_get_risk_color(privacy_results['overall_privacy_score'])}">
                            {privacy_results['overall_privacy_score']:.2f}
                        </div>
                        <p><strong>Overall Privacy Risk Score</strong></p>
                    </div>
                    
                    <h3>Risk Distribution</h3>
                    <p>
                        The dataset contains {len(privacy_results['high_risk_columns'])} high-risk columns, 
                        {len(privacy_results['medium_risk_columns'])} medium-risk columns, and 
                        {len(privacy_results['low_risk_columns'])} low-risk columns.
                    </p>
                    
                    <h3>High Risk Columns</h3>
        """
        
        # Add high risk columns table if present
        if privacy_results['high_risk_columns']:
            html_content += """
                    <table>
                        <tr>
                            <th>Column</th>
                            <th>Risk Score</th>
                            <th>Sensitivity Type</th>
                        </tr>
            """
            
            for col in privacy_results['high_risk_columns']:
                score = privacy_results['column_scores'][col]['privacy_risk_score']
                sensitivity = privacy_results['column_scores'][col]['sensitivity_type']
                html_content += f"""
                        <tr>
                            <td>{col}</td>
                            <td class="risk-high">{score:.2f}</td>
                            <td>{sensitivity}</td>
                        </tr>
                """
            
            html_content += """
                    </table>
            """
        else:
            html_content += """
                    <p>No high-risk columns were detected in this dataset.</p>
            """
        
        # Add data quality section
        html_content += f"""
                </div>
                
                <div class="section">
                    <h2>Data Quality Assessment</h2>
                    
                    <div class="score-container">
                        <div class="score-box" style="background-color: {_get_quality_color(quality_results['overall_quality_score'])}">
                            {quality_results['overall_quality_score']:.2f}
                        </div>
                        <p><strong>Overall Data Quality Score</strong></p>
                    </div>
                    
                    <h3>Quality Score Components</h3>
                    <table>
                        <tr>
                            <th>Missing Data Score</th>
                            <td>{quality_results['missing_score']:.2f}</td>
                        </tr>
                        <tr>
                            <th>Outlier Score</th>
                            <td>{quality_results['outlier_score']:.2f}</td>
                        </tr>
                        <tr>
                            <th>Consistency Score</th>
                            <td>{quality_results['consistency_score']:.2f}</td>
                        </tr>
                        <tr>
                            <th>Completeness</th>
                            <td>{quality_results['completeness']['completeness_score'] * 100:.1f}%</td>
                        </tr>
                    </table>
                    
                    <h3>Columns with Highest Missing Values</h3>
                    <table>
                        <tr>
                            <th>Column</th>
                            <th>Missing Values</th>
                            <th>Percentage</th>
                        </tr>
        """
        
        # Add missing values table
        missing_values = [(col, info['missing_percentage']) for col, info in quality_results['column_details']['missing_values'].items()]
        missing_values.sort(key=lambda x: x[1], reverse=True)
        
        for col, percentage in missing_values[:5]:
            html_content += f"""
                        <tr>
                            <td>{col}</td>
                            <td>{quality_results['column_details']['missing_values'][col]['missing_count']}</td>
                            <td>{percentage * 100:.1f}%</td>
                        </tr>
            """
        
        # Add recommendations section
        html_content += f"""
                    </table>
                </div>
                
                <div class="section">
                    <h2>Recommendations</h2>
                    
                    <h3>Privacy Recommendations</h3>
                    <ul>
        """
        
        # Add privacy recommendations based on risk scores
        if privacy_results['overall_privacy_score'] > 0.7:
            html_content += """
                        <li><strong class="risk-high">High Privacy Risk:</strong> This dataset contains highly sensitive information. Consider robust anonymization techniques before sharing.</li>
                        <li>Implement pseudonymization for high-risk columns to replace identifiable information with pseudonyms.</li>
                        <li>Consider data minimization by removing unnecessary high-risk columns.</li>
                        <li>Apply k-anonymity techniques to prevent re-identification of individuals.</li>
            """
        elif privacy_results['overall_privacy_score'] > 0.3:
            html_content += """
                        <li><strong class="risk-medium">Medium Privacy Risk:</strong> This dataset contains potentially sensitive information. Apply privacy-enhancing techniques before sharing.</li>
                        <li>Consider generalizing or masking data in medium-risk columns.</li>
                        <li>Ensure proper access controls are in place for data sharing.</li>
                        <li>Document data usage policies and ensure they comply with privacy regulations.</li>
            """
        else:
            html_content += """
                        <li><strong class="risk-low">Low Privacy Risk:</strong> This dataset has minimal privacy concerns, but still follow privacy best practices.</li>
                        <li>Regular privacy audits are recommended even for low-risk datasets.</li>
                        <li>Maintain proper documentation on data usage and access controls.</li>
            """
        
        # Add data quality recommendations
        html_content += """
                    </ul>
                    
                    <h3>Data Quality Recommendations</h3>
                    <ul>
        """
        
        if quality_results['missing_score'] < 0.8:
            html_content += """
                        <li>Consider techniques to handle missing data, such as imputation or removal of incomplete records.</li>
            """
        
        if quality_results['outlier_score'] < 0.8:
            html_content += """
                        <li>Review and address outliers in numerical columns to improve data reliability.</li>
            """
        
        if quality_results['consistency_score'] < 0.8:
            html_content += """
                        <li>Standardize data formats and values to improve consistency across the dataset.</li>
            """
        
        html_content += """
                        <li>Implement data validation rules for future data collection to minimize quality issues.</li>
                        <li>Document data definitions and quality standards for consistent interpretation.</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>Next Steps</h2>
                    <ol>
                        <li>Address identified privacy risks by implementing recommended techniques.</li>
                        <li>Improve data quality by handling missing values and outliers.</li>
                        <li>Establish governance processes for ongoing data privacy and quality management.</li>
                        <li>Conduct periodic re-assessment as data evolves or new data is collected.</li>
                    </ol>
                </div>
                
                <div class="footer">
                    <p>Generated by Data Privacy Assist | Confidential Report</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Generate PDF
        pdf_options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
        }
        
        try:
            # Try to generate PDF with wkhtmltopdf if installed
            pdf_data = pdfkit.from_string(html_content, False, options=pdf_options)
            encoded_pdf = base64.b64encode(pdf_data).decode()
            
            return dict(
                content=encoded_pdf,
                filename="data_privacy_report.pdf",
                type="application/pdf",
                base64=True,
            )
        except Exception as e:
            print(f"Error generating PDF with pdfkit: {e}")
            # If pdfkit fails, return HTML as fallback
            encoded_html = base64.b64encode(html_content.encode()).decode()
            
            return dict(
                content=encoded_html,
                filename="data_privacy_report.html",
                type="text/html",
                base64=True,
            )
    
    except Exception as e:
        print(f"Error generating report: {e}")
        # Return a simple error message as fallback
        error_message = f"Error generating report: {str(e)}"
        encoded_error = base64.b64encode(error_message.encode()).decode()
        
        return dict(
            content=encoded_error,
            filename="error_report.txt",
            type="text/plain",
            base64=True,
        )

def _get_risk_color(score):
    """Get color based on risk score."""
    if score > 0.7:
        return "#FF4136"  # High risk (red)
    elif score > 0.3:
        return "#FF851B"  # Medium risk (orange)
    else:
        return "#2ECC40"  # Low risk (green)

def _get_quality_color(score):
    """Get color based on quality score."""
    if score < 0.3:
        return "#FF4136"  # Low quality (red)
    elif score < 0.7:
        return "#FF851B"  # Medium quality (orange)
    else:
        return "#2ECC40"  # High quality (green)

def generate_report(df, privacy_results, quality_results, report_format):
    """Generate a report in either PDF or JSON format."""
    if report_format == "pdf":
        return generate_pdf_report(df, privacy_results, quality_results)
    else:
        return generate_json_report(df, privacy_results, quality_results)
