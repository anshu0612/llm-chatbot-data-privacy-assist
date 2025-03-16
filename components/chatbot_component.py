from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, ctx, clientside_callback, no_update
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
from langchain_anthropic import ChatAnthropic
from langchain.chat_models.base import BaseChatModel
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

# Get model provider from environment variable or default to 'openai'
LLM_PROVIDER = "openai" #os.getenv("LLM_PROVIDER", "openai").lower()

# Initialize the appropriate chat model based on provider
try:
    if LLM_PROVIDER == "anthropic":
        print("*"*1000)
        # Check if Anthropic API key is set
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        print("Anthropi's:", anthropic_api_key)
        if not anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY environment variable is not set")
            raise ValueError("Anthropic API key not found in environment variables")
        
        llm = ChatAnthropic(
            model_name="claude-3-7-sonnet-20250219",  # Corresponds to Claude 3 Haiku
            temperature=0,
            anthropic_api_key=anthropic_api_key,
            max_tokens=4096
        )
        logger.info("ChatAnthropic initialized with API key from environment variable")
    else:  # Default to OpenAI
        # Check API key validity
        key_valid, key_message = check_api_key()
        if not key_valid:
            raise ValueError(key_message)
            
        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        
        llm = ChatOpenAI(
            model_name="gpt-4o", #"gpt-4o-mini",
            temperature=0,
            api_key=api_key
        )
        logger.info("ChatOpenAI initialized with API key from environment variable")
except Exception as e:
    logger.error(f"Error initializing LLM: {e}")
    llm = None

# Default system prompt for the privacy assistant
DEFAULT_SYSTEM_PROMPT = """
You are a DataSharingAssist AI supporting data providers by evaluating privacy risks and offering tailored, data-driven recommendations for managing privacy risks in their datasets. Your responses must align closely with Singapore's IM8 guidelines and other relevant government privacy regulations.

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

You should avoid answering questions that are not related to data sharing. Skip them politely.

Current dataset context:
{privacy_context}
{quality_context}
"""

