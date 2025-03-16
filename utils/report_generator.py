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

def _get_risk_color(score):
    """Get color based on privacy risk score."""
    if score < 0.4:
        return "#10b981"  # Low risk - Green
    elif score < 0.7:
        return "#f59e0b"  # Medium risk - Amber
    else:
        return "#ef4444"  # High risk - Red

def _get_quality_color(score):
    """Get color based on quality score."""
    if score < 0.4:
        return "#ef4444"  # Poor quality - Red
    elif score < 0.7:
        return "#f59e0b"  # Medium quality - Amber
    else:
        return "#10b981"  # High quality - Green

def _get_privacy_level(score):
    """Get textual privacy level based on score."""
    if score < 0.4:
        return "low"
    elif score < 0.7:
        return "medium"
    else:
        return "high"

def _get_quality_level(score):
    """Get textual quality level based on score."""
    if score < 0.4:
        return "poor"
    elif score < 0.7:
        return "moderate"
    else:
        return "good"

def _get_combined_recommendation(privacy_score, quality_score):
    """Generate recommendation based on both privacy and quality scores."""
    if privacy_score > 0.7 and quality_score < 0.4:
        return "This dataset presents significant privacy risks and poor data quality. Consider substantial revisions before sharing."
    elif privacy_score > 0.7 and quality_score > 0.7:
        return "While the data quality is good, the high privacy risk requires mitigation measures before sharing."
    elif privacy_score < 0.4 and quality_score < 0.4:
        return "The data has low privacy risk but poor quality. Focus on improving data quality before sharing."
    elif privacy_score < 0.4 and quality_score > 0.7:
        return "This dataset has both low privacy risk and good quality, making it suitable for sharing with minimal changes."
    else:
        return "Consider addressing both privacy and quality aspects before sharing this dataset."

