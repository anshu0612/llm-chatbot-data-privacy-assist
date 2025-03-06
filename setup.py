#!/usr/bin/env python3
import os
import shutil
import sys

def setup_environment():
    """Set up the environment for the Data Privacy Assist application."""
    print("\n===== Data Privacy Assist Setup =====")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        if os.path.exists(".env.sample"):
            shutil.copy(".env.sample", ".env")
            print("✅ Created .env file from sample")
        else:
            with open(".env", "w") as f:
                f.write("# OpenAI API configuration\n")
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n\n")
                f.write("# Application settings\n")
                f.write("DEBUG=True\n")
                f.write("UPLOAD_FOLDER=./uploads\n")
                f.write("MAX_CONTENT_LENGTH=16777216  # 16MB max file size\n")
            print("✅ Created .env file")
    else:
        print("✅ .env file already exists")
    
    # Create uploads directory if it doesn't exist
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        print("✅ Created uploads directory")
    else:
        print("✅ Uploads directory already exists")
    
    # Prompt user to set OpenAI API key
    print("\n🔑 Please edit the .env file to add your OpenAI API key.")
    print("   You can use any text editor to modify the .env file.")
    
    # Check if wkhtmltopdf is installed (required for PDF generation)
    print("\n🔍 Checking for wkhtmltopdf (required for PDF generation)...")
    exit_code = os.system("which wkhtmltopdf > /dev/null 2>&1")
    if exit_code == 0:
        print("✅ wkhtmltopdf is installed")
    else:
        print("⚠️  wkhtmltopdf is not installed")
        print("   PDF generation will fall back to HTML if wkhtmltopdf is not available.")
        print("   To install wkhtmltopdf:")
        print("   - On macOS: brew install wkhtmltopdf")
        print("   - On Ubuntu: sudo apt-get install wkhtmltopdf")
        print("   - On Windows: Download from https://wkhtmltopdf.org/downloads.html")
    
    print("\n✨ Setup complete! You can now run the application with:")
    print("   python app.py")
    print("==================================\n")

if __name__ == "__main__":
    setup_environment()
