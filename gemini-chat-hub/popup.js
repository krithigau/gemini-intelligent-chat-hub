document.addEventListener('DOMContentLoaded', () => {
    
    // --- Elements ---
    const searchBar = document.getElementById('search-bar');
    const collectionsView = document.getElementById('collections-view');
    const chatsView = document.getElementById('chats-view');
    const searchView = document.getElementById('search-view');
    
    const collectionsList = document.getElementById('collections-list');
    const chatsList = document.getElementById('chats-list');
    const searchResults = document.getElementById('search-results');
    const backBtn = document.getElementById('back-to-collections');
    const backSearchBtn = document.getElementById('back-from-search');
    const currentCollectionTitle = document.getElementById('current-collection-name');

    // --- API URL ---
    const API_BASE = 'http://127.0.0.1:8000';

    // --- Initial Load ---
    loadCollections();

    // --- Event Listeners ---
    
    // 1. Search Handler (Press Enter)
    searchBar.addEventListener('keyup', (event) => {
        const query = searchBar.value.trim();

        // If search bar is empty, show collections again
        if (query.length === 0) {
            showView('collections');
            return;
        }

        // Only search on Enter
        if (event.key === 'Enter') {
            if (query.length < 3) {
                // Optional: Show a subtle toast or message
                return;
            }
            performAiSearch(query);
        }
    });

    // 2. Back Buttons
    backBtn.addEventListener('click', () => {
        showView('collections');
        currentCollectionTitle.innerText = ''; 
    });
    
    backSearchBtn.addEventListener('click', () => {
        showView('collections');
        searchBar.value = ''; 
        currentCollectionTitle.innerText = ''; 
    });


    // --- Functions ---

    function showView(viewName) {
        collectionsView.classList.remove('active');
        chatsView.classList.remove('active');
        searchView.classList.remove('active');

        if (viewName === 'collections') collectionsView.classList.add('active');
        if (viewName === 'chats') chatsView.classList.add('active');
        if (viewName === 'search') searchView.classList.add('active');
    }

    async function loadCollections() {
        try {
            const response = await fetch(`${API_BASE}/api/collections`);
            const collections = await response.json();

            collectionsList.innerHTML = ''; 

            if (collections.length === 0) {
                collectionsList.innerHTML = '<div style="padding:10px; color:#999; font-size:13px;">No collections found. Save a chat to get started!</div>';
                return;
            }

            collections.forEach(name => {
                const tag = document.createElement('div');
                tag.className = 'collection-tag';
                tag.innerText = name;
                tag.addEventListener('click', () => loadChatsForCollection(name));
                collectionsList.appendChild(tag);
            });
        } catch (error) {
            console.error('Error loading collections:', error);
            collectionsList.innerHTML = '<div style="color:#d93025; font-size:13px;">Error connecting to server.</div>';
        }
    }

    async function loadChatsForCollection(collectionName) {
        currentCollectionTitle.innerText = collectionName;
        showView('chats');
        chatsList.innerHTML = '<div style="color:#666; font-size:13px;">Loading...</div>';

        try {
            const response = await fetch(`${API_BASE}/api/chats?collection=${encodeURIComponent(collectionName)}`);
            const chats = await response.json();

            chatsList.innerHTML = ''; 

            if (chats.length === 0) {
                chatsList.innerHTML = '<div style="color:#666; font-size:13px;">No chats in this collection.</div>';
                return;
            }

            chats.forEach(chat => {
                const link = document.createElement('a');
                link.className = 'chat-link';
                link.href = chat.url;
                link.target = '_blank'; 
                link.innerText = chat.title || 'Untitled Chat';
                chatsList.appendChild(link);
            });

        } catch (error) {
            chatsList.innerHTML = '<div style="color:#d93025">Error loading chats.</div>';
        }
    }

    async function performAiSearch(query) {
        showView('search');
        // New Ghibli-style loading message
searchResults.innerHTML = `
    <div style="padding:20px; text-align:center; color:#88a087;">
        <div style="font-size:24px; margin-bottom:10px;">🍃</div>
        <i>The spirits are gathering your memories...</i>
    </div>
`;
        let activeCollection = null;
        if (currentCollectionTitle.innerText !== "") {
            activeCollection = currentCollectionTitle.innerText;
        }

        try {
            const response = await fetch(`${API_BASE}/api/ai_search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    "query": query,
                    "collection_filter": activeCollection 
                })
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            
            const data = await response.json();
            displayAiResults(data, activeCollection);

        } catch (error) {
            searchResults.innerHTML = `<div style="color:#d93025; padding:10px; font-size:13px;">Error: ${error.message}</div>`;
        }
    }

    function displayAiResults(data, filteredBy) {
        searchResults.innerHTML = ''; 

        if (filteredBy) {
            const filterBadge = document.createElement('div');
            filterBadge.style.fontSize = '12px';
            filterBadge.style.color = '#1a73e8';
            filterBadge.style.marginBottom = '12px';
            filterBadge.style.padding = '4px 8px';
            filterBadge.style.backgroundColor = '#e8f0fe';
            filterBadge.style.borderRadius = '4px';
            filterBadge.style.display = 'inline-block';
            filterBadge.innerHTML = `Searching inside: <b>${filteredBy}</b>`;
            searchResults.appendChild(filterBadge);
        }

        const answerDiv = document.createElement('div');
        answerDiv.className = 'ai-answer';
        // Simple formatting for bold text from markdown (basic)
        let formattedAnswer = data.answer.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>'); 
        answerDiv.innerHTML = formattedAnswer;
        searchResults.appendChild(answerDiv);

        if (data.sources && data.sources.length > 0) {
            const sourcesSection = document.createElement('div');
            sourcesSection.className = 'sources-section';
            
            const sourcesHeader = document.createElement('div');
            sourcesHeader.style.fontSize = '11px';
            sourcesHeader.style.fontWeight = 'bold';
            sourcesHeader.style.color = '#5f6368';
            sourcesHeader.style.marginBottom = '5px';
            sourcesHeader.innerText = 'SOURCES';
            sourcesSection.appendChild(sourcesHeader);

            data.sources.forEach(source => {
                const sourceDiv = document.createElement('div');
                sourceDiv.className = 'source-link';
                // Use a little link icon
                sourceDiv.innerHTML = `🔗 <a href="${source.url}" target="_blank">${source.title}</a>`;
                sourcesSection.appendChild(sourceDiv);
            });
            
            searchResults.appendChild(sourcesSection);
        }
    }
});