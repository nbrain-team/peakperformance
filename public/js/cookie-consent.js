(function () {
  'use strict';

  var STORAGE_KEY = 'ppp_cookie_consent';
  var CONSENT_VERSION = 1;
  var MAX_AGE_MS = 13 * 30 * 24 * 60 * 60 * 1000; // ~13 months

  var EU_TIMEZONES = [
    'Europe/Amsterdam', 'Europe/Andorra', 'Europe/Athens', 'Europe/Belgrade',
    'Europe/Berlin', 'Europe/Bratislava', 'Europe/Brussels', 'Europe/Bucharest',
    'Europe/Budapest', 'Europe/Busingen', 'Europe/Chisinau', 'Europe/Copenhagen',
    'Europe/Dublin', 'Europe/Gibraltar', 'Europe/Guernsey', 'Europe/Helsinki',
    'Europe/Isle_of_Man', 'Europe/Jersey', 'Europe/Kiev', 'Europe/Kyiv',
    'Europe/Lisbon', 'Europe/Ljubljana', 'Europe/London', 'Europe/Luxembourg',
    'Europe/Madrid', 'Europe/Malta', 'Europe/Mariehamn', 'Europe/Monaco',
    'Europe/Oslo', 'Europe/Paris', 'Europe/Podgorica', 'Europe/Prague',
    'Europe/Riga', 'Europe/Rome', 'Europe/San_Marino', 'Europe/Sarajevo',
    'Europe/Skopje', 'Europe/Sofia', 'Europe/Stockholm', 'Europe/Tallinn',
    'Europe/Tirane', 'Europe/Vaduz', 'Europe/Vatican', 'Europe/Vienna',
    'Europe/Vilnius', 'Europe/Warsaw', 'Europe/Zagreb', 'Europe/Zurich',
    'Atlantic/Canary', 'Atlantic/Faroe', 'Atlantic/Madeira',
    'Arctic/Longyearbyen'
  ];

  function isEU() {
    try {
      var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      return EU_TIMEZONES.indexOf(tz) !== -1;
    } catch (e) {
      return true; // default to showing banner if detection fails
    }
  }

  function getStoredConsent() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var data = JSON.parse(raw);
      if (data.version !== CONSENT_VERSION) return null;
      if (Date.now() - data.timestamp > MAX_AGE_MS) {
        localStorage.removeItem(STORAGE_KEY);
        return null;
      }
      return data;
    } catch (e) {
      return null;
    }
  }

  function saveConsent(analytics, marketing) {
    var payload = {
      version: CONSENT_VERSION,
      timestamp: Date.now(),
      categories: {
        necessary: true,
        analytics: !!analytics,
        marketing: !!marketing
      }
    };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (e) { /* storage full or disabled */ }
    return payload;
  }

  function updateGtagConsent(analytics, marketing) {
    if (typeof gtag !== 'function') return;
    gtag('consent', 'update', {
      analytics_storage: analytics ? 'granted' : 'denied',
      ad_storage: marketing ? 'granted' : 'denied',
      ad_user_data: marketing ? 'granted' : 'denied',
      ad_personalization: marketing ? 'granted' : 'denied'
    });
  }

  var _ccTrap = null;
  var _ccPrevFocus = null;

  function hideBanner() {
    var banner = document.getElementById('cc-banner');
    if (_ccTrap) { _ccTrap.release(); _ccTrap = null; }
    if (_ccPrevFocus && _ccPrevFocus.focus) {
      _ccPrevFocus.focus();
      _ccPrevFocus = null;
    }
    if (banner) {
      banner.classList.remove('cc-banner--visible');
      setTimeout(function () { banner.remove(); }, 400);
    }
  }

  function showPrefs(banner) {
    var prefs = banner.querySelector('.cc-prefs');
    if (prefs) prefs.classList.toggle('cc-prefs--open');
  }

  function renderBanner() {
    var banner = document.createElement('div');
    banner.id = 'cc-banner';
    banner.className = 'cc-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Cookie consent');
    banner.innerHTML =
      '<div class="cc-banner__inner">' +
        '<div class="cc-banner__text">' +
          '<p>We use cookies to understand how visitors interact with this site. ' +
          'Essential cookies are always active. You can accept or reject optional categories below. ' +
          '<a href="/cookie-policy/">Cookie Policy</a></p>' +
        '</div>' +
        '<div class="cc-banner__actions">' +
          '<button class="cc-btn cc-btn--accept" data-cc="accept">Accept All</button>' +
          '<button class="cc-btn cc-btn--reject" data-cc="reject">Reject All</button>' +
          '<button class="cc-btn cc-btn--manage" data-cc="manage">Manage Preferences</button>' +
        '</div>' +
        '<div class="cc-prefs" role="region" aria-label="Cookie preferences">' +
          '<p class="cc-prefs__heading">Cookie Preferences</p>' +
          '<div class="cc-prefs__category">' +
            '<div class="cc-prefs__label">' +
              '<span class="cc-prefs__name">Necessary</span>' +
              '<span class="cc-prefs__desc">Required for the site to function. Always active.</span>' +
            '</div>' +
            '<label class="cc-toggle">' +
              '<input type="checkbox" checked disabled/>' +
              '<span class="cc-toggle__track"></span>' +
            '</label>' +
          '</div>' +
          '<div class="cc-prefs__category">' +
            '<div class="cc-prefs__label">' +
              '<span class="cc-prefs__name">Analytics</span>' +
              '<span class="cc-prefs__desc">Help us understand site usage via Google Analytics.</span>' +
            '</div>' +
            '<label class="cc-toggle">' +
              '<input type="checkbox" id="cc-analytics"/>' +
              '<span class="cc-toggle__track"></span>' +
            '</label>' +
          '</div>' +
          '<div class="cc-prefs__category">' +
            '<div class="cc-prefs__label">' +
              '<span class="cc-prefs__name">Marketing</span>' +
              '<span class="cc-prefs__desc">Enable personalized advertising and remarketing.</span>' +
            '</div>' +
            '<label class="cc-toggle">' +
              '<input type="checkbox" id="cc-marketing"/>' +
              '<span class="cc-toggle__track"></span>' +
            '</label>' +
          '</div>' +
          '<button class="cc-btn cc-btn--accept cc-prefs__save" data-cc="save">Save Preferences</button>' +
        '</div>' +
      '</div>';

    document.body.appendChild(banner);

    _ccPrevFocus = document.activeElement;

    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        banner.classList.add('cc-banner--visible');
        if (typeof window.OWTrapFocus === 'function') {
          _ccTrap = window.OWTrapFocus(banner);
        }
        var firstBtn = banner.querySelector('.cc-btn');
        if (firstBtn) firstBtn.focus();
      });
    });

    banner.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-cc]');
      if (!btn) return;
      var action = btn.getAttribute('data-cc');

      if (action === 'accept') {
        saveConsent(true, true);
        updateGtagConsent(true, true);
        hideBanner();
      } else if (action === 'reject') {
        saveConsent(false, false);
        updateGtagConsent(false, false);
        hideBanner();
      } else if (action === 'manage') {
        showPrefs(banner);
      } else if (action === 'save') {
        var analytics = document.getElementById('cc-analytics').checked;
        var marketing = document.getElementById('cc-marketing').checked;
        saveConsent(analytics, marketing);
        updateGtagConsent(analytics, marketing);
        hideBanner();
      }
    });
  }

  function bindFooterLink() {
    document.addEventListener('click', function (e) {
      var link = e.target.closest('[data-cc-settings]');
      if (!link) return;
      e.preventDefault();
      localStorage.removeItem(STORAGE_KEY);
      if (!document.getElementById('cc-banner')) {
        renderBanner();
      }
    });
  }

  function init() {
    var stored = getStoredConsent();

    if (!isEU()) {
      if (!stored) saveConsent(true, true);
      updateGtagConsent(true, true);
      bindFooterLink();
      return;
    }

    if (stored) {
      updateGtagConsent(stored.categories.analytics, stored.categories.marketing);
      bindFooterLink();
      return;
    }

    renderBanner();
    bindFooterLink();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
