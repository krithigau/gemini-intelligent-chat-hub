
function updateButtonAppearance(button, isSaved) {
    if (isSaved) {
        button.innerText = '✔️';
        button.title = 'Chat saved';
        button.style.opacity = '0.6';
        // button.disabled = true; // Optional
    } else {
        button.innerText = '💾';
        button.title = 'Save Chat';
        button.style.opacity = '1';
        button.disabled = false;
        button.style.cursor = 'pointer';
    }
}

// MAIN LOGIC
function addSaveButtons() {
    // 1. Find the chat items (UPDATED SELECTOR SAFETY)
    // We look for the specific class we identified earlier.
    const chatLinks = document.querySelectorAll('div.conversation');
    
    // console.log(`Found ${chatLinks.length} conversations.`); // Debug log

    chatLinks.forEach(link => {
        // 2. Check if button already exists (Prevent duplicates)
        if (link.querySelector('.save-chat-button')) {
            return;
        }

        // 3. Create the button
        const saveButton = document.createElement('button');
        saveButton.innerText = '💾';
        saveButton.className = 'save-chat-button';
        saveButton.title = 'Save Chat';
        
        // Styling (Can move this to a CSS file later if needed)
        Object.assign(saveButton.style, {
            marginLeft: '10px',
            padding: '2px 6px',
            borderRadius: '5px',
            border: '1px solid #ccc',
            cursor: 'pointer',
            backgroundColor: 'transparent',
            color: 'inherit',
            fontSize: '14px',
            lineHeight: '1',
            zIndex: '9999' // Ensure it sits on top
        });

        // 4. Add Click Listener
        saveButton.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();

            if (saveButton.innerText === '✔️') return;

            saveButton.innerText = '⏳';
            
            // Click the link to ensure the chat loads
            link.click();
            
            // Wait for load
            setTimeout(() => {
                const conversationData = scrapeCurrentChat();
                
                if (!conversationData) {
                    console.error("Scraping failed.");
                    updateButtonAppearance(saveButton, false);
                    return;
                }

                // Prompt for collection
                const collectionName = window.prompt("Enter collection name:", "Uncategorized");
                if (collectionName === null) {
                    updateButtonAppearance(saveButton, false);
                    return;
                }

                conversationData.collection = collectionName;
                conversationData.sidebarTitle = link.innerText.trim();
                conversationData.url = window.location.href;

                // Send to Backend
                fetch('http://127.0.0.1:8000/api/save_chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(conversationData)
                })
                .then(res => res.json())
                .then(data => {
                    updateButtonAppearance(saveButton, true);
                })
                .catch(err => {
                    console.error(err);
                    updateButtonAppearance(saveButton, false);
                });

            }, 1000);
        });

        // 5. Append to the Sidebar Item
        // We try to append to a specific child if possible, or just the link itself
        link.appendChild(saveButton);
        // console.log("Button added to:", link.innerText); // Debug log
    });
}

// SCAPER FUNCTION
function scrapeCurrentChat() {
    const messageElements = document.querySelectorAll('p.query-text-line, div.message-content');
    if (messageElements.length === 0) return null;

    const messages = Array.from(messageElements).map(elem => ({
        role: elem.classList.contains('query-text-line') ? 'user' : 'model',
        content: elem.innerText.trim()
    }));

    return {
        title: document.title,
        url: window.location.href,
        messages: messages
    };
}

// ROBUST OBSERVER
let debounceTimer = null;

const observer = new MutationObserver((mutations) => {
    // Clear the previous timer - we are "resetting the clock"
    if (debounceTimer) clearTimeout(debounceTimer);

    // Set a new timer. We wait 500ms for the page to "settle"
    debounceTimer = setTimeout(() => {
        addSaveButtons();
    }, 500); 
});

// Start observing
observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Also run once immediately just in case
addSaveButtons();
