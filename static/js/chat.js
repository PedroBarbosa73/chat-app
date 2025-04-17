// Chat window management
function openPrivateChat(username) {
    if (username === currentUsername) {
        alert("You cannot chat with yourself");
        return;
    }

    let chatWindow = document.querySelector(`#chat-${username}`);
    if (!chatWindow) {
        chatWindow = document.createElement('div');
        chatWindow.id = `chat-${username}`;
        chatWindow.className = 'chat-window';
        chatWindow.dataset.username = username;
        chatWindow.style.right = getNextChatWindowPosition() + 'px';
        chatWindow.innerHTML = `
            <div class="chat-window-header">
                <span>Chat with ${username}</span>
                <div class="chat-window-controls">
                    <button onclick="toggleChatWindow('${username}')" class="minimize-btn">-</button>
                    <button onclick="closeChatWindow('${username}')" class="close-btn">×</button>
                </div>
            </div>
            <div class="chat-window-messages">
                <div id="private-messages-${username}" class="message-list">
                    <div class="text-center text-gray-500 py-2">Loading messages...</div>
                </div>
            </div>
            <div class="chat-window-input">
                <input type="text" class="message-input flex-1 p-2 border rounded" 
                       placeholder="Type a message..."
                       onkeydown="handleMessageInputKeydown(event, '${username}')">
                <label for="file-upload-${username}" class="file-upload-label">
                    <i class="fas fa-paperclip"></i>
                </label>
                <input type="file" id="file-upload-${username}" class="file-upload" accept="image/*,video/*" style="display: none;" onchange="handlePrivateFileSelect('${username}', event)">
                <button type="button" class="send-button bg-blue-500 text-white px-3 py-1 rounded" onclick="sendPrivateMessage('${username}')">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        `;
        document.body.appendChild(chatWindow);

        setTimeout(() => {
            loadChatHistory(username);
            forceScrollToBottom(username);
        }, 50);
    } else {
        if (chatWindow.classList.contains('minimized')) {
            toggleChatWindow(username);
        }
        const input = chatWindow.querySelector('.message-input');
        if (input) {
            input.focus();
            forceScrollToBottom(username);
        }
    }
}

function toggleChatWindow(username) {
    const chatWindow = document.querySelector(`#chat-${username}`);
    if (chatWindow) {
        chatWindow.classList.toggle('minimized');
    }
}

function closeChatWindow(username) {
    const chatWindow = document.querySelector(`#chat-${username}`);
    if (chatWindow) {
        chatWindow.remove();
    }
}

function getNextChatWindowPosition() {
    const chatWindows = document.querySelectorAll('.chat-window');
    return 20 + (chatWindows.length * 320); // 320px is the width of chat window + margin
}

function handleMessageInputKeydown(event, username) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendPrivateMessage(username);
    }
}

// Message handling
function sendPrivateMessage(username) {
    const chatWindow = document.querySelector(`#chat-${username}`);
    if (!chatWindow) return;

    const input = chatWindow.querySelector('.message-input');
    const fileInput = chatWindow.querySelector('.file-upload');
    const file = fileInput.files[0];
    
    if (!input.value.trim() && !file) return;

    let tempId;
    try {
        const tempMessage = {
            content: input.value.trim(),
            sender: currentUsername,
            receiver: username,
            timestamp: getCurrentTimestamp(),
            has_media: !!file,
            media_type: file?.type,
            status: 'sending'
        };

        if (file && file.type.startsWith('image/')) {
            const tempUrl = URL.createObjectURL(file);
            tempMessage.media_url = tempUrl;
            tempMessage.temp_media_url = true;
        }

        tempId = appendPrivateMessage(username, tempMessage, true, tempMessage.timestamp);
    } catch (error) {
        console.error('Error creating temporary message:', error);
    }
    
    const formData = new FormData();
    formData.append('receiver', username);
    if (input.value.trim()) formData.append('content', input.value.trim());
    if (file) formData.append('media', file);
    
    fetch('/send_message', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(handleMessageSuccess(username, input, fileInput, file, tempId))
    .catch(error => handleMessageError(error, username, tempId))
    .finally(() => cleanupTempUrls(username, file, tempId));
}

function handleMessageSuccess(username, input, fileInput, file, tempId) {
    return data => {
        if (!data.success) throw new Error(data.error || 'Error sending message');
        
        input.value = '';
        if (file) fileInput.value = '';
        
        updateTempMessage(username, tempId, data.message);
        updateMessageCache(username, data.message);
    };
}

function handleMessageError(error, username, tempId) {
    console.error('Error sending message:', error);
    const errorMessage = {
        content: `Failed to send message: ${error.message}`,
        timestamp: getCurrentTimestamp(),
        status: 'error'
    };
    appendPrivateMessage(username, errorMessage, true);
    
    if (tempId) markMessageAsFailed(username, tempId);
}

function cleanupTempUrls(username, file, tempId) {
    if (file && file.type.startsWith('image/')) {
        const messagesContainer = document.getElementById(`private-messages-${username}`);
        const tempMessageElement = messagesContainer?.querySelector(`[data-message-id="${tempId}"]`);
        if (tempMessageElement) {
            const img = tempMessageElement.querySelector('img');
            if (img && img.src.startsWith('blob:')) {
                URL.revokeObjectURL(img.src);
            }
        }
    }
}

// Export functions that need to be globally available
window.openPrivateChat = openPrivateChat;
window.toggleChatWindow = toggleChatWindow;
window.closeChatWindow = closeChatWindow;
window.handleMessageInputKeydown = handleMessageInputKeydown;
window.sendPrivateMessage = sendPrivateMessage; 