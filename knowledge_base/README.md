# Knowledge Base Setup

This directory contains the knowledge base documents for the Data Privacy Assist application.

## Directory Structure

```
knowledge_base/
├── embeddings/     # Contains the vector database
└── *.pdf          # Your PDF documents
```

## Adding Documents

1. Place your PDF documents directly in this directory
2. Documents should be Singapore privacy policy related, such as:
   - IM8 Policy Documents
   - Public Sector Data Security Review Committee (PSDSRC) Guidelines
   - Government Instruction Manual 8 (IM8) on IT Security
   - Public Sector (Governance) Act
   - Data Privacy Best Practices
   - Government Privacy Standards

## Generating Embeddings

After adding documents, run the ingestion script:

```bash
python3 ingest_documents.py
```

This will:
1. Process all PDF files in this directory
2. Generate embeddings using OpenAI's embedding model
3. Store the embeddings in the `embeddings/` directory

## Important Notes

- The embeddings must be generated before the chatbot can use RAG functionality
- New documents require re-running the ingestion script
- Make sure your OpenAI API key is set in the `.env` file
- Large documents may take some time to process