def generate_html_report(df, privacy_results, quality_results):
    """Generate an HTML report containing privacy and data quality analysis results."""
    try:
        # Generate css styles
        css_style = """
            body {font-family: 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; margin: 30px; color: #374151; background-color: #f9fafb;}
            .container {max-width: 1000px; margin: 0 auto; background-color: white; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border-radius: 8px; padding: 40px;}
            .header {text-align: center; margin-bottom: 40px; border-bottom: 1px solid #f3f4f6; padding-bottom: 20px;}
            .section {margin-bottom: 40px; padding-top: 10px;}
            h1 {color: #3a0ca3; font-weight: 600; margin-bottom: 10px; font-size: 2.2rem;}
            h2 {color: #4361ee; border-bottom: 1px solid #f3f4f6; padding-bottom: 10px; font-weight: 500; margin-top: 30px; margin-bottom: 20px; font-size: 1.5rem; display: flex; align-items: center;}
            h2::before {content: ''; display: inline-block; width: 4px; height: 20px; background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%); margin-right: 10px; border-radius: 2px;}
            h3 {color: #3a0ca3; font-weight: 500; margin-top: 25px; font-size: 1.2rem;}
            table {width: 100%; border-collapse: collapse; margin-bottom: 30px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.06);}
            table, th, td {border: none;}
            tr {border-bottom: 1px solid #f3f4f6;}
            tr:last-child {border-bottom: none;}
            th, td {padding: 14px 16px; text-align: left;}
            th {background-color: #f5f7ff; color: #4361ee; font-weight: 600; font-size: 0.95rem;}
            td {font-size: 0.95rem;}
            .risk-high {color: #ef4444; font-weight: 600;}
            .risk-medium {color: #f59e0b; font-weight: 600;}
            .risk-low {color: #10b981; font-weight: 600;}
            .score-container {display: flex; justify-content: center; align-items: center; gap: 30px; margin: 30px 0;}
            .score-card {display: flex; flex-direction: column; align-items: center; background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); width: 180px;}
            .score-donut {position: relative; width: 120px; height: 120px; border-radius: 50%; margin-bottom: 15px;}
            .score-value {position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 28px; font-weight: 600; color: #374151;}
            .score-label {font-size: 0.95rem; font-weight: 500; color: #6b7280; text-align: center;}
            .combined-assessment {background-color: #f5f7ff; border-radius: 12px; padding: 30px; margin: 40px 0 30px; border-left: 5px solid #4361ee; box-shadow: 0 4px 15px rgba(67, 97, 238, 0.1);}
            .combined-assessment h3 {color: #3a0ca3; margin-top: 0; margin-bottom: 20px; text-align: center; font-size: 1.3rem; font-weight: 600;}
            .score-summary {display: flex; justify-content: center; gap: 40px; margin-bottom: 25px;}
            .summary-card {background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); width: 180px; text-align: center;}
            .privacy-score .summary-value {font-size: 2em; font-weight: 600; margin: 0; padding: 0; color: #4361ee;}
            .quality-score .summary-value {font-size: 2em; font-weight: 600; margin: 0; padding: 0; color: #10b981;}
            .summary-label {display: block; font-size: 1em; font-weight: 500; color: #6b7280; margin: 10px 0 5px;}
            .summary-indicator {height: 6px; border-radius: 3px; width: 100%; margin: 12px auto 0; background-color: #f3f4f6; position: relative; overflow: hidden;}
            .assessment-conclusion {background-color: white; border-radius: 10px; padding: 20px 25px; margin-top: 20px; color: #374151; line-height: 1.6; box-shadow: 0 2px 8px rgba(0,0,0,0.05); font-size: 1.05rem;}
            .assessment-conclusion strong {color: #3a0ca3;}
            .footer {text-align: center; margin-top: 40px; color: #6b7280; font-size: 0.9rem;}
        """
        
        # Prepare variables
        privacy_score = f"{privacy_results['overall_privacy_score']:.2f}"
        quality_score = f"{quality_results['overall_quality_score']:.2f}"
        privacy_color = _get_risk_color(privacy_results['overall_privacy_score'])
        quality_color = _get_quality_color(quality_results['overall_quality_score'])
        privacy_level = _get_privacy_level(privacy_results['overall_privacy_score'])
        quality_level = _get_quality_level(quality_results['overall_quality_score'])
        combined_recommendation = _get_combined_recommendation(
            privacy_results['overall_privacy_score'], 
            quality_results['overall_quality_score']
        )
        
        # Create start of HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Privacy and Quality Report</title>
    <style>{css_style}</style>
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
                <div class="score-card">
                    <div class="score-donut" style="background: conic-gradient({privacy_color} {float(privacy_score) * 100}%, #f3f4f6 0)">
                        <div class="score-value">{privacy_score}</div>
                    </div>
                    <div class="score-label">Privacy Risk Score</div>
                </div>
            </div>
            
            <h3>Risk Distribution</h3>
            <p>
                The dataset contains {len(privacy_results['high_risk_columns'])} high-risk columns, 
                {len(privacy_results['medium_risk_columns'])} medium-risk columns, and 
                {len(privacy_results['low_risk_columns'])} low-risk columns.
            </p>
            
            <h3>High Risk Columns</h3>"""
        
        # Add high risk columns table if present
        if privacy_results['high_risk_columns']:
            html_content += """
            <table>
                <tr>
                    <th>Column</th>
                    <th>Risk Score</th>
                    <th>Sensitivity Type</th>
                </tr>"""
            
            for col in privacy_results['high_risk_columns']:
                score = privacy_results['column_scores'][col]['privacy_risk_score']
                sensitivity = privacy_results['column_scores'][col]['sensitivity_type']
                html_content += f"""
                <tr>
                    <td>{col}</td>
                    <td class="risk-high">{score:.2f}</td>
                    <td>{sensitivity}</td>
                </tr>"""
            
            html_content += """
            </table>"""
        else:
            html_content += """
            <p>No high-risk columns were detected in this dataset.</p>"""
        
        # Add data quality section
        html_content += f"""
        </div>
        
        <div class="section">
            <h2>Data Quality Assessment</h2>
            
            <div class="score-container">
                <div class="score-card">
                    <div class="score-donut" style="background: conic-gradient({quality_color} {float(quality_score) * 100}%, #f3f4f6 0)">
                        <div class="score-value">{quality_score}</div>
                    </div>
                    <div class="score-label">Quality Score</div>
                </div>
            </div>
            
            <h3>Quality Score Components</h3>
            <table>
                <tr>
                    <th>Completeness Score</th>
                    <td>{quality_results['missing_score']:.2f}</td>
                </tr>
                <tr>
                    <th>Accuracy Score</th>
                    <td>{quality_results['dimensions']['accuracy']['overall_score']:.2f}</td>
                </tr>
                <tr>
                    <th>Consistency Score</th>
                    <td>{quality_results['consistency_score']:.2f}</td>
                </tr>
                <tr>
                    <th>Uniqueness Score</th>
                    <td>{quality_results['dimensions']['uniqueness']['overall_score']:.2f}</td>
                </tr>
                <tr>
                    <th>Validity Score</th>
                    <td>{quality_results['dimensions']['validity']['overall_score']:.2f}</td>
                </tr>
            </table>
            
            <h3>Recommendations for Improving Data Quality</h3>
            <ol>
                <li>Address identified privacy risks by implementing recommended techniques.</li>
                <li>Improve data quality by handling missing values and outliers.</li>
                <li>Establish governance processes for ongoing data privacy and quality management.</li>
                <li>Conduct periodic re-assessment as data evolves or new data is collected.</li>
            </ol>
        </div>
        
        <div class="combined-assessment">
            <h3>Combined Assessment Summary</h3>
            <div class="score-summary">
                <div class="summary-card privacy-score">
                    <div class="summary-label">Privacy Risk</div>
                    <div class="summary-value">{privacy_score}</div>
                    <div class="summary-indicator" style="--score-percent: {float(privacy_score) * 100}%; --score-color: {privacy_color}"></div>
                </div>
                <div class="summary-card quality-score">
                    <div class="summary-label">Data Quality</div>
                    <div class="summary-value">{quality_score}</div>
                    <div class="summary-indicator" style="--score-percent: {float(quality_score) * 100}%; --score-color: {quality_color}"></div>
                </div>
            </div>
            <div class="assessment-conclusion">
                <strong>Assessment Summary:</strong> This dataset has <span style="color: {privacy_color}">{privacy_level}</span> privacy risk and
                <span style="color: {quality_color}">{quality_level}</span> quality.<br>
                {combined_recommendation}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by DataSharingAssist | Confidential Report</p>
        </div>
    </div>
