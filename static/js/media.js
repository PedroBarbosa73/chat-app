// Image modal functions
function openImageModal(imageUrl) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const url = imageUrl.startsWith('/') ? imageUrl : '/' + imageUrl;
    modalImage.src = url;
    modal.classList.remove('hidden');
    
    document.addEventListener('keydown', handleModalKeyPress);
}

function closeImageModal() {
    const modal = document.getElementById('imageModal');
    modal.classList.add('hidden');
    document.removeEventListener('keydown', handleModalKeyPress);
}

function handleModalKeyPress(event) {
    if (event.key === 'Escape') {
        closeImageModal();
    }
}

// File handling functions
function handlePrivateFileSelect(username, event) {
    const file = event.target.files[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
        alert('File size must be less than 10MB');
        event.target.value = '';
        return;
    }

    const chatWindow = document.querySelector(`#chat-${username}`);
    if (!chatWindow) return;

    const previewContainer = chatWindow.querySelector('.media-preview') || document.createElement('div');
    previewContainer.className = 'media-preview p-2 border-t';
    previewContainer.innerHTML = '';

    if (file.type.startsWith('image/')) {
        const img = document.createElement('img');
        img.className = 'max-h-32 rounded';
        const reader = new FileReader();
        reader.onload = (e) => {
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
        previewContainer.appendChild(img);
    } else {
        const fileInfo = document.createElement('div');
        fileInfo.className = 'text-gray-700';
        fileInfo.textContent = file.name;
        previewContainer.appendChild(fileInfo);
    }

    const removeButton = document.createElement('button');
    removeButton.className = 'text-red-500 ml-2';
    removeButton.innerHTML = '×';
    removeButton.onclick = () => {
        event.target.value = '';
        previewContainer.remove();
    };
    previewContainer.appendChild(removeButton);

    chatWindow.querySelector('.chat-window-input').prepend(previewContainer);
}

function preloadImage(url) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error('Image failed to load'));
        img.src = url;
    });
}

// Initialize modal event listeners
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.addEventListener('click', function(event) {
            if (event.target === this) {
                closeImageModal();
            }
        });
    }
});

// Export functions that need to be globally available
window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;
window.handlePrivateFileSelect = handlePrivateFileSelect;
window.preloadImage = preloadImage; 