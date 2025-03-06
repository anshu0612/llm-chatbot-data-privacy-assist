"""
Script to ingest documents into the RAG knowledge base.
"""

import os
import logging
from utils.rag_processor import RAGProcessor
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main function to ingest documents."""
    logger.info("Starting document ingestion process...")
    
    # Initialize RAG processor
    rag = RAGProcessor(
        knowledge_base_dir="./knowledge_base/more",
        embeddings_dir="./knowledge_base/embeddings",
        chunk_size=1000,
        chunk_overlap=200,
        use_openai_embeddings=True
    )
    
    # Ingest documents
    success = rag.ingest_documents()
    
    if success:
        logger.info("✅ Document ingestion completed successfully!")
    else:
        logger.error("❌ Document ingestion failed!")

if __name__ == "__main__":
    main()
