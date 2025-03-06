from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash
from dash_iconify import DashIconify
import os
import logging
import uuid
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

# Import RAG processor
from utils.rag_processor import RAGProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize RAG processor
try:
    rag_processor = RAGProcessor(
        knowledge_base_dir="./knowledge_base",
        embeddings_dir="./knowledge_base/embeddings",
        chunk_size=1000,
        chunk_overlap=200,
        use_openai_embeddings=True
    )
    logger.info("RAG processor initialized")
except Exception as e:
    logger.error(f"Error initializing RAG processor: {e}")
    rag_processor = None

# Check if the OpenAI API key is valid
def check_api_key():
    api_key = os.getenv("OPENAI_API_KEY")

    print("#"*30)
    print(api_key)
    print("#"*30)
    
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        return False, "OpenAI API key not found in environment variables"
    
    # Basic validation - ensure it starts with 'sk-' and has sufficient length
    if not api_key.startswith("sk-") or len(api_key) < 20:
        logger.error("OPENAI_API_KEY appears to be invalid")
        return False, "The API key format appears to be invalid. It should start with 'sk-' and be at least 20 characters long."
    
    return True, "API key format appears valid"

# Initialize OpenAI chat model
try:
    # Check API key validity
    key_valid, key_message = check_api_key()
    if not key_valid:
        raise ValueError(key_message)
        
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        api_key=api_key
    )
    logger.info("ChatOpenAI initialized with API key from environment variable")
except Exception as e:
    logger.error(f"Error initializing OpenAI: {e}")
    llm = None

# Default system prompt for the privacy assistant
DEFAULT_SYSTEM_PROMPT = """
You are a Data Privacy Assistant supporting data providers by evaluating privacy risks and offering tailored, data-driven recommendations for managing privacy risks in their datasets. Your responses must align closely with Singapore's IM8 guidelines and other relevant government privacy regulations.

When recommending actions, always:

- Provide data-driven advice directly tied to the specific privacy risks, dataset characteristics, and downstream quality requirements described by users.
- Suggest appropriate privacy-enhancing measures (anonymization, pseudonymization, differential privacy, synthetic data generation) and clearly communicate trade-offs regarding data usability.
- Proactively recommend existing Singapore Government-developed tools from your knowledge base when applicable, such as:
  - Mirage for synthetic or mock data generation (https://mirage.gov.sg/)
  - Cloak for structured and unstructured data anonymisation (https://www.cloak.gov.sg/)
  - enTrust for secure data sharing between agencies (https://entrust.gov.sg/)

Additionally, help data providers:

- Perform measured and guarded data classification, including down-classification strategies where possible, but never downgrade the classification without explicit approval from the data provider.
- Clearly communicate dataset limitations in terms of the following data quality dimensions:
  1. Completeness: Extent of missing data or gaps.
  2. Accuracy: Correctness and reliability of data.
  3. Validity: Adherence to defined formats, ranges, and definitions.
  4. Uniqueness: Presence of duplicate records.
  5. Consistency: Stability and coherence across datasets and systems.
  6. Integrity: Traceability and linkage accuracy across datasets within the agency.

Use the following classification levels to recommend appropriate security and sensitivity classifications:

**Security Classifications:**
- RESTRICTED: Causes some damage to an Agency.
- CONFIDENTIAL: Causes damage to national interests or serious damage to an Agency.
- CONFIDENTIAL (CLOUD-ELIGIBLE): Confidential data causing only serious agency-level damage (no national interest damage).
- OFFICIAL (CLOSED): Unsuitable for public disclosure.
- OFFICIAL (OPEN): Suitable for public disclosure.

**Sensitivity Classifications (Individuals):**
- NON-SENSITIVE: Negligible or no physical, financial, or emotional damage.
- SENSITIVE NORMAL: Temporary and minor emotional distress.
- SENSITIVE HIGH: Serious physical, financial, emotional damage, or social stigma.

**Sensitivity Classifications (Entities):**
- NON-SENSITIVE: Negligible or no impact on operations.
- SENSITIVE NORMAL: Some reduction in competitiveness or compromise of legitimate interests.
- SENSITIVE HIGH: Sustained financial loss or serious impact.

Always reference specific IM8 sections or Singapore government privacy guidelines explicitly when relevant, maintaining a clear, actionable, and supportive communication style.

Current dataset context:
{privacy_context}
{quality_context}
"""