# Create provider-specific chat prompt templates with RAG support
def get_prompt_template():
    """Get the appropriate prompt template based on the LLM provider"""
    if LLM_PROVIDER == "anthropic":
        # Claude models only support a single system message, so we need to combine them
        combined_system_prompt = f"""{DEFAULT_SYSTEM_PROMPT}

Relevant Singapore policy information: {{rag_context}}

When referencing policies, use citation markers like [1], [2], etc. and provide a list of references at the end."""
        
        return ChatPromptTemplate.from_messages([
            ("system", combined_system_prompt),
            ("human", "{input}"),
        ])
    else:  # OpenAI and others can handle multiple system messages
        return ChatPromptTemplate.from_messages([
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

# Get the model provider name
def get_provider_name() -> str:
    """Get the name of the current LLM provider"""
    return "Anthropic Claude" if os.getenv("LLM_PROVIDER", "openai").lower() == "anthropic" else "OpenAI"

# This section was cleaned up since loading animation is now handled in app.py

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
            provider_name = get_provider_name()
            raise ValueError(f"{provider_name} client is not initialized. Please check your API key.")
        
        # Format the variables for the prompt
        formatted_variables = {
            "input": user_input,
            "privacy_context": privacy_context_str,
            "quality_context": quality_context_str,
            "rag_context": rag_context_data["context"]
        }
        
        # Get the appropriate prompt template and format it with the variables
        rag_chat_prompt = get_prompt_template()
        formatted_messages = rag_chat_prompt.format_messages(**formatted_variables)
            
        provider_name = get_provider_name()
        logger.info(f"Sending request to {provider_name} API...")
        
        # Log the message format for debugging
        logger.info(f"Formatted messages: {formatted_messages}")
        
        try:
            response = llm.invoke(formatted_messages)
            content = response.content
            logger.info(f"Successfully received response from {provider_name} API")
        except Exception as e:
            # Detailed error logging
            logger.error(f"Error during {provider_name} API call: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            
            if LLM_PROVIDER == "anthropic":
                # Additional Anthropic-specific debugging
                try:
                    # Try with a very simple message to test basic connectivity
                    from langchain_core.messages import SystemMessage, HumanMessage
                    simple_messages = [
                        SystemMessage(content="You are a helpful assistant."),
                        HumanMessage(content="Say hello")
                    ]
                    logger.info("Attempting simple message test with Anthropic...")
                    simple_response = llm.invoke(simple_messages)
                    logger.info(f"Simple message test succeeded: {simple_response.content}")
                    # If simple message works but complex one doesn't, it's likely a message format issue
                    logger.error("The issue appears to be with the message format, not connectivity.")
                except Exception as inner_e:
                    logger.error(f"Simple message test also failed: {inner_e}")
                    logger.error("This suggests a fundamental connectivity or authentication issue.")
            
            # Re-raise the exception to be caught by the outer try/except
            raise
        
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
            "citations": citations,  # Include citation information
            "provider": get_provider_name()  # Add provider information
        }
    except ValueError as e:
        # Handle API key issues
        error_message = str(e)
        provider_name = get_provider_name()
        env_var = "ANTHROPIC_API_KEY" if provider_name == "Anthropic Claude" else "OPENAI_API_KEY"
        logger.error(f"{provider_name} API key error: {error_message}")
        return {
            "content": f"Error: {error_message}. Please set your {env_var} environment variable with a valid API key.",
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "feedback": None,
            "citations": [],
            "provider": provider_name
        }
    except Exception as e:
        # Handle other errors
        provider_name = get_provider_name()
        logger.error(f"Error getting response from {provider_name}: {e}")
        return {
            "content": f"I'm sorry, I encountered an error while processing your request: {str(e)}. Please check your API key and network connection.",
            "id": str(uuid.uuid4()),
            "provider": provider_name,
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
            "backgroundColor": "#f0f5ff" if feedback == "like" else "#fff0f7",
            "borderLeft": f"3px solid {'#4361ee' if feedback == 'like' else '#7209b7'}",
            "padding": "12px",
            "borderRadius": "4px"
        }
    
    return html.Div(
        [
            # Add a row structure for avatar and message content
            dbc.Row(
                [
                    # Avatar column
                    dbc.Col(
                        html.Img(
                            src="/assets/logo.png",
                            className="bot-avatar",
                            style={
                                "width": "32px",
                                "height": "32px",
                                "borderRadius": "50%",
                                "objectFit": "cover",
                                "boxShadow": "0 2px 4px rgba(67, 97, 238, 0.2)"
                            }
                        ),
                        width="auto",
                        className="pe-2 d-flex align-items-start pt-1"
                    ),
                    # Message content column
                    dbc.Col(
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
                        ]
                    )
                ],
                className="g-0"
            )
        ],
        className="bot-message mb-3",
        id={"type": "bot-message", "index": message_id}
    )

# API diagnostic button has been removed

def create_chatbot_component():
    """Create the chatbot component."""
    # Create a store for loading state
    loading_state_store = dcc.Store(id="chat-loading-state", data=False)
    
    # Create welcome message data
    welcome_message = {
        "id": "welcome-message",
        "content": """**Welcome to DataSharingAssist!**

I'm your AI-powered data sharing and privacy assistant, aligned with Singapore's IM8 guidelines and public sector data security standards. I provide data-driven insights to help you confidently manage privacy risks and ensure compliant data sharing.

**Here's how I can assist you:**

- Evaluate privacy risks specific to your dataset.
- Recommend suitable privacy protection measures.
- Guide you clearly through IM8 compliance and data classification.
- Provide practical data quality metrics to communicate clearly with data requestors.
- Suggest trusted Singapore government-developed privacy tools (Mirage, Cloak, enTrust).

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
            
            # Store for tracking loading state
            loading_state_store,
            
            html.Div(
                [
                    # Main chat messages container
                    html.Div(
                        [
                            create_bot_message(welcome_message),
                        ],
                        id="chat-messages",
                        className="chat-messages p-3",
                        style={
                            "flexGrow": "1", 
                            "overflowY": "auto", 
                            "minHeight": "300px", 
                            "maxHeight": "360px",
                            "scrollBehavior": "smooth"  # Enable smooth scrolling
                        },
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
                                        className="send-button",
                                        style={"borderRadius": "0"}
                                    ),
                                ]
                            ),
                        ],
                        className="chat-input px-3 pb-3 pt-2",
                    ),
                ],
                className="chat-container d-flex flex-column",
                style={"flex": "1", "minHeight": "300px", "maxHeight": "450px"},
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
                    dbc.ListGroup(
                        [
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:robot",
                                        width=18,
                                        height=18,
                                        color="#4361ee",
                                        className="me-2"
                                    ),
                                    "What privacy risks exist in my dataset?"
                                ],
                                id={"type": "suggested-question", "index": 0},
                                action=True,
                                n_clicks=0,  # Initialize click counter
                                className="border-0 suggested-question guided-question",
                                style={"cursor": "pointer", "transition": "all 0.2s ease"},  # Ensure cursor shows pointer
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:folder-eye",
                                        width=18,
                                        height=18,
                                        color="#4361ee",
                                        className="me-2"
                                    ),
                                    "What security and sensitivity classification level is appropriate for my dataset?"
                                ],
                                id={"type": "suggested-question", "index": 1},
                                action=True,
                                n_clicks=0,  # Initialize click counter
                                className="border-0 suggested-question guided-question",
                                style={"cursor": "pointer", "transition": "all 0.2s ease"},  # Ensure cursor shows pointer
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:shield-lock",
                                        width=16,
                                        height=16,
                                        color="#4361ee",
                                        className="me-2"
                                    ),
                                    "How can GovTech privacy tools support my data-sharing needs?"
                                ],
                                id={"type": "suggested-question", "index": 2},
                                action=True,
                                n_clicks=0,  # Initialize click counter
                                className="border-0 suggested-question guided-question",
                                style={"cursor": "pointer", "transition": "all 0.2s ease"},  # Ensure cursor shows pointer
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:file-document",
                                        width=16,
                                        height=16,
                                        color="#4361ee",
                                        className="me-2"
                                    ),
                                    "How can I use Cloak to safely down-classify my dataset?"
                                ],
                                id={"type": "suggested-question", "index": 3},
                                action=True,
                                n_clicks=0,  # Initialize click counter
                                className="border-0 suggested-question guided-question",
                                style={"cursor": "pointer", "transition": "all 0.2s ease"},  # Ensure cursor shows pointer
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:chart-line",
                                        width=16,
                                        height=16,
                                        color="#4361ee",
                                        className="me-2"
                                    ),
                                    "What metrics should I consider when evaluating data quality?"
                                ],
                                id={"type": "suggested-question", "index": 4},
                                action=True,
                                n_clicks=0,  # Initialize click counter
                                className="border-0 suggested-question guided-question",
                                style={"cursor": "pointer", "transition": "all 0.2s ease"},  # Ensure cursor shows pointer
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:message-text",
                                        width=16,
                                        height=16,
                                        color="#4361ee",
                                        className="me-2"
                                    ),
                                    "What data limitations in my dataset I should communicate to the data requestor?"
                                ],
                                id={"type": "suggested-question", "index": 5},
                                action=True,
                                n_clicks=0,  # Initialize click counter
                                className="border-0 suggested-question guided-question",
                                style={"cursor": "pointer", "transition": "all 0.2s ease"},  # Ensure cursor shows pointer
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:scale-balance",
                                        width=16,
                                        height=16,
                                        color="#4361ee",
                                        className="me-2"
                                    ),
                                    "Which privacy measures balance protection with data quality?"
                                ],
                                id={"type": "suggested-question", "index": 6},
                                action=True,
                                n_clicks=0,  # Initialize click counter
                                className="border-0 suggested-question guided-question",
                                style={"cursor": "pointer", "transition": "all 0.2s ease"},  # Ensure cursor shows pointer
                            ),
                            dbc.ListGroupItem(
                                [
                                    DashIconify(
                                        icon="mdi:steps",
                                        width=16,
                                        height=16,
                                        color="#4361ee",
                                        className="me-2"
                                    ),
                                    "What steps must I follow to safely down-classify my dataset?"
                                ],
                                id={"type": "suggested-question", "index": 7},
                                action=True,
                                n_clicks=0,  # Initialize click counter
                                className="border-0 suggested-question guided-question",
                                style={"cursor": "pointer", "transition": "all 0.2s ease"},  # Ensure cursor shows pointer
                            ),
                        ],
                        flush=True,
                        className="suggested-questions-list"
                    ),
                ],
                className="suggested-questions-container",
                style={"maxHeight": "180px", "overflowY": "auto", "marginTop": "8px"},
            ),
        ],
        className="chat-component d-flex flex-column",
        style={"height": "100%"},
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


# Implement both server-side and client-side callbacks for suggested questions

# Client-side callback for immediate response - removing to avoid duplicate callback issue
# For now, we'll rely on the server-side callback, which is already working

# Loading animation is now handled in app.py

# Callback to populate chat input with suggested question text when clicked
@callback(
    Output("user-input", "value", allow_duplicate="initial_duplicate"),
    Input({"type": "suggested-question", "index": ALL}, "n_clicks"),
    State({"type": "suggested-question", "index": ALL}, "children"),
    prevent_initial_call=True
)
def populate_suggested_question(n_clicks_list, question_texts):
    """When a suggested question is clicked, populate it in the chat input field."""
    # Debug logging
    # print("\n=== SUGGESTED QUESTION CALLBACK TRIGGERED ===\n")
    # print(f"n_clicks_list: {n_clicks_list}")
    # print(f"question_texts: {str(question_texts)[:200]}...")
    # print(f"triggered_id: {ctx.triggered_id}")
    
    # Safety check
    if not ctx.triggered_id:
        print("No triggered_id found, preventing update")
        raise PreventUpdate
    
    # Find which suggestion was clicked
    if not any(n_clicks and n_clicks > 0 for n_clicks in n_clicks_list):
        print("No clicks detected, preventing update")
        raise PreventUpdate
    
    try:    
        # Get the index of the clicked question
        question_index = ctx.triggered_id["index"]
        print(f"Question index: {question_index}")
        
        # Extract the text content from the question
        selected_question = question_texts[question_index]
        print(f"Selected question (raw): {selected_question}")
        
        # Extract just the text part, not the icon
        if isinstance(selected_question, list):
            # The question contains multiple elements (typically icon and text)
            # The text element is the second item in the list
            if len(selected_question) > 1:
                question_text = selected_question[1]
                if isinstance(question_text, str):
                    print(f"Extracted question text: {question_text}")
                else:
                    # Handle the case when the second element might be another component
                    question_text = str(selected_question[1])
                    print(f"Converted question component to text: {question_text}")
            else:
                # If there's only one element, use it
                question_text = str(selected_question[0])
                print(f"Using first element as text: {question_text}")
        else:
            # If it's not a list, use it directly
            question_text = str(selected_question)
            print(f"Using question as is: {question_text}")
        
        # Log the selection
        logger.info(f"Suggested question selected: {question_text}")
        
        # Return the question text to populate the input field
        return question_text
    
    except Exception as e:
        print(f"Error in populate_suggested_question: {e}")
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        logger.error(f"Error in populate_suggested_question: {e}\n{traceback_str}")
        raise PreventUpdate

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

# API Diagnostic callback has been removed
