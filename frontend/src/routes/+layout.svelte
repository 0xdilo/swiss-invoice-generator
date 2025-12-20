<script>
  import { page } from '$app/stores';
  import '../app.css';
</script>

<div class="flex min-h-screen">
  <aside class="w-60 bg-sidebar flex flex-col fixed top-0 left-0 bottom-0 z-50
                lg:w-[72px]
                max-sm:fixed max-sm:bottom-0 max-sm:top-auto max-sm:left-0 max-sm:right-0 max-sm:w-full max-sm:h-auto max-sm:flex-row max-sm:p-2 max-sm:border-t max-sm:border-white/10">

    <div class="px-5 pt-5 pb-4 border-b border-white/[0.08] lg:hidden max-sm:hidden">
      <div class="flex items-center gap-3 text-text-inverse font-semibold text-lg">
        <svg class="opacity-90" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
        <span>Gestionale</span>
      </div>
    </div>

    <nav class="flex-1 py-4 overflow-y-auto
                lg:py-4
                max-sm:flex max-sm:justify-around max-sm:w-full max-sm:p-0 max-sm:overflow-x-auto">
      <div class="mb-6 max-sm:flex max-sm:m-0">
        <span class="block px-5 mb-2 text-[11px] font-semibold uppercase tracking-widest text-white/40 lg:hidden max-sm:hidden">Overview</span>
        <a href="/dashboard"
           class="flex items-center gap-3 px-5 py-2.5 mx-2 my-0.5 rounded-lg text-[15px] font-medium text-white/65 transition-all duration-150
                  hover:bg-sidebar-hover hover:text-text-inverse
                  lg:justify-center lg:px-3 lg:py-3 lg:mx-2 lg:my-1
                  max-sm:flex-col max-sm:p-2 max-sm:m-0 max-sm:text-[10px] max-sm:gap-1
                  {$page.url.pathname === '/dashboard' || $page.url.pathname === '/' ? 'bg-sidebar-active text-text-inverse' : ''}">
          <svg class="opacity-70 flex-shrink-0 max-sm:w-[22px] max-sm:h-[22px] {$page.url.pathname === '/dashboard' || $page.url.pathname === '/' ? 'opacity-100' : ''}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
          </svg>
          <span class="lg:hidden max-sm:block">Dashboard</span>
        </a>
        <a href="/calendar"
           class="flex items-center gap-3 px-5 py-2.5 mx-2 my-0.5 rounded-lg text-[15px] font-medium text-white/65 transition-all duration-150
                  hover:bg-sidebar-hover hover:text-text-inverse
                  lg:justify-center lg:px-3 lg:py-3 lg:mx-2 lg:my-1
                  max-sm:flex-col max-sm:p-2 max-sm:m-0 max-sm:text-[10px] max-sm:gap-1
                  {$page.url.pathname === '/calendar' ? 'bg-sidebar-active text-text-inverse' : ''}">
          <svg class="opacity-70 flex-shrink-0 max-sm:w-[22px] max-sm:h-[22px] {$page.url.pathname === '/calendar' ? 'opacity-100' : ''}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <span class="lg:hidden max-sm:block">Calendar</span>
        </a>
        <a href="/todos"
           class="flex items-center gap-3 px-5 py-2.5 mx-2 my-0.5 rounded-lg text-[15px] font-medium text-white/65 transition-all duration-150
                  hover:bg-sidebar-hover hover:text-text-inverse
                  lg:justify-center lg:px-3 lg:py-3 lg:mx-2 lg:my-1
                  max-sm:flex-col max-sm:p-2 max-sm:m-0 max-sm:text-[10px] max-sm:gap-1
                  {$page.url.pathname === '/todos' ? 'bg-sidebar-active text-text-inverse' : ''}">
          <svg class="opacity-70 flex-shrink-0 max-sm:w-[22px] max-sm:h-[22px] {$page.url.pathname === '/todos' ? 'opacity-100' : ''}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
          <span class="lg:hidden max-sm:block">Tasks</span>
        </a>
      </div>

      <div class="mb-6 max-sm:flex max-sm:m-0">
        <span class="block px-5 mb-2 text-[11px] font-semibold uppercase tracking-widest text-white/40 lg:hidden max-sm:hidden">Business</span>
        <a href="/clients"
           class="flex items-center gap-3 px-5 py-2.5 mx-2 my-0.5 rounded-lg text-[15px] font-medium text-white/65 transition-all duration-150
                  hover:bg-sidebar-hover hover:text-text-inverse
                  lg:justify-center lg:px-3 lg:py-3 lg:mx-2 lg:my-1
                  max-sm:flex-col max-sm:p-2 max-sm:m-0 max-sm:text-[10px] max-sm:gap-1
                  {$page.url.pathname.startsWith('/clients') ? 'bg-sidebar-active text-text-inverse' : ''}">
          <svg class="opacity-70 flex-shrink-0 max-sm:w-[22px] max-sm:h-[22px] {$page.url.pathname.startsWith('/clients') ? 'opacity-100' : ''}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <span class="lg:hidden max-sm:block">Clients</span>
        </a>
        <a href="/invoices"
           class="flex items-center gap-3 px-5 py-2.5 mx-2 my-0.5 rounded-lg text-[15px] font-medium text-white/65 transition-all duration-150
                  hover:bg-sidebar-hover hover:text-text-inverse
                  lg:justify-center lg:px-3 lg:py-3 lg:mx-2 lg:my-1
                  max-sm:flex-col max-sm:p-2 max-sm:m-0 max-sm:text-[10px] max-sm:gap-1
                  {$page.url.pathname === '/invoices' ? 'bg-sidebar-active text-text-inverse' : ''}">
          <svg class="opacity-70 flex-shrink-0 max-sm:w-[22px] max-sm:h-[22px] {$page.url.pathname === '/invoices' ? 'opacity-100' : ''}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          <span class="lg:hidden max-sm:block">Invoices</span>
        </a>
        <a href="/expenses"
           class="flex items-center gap-3 px-5 py-2.5 mx-2 my-0.5 rounded-lg text-[15px] font-medium text-white/65 transition-all duration-150
                  hover:bg-sidebar-hover hover:text-text-inverse
                  lg:justify-center lg:px-3 lg:py-3 lg:mx-2 lg:my-1
                  max-sm:flex-col max-sm:p-2 max-sm:m-0 max-sm:text-[10px] max-sm:gap-1
                  {$page.url.pathname === '/expenses' ? 'bg-sidebar-active text-text-inverse' : ''}">
          <svg class="opacity-70 flex-shrink-0 max-sm:w-[22px] max-sm:h-[22px] {$page.url.pathname === '/expenses' ? 'opacity-100' : ''}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="1" x2="12" y2="23"/>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
          <span class="lg:hidden max-sm:block">Expenses</span>
        </a>
      </div>
    </nav>

    <div class="py-4 border-t border-white/[0.08] max-sm:hidden">
      <a href="/settings"
         class="flex items-center gap-3 px-5 py-2.5 mx-2 my-0.5 rounded-lg text-[15px] font-medium text-white/65 transition-all duration-150
                hover:bg-sidebar-hover hover:text-text-inverse
                lg:justify-center lg:px-3 lg:py-3 lg:mx-2 lg:my-1
                {$page.url.pathname === '/settings' ? 'bg-sidebar-active text-text-inverse' : ''}">
        <svg class="opacity-70 flex-shrink-0 {$page.url.pathname === '/settings' ? 'opacity-100' : ''}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span class="lg:hidden">Settings</span>
      </a>
    </div>
  </aside>

  <main class="flex-1 ml-60 p-8 min-h-screen max-w-[calc(100vw-240px)]
               lg:ml-[72px] lg:max-w-[calc(100vw-72px)]
               max-sm:ml-0 max-sm:mb-[70px] max-sm:p-5 max-sm:max-w-full">
    <slot />
  </main>
</div>
