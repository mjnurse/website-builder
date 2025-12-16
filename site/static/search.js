// Search functionality with Lunr.js - activated with / or search button
(function() {
  // Wait for Lunr to be available
  function waitForLunr(callback, timeout = 5000) {
    const start = Date.now();
    const checkInterval = setInterval(() => {
      if (typeof lunr !== 'undefined') {
        clearInterval(checkInterval);
        callback();
      } else if (Date.now() - start > timeout) {
        clearInterval(checkInterval);
        console.warn('Lunr.js failed to load, search may not work optimally');
        callback();
      }
    }, 100);
  }
  
  // Initialize search UI and handlers immediately so shortcuts work
  initSearch();

  function initSearch() {
    let searchActive = false;
    let searchQuery = '';
    let searchResults = [];
    let selectedResultIndex = -1;
    let lunrIndex = null;
    
    // Create search overlay and input
    const searchOverlay = document.createElement('div');
    searchOverlay.id = 'search-overlay';
    searchOverlay.className = 'search-overlay';
    searchOverlay.innerHTML = `
      <div class="search-box">
        <input type="text" id="search-input" placeholder="Search pages..." autofocus>
        <div id="search-results" class="search-results"></div>
        <div class="search-hint">Press Esc to close • ↑↓ to navigate • Enter to select</div>
      </div>
    `;
    document.body.appendChild(searchOverlay);
    
    const searchInput = document.getElementById('search-input');
    const searchResultsContainer = document.getElementById('search-results');
    const searchBtn = document.getElementById('searchBtn');
    
    let documents = [];
    let documentStore = {};
    
    // Load search index from JSON file
    function loadSearchIndex() {
      fetch('/static/search-index.json')
        .then(response => response.json())
        .then(data => {
          documents = data;
          buildLunrIndex();
        })
        .catch(err => {
          console.error('Failed to load search index:', err);
        });
    }
    
    // Build Lunr index from loaded documents
    function buildLunrIndex() {
      if (typeof lunr === 'undefined' || !documents.length) {
        return;
      }
      
      try {
        lunrIndex = lunr(function() {
          this.ref('id');
          this.field('title', { boost: 10 });
          this.field('content');
          
          documents.forEach(doc => {
            this.add(doc);
          });
        });
        console.log('Search index built with', documents.length, 'documents');
      } catch (e) {
        console.error('Error building Lunr index:', e);
      }
    }
    
    function performSearch(query) {
      if (!query.trim()) {
        searchResults = [];
        renderResults();
        return;
      }
      
      if (!lunrIndex || typeof lunr === 'undefined') {
        // Fallback to simple string matching if Lunr not available
        fallbackSearch(query);
        return;
      }
      
      try {
        // Use Lunr search with wildcard
        const results = lunrIndex.search(query + '*');
        
        // Convert Lunr results to our format
        searchResults = results
          .map(result => {
            const doc = documents.find(d => d.id === result.ref);
            return doc;
          })
          .filter(doc => doc)
          .slice(0, 10);
      } catch (e) {
        console.error('Search error:', e);
        searchResults = [];
      }
      
      selectedResultIndex = -1;
      renderResults();
    }
    
    function fallbackSearch(query) {
      const lowerQuery = query.toLowerCase();
      
      searchResults = documents
        .filter(doc => 
          doc.title.toLowerCase().includes(lowerQuery) || 
          doc.content.toLowerCase().includes(lowerQuery)
        )
        .slice(0, 10);
      
      selectedResultIndex = -1;
      renderResults();
    }
    
    function getSnippet(content, query) {
      if (!content || !query) return '';
      
      const lowerContent = content.toLowerCase();
      const lowerQuery = query.toLowerCase();
      const queryTerms = lowerQuery.split(/\s+/).filter(t => t.length > 0);
      
      // Find the first occurrence of any query term
      let matchIndex = -1;
      for (const term of queryTerms) {
        matchIndex = lowerContent.indexOf(term);
        if (matchIndex !== -1) break;
      }
      
      if (matchIndex === -1) {
        // No match found, return first 150 chars
        return content.substring(0, 150) + (content.length > 150 ? '...' : '');
      }
      
      // Extract context around match
      const contextSize = 75;
      const start = Math.max(0, matchIndex - contextSize);
      const end = Math.min(content.length, matchIndex + contextSize);
      
      let snippet = content.substring(start, end);
      
      // Add ellipsis if truncated
      if (start > 0) snippet = '...' + snippet;
      if (end < content.length) snippet = snippet + '...';
      
      // Highlight matching terms
      queryTerms.forEach(term => {
        if (term.length > 2) {
          const regex = new RegExp(`(${term})`, 'gi');
          snippet = snippet.replace(regex, '<mark>$1</mark>');
        }
      });
      
      return snippet;
    }
    
    function renderResults() {
      searchResultsContainer.innerHTML = '';
      
      if (searchResults.length === 0) {
        if (searchQuery.trim()) {
          searchResultsContainer.innerHTML = '<div class="search-no-results">No results found</div>';
        }
        return;
      }
      
      const list = document.createElement('ul');
      list.className = 'search-results-list';
      
      searchResults.forEach((result, index) => {
        const snippet = getSnippet(result.content, searchQuery);
        const li = document.createElement('li');
        li.className = index === selectedResultIndex ? 'selected' : '';
        li.innerHTML = `
          <a href="${result.url}">
            <div class="result-title">${result.title}</div>
            <div class="result-snippet">${snippet}</div>
          </a>
        `;
        li.addEventListener('click', (e) => {
          e.preventDefault();
          window.location.href = result.url;
        });
        list.appendChild(li);
      });
      
      searchResultsContainer.appendChild(list);
    }
    
    function openSearch() {
      searchActive = true;
      searchOverlay.classList.add('active');
      searchInput.focus();
      searchInput.value = '';
      searchQuery = '';
      searchResults = [];
      selectedResultIndex = -1;
      renderResults();
    }
    
    function closeSearch() {
      searchActive = false;
      searchOverlay.classList.remove('active');
      searchInput.value = '';
      searchQuery = '';
      searchResults = [];
      selectedResultIndex = -1;
    }
    
    // Event listeners
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value;
      performSearch(searchQuery);
    });
    
    // Search button click
    if (searchBtn) {
      searchBtn.addEventListener('click', openSearch);
    }
    
    document.addEventListener('keydown', (e) => {
      // Home shortcut (H)
      if (e.key === 'h' || e.key === 'H') {
        if (!searchActive && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA' && !e.ctrlKey && !e.metaKey && !e.altKey) {
          window.location.href = '/';
        }
      }
      
      // Open search with /
      if (e.key === '/' && !searchActive && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        openSearch();
      }
      
      if (!searchActive) return;
      
      // Close search with Esc
      if (e.key === 'Escape') {
        e.preventDefault();
        closeSearch();
      }
      
      // Arrow down in search
      else if (e.key === 'ArrowDown') {
        e.preventDefault();
        const nextIndex = Math.min(selectedResultIndex + 1, searchResults.length - 1);
        if (nextIndex >= 0) {
          selectedResultIndex = nextIndex;
          renderResults();
        }
      }
      
      // Arrow up in search
      else if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prevIndex = Math.max(selectedResultIndex - 1, -1);
        selectedResultIndex = prevIndex;
        renderResults();
      }
      
      // Enter to select
      else if (e.key === 'Enter' && selectedResultIndex >= 0 && searchResults[selectedResultIndex]) {
        e.preventDefault();
        window.location.href = searchResults[selectedResultIndex].url;
      }
    });
    
    // Close search when clicking outside
    searchOverlay.addEventListener('click', (e) => {
      if (e.target === searchOverlay) {
        closeSearch();
      }
    });
    
    // Hook hero search box to open overlay if present
    const heroSearch = document.getElementById('hero-search-box');
    if (heroSearch) {
      heroSearch.addEventListener('focus', (e) => { openSearch(); });
      heroSearch.addEventListener('click', (e) => { openSearch(); });
    }

    // Load search index on initialization
    loadSearchIndex();

    // Also ensure we attempt to build the Lunr index when Lunr becomes available
    waitForLunr(function() {
      if (typeof buildLunrIndex === 'function') buildLunrIndex();
    });
  }
})();
