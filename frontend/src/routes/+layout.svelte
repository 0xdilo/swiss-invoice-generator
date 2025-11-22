<script>
</script>

<div class="app-container">
  <nav class="main-nav">
    <div class="nav-links">
      <a href="/clients">Clients</a>
      <a href="/templates">Templates</a>
      <a href="/invoices">Invoices</a>
      <a href="/payments">Payments</a>
      <a href="/bank">Bank Details</a>
    </div>
  </nav>
  <main class="main-content">
    <slot />
  </main>
</div>

<style>
  .app-container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .main-nav {
    background-color: var(--surface-color);
    padding: 0 2rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 1000;
  }

  .nav-links {
    display: flex;
    align-items: center;
    max-width: 1000px;
    margin: 0 auto;
    height: 60px;
  }

  .nav-links a {
    padding: 0.75rem 1rem;
    margin-right: 1rem;
    font-weight: 500;
    color: var(--text-secondary-color);
    border-bottom: 2px solid transparent;
    transition:
      color 0.2s ease-in-out,
      border-color 0.2s ease-in-out;
  }

  .nav-links a:hover {
    color: var(--primary-color);
    text-decoration: none;
  }

  .main-content {
    flex-grow: 1;
    padding: 2rem;
    max-width: 1000px;
    width: 100%;
    margin: 0 auto;
  }

  :global(.main-content h2) {
    margin-bottom: 2rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
  }

  @media (max-width: 768px) {
    .main-nav {
      padding: 0 1rem;
    }
    .nav-links {
      overflow-x: auto;
      white-space: nowrap;
      -ms-overflow-style: none;
      scrollbar-width: none;
    }
    .nav-links::-webkit-scrollbar {
      display: none;
    }
    .nav-links a {
      padding: 0.5rem 0.75rem;
      margin-right: 0.5rem;
    }
    .main-content {
      padding: 1rem;
    }
    :global(.main-content h2) {
      font-size: 1.5rem;
    }
  }
</style>