</body>
</html>"""
        
        # For HTML report, we can just encode the content directly
        html_base64 = base64.b64encode(html_content.encode('utf-8')).decode()
        
        return dict(
            content=html_base64,
            filename="data_privacy_report.html",
            type="text/html",
            base64=True,
        )
    except Exception as e:
        print(f"Error generating HTML report: {e}")
        # Return an error message
        return None

def generate_pdf_report(df, privacy_results, quality_results):
    """Generate a PDF report containing privacy and data quality analysis results."""
    try:
        # First generate the HTML content
        html_report = generate_html_report(df, privacy_results, quality_results)
        
        if html_report is None:
            raise Exception("Failed to generate HTML report")
            
        # Check if wkhtmltopdf is available
        try:
            # Generate PDF
            html_content = base64.b64decode(html_report['content']).decode('utf-8')
            pdf_bytes = pdfkit.from_string(html_content, False)
            
            # Encode for download
            pdf_base64 = base64.b64encode(pdf_bytes).decode()
            
            return dict(
                content=pdf_base64,
                filename="data_privacy_report.pdf",
                type="application/pdf",
                base64=True,
            )
        except Exception as pdf_error:
            print(f"Error generating PDF (falling back to HTML): {pdf_error}")
            # If PDF generation fails, return HTML report instead
            html_report['filename'] = "data_privacy_report.html"
            return html_report
    except Exception as e:
        print(f"Error generating report: {e}")
        # Return an error message
        return None

def generate_report(df, privacy_results, quality_results, report_format):
    """Generate a report in the specified format."""
    # Report is already using a DataFrame, no need to convert
    
    if report_format == "pdf":
        return generate_pdf_report(df, privacy_results, quality_results)
    elif report_format == "html":
        return generate_html_report(df, privacy_results, quality_results)
    elif report_format == "json":
        return generate_json_report(df, privacy_results, quality_results)
    else:
        raise ValueError(f"Unsupported report format: {report_format}")
