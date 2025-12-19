<script>
  import { page } from '$app/stores';
</script>

<div class="app-shell">
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="logo">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
        <span>Gestionale</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-section">
        <span class="nav-section-label">Overview</span>
        <a href="/dashboard" class:active={$page.url.pathname === '/dashboard' || $page.url.pathname === '/'}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
          </svg>
          <span>Dashboard</span>
        </a>
        <a href="/calendar" class:active={$page.url.pathname === '/calendar'}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <span>Calendar</span>
        </a>
        <a href="/todos" class:active={$page.url.pathname === '/todos'}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
          <span>Tasks</span>
        </a>
      </div>

      <div class="nav-section">
        <span class="nav-section-label">Business</span>
        <a href="/clients" class:active={$page.url.pathname.startsWith('/clients')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <span>Clients</span>
        </a>
        <a href="/invoices" class:active={$page.url.pathname === '/invoices'}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          <span>Invoices</span>
        </a>
        <a href="/expenses" class:active={$page.url.pathname === '/expenses'}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="1" x2="12" y2="23"/>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
          <span>Expenses</span>
        </a>
      </div>
    </nav>

    <div class="sidebar-footer">
      <a href="/settings" class:active={$page.url.pathname === '/settings'}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span>Settings</span>
      </a>
    </div>
  </aside>

  <main class="main-content">
    <slot />
  </main>
</div>

<style>
  .app-shell {
    display: flex;
    min-height: 100vh;
  }

  .sidebar {
    width: var(--sidebar-width);
    background: var(--color-sidebar);
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 100;
  }

  .sidebar-header {
    padding: 1.25rem 1.25rem 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: var(--color-text-inverse);
    font-weight: 600;
    font-size: 1.125rem;
  }

  .logo svg {
    opacity: 0.9;
  }

  .sidebar-nav {
    flex: 1;
    padding: 1rem 0;
    overflow-y: auto;
  }

  .nav-section {
    margin-bottom: 1.5rem;
  }

  .nav-section-label {
    display: block;
    padding: 0 1.25rem;
    margin-bottom: 0.5rem;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(255, 255, 255, 0.4);
  }

  .sidebar-nav a,
  .sidebar-footer a {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.625rem 1.25rem;
    margin: 0.125rem 0.5rem;
    border-radius: var(--radius-md);
    color: rgba(255, 255, 255, 0.65);
    font-size: 0.9375rem;
    font-weight: 500;
    transition: all 0.15s ease;
  }

  .sidebar-nav a:hover,
  .sidebar-footer a:hover {
    background: var(--color-sidebar-hover);
    color: var(--color-text-inverse);
  }

  .sidebar-nav a.active,
  .sidebar-footer a.active {
    background: var(--color-sidebar-active);
    color: var(--color-text-inverse);
  }

  .sidebar-nav a svg,
  .sidebar-footer a svg {
    opacity: 0.7;
    flex-shrink: 0;
  }

  .sidebar-nav a.active svg,
  .sidebar-footer a.active svg,
  .sidebar-nav a:hover svg,
  .sidebar-footer a:hover svg {
    opacity: 1;
  }

  .sidebar-footer {
    padding: 1rem 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }

  .main-content {
    flex: 1;
    margin-left: var(--sidebar-width);
    padding: 2rem 2.5rem;
    min-height: 100vh;
    max-width: calc(100vw - var(--sidebar-width));
  }

  @media (max-width: 1024px) {
    .sidebar {
      width: var(--sidebar-collapsed);
    }

    .logo span,
    .nav-section-label,
    .sidebar-nav a span,
    .sidebar-footer a span {
      display: none;
    }

    .sidebar-nav a,
    .sidebar-footer a {
      justify-content: center;
      padding: 0.75rem;
      margin: 0.25rem 0.5rem;
    }

    .main-content {
      margin-left: var(--sidebar-collapsed);
      max-width: calc(100vw - var(--sidebar-collapsed));
    }
  }

  @media (max-width: 640px) {
    .sidebar {
      position: fixed;
      bottom: 0;
      top: auto;
      left: 0;
      right: 0;
      width: 100%;
      height: auto;
      flex-direction: row;
      padding: 0.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .sidebar-header,
    .nav-section-label,
    .sidebar-footer {
      display: none;
    }

    .sidebar-nav {
      display: flex;
      justify-content: space-around;
      width: 100%;
      padding: 0;
      overflow-x: auto;
    }

    .nav-section {
      display: flex;
      margin: 0;
    }

    .sidebar-nav a {
      flex-direction: column;
      padding: 0.5rem;
      margin: 0;
      font-size: 0.625rem;
      gap: 0.25rem;
    }

    .sidebar-nav a span {
      display: block;
    }

    .sidebar-nav a svg {
      width: 22px;
      height: 22px;
    }

    .main-content {
      margin-left: 0;
      margin-bottom: 70px;
      padding: 1.25rem;
      max-width: 100vw;
    }
  }
</style>
