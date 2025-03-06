"""
Retrieval Augmented Generation (RAG) processor for the Data Privacy Assist application.
This module handles the processing of PDF documents and provides RAG functionality for the chatbot.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple

# LangChain and embedding imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document

# Environment variable handling
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGProcessor:
    """
    Class to handle RAG functionality including document ingestion, 
    embedding generation, and knowledge retrieval.
    """
    
    def __init__(self, 
                knowledge_base_dir: str = "./knowledge_base",
                embeddings_dir: str = "./knowledge_base/embeddings",
                chunk_size: int = 1000,
                chunk_overlap: int = 200,
                use_openai_embeddings: bool = False):
        """
        Initialize the RAG processor.
        
        Args:
            knowledge_base_dir: Directory containing the policy documents
            embeddings_dir: Directory to store the vector database
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks to maintain context
            use_openai_embeddings: Whether to use OpenAI embeddings (otherwise HuggingFace)
        """
        self.knowledge_base_dir = knowledge_base_dir
        self.embeddings_dir = embeddings_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_openai_embeddings = use_openai_embeddings
        
        # Create directories if they don't exist
        os.makedirs(knowledge_base_dir, exist_ok=True)
        os.makedirs(embeddings_dir, exist_ok=True)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # Initialize embeddings model
        if use_openai_embeddings:
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",  # Most cost-effective OpenAI embedding model ($0.00002 per 1K tokens)
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                chunk_size=1000,  # Process texts in chunks of 1000 tokens
                max_retries=3,    # Retry failed requests up to 3 times
                show_progress_bar=True  # Show progress when embedding large texts
            )
            logger.info("Initialized OpenAI embeddings with model: text-embedding-3-small")
        else:
            # Use a smaller model suitable for local deployment
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            logger.info("Initialized HuggingFace embeddings with model: all-MiniLM-L6-v2")
        
        # Set up vector database
        self._initialize_vector_db()
    
    def _initialize_vector_db(self) -> None:
        """Initialize or load the vector database."""
        try:
            # Check if vector database already exists
            if os.path.exists(os.path.join(self.embeddings_dir, 'chroma.sqlite3')):
                logger.info("Loading existing vector database...")
                self.vector_db = Chroma(
                    persist_directory=self.embeddings_dir, 
                    embedding_function=self.embeddings
                )
                logger.info(f"Vector database loaded with {self.vector_db._collection.count()} documents")
            else:
                logger.info("No existing vector database found.")
                self.vector_db = None
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            self.vector_db = None
    
    def ingest_documents(self, specific_dir: Optional[str] = None) -> bool:
        """
        Process and ingest all PDF documents in the specified directory.
        
        Args:
            specific_dir: Optional specific directory to process, if None uses knowledge_base_dir
            
        Returns:
            bool: True if ingestion was successful, False otherwise
        """
        target_dir = specific_dir if specific_dir else self.knowledge_base_dir
        
        try:
            # Load all PDF documents from the directory
            logger.info(f"Loading documents from {target_dir}...")
            loader = DirectoryLoader(
                target_dir, 
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=True
            )
            
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} documents")
            
            if not documents:
                logger.warning("No documents found to process")
                return False
            
            # Split documents into chunks
            logger.info("Splitting documents into chunks...")
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Created {len(chunks)} text chunks")
            
            # Create or update vector database
            logger.info("Creating vector database...")
            self.vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.embeddings_dir
            )
            
            # Persist the database
            self.vector_db.persist()
            logger.info(f"Vector database created and persisted with {len(chunks)} chunks")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting documents: {e}")
            return False
    
    def query_knowledge_base(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Query the knowledge base for relevant documents.
        
        Args:
            query: The query string
            top_k: Number of most relevant documents to return
            
        Returns:
            List of documents with content and metadata
        """
        if not self.vector_db:
            logger.warning("Vector database not initialized. Please ingest documents first.")
            return []
        
        try:
            # Similarity search
            relevant_docs = self.vector_db.similarity_search(query, k=top_k)
            logger.info(f"Retrieved {len(relevant_docs)} documents for query: {query[:50]}...")
            return relevant_docs
        
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return []
    
    def get_relevant_context(self, query: str, top_k: int = 5, include_citations: bool = True) -> dict:
        """
        Get relevant context and citation information.
        
        Args:
            query: The query string
            top_k: Number of most relevant documents to include
            include_citations: Whether to include citation information
            
        Returns:
            Dictionary with context text and citation information if requested
        """
        docs = self.query_knowledge_base(query, top_k)
        
        if not docs:
            return {"context": "", "citations": []}
        
        # Format the context
        context_parts = []
        citations = []
        
        for i, doc in enumerate(docs):
            source = doc.metadata.get('source', 'Unknown source')
            source_filename = os.path.basename(source) if source != 'Unknown source' else 'Unknown'
            page = doc.metadata.get('page', 'Unknown page')
            
            # Create a citation ID
            citation_id = f"citation-{i+1}"
            
            # Add to context
            context_parts.append(
                f"Document {i+1} [#{citation_id}] (Source: {source_filename}, Page: {page}):\n{doc.page_content}\n"
            )
            
            # Add to citations
            if include_citations:
                citation_obj = {
                    "id": citation_id,
                    "source": source,
                    "source_filename": source_filename,
                    "page": page,
                    "content": doc.page_content,
                    "score": getattr(doc, 'score', None),  # Include relevance score if available
                    "section": self._extract_section_title(doc.page_content)
                }
                citations.append(citation_obj)
        
        return {
            "context": "\n".join(context_parts),
            "citations": citations
        }
    
    def _extract_section_title(self, text: str, max_length: int = 100) -> str:
        """
        Attempt to extract a section title from the text.
        
        Args:
            text: The document text
            max_length: Maximum length for the section title
            
        Returns:
            Extracted section title or first few words
        """
        # Try to find a title - often the first line or a line with specific formatting
        lines = text.split('\n')
        if not lines:
            return "Unknown section"
            
        # Try the first line that's not empty as the title
        for line in lines:
            line = line.strip()
            if line and len(line) < max_length:
                return line
            elif line:
                # If no short line found, use the first part of the first non-empty line
                return line[:max_length] + "..." if len(line) > max_length else line
                
        return "Unknown section"
    
    def get_doc_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the ingested documents.
        
        Returns:
            Dictionary with statistics
        """
        if not self.vector_db:
            return {"status": "No documents ingested"}
        
        try:
            doc_count = self.vector_db._collection.count()
            return {
                "status": "Ready",
                "document_chunks": doc_count,
                "embeddings_dir": self.embeddings_dir
            }
        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            return {"status": f"Error: {str(e)}"}