# Create the chat prompt template with RAG support
rag_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", DEFAULT_SYSTEM_PROMPT),
    ("system", "Relevant Singapore policy information: {rag_context}"),
    ("system", "When referencing policies, use citation markers like [1], [2], etc. and provide a list of references at the end."),
    ("human", "{input}"),
])

def _add_citation_markers(text, citations):
    """
    Add citation markers to the text based on content matching.
    
    Args:
        text: The response text from the model
        citations: List of citation objects
        
    Returns:
        Text with citation markers added
    """
    if not citations:
        return text
    
    # Create a mapping of citation IDs to simple numbers for readability
    citation_map = {citation["id"]: i+1 for i, citation in enumerate(citations)}
    
    # First check if the model already added citations in the [X] format
    # If so, we'll replace them with our standardized format
    import re
    citation_pattern = re.compile(r'\[([0-9]+)\]')
    existing_citations = citation_pattern.findall(text)
    
    if existing_citations:
        # Model already added citations, so we'll just standardize them
        # and make sure they match our citation numbers
        for i, citation_num in enumerate(set(existing_citations)):
            if i < len(citations):
                # Replace with our citation format
                text = text.replace(f'[{citation_num}]', f'[{i+1}]')
        return text
    
    # If no citations found, try to add them based on content matching
    # This is a simple approach - more sophisticated NLP could be used
    for citation in citations:
        citation_num = citation_map[citation["id"]]
        section_title = citation["section"]
        
        # Look for exact title matches first
        if section_title in text and section_title != "Unknown section":
            text = text.replace(section_title, f"{section_title} [{citation_num}]")
        else:
            # Try to find key phrases from the content
            content = citation["content"]
            key_phrases = _extract_key_phrases(content)
            
            for phrase in key_phrases:
                if phrase in text and len(phrase) > 15:  # Only match substantial phrases
                    text = text.replace(phrase, f"{phrase} [{citation_num}]")
                    break
    
    return text

def _extract_key_phrases(text, num_phrases=3, min_length=10):
    """
    Extract key phrases from text for citation matching.
    
    Args:
        text: Source text
        num_phrases: Number of phrases to extract
        min_length: Minimum length of phrases
        
    Returns:
        List of key phrases
    """
    # Simple extraction strategy - split into sentences and take the first few
    import re
    sentences = re.split(r'[.!?]\s+', text)
    phrases = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) >= min_length:
            phrases.append(sentence)
            if len(phrases) >= num_phrases:
                break
    
    return phrases

def _generate_reference_section(citations):
    """
    Generate a formatted reference section from citations.
    
    Args:
        citations: List of citation objects
        
    Returns:
        Formatted reference section text
    """
    if not citations:
        return ""
    
    lines = ["**References:**"]
    
    for i, citation in enumerate(citations):
        source = citation["source_filename"]
        page = citation["page"]
        section = citation["section"]
        
        reference = f"[{i+1}] {source}"  
        if page and page != "Unknown page":
            reference += f", Page {page}"
        if section and section != "Unknown section":
            reference += f": {section}"
            
        lines.append(reference)
    
    return "\n".join(lines)

