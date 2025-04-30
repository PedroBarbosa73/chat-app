// Message display and UI functions
function appendPrivateMessage(username, message, isOutgoing, timestamp = getCurrentTimestamp(), shouldScroll = true) {
    const messagesContainer = document.getElementById(`private-messages-${username}`);
    if (!messagesContainer) return;

    const messageId = message.id || `temp-${Date.now()}`;
    if (messagesContainer.querySelector(`[data-message-id="${messageId}"]`)) {
        return;
    }

    const parsedTimestamp = parseTimestamp(timestamp);
    const displayTime = formatMessageTime(parsedTimestamp);
    const messageTime = parsedTimestamp.getTime();

    const existingMessages = Array.from(messagesContainer.children);
    let insertIndex = existingMessages.length;

    for (let i = 0; i < existingMessages.length; i++) {
        const existingTime = parseTimestamp(existingMessages[i].dataset.timestamp).getTime();
        if (messageTime < existingTime) {
            insertIndex = i;
            break;
        }
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isOutgoing ? 'outgoing' : 'incoming'}`;
    messageDiv.dataset.timestamp = parsedTimestamp.toISOString();
    messageDiv.dataset.messageId = messageId;
    
    if (message.status === 'sending') {
        messageDiv.classList.add('temp-message');
    }
    
    let content = '';
    
    if (typeof message === 'object' && message !== null) {
        if (message.has_media) {
            let mediaUrl = message.media_url;
            if (!message.temp_media_url && mediaUrl) {
                mediaUrl = mediaUrl.startsWith('/') ? mediaUrl : '/' + mediaUrl;
            }
            
            if (message.media_type && message.media_type.startsWith('image/')) {
                content = createImageContent(mediaUrl, username);
            } else if (message.media_type && message.media_type.startsWith('video/')) {
                content = createVideoContent(mediaUrl, message.media_type, username);
            } else {
                content = createFileContent(mediaUrl, message.media_filename);
            }
        }
        if (message.content) {
            content = message.content + '<br>' + content;
        }
    } else {
        content = message;
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-time">${displayTime}</div>
    `;

    if (insertIndex === existingMessages.length) {
        messagesContainer.appendChild(messageDiv);
    } else {
        messagesContainer.insertBefore(messageDiv, existingMessages[insertIndex]);
    }

    if (shouldScroll) {
        forceScrollToBottom(username);
    }

    return messageId;
}

function createImageContent(mediaUrl, username) {
    return `
        <div class="message-image-container">
            <div class="image-loader"></div>
            <img src="${mediaUrl}" 
                alt="Image" 
                class="max-w-full h-auto rounded cursor-pointer hover:opacity-90" 
                style="opacity: 0;"
                onclick="openImageModal('${mediaUrl}')"
                onload="handleImageLoad(this, '${username}')"
                onerror="handleImageError(this)">
        </div>`;
}

function createVideoContent(mediaUrl, mediaType, username) {
    return `<video controls class="max-w-full h-auto rounded" onloadeddata="scrollToBottom('${username}')">
                <source src="${mediaUrl}" type="${mediaType}">
                Your browser does not support the video tag.
            </video>`;
}

function createFileContent(mediaUrl, filename) {
    return `<a href="${mediaUrl}" target="_blank" class="text-blue-500 hover:underline">
                <i class="fas fa-file"></i> ${filename || 'File'}
            </a>`;
}

function handleImageLoad(img, username) {
    const loader = img.parentElement.querySelector('.image-loader');
    if (loader) {
        loader.remove();
    }

    img.classList.add('loaded');
    img.style.opacity = '1';

    const messagesContainer = document.getElementById(`private-messages-${username}`);
    const isAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop <= messagesContainer.clientHeight + 100;
    
    if (isAtBottom) {
        forceScrollToBottom(username);
    }
}

