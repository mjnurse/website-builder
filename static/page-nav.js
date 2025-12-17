// Page list navigation with numbers and arrow keys
(function() {
  const pageList = document.querySelector('.page-list');
  if (!pageList) return;
  
  const links = Array.from(pageList.querySelectorAll('a[data-number]'));
  let currentIndex = -1;
  let numberBuffer = '';
  let numberTimeout = null;
  let keyboardNavActive = false;
  
  function setKeyboardNavMode(active) {
    keyboardNavActive = active;
    if (active) {
      pageList.classList.add('keyboard-nav-active');
    } else {
      pageList.classList.remove('keyboard-nav-active');
    }
  }
  
  function clearHighlight() {
    links.forEach(link => link.classList.remove('highlighted'));
  }
  
  function highlightLink(index) {
    clearHighlight();
    setKeyboardNavMode(true);
    if (index >= 0 && index < links.length) {
      currentIndex = index;
      links[index].classList.add('highlighted');
      // Scroll with offset to account for sticky header
      const headerHeight = document.querySelector('.header')?.offsetHeight || 80;
      const linkTop = links[index].getBoundingClientRect().top + window.scrollY;
      window.scrollTo({
        top: linkTop - headerHeight - 20,
        behavior: 'smooth'
      });
    }
  }
  
  function navigateToLink() {
    if (currentIndex >= 0 && currentIndex < links.length) {
      window.location.href = links[currentIndex].href;
    }
  }
  
  function handleNumberKey(num) {
    // Clear existing timeout
    if (numberTimeout) {
      clearTimeout(numberTimeout);
    }

    numberBuffer += num;
    
    // Wait 500ms for additional digits before highlighting
    numberTimeout = setTimeout(() => {
      const linkIndex = parseInt(numberBuffer, 10) - 1;
      
      // If valid link number, highlight it (do NOT navigate yet)
      if (Number.isFinite(linkIndex) && linkIndex >= 0 && linkIndex < links.length) {
        highlightLink(linkIndex);
      }
      
      // Clear buffer after highlighting (or if invalid)
      numberBuffer = '';
    }, 400);
  }
  
  document.addEventListener('keydown', (e) => {
    // Skip if in input/textarea or modifier keys are pressed (except for forward slash in search)
    if ((e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') && e.key !== '/') {
      return;
    }
    if (e.ctrlKey || e.metaKey || e.altKey) {
      return;
    }
    
    // Arrow down
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = currentIndex + 1;
      if (nextIndex < links.length) {
        highlightLink(nextIndex);
      }
      numberBuffer = '';
      if (numberTimeout) clearTimeout(numberTimeout);
    }
    
    // Arrow up
    else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = currentIndex - 1;
      if (prevIndex >= 0) {
        highlightLink(prevIndex);
      }
      numberBuffer = '';
      if (numberTimeout) clearTimeout(numberTimeout);
    }
    
    // Enter -> navigate to highlighted item
    else if (e.key === 'Enter' && currentIndex >= 0) {
      e.preventDefault();
      navigateToLink();
    }
    
    // Number keys (0-9)
    else if (e.key >= '0' && e.key <= '9') {
      e.preventDefault();
      handleNumberKey(e.key);
    }
  });
  
  // Detect mouse movement to exit keyboard navigation mode
  pageList.addEventListener('mousemove', () => {
    if (keyboardNavActive) {
      setKeyboardNavMode(false);
      clearHighlight();
      currentIndex = -1;
    }
  });
})();
