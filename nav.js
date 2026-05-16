/* ============================================================
   ROMANS ROAD — SHARED APP JAVASCRIPT
   nav.js — navigation, mobile menu, PWA, expansion slots
   ============================================================ */

(function () {
  'use strict';

  // ── SITE NAVIGATION CONFIG ─────────────────────────────────
  // Add new sections here. Nothing else needs to change.
  const SITE_NAV = [
    {
      label: 'Commentary',
      items: [
        { label: 'Romans — Volume I',   url: '/Romans_Road.html' },
        { label: 'Romans — Volume II',  url: '/Romans_Road_2.html' },
        { label: 'Romans — Volume III', url: '/Romans_Road_3.html' },
        { label: 'Romans — Volume IV',  url: '/Romans_Road_4.html' },
        { label: 'Romans — Volume V',   url: '/Romans_Road_5.html' },
        // { label: 'Gospel of John — Volume I', url: '/John_1.html' },
      ]
    },
    {
      label: 'Growth Lessons',
      items: [
        { label: 'Spiritual Growth Lessons', url: 'https://lessons.intelligencereport.info/index.html' },
        { label: 'Search lessons',            url: 'https://lessons.intelligencereport.info/search.html' },
      ]
    },
    {
      label: 'Illuminations',
      url: '/illuminations.html',
      items: [
        { label: 'All Illuminations',         url: '/illuminations.html' },
        { label: 'Romans 1:16–17',             url: '/illuminations/romans_1_16-17.html' },
        { label: 'Forty Things at Salvation',  url: '/illuminations/forty_things.html' },
        { label: 'Chapter 33 — φθόνος/φόνος', url: '/illuminations/chapter_33.html' },
      ]
    },
    {
      label: 'Language',
      items: [
        { label: 'Guide to the Greek NT', url: '/greek-guide.html' },
      ]
    },
    {
      label: 'Search',
      url: '/search.html'
    },
    {
      label: 'Home',
      url: '/index.html'
    },
  ];

  // ── SITE TOP NAV HEIGHT (CSS var --site-top-nav-h for sidebar / progress bar) ──
  function updateSiteTopNavHeight() {
    const el = document.getElementById('site-top-nav');
    if (!el) return;
    const h = Math.ceil(el.getBoundingClientRect().height);
    document.documentElement.style.setProperty('--site-top-nav-h', h + 'px');
  }

  // ── SITE NAV INJECTOR ──────────────────────────────────────
  function initSiteNav() {
    // Don't inject twice
    if (document.getElementById('site-top-nav')) return;

    // Landing page already has a horizontal .top-bar; avoid duplicate nav
    if (document.querySelector('.landing-wrap')) return;

    const nav = document.createElement('nav');
    nav.id = 'site-top-nav';

    // Determine current path for active highlighting
    const currentPath = window.location.pathname.replace(/\/$/, '') || '/index.html';

    const ul = document.createElement('ul');

    SITE_NAV.forEach(section => {
      const li = document.createElement('li');
      const hasDropdown = section.items && section.items.length > 0;

      if (hasDropdown) {
        li.className = 'site-nav-dropdown';
        const btn = document.createElement('button');
        btn.textContent = section.label;
        btn.setAttribute('aria-haspopup', 'true');
        btn.setAttribute('aria-expanded', 'false');
        li.appendChild(btn);

        const dropdown = document.createElement('ul');
        dropdown.className = 'site-nav-menu';
        section.items.forEach(item => {
          const dli = document.createElement('li');
          const a = document.createElement('a');
          a.href = item.url;
          a.textContent = item.label;
          if (currentPath.endsWith(item.url.replace(/^\//, ''))) {
            a.classList.add('active');
          }
          dli.appendChild(a);
          dropdown.appendChild(dli);
        });
        li.appendChild(dropdown);

        // Toggle on click
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const open = li.classList.contains('open');
          // Close all
          ul.querySelectorAll('.site-nav-dropdown').forEach(d => {
            d.classList.remove('open');
            d.querySelector('button').setAttribute('aria-expanded', 'false');
          });
          if (!open) {
            li.classList.add('open');
            btn.setAttribute('aria-expanded', 'true');
          }
        });

      } else {
        // Simple link
        const a = document.createElement('a');
        a.href = section.url;
        a.textContent = section.label;
        if (currentPath.endsWith(section.url.replace(/^\//, ''))) {
          a.classList.add('active');
        }
        li.appendChild(a);
      }

      ul.appendChild(li);
    });

    // Close dropdowns on outside click
    document.addEventListener('click', () => {
      ul.querySelectorAll('.site-nav-dropdown').forEach(d => {
        d.classList.remove('open');
        const btn = d.querySelector('button');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      });
    });

    nav.appendChild(ul);

    // Inject at top of body
    document.body.insertBefore(nav, document.body.firstChild);

    updateSiteTopNavHeight();
    window.addEventListener('resize', updateSiteTopNavHeight);
    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(updateSiteTopNavHeight);
      ro.observe(nav);
    }
  }

  // ── NAV SEARCH FILTER ──────────────────────────────────────
  window.filterNav = function (q) {
    const items = document.querySelectorAll('#nav-list li');
    q = q.toLowerCase();
    items.forEach(li => {
      li.style.display = li.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  };

  // ── MOBILE SIDEBAR ─────────────────────────────────────────
  function initMobileMenu() {
    const toggle  = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!toggle || !sidebar) return;

    function openMenu() {
      sidebar.classList.add('open');
      overlay.classList.add('open');
      document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
      sidebar.classList.remove('open');
      overlay.classList.remove('open');
      document.body.style.overflow = '';
    }

    toggle.addEventListener('click', openMenu);
    overlay.addEventListener('click', closeMenu);

    document.querySelectorAll('#nav-list a').forEach(a => {
      a.addEventListener('click', () => {
        if (window.innerWidth <= 900) closeMenu();
      });
    });
  }

  // ── ACTIVE SECTION HIGHLIGHT ───────────────────────────────
  function initSectionObserver() {
    const headings = document.querySelectorAll('h1[id], h2[id], h3[id]');
    const navLinks = document.querySelectorAll('#nav-list a');

    if (navLinks.length > 0) navLinks[0].classList.add('active');

    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        navLinks.forEach(a => a.classList.remove('active'));
        const active = document.querySelector(
          `#nav-list a[href="#${entry.target.id}"]`
        );
        if (active) {
          active.classList.add('active');
          active.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      });
    }, { rootMargin: '-10% 0px -85% 0px', threshold: 0 });

    headings.forEach(h => observer.observe(h));
  }

  // ── SCROLL TO TOP ──────────────────────────────────────────
  function initScrollTop() {
    const btn = document.getElementById('top-btn');
    if (!btn) return;
    window.addEventListener('scroll', () => {
      btn.classList.toggle('visible', window.scrollY > 400);
    });
  }

  // ── READING PROGRESS BAR ───────────────────────────────────
  function initProgressBar() {
    const bar = document.getElementById('progress-bar');
    if (!bar) return;
    window.addEventListener('scroll', () => {
      const scrolled  = window.scrollY;
      const total     = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = total > 0 ? (scrolled / total * 100) + '%' : '0%';
    });
  }

  // ── PWA INSTALL BANNER ─────────────────────────────────────
  function initInstallBanner() {
    let deferredPrompt = null;
    const banner = document.getElementById('install-banner');
    if (!banner) return;

    window.addEventListener('beforeinstallprompt', e => {
      e.preventDefault();
      deferredPrompt = e;
      banner.style.display = 'flex';
    });

    const installBtn = banner.querySelector('.install-btn');
    const dismissBtn = banner.querySelector('.dismiss');

    if (installBtn) {
      installBtn.addEventListener('click', async () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        deferredPrompt = null;
        banner.style.display = 'none';
      });
    }

    if (dismissBtn) {
      dismissBtn.addEventListener('click', () => {
        banner.style.display = 'none';
      });
    }
  }

  // ── SERVICE WORKER REGISTRATION ────────────────────────────
  function initServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' })
        .then(reg => {
          reg.update();
          console.log('SW registered:', reg.scope);
        })
        .catch(err => console.warn('SW registration failed:', err));
    }
  }

  // ══════════════════════════════════════════════════════════
  // EXPANSION SLOTS
  // ══════════════════════════════════════════════════════════

  function initGreekPopups() { console.log('[SLOT 1] Greek popups: ready to wire'); }
  function initCrossReferences() { console.log('[SLOT 2] Cross-references: ready to wire'); }
  function initFullTextSearch() { console.log('[SLOT 3] Full-text search: ready to wire'); }
  function initUserNotes() { console.log('[SLOT 4] User notes: ready to wire'); }
  function initThemeToggle() { console.log('[SLOT 5] Theme toggle: ready to wire'); }
  function initAIFeatures() { console.log('[SLOT 6] AI features: ready to wire'); }

  // ── BOOT ──────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    initSiteNav();
    initMobileMenu();
    initSectionObserver();
    initScrollTop();
    initProgressBar();
    initInstallBanner();
    initServiceWorker();

    initGreekPopups();
    initCrossReferences();
    initFullTextSearch();
    initUserNotes();
    initThemeToggle();
    initAIFeatures();
  });

})();
