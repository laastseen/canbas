(function () {
    const STORAGE_KEY = 'canbas_cookie_consent';
    const banner = document.getElementById('cookie-banner');
    if (!banner) return;

    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    function hideBanner() {
        banner.classList.add('d-none');
        banner.setAttribute('aria-hidden', 'true');
    }

    function showBanner() {
        banner.classList.remove('d-none');
        banner.setAttribute('aria-hidden', 'false');
    }

    function sendConsent(choice) {
        return fetch('/api/cookie-consent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({ choice: choice }),
        }).catch(function () {
            /* сеть недоступна — выбор всё равно сохраняем локально */
        });
    }

    function applyChoice(choice) {
        localStorage.setItem(STORAGE_KEY, choice);
        hideBanner();
        sendConsent(choice);
    }

    if (localStorage.getItem(STORAGE_KEY)) {
        hideBanner();
    } else {
        showBanner();
    }

    banner.querySelector('[data-cookie-choice="necessary"]')?.addEventListener('click', function () {
        applyChoice('necessary');
    });
    banner.querySelector('[data-cookie-choice="all"]')?.addEventListener('click', function () {
        applyChoice('all');
    });
})();