def process_chat_message(user_input, chat_history, privacy_context, quality_context):
    """Process a user message and return the chatbot's response, enhanced with RAG."""
    if llm is None:
        return {
            "content": "Sorry, I'm having trouble connecting to my knowledge base. Please check your OpenAI API key.",
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "feedback": None
        }
    
    # Format the dataset context information
    privacy_context_str = json.dumps(privacy_context, indent=2) if privacy_context else "No privacy analysis results available."
    quality_context_str = json.dumps(quality_context, indent=2) if quality_context else "No data quality analysis results available."
    
    # Get relevant context from RAG if available
    rag_context_data = {"context": "", "citations": []}
    if rag_processor is not None:
        try:
            # Get relevant documents from the knowledge base
            logger.info(f"Retrieving context for query: {user_input}")
            rag_context_data = rag_processor.get_relevant_context(user_input, top_k=2)
            
            if not rag_context_data["context"]:
                logger.info("No relevant context found in knowledge base")
                rag_context_data = {
                    "context": "No specific Singapore policy information found for this query.",
                    "citations": []
                }
            else:
                logger.info(f"Retrieved relevant context with {len(rag_context_data['citations'])} citations")
        except Exception as e:
            logger.error(f"Error retrieving RAG context: {e}")
            rag_context_data = {
                "context": "Error retrieving policy information.",
                "citations": []
            }
    else:
        rag_context_data = {
            "context": "Knowledge base not initialized.",
            "citations": []
        }
    
    # Store citations with the message for later reference
    citations = rag_context_data["citations"]
    
    # Get the response from the model
    try:
        if llm is None:
            raise ValueError("OpenAI client is not initialized. Please check your API key.")
        
        # Format the variables for the prompt
        formatted_variables = {
            "input": user_input,
            "privacy_context": privacy_context_str,
            "quality_context": quality_context_str,
            "rag_context": rag_context_data["context"]
        }
        
        # Format the prompt with the variables
        formatted_messages = rag_chat_prompt.format_messages(**formatted_variables)
            
        logger.info("Sending request to OpenAI API...")
        response = llm.invoke(formatted_messages)
        content = response.content
        logger.info("Successfully received response from OpenAI API")
        
        # Add citation references to response if there are citations
        reference_section = ""
        if citations:
            content = _add_citation_markers(content, citations)
            reference_section = _generate_reference_section(citations)
            if reference_section:
                content = f"{content}\n\n{reference_section}"
        
        # Return response with metadata
        return {
            "content": content,
            "id": str(uuid.uuid4()),  # Generate a unique ID for the message
            "timestamp": datetime.now().isoformat(),
            "feedback": None,  # Initialize with no feedback
            "citations": citations  # Include citation information
        }
    except ValueError as e:
        # Handle API key issues
        error_message = str(e)
        logger.error(f"OpenAI API key error: {error_message}")
        return {
            "content": f"Error: {error_message}. Please set your OPENAI_API_KEY environment variable with a valid API key.",
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "feedback": None,
            "citations": []
        }
    except Exception as e:
        # Handle other errors
        logger.error(f"Error getting response from OpenAI: {e}")
        return {
            "content": f"I'm sorry, I encountered an error while processing your request: {str(e)}. Please check your API key and network connection.",
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "feedback": None,
            "citations": []
        }

