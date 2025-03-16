# DataSharingAssist

![DataSharingAssist Logo](assets/logo.png)

## 🔒 Smart Data Sharing & Privacy Solution

DataSharingAssist is an AI-powered platform that helps you understand and address privacy concerns in your datasets before sharing them. It combines data quality analysis, privacy risk assessment, and an intelligent chatbot assistant to provide personalized guidance on secure data sharing practices.

## ✨ Key Features

- **🔍 Data Privacy Analysis**: Assess privacy risks in your dataset with entropy metrics and identification of sensitive data columns
- **📊 Data Quality Assessment**: Evaluate data completeness, accuracy, and consistency with customizable constraints
- **🤖 AI Assistant**: Chat with our LLM-powered assistant to get personalized guidance on data sharing best practices
- **📝 Report Generation**: Create detailed PDF or JSON reports on privacy risks and data quality metrics
- **🧠 Knowledge Base**: Utilizes RAG (Retrieval-Augmented Generation) for context-aware responses about data privacy regulations and practices

## 📋 Requirements

- Python 3.13
- pip (Python package manager)

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/anshu0612/llm-chatbot-data-privacy-assist.git
   cd llm-chatbot-data-privacy-assist
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys (OpenAI, Anthropic) and configure other settings
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and settings
   ```

## 🏃‍♂️ Getting Started

1. Run the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:3000
   ```

3. Follow the 3-step guided workflow:
   - **Step 1**: Upload your dataset (CSV/Excel file)
   - **Step 2**: Review privacy and data quality analysis
   - **Step 3**: Chat with the AI assistant for personalized guidance

## 📱 User Journey

DataSharingAssist guides you through a seamless 3-step process:

1. **Upload Dataset**: Upload your CSV or Excel file to begin the analysis
2. **Review Analysis**: Examine the privacy scores and data quality metrics
3. **Chat with Assistant**: Get personalized guidance on how to address identified issues

## 💻 Developer Information

### Project Structure

```
.
├── app.py                 # Main application file
├── components/            # UI components
├── utils/                 # Utility functions for analysis
├── knowledge_base/        # Storage for RAG documents
├── assets/                # CSS, JS, and image files
└── requirements.txt       # Python dependencies
```

### Key Technologies

- **Dash & Plotly**: Interactive web interface
- **LangChain**: Framework for LLM applications
- **OpenAI/Anthropic**: LLM providers
- **ChromaDB**: Vector database for RAG implementation
- **Pandas & NumPy**: Data analysis libraries
- **scikit-learn**: Machine learning for data analysis

