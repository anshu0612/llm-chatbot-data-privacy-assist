"""
Knowledge Manager Component for Data Privacy Assist.

This component provides a UI for managing the knowledge base used by the RAG system,
including uploading PDF documents and processing them for use with the chatbot.
"""

import os
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State
from dash_iconify import DashIconify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_knowledge_manager_component():
    """Create the knowledge management component for the RAG system."""
    return html.Div(
        [
            html.Div(
                [
                    html.H4("Knowledge Base Management", className="mb-3 privacy-recommendation-title"),
                    html.Div(
                        [
                            html.Span("Singapore Policy Document Repository"),
                            html.Span(
                                "ACTIVE",
                                className="ms-2 badge bg-primary",
                                style={
                                    "backgroundColor": "var(--primary) !important",
                                    "fontSize": "10px",
                                    "fontWeight": "500",
                                    "paddingTop": "3px",
                                    "paddingBottom": "3px"
                                }
                            )
                        ],
                        className="text-muted mb-3 small d-flex align-items-center"
                    ),
                ],
                className="mb-3"
            ),
            
            # Document Upload Section
            html.Div(
                [
                    html.H5("Upload Policy Documents", className="mb-3"),
                    html.P(
                        "Upload Singapore privacy regulation PDF documents to enhance the chatbot's knowledge.",
                        className="text-muted"
                    ),
                    dcc.Upload(
                        id="policy-document-upload",
                        children=html.Div(
                            [
                                html.Div(className="upload-icon"),
                                html.Div(
                                    "Drag and Drop or Select PDF Files",
                                    className="upload-text"
                                ),
                                html.Div(
                                    "Supported format: PDF (max 100 MB per file)",
                                    className="upload-hint"
                                ),
                            ],
                            className="upload-area d-flex flex-column align-items-center justify-content-center",
                        ),
                        style={
                            "width": "100%",
                            "height": "180px",
                            "borderRadius": "8px",
                            "cursor": "pointer",
                        },
                        multiple=True,
                        accept="application/pdf",
                    ),
                    html.Div(id="policy-upload-status", className="mt-2"),
                    
                    # Process Documents Button
                    html.Div(
                        [
                            dbc.Button(
                                "Process Documents",
                                id="process-documents-btn",
                                color="primary",
                                className="mt-3 run-analysis-btn"
                            ),
                        ],
                        className="d-flex justify-content-between align-items-center mt-2"
                    ),
                ],
                className="mb-4 p-3 border-bottom"
            ),
            
            # Knowledge Base Status
            html.Div(
                [
                    html.H5("Knowledge Base Status", className="mb-3"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.P("Indexed Documents", className="mb-1 text-muted small"),
                                    html.H6(id="indexed-document-count", children="Loading...", className="mb-0")
                                ],
                                className="me-4"
                            ),
                            html.Div(
                                [
                                    html.P("Text Chunks", className="mb-1 text-muted small"),
                                    html.H6(id="text-chunk-count", children="Loading...", className="mb-0")
                                ],
                                className="me-4"
                            ),
                            html.Div(
                                [
                                    html.P("Status", className="mb-1 text-muted small"),
                                    html.Div(
                                        [
                                            html.Span(id="kb-status", children="Loading..."),
                                            html.Span(
                                                "",
                                                id="kb-status-indicator",
                                                className="status-indicator ms-2"
                                            )
                                        ],
                                        className="d-flex align-items-center"
                                    )
                                ]
                            )
                        ],
                        className="d-flex"
                    ),
                ],
                className="mb-3 p-3"
            ),
            
            # Document Management
            html.Div(
                [
                    html.H5("Manage Documents", className="mb-3"),
                    html.Div(id="document-list-container", children=[
                        html.P("Loading document list...", className="text-muted")
                    ]),
                ],
                className="p-3"
            ),
        ],
        className="knowledge-manager p-4",
        style={
            "backgroundColor": "var(--surface)",
            "border": "none",
            "borderRadius": "16px",
            "boxShadow": "var(--elevation-2)",
            "height": "100%"
        }
    )