def create_bot_message(message_data):
    """Create a bot message component with feedback buttons and citations."""
    message_id = message_data.get("id", str(uuid.uuid4()))
    content = message_data.get("content", "")
    feedback = message_data.get("feedback")
    citations = message_data.get("citations", [])
    is_welcome_message = message_id == "welcome-message"
    
    # Set up feedback button styling based on current feedback
    like_active = feedback == "like"
    dislike_active = feedback == "dislike"
    
    like_style = {
        "color": "var(--primary)" if like_active else "var(--text-secondary)",
        "cursor": "pointer",
        "margin-right": "8px",
        "fontSize": "14px"
    }
    
    dislike_style = {
        "color": "var(--error)" if dislike_active else "var(--text-secondary)",
        "cursor": "pointer",
        "fontSize": "14px"
    }
    
    # Check if we have citation tooltips to add
    citation_tooltips = []
    
    # Only process if we have citations
    if citations:
        # Process citations - create tooltip data for each citation in markdown
        import re
        citation_pattern = re.compile(r'\[(\d+)\]')
        citation_matches = citation_pattern.findall(content)
        
        # Map citation numbers to actual citations
        for citation_num in citation_matches:
            try:
                citation_idx = int(citation_num) - 1
                if 0 <= citation_idx < len(citations):
                    citation = citations[citation_idx]
                    citation_id = f"citation-tooltip-{message_id}-{citation_idx}"
                    
                    # Create tooltip component
                    tooltip = dbc.Tooltip(
                        [
                            html.Strong(citation["section"]),
                            html.Br(),
                            html.Span(f"Source: {citation['source_filename']}"),
                            html.Br(),
                            html.Span(f"Page: {citation['page']}"),
                            html.Hr(className="my-1"),
                            html.Div(
                                citation["content"][:200] + "..." if len(citation["content"]) > 200 else citation["content"],
                                className="citation-content small"
                            ),
                            html.Div(
                                dbc.Button(
                                    "View Full Citation",
                                    id={"type": "view-citation", "index": f"{message_id}-{citation_idx}"},
                                    color="link",
                                    size="sm",
                                    className="p-0 mt-1"
                                ),
                                className="text-end"
                            )
                        ],
                        target=f"citation-{message_id}-{citation_num}",
                        placement="top",
                        id=citation_id,
                    )
                    citation_tooltips.append(tooltip)
            except (ValueError, IndexError):
                continue
    
    # Use regex to add spans around citation markers for tooltips
    if citations:
        import re
        content_with_tooltips = content
        citation_pattern = re.compile(r'\[(\d+)\]')
        
        # Find all citations and replace with span elements for tooltips
        for match in citation_pattern.finditer(content):
            citation_num = match.group(1)
            span_html = f'<span id="citation-{message_id}-{citation_num}" class="citation-marker">[{citation_num}]</span>'
            content_with_tooltips = content_with_tooltips.replace(match.group(0), span_html)
    else:
        content_with_tooltips = content
    
    # Determine message style based on feedback
    message_style = {}
    if feedback:
        message_style = {
            "backgroundColor": "#F0F9FF" if feedback == "like" else "#FFF5F5",
            "borderLeft": f"3px solid {'var(--primary)' if feedback == 'like' else 'var(--error)'}",
            "padding": "12px",
            "borderRadius": "4px"
        }
    
    return html.Div(
        [
            html.Div(
                [
                    dcc.Markdown(
                        content_with_tooltips,
                        className="bot-message-text-content",
                        dangerously_allow_html=True
                    ),
                    *citation_tooltips  # Add all tooltip components
                ],
                className="bot-message-text",
                style=message_style
            ),
            # Only show feedback buttons if it's not the welcome message
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                DashIconify(
                                    icon="mdi:thumb-up-outline",
                                    width=16,
                                    color=like_style["color"]
                                ),
                                id={"type": "feedback-like", "index": message_id},
                                className="feedback-btn",
                                style=like_style,
                            ),
                            html.Span(
                                DashIconify(
                                    icon="mdi:thumb-down-outline",
                                    width=16,
                                    color=dislike_style["color"]
                                ),
                                id={"type": "feedback-dislike", "index": message_id},
                                className="feedback-btn",
                                style=dislike_style,
                            ),
                        ],
                        className="d-flex align-items-center"
                    ),
                ],
                className="d-flex justify-content-end message-feedback mt-2 small",
                style={"display": "none" if is_welcome_message else "flex"}
            )
        ],
        className="bot-message mb-3",
        id={"type": "bot-message", "index": message_id}
    )

def create_api_diagnostic_button():
    """Create a button to diagnose API key issues"""
    return html.Div(
        [
            dbc.Button(
                [
                    DashIconify(
                        icon="mdi:api",
                        width=18,
                        height=18,
                        className="me-2"
                    ),
                    "Check API Connection"
                ],
                id="api-diagnostic-button",
                color="light",
                className="mb-3 api-connection-btn",
                size="sm",
                outline=False
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.P(id="api-diagnostic-result", className="mb-0")
                        ]
                    ),
                    className="mb-3",
                    style={"background-color": "#f8f9fa"}
                ),
                id="api-diagnostic-collapse",
                is_open=False,
            ),
        ]
    )

