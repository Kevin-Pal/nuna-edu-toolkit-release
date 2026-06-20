/* demo.js — makes the static, no-backend demo behave.
   - applies the bundled sample tone to every <audio>
   - renders .local-time elements from data-ts (mirrors the real app's base.html)
   - stubs every form submit / delete so nothing posts or navigates away
   - shows a "not saved" toast
   Loaded on every demo page, alongside the real task_detail.js / block_detail.js. */
(function () {
    function applyAudio() {
        var uri = window.__DEMO_AUDIO;
        if (!uri) return;
        document.querySelectorAll('audio').forEach(function (a) {
            var sources = a.querySelectorAll('source');
            if (sources.length) {
                sources.forEach(function (s) { s.src = uri; });
            } else {
                a.src = uri;
            }
            try { a.load(); } catch (e) { /* noop */ }
        });
    }

    function renderTimes() {
        document.querySelectorAll('.local-time').forEach(function (el) {
            var ts = parseInt(el.getAttribute('data-ts'), 10);
            if (!ts || ts <= 0) {
                el.textContent = el.getAttribute('data-placeholder') || '-';
                return;
            }
            var d = new Date(ts * 1000);
            var fmt = el.getAttribute('data-format') || 'full';
            el.textContent = (fmt === 'time')
                ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
                : d.toLocaleString([], {
                    year: 'numeric', month: '2-digit', day: '2-digit',
                    hour: '2-digit', minute: '2-digit', hour12: false
                });
        });
    }

    var toastTimer = null;
    function toast(msg) {
        var el = document.getElementById('demo-toast');
        if (!el) {
            el = document.createElement('div');
            el.id = 'demo-toast';
            document.body.appendChild(el);
        }
        el.innerHTML = '<i class="bi bi-info-circle me-2"></i>' + msg;
        el.classList.add('show');
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { el.classList.remove('show'); }, 3400);
    }
    window.demoToast = toast;

    function hideModalContaining(node) {
        var modalEl = node.closest('.modal');
        if (modalEl && window.bootstrap) {
            var inst = bootstrap.Modal.getInstance(modalEl) || bootstrap.Modal.getOrCreateInstance(modalEl);
            inst.hide();
        }
    }

    function markSelectedLabeled() {
        var checked = Array.from(document.querySelectorAll('.segment-selector:checked'));
        checked.forEach(function (cb) {
            var row = cb.closest('.segment-row');
            if (!row) return;
            row.classList.add('status-labeled');
            row.setAttribute('data-label-status', 'labeled');
            cb.checked = false;
            cb.disabled = true;
            var asrCol = row.querySelector('.asr-col');
            if (asrCol && !asrCol.querySelector('.demo-block-badge')) {
                var b = document.createElement('div');
                b.className = 'mb-1 demo-block-badge';
                b.innerHTML = '<a href="block.html" class="badge bg-primary text-decoration-none">' +
                    'Block #demo: quiet office &middot; focused working</a> ' +
                    '<span class="badge bg-light text-dark border">mid/high</span>';
                asrCol.appendChild(b);
            }
        });
        var clearBtn = document.getElementById('clear-selection-btn');
        if (clearBtn) clearBtn.click();
    }

    function stubMutations() {
        document.querySelectorAll('form').forEach(function (f) {
            f.addEventListener('submit', function (e) {
                e.preventDefault();
                hideModalContaining(f);
                if (f.id === 'createBlockForm') {
                    markSelectedLabeled();
                    toast('Block annotation created — <strong>not saved</strong> in demo mode.');
                } else if (f.id === 'createPointForm') {
                    toast('Point annotation created — <strong>not saved</strong> in demo mode.');
                } else {
                    toast('Demo mode — action not saved.');
                }
            });
        });
        var del = document.getElementById('delete-button');
        if (del) del.addEventListener('click', function () {
            toast('Delete is disabled in the demo.');
        });
        document.querySelectorAll('[data-demo-noop]').forEach(function (a) {
            a.addEventListener('click', function (e) {
                e.preventDefault();
                toast(a.getAttribute('data-demo-noop') || 'Not available in the demo.');
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        applyAudio();
        renderTimes();
        stubMutations();
    });
})();
