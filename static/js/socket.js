// Socket.io initialization and event handling
const socket = io();

socket.on('connect', () => {
    console.log('Connected to server');
    socket.emit('join', { username: currentUsername });
});

socket.on('new_message', (data) => {
    const { sender, receiver, timestamp } = data;
    const otherUser = currentUsername === sender ? receiver : sender;
    const isOutgoing = currentUsername === sender;
    
    // Create chat window if it doesn't exist
    if (!document.querySelector(`#chat-${otherUser}`)) {
        openPrivateChat(otherUser);
    } else {
        // If chat window exists but is minimized, maximize it for new messages
        const chatWindow = document.querySelector(`#chat-${otherUser}`);
        if (chatWindow.classList.contains('minimized')) {
            toggleChatWindow(otherUser);
        }
    }
    
    // If this is a confirmation of our sent message, update the temporary message
    const messagesContainer = document.getElementById(`private-messages-${otherUser}`);
    const tempMessage = messagesContainer?.querySelector('.temp-message');
    if (tempMessage && isOutgoing) {
        tempMessage.classList.remove('temp-message');
        tempMessage.dataset.messageId = data.id;
        // Update the time display
        const timeDiv = tempMessage.querySelector('.message-time');
        if (timeDiv) {
            timeDiv.textContent = formatMessageTime(timestamp);
        }
        tempMessage.dataset.timestamp = parseTimestamp(timestamp).toISOString();
    } else {
        // Otherwise append as new message
        appendPrivateMessage(otherUser, data, isOutgoing, timestamp);
    }
    
    // Update cache
    updateMessageCache(otherUser, data);
});

// Load chat history
function loadChatHistory(username) {
    const messagesContainer = document.getElementById(`private-messages-${username}`);
    if (!messagesContainer) return;

    // Show loading indicator
    messagesContainer.innerHTML = '<div class="text-center text-gray-500 py-2">Loading messages...</div>';

    // First, try to load cached messages
    const cachedMessages = getCachedMessages(username);
    if (cachedMessages) {
        messagesContainer.innerHTML = '';
        cachedMessages.forEach(msg => {
            const isOutgoing = msg.sender === currentUsername;
            appendPrivateMessage(username, msg, isOutgoing, msg.timestamp, false);
        });
        forceScrollToBottom(username);
    }

    // Then fetch new messages from server
    fetch(`/messages/${username}`)
        .then(response => response.json())
        .then(async data => {
            if (data.success && Array.isArray(data.messages)) {
                if (!cachedMessages) {
                    messagesContainer.innerHTML = '';
                }
                
                const sortedMessages = data.messages.sort((a, b) => 
                    new Date(a.timestamp) - new Date(b.timestamp)
                );
                
                cacheMessages(username, sortedMessages);

                const lastCachedTimestamp = cachedMessages ? getLastMessageTimestamp(username) : null;
                const newMessages = lastCachedTimestamp 
                    ? sortedMessages.filter(msg => new Date(msg.timestamp) > new Date(lastCachedTimestamp))
                    : sortedMessages;

                newMessages.forEach(msg => {
                    const isOutgoing = msg.sender === currentUsername;
                    appendPrivateMessage(username, msg, isOutgoing, msg.timestamp, false);
                });

                forceScrollToBottom(username);

                // Preload images
                const imageMessages = newMessages.filter(msg => 
                    msg.has_media && msg.media_type?.startsWith('image/')
                );

                for (let i = 0; i < imageMessages.length; i += 3) {
                    const batch = imageMessages.slice(i, i + 3);
                    await Promise.all(
                        batch.map(msg => 
                            preloadImage(msg.media_url)
                                .catch(() => console.error('Failed to preload image:', msg.media_url))
                        )
                    );
                }
            }
        })
        .catch(error => {
            console.error('Error loading chat history:', error);
            if (!cachedMessages) {
                messagesContainer.innerHTML = '<div class="text-center text-red-500 py-2">Failed to load messages</div>';
            }
        });
}

// Export functions that need to be globally available
window.loadChatHistory = loadChatHistory; 