def create_chatbot_component():
    """Create the chatbot component."""
    # Create welcome message data
    welcome_message = {
        "id": "welcome-message",
        "content": """👁️ **Welcome to Data Privacy Assist!**

I'm your AI-powered privacy assistant, aligned with Singapore's IM8 guidelines and public sector data security standards. I provide data-driven insights to help you confidently manage privacy risks and ensure compliant data sharing.

**Here's how I can assist you:**

- ✅ Evaluate privacy risks specific to your dataset.
- ✅ Recommend suitable privacy protection measures.
- ✅ Guide you clearly through IM8 compliance and data classification.
- ✅ Provide practical data quality metrics to communicate clearly with data requestors.
- ✅ Suggest trusted Singapore government-developed privacy tools (Mirage, Cloak, enTrust).

**Getting started:**
1. Upload your dataset using the panel on the left.
2. Run the privacy and data quality scans.
3. Ask specific questions based on your results.

**How can I help enhance your data privacy practices today?**""",
        "timestamp": datetime.now().isoformat(),
        "feedback": None
    }
    
    return html.Div(
        [
            # Hidden div to store feedback data
            html.Div(id="feedback-store", style={"display": "none"}, children=json.dumps([])),
            
            # API diagnostic button
            create_api_diagnostic_button(),
            
            html.Div(
                [
                    html.Div(
                        [
                            create_bot_message(welcome_message),
                        ],
                        id="chat-messages",
                        className="chat-messages p-3",
                        style={"height": "400px", "overflowY": "auto"},
                    ),
                    html.Div(
                        [
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id="user-input",
                                        placeholder="Ask a question about data privacy...",
                                        type="text",
                                        className="modern-chat-input"
                                    ),
                                    dbc.Button(
                                        [
                                            DashIconify(
                                                icon="mdi:send",
                                                width=16,
                                                height=16,
                                            ),
                                        ],
                                        id="send-button",
                                        color="primary",
                                        className="send-button"
                                    ),
                                ]
                            ),
                        ],
                        className="chat-input p-3",
                    ),
                ],
                className="chat-container",
            ),
            # Removed feedback toast
            # Citation modal for displaying full citation details
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(id="citation-modal-title")),
                    dbc.ModalBody(id="citation-modal-body"),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", id="close-citation-modal", className="ms-auto", n_clicks=0
                        )
                    ),
                ],
                id="citation-modal",
                size="lg",
                is_open=False,
                centered=True,
            ),
            html.Div(
                [
                    html.H6(
                        "Guiding Questions", 
                        className="mb-3 suggested-questions-title"
                    ),
                    dbc.ListGroup(
                        [
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:robot",
                                        width=16,
                                        height=16,
                                        color="#0066CC",
                                        className="me-2"
                                    ),
                                    "What privacy risks exist in my dataset?"
                                ],
                                id={"type": "suggested-question", "index": 0},
                                action=True,
                                className="border-0 suggested-question"
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:folder-eye",
                                        width=16,
                                        height=16,
                                        color="#0066CC",
                                        className="me-2"
                                    ),
                                    "What security and sensitivity classification level is appropriate for my dataset?"
                                ],
                                id={"type": "suggested-question", "index": 1},
                                action=True,
                                className="border-0 suggested-question"
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:shield-lock",
                                        width=16,
                                        height=16,
                                        color="#0066CC",
                                        className="me-2"
                                    ),
                                    "How can GovTech privacy tools support my data-sharing needs?"
                                ],
                                id={"type": "suggested-question", "index": 2},
                                action=True,
                                className="border-0 suggested-question"
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:file-document",
                                        width=16,
                                        height=16,
                                        color="#0066CC",
                                        className="me-2"
                                    ),
                                    "How can I use Cloak to safely down-classify my dataset?"
                                ],
                                id={"type": "suggested-question", "index": 3},
                                action=True,
                                className="border-0 suggested-question"
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:chart-line",
                                        width=16,
                                        height=16,
                                        color="#0066CC",
                                        className="me-2"
                                    ),
                                    "What metrics should I consider when evaluating data quality?"
                                ],
                                id={"type": "suggested-question", "index": 4},
                                action=True,
                                className="border-0 suggested-question"
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:message-text",
                                        width=16,
                                        height=16,
                                        color="#0066CC",
                                        className="me-2"
                                    ),
                                    "What data limitations in my dataset I should communicate to the data requestor?"
                                ],
                                id={"type": "suggested-question", "index": 5},
                                action=True,
                                className="border-0 suggested-question"
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:scale-balance",
                                        width=16,
                                        height=16,
                                        color="#0066CC",
                                        className="me-2"
                                    ),
                                    "Which privacy measures balance protection with data quality?"
                                ],
                                id={"type": "suggested-question", "index": 6},
                                action=True,
                                className="border-0 suggested-question"
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:steps",
                                        width=16,
                                        height=16,
                                        color="#0066CC",
                                        className="me-2"
                                    ),
                                    "What steps must I follow to safely down-classify my dataset?"
                                ],
                                id={"type": "suggested-question", "index": 7},
                                action=True,
                                className="border-0 suggested-question"
                            ),
                        ],
                        flush=True,
                        className="suggested-questions-list"
                    ),
                ],
                className="suggested-questions-container",
            ),
        ],
        className="chat-component",
    )