function handleImageError(img) {
    const container = img.closest('.message-image-container');
    if (container) {
        const loader = container.querySelector('.image-loader');
        if (loader) {
            loader.remove();
        }
        container.innerHTML = `
            <div class="p-2 text-red-500 text-sm">
                <i class="fas fa-exclamation-circle"></i> Failed to load image
            </div>`;
    }
}

function updateTempMessage(username, tempId, confirmedMessage) {
    const messagesContainer = document.getElementById(`private-messages-${username}`);
    const tempMessageElement = messagesContainer?.querySelector(`[data-message-id="${tempId}"]`);
    
    if (tempMessageElement) {
        tempMessageElement.classList.remove('temp-message');
        tempMessageElement.dataset.messageId = confirmedMessage.id;
        tempMessageElement.dataset.timestamp = parseTimestamp(confirmedMessage.timestamp).toISOString();

        if (confirmedMessage.has_media) {
            updateMediaElement(tempMessageElement, confirmedMessage, username);
        }

        updateTimeDisplay(tempMessageElement, confirmedMessage.timestamp);
    } else {
        appendPrivateMessage(username, confirmedMessage, true, confirmedMessage.timestamp);
    }
}

function updateMediaElement(messageElement, message, username) {
    const mediaUrl = message.media_url.startsWith('/') ? message.media_url : '/' + message.media_url;
    const mediaElement = messageElement.querySelector('img, video source, a');
    
    if (mediaElement) {
        if (mediaElement.tagName === 'IMG') {
            updateImageElement(mediaElement, mediaUrl, username);
        } else if (mediaElement.tagName === 'SOURCE') {
            mediaElement.src = mediaUrl;
        } else if (mediaElement.tagName === 'A') {
            mediaElement.href = mediaUrl;
        }
    }
}

function updateImageElement(imgElement, mediaUrl, username) {
    const errorDiv = imgElement.closest('.message-content').querySelector('.text-red-500');
    if (errorDiv) {
        errorDiv.remove();
    }
    
    const container = imgElement.closest('.message-image-container');
    if (container && !container.querySelector('.image-loader')) {
        const loader = document.createElement('div');
        loader.className = 'image-loader';
        container.insertBefore(loader, imgElement);
    }
    
    imgElement.style.opacity = '0';
    imgElement.src = mediaUrl;
    imgElement.onclick = () => openImageModal(mediaUrl);
    
    imgElement.onload = function() {
        handleImageLoad(this, username);
    };
    imgElement.onerror = function() {
        handleImageError(this);
    };
}

function updateTimeDisplay(messageElement, timestamp) {
    const timeDiv = messageElement.querySelector('.message-time');
    if (timeDiv) {
        timeDiv.textContent = formatMessageTime(timestamp);
    }
}

function markMessageAsFailed(username, tempId) {
    const messagesContainer = document.getElementById(`private-messages-${username}`);
    const tempMessageElement = messagesContainer?.querySelector(`[data-message-id="${tempId}"]`);
    if (tempMessageElement) {
        tempMessageElement.classList.add('failed');
        const contentDiv = tempMessageElement.querySelector('.message-content');
        if (contentDiv) {
            contentDiv.innerHTML += `
                <div class="text-red-500 text-sm mt-1">
                    <i class="fas fa-exclamation-circle"></i> Failed to send
                </div>`;
        }
    }
}

function forceScrollToBottom(username) {
    const messagesContainer = document.getElementById(`private-messages-${username}`);
    const chatWindow = document.querySelector(`#chat-${username}`);
    
    if (messagesContainer) {
        try {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            messagesContainer.scrollIntoView({ behavior: 'instant', block: 'end' });
            messagesContainer.lastElementChild?.scrollIntoView({ behavior: 'instant', block: 'end' });
        } catch (e) {
            console.error('Scroll error:', e);
        }
    }
}

// Export functions that need to be globally available
window.appendPrivateMessage = appendPrivateMessage;
window.handleImageLoad = handleImageLoad;
window.handleImageError = handleImageError;
window.forceScrollToBottom = forceScrollToBottom; 