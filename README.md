# Data Privacy Assist

A modern web application that helps users evaluate privacy risks in datasets and provides privacy recommendations based on Singapore government data privacy guidelines.

## Features

### Privacy Risk Assessment
- Upload CSV datasets for analysis
- Visualize privacy risks through intuitive charts
- Identify potential sensitive data columns
- Get numerical privacy risk scores

### Data Quality Assessment
- Evaluate dataset completeness and consistency
- Identify data quality issues
- Ensure data is suitable for further use

### Privacy Recommendations Chatbot
- Get personalized privacy recommendations based on dataset analysis
- Receive guidance on data classification and sharing policies
- Learn about privacy-enhancing measures
- Interactive Q&A with explanations and justifications

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Then add your OpenAI API key to the `.env` file

4. Run the application:
   ```
   python app.py
   ```

## Technologies Used
- Plotly Dash for the web interface
- LangChain and OpenAI for the recommendation chatbot
- Pandas and NumPy for data processing
- Plotly for data visualization
- PDF generation for reports

## License
MIT