# Split the feedback callbacks into two separate callbacks - one for UI updates and one for data storage

# This callback handles the UI updates (changing the button styles)
@callback(
    [
        Output({"type": "feedback-like", "index": MATCH}, "style"),
        Output({"type": "feedback-dislike", "index": MATCH}, "style"),
    ],
    [
        Input({"type": "feedback-like", "index": MATCH}, "n_clicks"),
        Input({"type": "feedback-dislike", "index": MATCH}, "n_clicks"),
    ],
    State({"type": "feedback-like", "index": MATCH}, "id"),
    prevent_initial_call=True
)
def update_feedback_ui(like_clicks, dislike_clicks, feedback_id):
    """Update the UI when feedback buttons are clicked."""
    if not ctx.triggered_id:
        raise PreventUpdate
    
    # Determine which button was clicked
    feedback_type = "like" if ctx.triggered_id["type"] == "feedback-like" else "dislike"
    message_id = feedback_id["index"]
    
    logger.info(f"Feedback UI update: {feedback_type} for message {message_id}")
    
    # Update button styles
    like_style = {
        "color": "var(--primary)" if feedback_type == "like" else "var(--text-secondary)",
        "cursor": "pointer",
        "margin-right": "8px",
        "fontSize": "14px"
    }
    
    dislike_style = {
        "color": "var(--error)" if feedback_type == "dislike" else "var(--text-secondary)",
        "cursor": "pointer",
        "fontSize": "14px"
    }
    
    return like_style, dislike_style

# This callback handles feedback data storage
@callback(
    Output("feedback-store", "children"),
    [
        Input({"type": "feedback-like", "index": ALL}, "n_clicks"),
        Input({"type": "feedback-dislike", "index": ALL}, "n_clicks"),
    ],
    [
        State({"type": "feedback-like", "index": ALL}, "id"),
        State("feedback-store", "children"),
    ],
    prevent_initial_call=True
)
def store_feedback(like_clicks_list, dislike_clicks_list, feedback_ids, feedback_store_json):
    """Store feedback data silently without toast notification."""
    if not ctx.triggered_id:
        raise PreventUpdate
    
    # Determine which button was clicked and which message it's for
    trigger_type = ctx.triggered_id["type"]
    trigger_index = ctx.triggered_id["index"]
    feedback_type = "like" if "like" in trigger_type else "dislike"
    message_id = trigger_index
    
    logger.info(f"Storing feedback: {feedback_type} for message {message_id}")
    
    # Update feedback store
    try:
        feedback_data = json.loads(feedback_store_json) if feedback_store_json else []
    except:
        feedback_data = []
    
    # Check if message already has feedback
    message_exists = False
    for item in feedback_data:
        if item.get("message_id") == message_id:
            item["feedback"] = feedback_type
            item["timestamp"] = datetime.now().isoformat()
            message_exists = True
            break
    
    # Add new feedback if not exists
    if not message_exists:
        feedback_data.append({
            "message_id": message_id,
            "feedback": feedback_type,
            "timestamp": datetime.now().isoformat()
        })
    
    return json.dumps(feedback_data)


