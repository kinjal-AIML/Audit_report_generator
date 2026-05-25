/**
 * Responsive Web Application - Utility Functions
 * Handles responsive behavior, mobile interactions, and accessibility
 */

// ============================================================
// RESPONSIVE SIDEBAR HANDLING
// ============================================================

/**
 * Check if device is mobile
 */
function isMobileDevice() {
  return window.innerWidth < 768;
}

/**
 * Toggle sidebar visibility on all screen sizes
 */
function toggleSidebar() {
  const sidebar = document.getElementById('mainSidebar');
  const contentWrapper = document.querySelector('.content-wrapper');
  const overlay = document.getElementById('sidebarOverlay');
  
  if (!sidebar) return;
  
  // Toggle sidebar visibility
  sidebar.classList.toggle('sidebar-closed');
  
  // Also toggle content wrapper margin on desktop
  if (contentWrapper && !isMobileDevice()) {
    contentWrapper.classList.toggle('sidebar-closed');
  }
  
  // Show/hide overlay on mobile
  if (isMobileDevice() && overlay) {
    overlay.classList.toggle('active');
  }
}

/**
 * Handle sidebar toggle for all screen sizes
 */
function setupResponsiveSidebar() {
  const sidebar = document.getElementById('mainSidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggleBtn = document.getElementById('sidebarFloatToggle');

  if (!toggleBtn || !sidebar) return;

  // Toggle button click handler
  toggleBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    toggleSidebar();
  });

  // Close sidebar when clicking overlay (mobile only)
  if (overlay) {
    overlay.addEventListener('click', function() {
      if (sidebar.classList.contains('sidebar-closed') === false && isMobileDevice()) {
        toggleSidebar();
      }
    });
  }

  // Close sidebar on ESC key
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && sidebar && !sidebar.classList.contains('sidebar-closed')) {
      closeSidebar();
    }
  });

  // Click anywhere in content to close sidebar on mobile
  document.addEventListener('click', function(event) {
    if (isMobileDevice() && 
        sidebar && 
        !sidebar.classList.contains('sidebar-closed') && 
        !sidebar.contains(event.target) && 
        !toggleBtn.contains(event.target)) {
      closeSidebar();
    }
  });

  // Handle resize - maintain proper sidebar state
  window.addEventListener('resize', debounce(function() {
    const contentWrapper = document.querySelector('.content-wrapper');
    
    if (isMobileDevice()) {
      // On mobile, close sidebar
      sidebar.classList.add('sidebar-closed');
      if (contentWrapper) contentWrapper.classList.remove('sidebar-closed');
      if (overlay) overlay.classList.remove('active');
    } else {
      // On desktop, show sidebar
      sidebar.classList.remove('sidebar-closed');
      if (contentWrapper) contentWrapper.classList.remove('sidebar-closed');
      if (overlay) overlay.classList.remove('active');
    }
  }, 250));

  // Initial state
  const contentWrapper = document.querySelector('.content-wrapper');
  if (isMobileDevice()) {
    sidebar.classList.add('sidebar-closed');
    if (contentWrapper) contentWrapper.classList.remove('sidebar-closed');
  } else {
    sidebar.classList.remove('sidebar-closed');
    if (contentWrapper) contentWrapper.classList.remove('sidebar-closed');
  }
}

/**
 * Debounce function for performance
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Close sidebar
 */
function closeSidebar() {
  const sidebar = document.getElementById('mainSidebar');
  const contentWrapper = document.querySelector('.content-wrapper');
  const overlay = document.getElementById('sidebarOverlay');

  if (sidebar) sidebar.classList.add('sidebar-closed');
  if (contentWrapper && !isMobileDevice()) contentWrapper.classList.add('sidebar-closed');
  if (overlay) overlay.classList.remove('active');
}

/**
 * Open sidebar
 */
function openSidebar() {
  const sidebar = document.getElementById('mainSidebar');
  const contentWrapper = document.querySelector('.content-wrapper');

  if (sidebar) sidebar.classList.remove('sidebar-closed');
  if (contentWrapper && !isMobileDevice()) contentWrapper.classList.remove('sidebar-closed');
}

// ============================================================
// RESPONSIVE GRAPH SIZING
// ============================================================

/**
 * Get responsive graph dimensions
 */
