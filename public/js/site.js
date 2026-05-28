/* ============================================================
   site.js — WCAG 2.1 AA accessibility layer
   Peak Property Performance®
   Loaded defer before cookie-consent.js on every page.
   ============================================================ */
(function () {
  'use strict';

  /* ---- Phase 1: Skip-to-main-content link ---- */
  function injectSkipLink() {
    var nav = document.querySelector('nav');
    if (!nav) return;
    var main = document.querySelector('main');
    if (main) main.id = 'main-content';

    var skip = document.createElement('a');
    skip.className = 'ow-skip-link';
    skip.href = '#main-content';
    skip.textContent = 'Skip to main content';
    nav.parentNode.insertBefore(skip, nav);
  }

  /* ---- Phase 2: Navigation ARIA ---- */
  function enhanceNav() {
    var nav = document.querySelector('nav.nav');
    if (!nav) return;
    nav.setAttribute('aria-label', 'Main navigation');

    var triggers = nav.querySelectorAll('.nav__dropdown-trigger');
    triggers.forEach(function (trigger) {
      if (!trigger.hasAttribute('aria-expanded')) {
        trigger.setAttribute('aria-expanded', 'false');
      }

      var dropdown = trigger.closest('.nav__dropdown');
      if (!dropdown) return;
      var menu = dropdown.querySelector('.nav__dropdown-menu');
      if (!menu) return;

      menu.setAttribute('role', 'menu');
      var items = menu.querySelectorAll('a.nav__link');
      items.forEach(function (item) {
        item.setAttribute('role', 'menuitem');
      });

      function open() {
        trigger.setAttribute('aria-expanded', 'true');
        dropdown.classList.add('nav__dropdown--open');
      }
      function close() {
        trigger.setAttribute('aria-expanded', 'false');
        dropdown.classList.remove('nav__dropdown--open');
      }
      function isOpen() {
        return trigger.getAttribute('aria-expanded') === 'true';
      }

      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        if (isOpen()) { close(); } else { open(); }
      });
      trigger.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          if (isOpen()) { close(); } else { open(); items[0] && items[0].focus(); }
        }
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          open();
          items[0] && items[0].focus();
        }
        if (e.key === 'Escape') {
          close();
          trigger.focus();
        }
      });

      items.forEach(function (item, idx) {
        item.addEventListener('keydown', function (e) {
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            var next = items[idx + 1] || items[0];
            next.focus();
          }
          if (e.key === 'ArrowUp') {
            e.preventDefault();
            var prev = items[idx - 1] || items[items.length - 1];
            prev.focus();
          }
          if (e.key === 'Escape') {
            e.preventDefault();
            close();
            trigger.focus();
          }
        });
      });

      dropdown.addEventListener('focusout', function (e) {
        requestAnimationFrame(function () {
          if (!dropdown.contains(document.activeElement)) close();
        });
      });
    });
  }

  /* ---- Phase 3: Reusable focus trap ---- */
  function trapFocus(container) {
    var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),' +
      'select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
    var first, last;

    function update() {
      var els = container.querySelectorAll(FOCUSABLE);
      var visible = [];
      els.forEach(function (el) {
        if (el.offsetParent !== null || el.offsetWidth > 0 || el.offsetHeight > 0) {
          visible.push(el);
        }
      });
      first = visible[0];
      last = visible[visible.length - 1];
    }

    function handler(e) {
      if (e.key !== 'Tab') return;
      update();
      if (!first) return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    update();
    container.addEventListener('keydown', handler);

    return {
      release: function () {
        container.removeEventListener('keydown', handler);
      },
      update: update
    };
  }
  window.OWTrapFocus = trapFocus;

  /* ---- Phase 5: HTML structure — footer ARIA, heading audit ---- */
  function enhanceStructure() {
    var footer = document.querySelector('footer.footer');
    if (footer) {
      footer.setAttribute('aria-label', 'Site footer');
    }

    var main = document.querySelector('main');
    if (main) {
      main.setAttribute('role', 'main');
    }

    var imgs = document.querySelectorAll('img:not([alt])');
    imgs.forEach(function (img) {
      img.setAttribute('alt', '');
    });

    var emptyLinks = document.querySelectorAll('a:not([aria-label])');
    emptyLinks.forEach(function (a) {
      if (!a.textContent.trim() && !a.querySelector('img[alt]') && !a.getAttribute('aria-label')) {
        var img = a.querySelector('img');
        if (img && img.alt) {
          a.setAttribute('aria-label', img.alt);
        } else if (!a.textContent.trim()) {
          a.setAttribute('aria-label', 'Link');
        }
      }
    });
  }

  /* ---- Init ---- */
  function init() {
    injectSkipLink();
    enhanceNav();
    enhanceStructure();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