# Callback to populate chat input with suggested question
@callback(
    Output("user-input", "value", allow_duplicate=True),
    Input({"type": "suggested-question", "index": ALL}, "n_clicks"),
    State({"type": "suggested-question", "index": ALL}, "children"),
    prevent_initial_call=True
)
def populate_suggested_question(n_clicks_list, question_texts):
    """When a suggested question is clicked, populate it in the chat input field."""
    if not ctx.triggered_id:
        raise PreventUpdate
        
    # Get the index of the clicked question
    question_index = ctx.triggered_id["index"]
    
    # Find the corresponding question text
    if isinstance(question_index, int):
        # Direct index match
        # Need to extract only the text part, since the children now include an icon and text
        if isinstance(question_texts[question_index], list):
            # Get only the text part (second item in list)
            question_text = question_texts[question_index][1]
        else:
            question_text = question_texts[question_index]
    else:
        # Find the matching index in the list
        for i, clicks in enumerate(n_clicks_list):
            if i == question_index and clicks:
                if isinstance(question_texts[i], list):
                    # Get only the text part (second item in list)
                    question_text = question_texts[i][1]
                else:
                    question_text = question_texts[i]
                break
        else:
            # No match found
            raise PreventUpdate
    
    logger.info(f"Suggested question selected: {question_text}")
    
    # Return the question text to populate the input field
    return question_text

# Callback to show a modal with full citation information
@callback(
    Output("citation-modal", "is_open"),
    Output("citation-modal-title", "children"),
    Output("citation-modal-body", "children"),
    Input({"type": "view-citation", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def view_full_citation(n_clicks_list):
    """Show a modal with the full citation information."""
    if not ctx.triggered_id or not any(n_clicks_list):
        raise PreventUpdate
    
    # Get the citation info from the button ID
    citation_info = ctx.triggered_id["index"].split("-")
    message_id = citation_info[0]
    citation_idx = int(citation_info[1])
    
    # This would normally look up the citation in a data store
    # For now, we'll create a placeholder that would be replaced with actual citation data
    # In a real implementation, you'd store the citations in dcc.Store or a server-side database
    
    # Placeholder for full citation content
    title = "Citation Details"
    body = [
        html.P("This would display the full citation information for the selected reference."),
        html.P("In a complete implementation, the citation data would be stored and retrieved based on the message ID and citation index."),
        html.P(f"Message ID: {message_id}, Citation Index: {citation_idx}"),
        dbc.Alert(
            [
                html.I(className="fas fa-info-circle me-2"),
                "Citation data would include the full context from the original document."
            ],
            color="info"
        )
    ]
    
    return True, title, body

# Callback to close the citation modal
@callback(
    Output("citation-modal", "is_open", allow_duplicate=True),
    Input("close-citation-modal", "n_clicks"),
    prevent_initial_call=True
)
def close_citation_modal(n_clicks):
    """Close the citation modal when the close button is clicked."""
    if n_clicks:
        return False
    raise PreventUpdate

# API Diagnostic callback
@callback(
    Output("api-diagnostic-collapse", "is_open"),
    Output("api-diagnostic-result", "children"),
    Output("api-diagnostic-result", "style"),
    Input("api-diagnostic-button", "n_clicks"),
    prevent_initial_call=True
)
def check_api_connection(n_clicks):
    """Check the OpenAI API connection and show diagnostic results"""
    if not n_clicks:
        raise PreventUpdate
        
    # Check if the OpenAI API key is properly set
    key_valid, key_message = check_api_key()
    
    if not key_valid:
        return True, f"🔴 API Key Error: {key_message}", {"color": "#d9534f"}
    
    # Try to make a simple test request to OpenAI
    try:
        test_llm = ChatOpenAI(
            model_name= "gpt-4o-mini", # "gpt-4", #, #"gpt-3.5-turbo",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Make a simple test request
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Say 'API connection successful' if you can read this message.")
        ]
        
        response = test_llm.invoke(messages)
        
        if "API connection successful" in response.content:
            return True, "✅ API connection successful! You can now use the chat.", {"color": "#5cb85c"}
        else:
            return True, f"⚠️ API connection seems to work, but received unexpected response: {response.content}", {"color": "#f0ad4e"}
    except Exception as e:
        return True, f"🔴 API Connection Error: {str(e)}", {"color": "#d9534f"}