function getResponsiveGraphHeight() {
  if (window.innerWidth < 576) {
    return 300;
  } else if (window.innerWidth < 768) {
    return 350;
  } else if (window.innerWidth < 1200) {
    return 400;
  } else {
    return 500;
  }
}

/**
 * Resize D3 graph responsively
 */
function resizeD3Graph() {
  const container = document.getElementById('networkGraphContainer');
  const svg = document.getElementById('networkGraphSvg');

  if (!container || !svg) return;

  const newHeight = getResponsiveGraphHeight();
  container.style.height = newHeight + 'px';
}

/**
 * Setup graph resize listener
 */
function setupGraphResize() {
  window.addEventListener('resize', debounce(resizeD3Graph, 300));
  resizeD3Graph(); // Initial call
}

// ============================================================
// RESPONSIVE TABLE HANDLING
// ============================================================

/**
 * Make table responsive for mobile
 */
function setupResponsiveTable() {
  const table = document.getElementById('resultsTable');
  if (!table) return;

  // Add horizontal scroll indicator on mobile
  const wrapper = table.closest('.table-responsive');
  if (wrapper && window.innerWidth < 768) {
    wrapper.style.overflowX = 'auto';
    wrapper.style.WebkitOverflowScrolling = 'touch';
  }
}

// ============================================================
// TOUCH FRIENDLY BUTTONS
// ============================================================

/**
 * Enhance button touch targets
 */
function setupTouchFriendlyButtons() {
  const buttons = document.querySelectorAll('.btn, [role="button"]');

  buttons.forEach(btn => {
    // Ensure minimum touch target size
    const styles = window.getComputedStyle(btn);
    const height = parseInt(styles.height);
    const width = parseInt(styles.width);

    if (height < 48 || width < 48) {
      // Add padding to meet 48x48px minimum
      btn.style.padding = 'calc(0.75rem + 2px) calc(1.5rem + 2px)';
      btn.style.minHeight = '48px';
    }
  });
}

// ============================================================
// ACCOUNT SIDEBAR RESPONSIVE
// ============================================================

/**
 * Setup account sidebar responsiveness
 */
function setupAccountSidebarResponsive() {
  const sidebar = document.getElementById('accountSidebar');
  const overlay = document.getElementById('sidebarOverlayBg');
  const closeBtn = document.querySelector('.sidebar-close-btn');

  if (!sidebar) return;

  // Close on overlay click
  if (overlay) {
    overlay.addEventListener('click', closeAccountSidebar);
  }

  // Close on close button click
  if (closeBtn) {
    closeBtn.addEventListener('click', closeAccountSidebar);
  }

  // Close on ESC key
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && sidebar.classList.contains('open')) {
      closeAccountSidebar();
    }
  });

  // Prevent body scroll when sidebar open
  if (sidebar.classList.contains('open')) {
    document.body.style.overflow = 'hidden';
  }
}

// ============================================================
// MODAL IMPROVEMENTS
// ============================================================

/**
 * Make modals responsive
 */
function setupResponsiveModals() {
  const modals = document.querySelectorAll('.modal, [role="dialog"]');

  modals.forEach(modal => {
    // Adjust modal size based on screen width
    if (window.innerWidth < 768) {
      modal.style.maxWidth = '95vw';
      modal.style.margin = '0 auto';
    }
  });
}

// ============================================================
// VIEWPORT HEIGHT FIXES
// ============================================================

/**
 * Fix viewport height for mobile (address bar issue)
 */
function setupViewportHeightFix() {
  function updateVH() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
  }

  updateVH();
  window.addEventListener('resize', debounce(updateVH, 250));
  window.addEventListener('orientationchange', debounce(updateVH, 250));
}

// ============================================================
// INITIALIZATION
// ============================================================

/**
 * Initialize all responsive features
 */
function initializeResponsiveFeatures() {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setupResponsiveSidebar();
      setupGraphResize();
      setupResponsiveTable();
      setupTouchFriendlyButtons();
      setupAccountSidebarResponsive();
      setupResponsiveModals();
      setupViewportHeightFix();
    });
  } else {
    setupResponsiveSidebar();
    setupGraphResize();
    setupResponsiveTable();
    setupTouchFriendlyButtons();
    setupAccountSidebarResponsive();
    setupResponsiveModals();
    setupViewportHeightFix();
  }
}

// Auto-initialize when script loads
initializeResponsiveFeatures();
