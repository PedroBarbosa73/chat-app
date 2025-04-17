// Constants
const MESSAGE_CACHE_PREFIX = 'chat_messages_';
const MESSAGE_CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

// Time handling functions
function getCurrentTimestamp() {
    return new Date().toISOString();
}

function parseTimestamp(timestamp) {
    try {
        if (typeof timestamp === 'string') {
            return new Date(timestamp);
        } else if (timestamp instanceof Date) {
            return timestamp;
        }
    } catch (e) {
        console.error('Invalid timestamp:', timestamp);
    }
    return new Date();
}

function formatMessageTime(timestamp) {
    const date = parseTimestamp(timestamp);
    const now = new Date();
    
    const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    const localNow = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
    
    const isToday = localDate.toDateString() === localNow.toDateString();
    const isYesterday = new Date(localNow - 86400000).toDateString() === localDate.toDateString();
    
    const timeString = date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });

    if (isToday) {
        return timeString;
    } else if (isYesterday) {
        return `Yesterday ${timeString}`;
    } else {
        return `${date.toLocaleDateString()} ${timeString}`;
    }
}

// Cache management functions
function getCacheKey(username) {
    return `${MESSAGE_CACHE_PREFIX}${currentUsername}_${username}`;
}

function getLastMessageTimestamp(username) {
    const cacheKey = getCacheKey(username);
    const cachedData = localStorage.getItem(cacheKey);
    if (cachedData) {
        const { messages } = JSON.parse(cachedData);
        if (messages && messages.length > 0) {
            return messages[messages.length - 1].timestamp;
        }
    }
    return null;
}

function cacheMessages(username, messages) {
    const cacheKey = getCacheKey(username);
    const cacheData = {
        messages,
        timestamp: new Date().getTime()
    };
    try {
        localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (e) {
        console.warn('Failed to cache messages:', e);
        clearOldCaches();
    }
}

function getCachedMessages(username) {
    const cacheKey = getCacheKey(username);
    const cachedData = localStorage.getItem(cacheKey);
    if (cachedData) {
        const { messages, timestamp } = JSON.parse(cachedData);
        const age = new Date().getTime() - timestamp;
        if (age < MESSAGE_CACHE_DURATION) {
            return messages;
        } else {
            localStorage.removeItem(cacheKey);
        }
    }
    return null;
}

function clearOldCaches() {
    const keys = Object.keys(localStorage);
    const now = new Date().getTime();
    keys.forEach(key => {
        if (key.startsWith(MESSAGE_CACHE_PREFIX)) {
            try {
                const { timestamp } = JSON.parse(localStorage.getItem(key));
                if (now - timestamp > MESSAGE_CACHE_DURATION) {
                    localStorage.removeItem(key);
                }
            } catch (e) {
                localStorage.removeItem(key);
            }
        }
    });
}

function updateMessageCache(username, newMessage) {
    const cachedMessages = getCachedMessages(username) || [];
    cachedMessages.push(newMessage);
    cacheMessages(username, cachedMessages);
}

// Export functions that need to be globally available
window.getCurrentTimestamp = getCurrentTimestamp;
window.parseTimestamp = parseTimestamp;
window.formatMessageTime = formatMessageTime;
window.getCachedMessages = getCachedMessages;
window.updateMessageCache = updateMessageCache;
window.getLastMessageTimestamp = getLastMessageTimestamp;
window.cacheMessages = cacheMessages; 