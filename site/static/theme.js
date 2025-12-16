// Theme toggle functionality
(function() {
  const html = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
  
  // Initialize theme from localStorage or system preference
  function initTheme() {
    const stored = localStorage.getItem('theme');
    if (stored) {
      html.setAttribute('data-theme', stored);
    } else if (prefersDark.matches) {
      html.setAttribute('data-theme', 'dark');
    } else {
      html.setAttribute('data-theme', 'light');
    }
  }
  
  // Toggle between light and dark
  function toggleTheme() {
    const current = html.getAttribute('data-theme') || 'dark';
    const next = current === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  }
  
  // Listen for system theme changes
  prefersDark.addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      html.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    }
  });
  
  // Attach click handler
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }
  
  // Initialize on load
  initTheme();
})();

// Keyboard navigation for sections
(function() {
  // Select all nav links (we'll derive a shortcut if none explicitly provided)
  const navLinks = document.querySelectorAll('.nav-link');
  const shortcuts = {};

  // Build shortcuts map: prefer explicit data-shortcut, otherwise use first letter of the directory
  navLinks.forEach(link => {
    const explicit = link.getAttribute('data-shortcut');
    let key = explicit ? explicit.toUpperCase() : null;

    if (!key) {
      // Derive from href: take first path segment and its first alphanumeric char
      const href = link.getAttribute('href') || link.href || '';
      const path = href.replace(/^\//, '').replace(/\/$/, '');
      const firstSeg = path.split('/')[0] || '';
      const match = firstSeg.replace(/[^a-zA-Z0-9]/g, '').charAt(0);
      if (match) key = match.toUpperCase();
    }

    // Only assign if we have a key and it's not already taken (explicit shortcuts win)
    if (key && !shortcuts[key]) {
      shortcuts[key] = link;
    }
  });

  // Listen for keyboard events
  document.addEventListener('keydown', (e) => {
    // Only trigger if no modifier keys are pressed and not in input
    if ((e.ctrlKey || e.metaKey || e.altKey) || e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
      return;
    }

    const key = e.key.toUpperCase();
    // Special-case: U = go up / back a page
    if (key === 'U') {
      e.preventDefault();
      // Use history.back() to go to previous page
      window.history.back();
      return;
    }
    if (shortcuts[key]) {
      e.preventDefault();
      shortcuts[key].click();
    }
  });
})();

