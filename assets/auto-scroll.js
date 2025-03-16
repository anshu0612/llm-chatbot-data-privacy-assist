// Auto-scroll chat messages to bottom
if (!window.dashExtensions) {
    window.dashExtensions = {};
}

window.dashExtensions.autoScroll = function() {
    // Function to scroll chat to bottom
    function scrollChatToBottom() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Set up a mutation observer to watch for changes to the chat container
    function setupMutationObserver() {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            // If chat container not found, try again in 100ms
            setTimeout(setupMutationObserver, 100);
            return;
        }

        // Create a mutation observer
        const observer = new MutationObserver(function(mutations) {
            // When content changes, scroll to bottom
            scrollChatToBottom();
        });

        // Start observing the chat container
        observer.observe(chatMessages, { 
            childList: true,      // Watch for added/removed children
            subtree: true,        // Watch all descendants
            characterData: true   // Watch for text changes
        });

        // Initial scroll
        scrollChatToBottom();
    }

    // Initialize when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupMutationObserver);
    } else {
        setupMutationObserver();
    }

    return null;
};