@callback(
    [
        Output("policy-upload-status", "children"),
        Output("indexed-document-count", "children"),
        Output("text-chunk-count", "children"),
        Output("kb-status", "children"),
        Output("kb-status-indicator", "className"),
    ],
    [Input("process-documents-btn", "n_clicks")],
    prevent_initial_call=True
)
def process_documents(n_clicks):
    """Process the uploaded documents and update the knowledge base."""
    from utils.rag_processor import RAGProcessor
    
    if n_clicks is None:
        return (
            "No files processed yet.", 
            "0",
            "0",
            "Not Started",
            "status-indicator"
        )
    
    try:
        # Initialize the RAG processor
        rag_processor = RAGProcessor(
            knowledge_base_dir="./knowledge_base",
            embeddings_dir="./knowledge_base/embeddings"
        )
        
        # Process the documents
        success = rag_processor.ingest_documents()
        
        if success:
            # Get stats
            stats = rag_processor.get_doc_stats()
            return (
                html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        "Documents processed and indexed successfully!"
                    ],
                    className="text-success"
                ),
                f"{len(os.listdir('./knowledge_base')) - 1}",  # Subtract embeddings dir
                f"{stats.get('document_chunks', 0)}",
                "Active",
                "status-indicator active"
            )
        else:
            return (
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-circle me-2 text-warning"),
                        "No documents found to process. Please upload PDF files."
                    ],
                    className="text-warning"
                ),
                "0",
                "0",
                "Inactive",
                "status-indicator"
            )
    except Exception as e:
        logger.error(f"Error processing documents: {e}")
        return (
            html.Div(
                [
                    html.I(className="fas fa-times-circle me-2 text-danger"),
                    f"Error processing documents: {str(e)}"
                ],
                className="text-danger"
            ),
            "Error",
            "Error",
            "Error",
            "status-indicator"
        )

@callback(
    Output("document-list-container", "children"),
    [Input("process-documents-btn", "n_clicks")],
)
def update_document_list(n_clicks):
    """Update the list of documents in the knowledge base."""
    try:
        knowledge_base_dir = "./knowledge_base"
        
        # List PDF files in the knowledge base directory
        pdf_files = []
        if os.path.exists(knowledge_base_dir):
            for file in os.listdir(knowledge_base_dir):
                if file.lower().endswith(".pdf"):
                    file_path = os.path.join(knowledge_base_dir, file)
                    file_size = os.path.getsize(file_path)
                    file_size_mb = file_size / (1024 * 1024)
                    file_size_str = f"{file_size_mb:.2f} MB"
                    
                    pdf_files.append({
                        "name": file,
                        "path": file_path,
                        "size": file_size_str
                    })
        
        if not pdf_files:
            return html.P("No documents found in the knowledge base.", className="text-muted")
        
        return html.Div(
            [
                html.Ul(
                    [
                        html.Li(
                            [
                                html.Div(
                                    [
                                        html.Span(
                                            DashIconify(
                                                icon="mdi:file-pdf-box",
                                                width=24,
                                                className="me-2",
                                                style={"color": "var(--primary)"}
                                            ),
                                            className="me-2"
                                        ),
                                        html.Span(file["name"], className="me-2"),
                                        html.Span(
                                            file["size"],
                                            className="badge bg-light text-dark"
                                        )
                                    ],
                                    className="d-flex align-items-center"
                                )
                            ],
                            className="list-group-item d-flex justify-content-between align-items-center"
                        )
                        for file in pdf_files
                    ],
                    className="list-group"
                )
            ]
        )
    except Exception as e:
        logger.error(f"Error updating document list: {e}")
        return html.P(f"Error loading document list: {str(e)}", className="text-danger")

@callback(
    Output("policy-upload-status", "children", allow_duplicate=True),
    [Input("policy-document-upload", "contents")],
    [State("policy-document-upload", "filename")],
    prevent_initial_call=True
)
def upload_policy_documents(contents, filenames):
    """Handle file uploads and save them to the knowledge base directory."""
    if contents is None or filenames is None:
        return "No files uploaded."
    
    knowledge_base_dir = "./knowledge_base"
    os.makedirs(knowledge_base_dir, exist_ok=True)
    
    saved_files = []
    failed_files = []
    
    for content, filename in zip(contents, filenames):
        try:
            # Check file extension
            if not filename.lower().endswith(".pdf"):
                failed_files.append(f"{filename} (not a PDF file)")
                continue
            
            # Decode and save the file
            import base64
            content_type, content_string = content.split(",")
            decoded = base64.b64decode(content_string)
            
            file_path = os.path.join(knowledge_base_dir, filename)
            with open(file_path, "wb") as file:
                file.write(decoded)
            
            saved_files.append(filename)
            
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            failed_files.append(f"{filename} ({str(e)})")
    
    if saved_files and not failed_files:
        return html.Div(
            [
                html.I(className="fas fa-check-circle me-2 text-success"),
                f"Successfully uploaded {len(saved_files)} files. Click 'Process Documents' to index them."
            ],
            className="text-success"
        )
    elif saved_files and failed_files:
        return html.Div(
            [
                html.I(className="fas fa-exclamation-circle me-2 text-warning"),
                f"Uploaded {len(saved_files)} files, but {len(failed_files)} failed. Click 'Process Documents' to index the successful uploads."
            ],
            className="text-warning"
        )
    else:
        return html.Div(
            [
                html.I(className="fas fa-times-circle me-2 text-danger"),
                f"Failed to upload all files: {', '.join(failed_files)}"
            ],
            className="text-danger"
        )
