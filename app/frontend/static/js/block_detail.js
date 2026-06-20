document.addEventListener('DOMContentLoaded', function() {
    const I18N = window.__I18N || {};
    const tr = (key, fallback) => I18N[key] || fallback || key;
    let lastCheckedIndex = null;
    const checkboxes = Array.from(document.querySelectorAll('.segment-selector'));
    const actionBar = document.getElementById('sticky-action-bar');
    const selectedCountSpan = document.getElementById('selected-count');
    const selectedRangeSpan = document.getElementById('selected-range');
    const createPointBtn = document.getElementById('create-point-btn');
    const clearBtn = document.getElementById('clear-selection-btn');

    const pointStartIdInput = document.getElementById('pointStartId');
    const pointEndIdInput = document.getElementById('pointEndId');
    const pointSelectionInfo = document.getElementById('pointSelectionInfo');

    const typeRadios = document.querySelectorAll('input[name="pe_type"]');
    const envFields = document.getElementById('env-fields');
    const actFields = document.getElementById('act-fields');

    // populate checkbox data-time using user's timezone
    checkboxes.forEach(cb => {
        const ts = parseInt(cb.dataset.ts, 10);
        if (!ts || ts <= 0) return;
        const date = new Date(ts * 1000);
        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        cb.dataset.time = timeStr;
    });

    checkboxes.forEach((checkbox, index) => {
        checkbox.addEventListener('click', function(e) {
            handleCheck(e, index);
            updateUI();
        });
    });

    typeRadios.forEach(r => r.addEventListener('change', toggleTypeFields));

    function toggleTypeFields() {
        const selected = document.querySelector('input[name="pe_type"]:checked');
        const val = selected ? selected.value : '';
        if (val === 'env_fluctuation') {
            envFields.style.display = '';
            actFields.style.display = 'none';
        } else if (val === 'personal_action') {
            envFields.style.display = 'none';
            actFields.style.display = '';
        } else {
            envFields.style.display = 'none';
            actFields.style.display = 'none';
        }
    }

    function handleCheck(e, currentIndex) {
        if (e.shiftKey && lastCheckedIndex !== null) {
            const start = Math.min(lastCheckedIndex, currentIndex);
            const end = Math.max(lastCheckedIndex, currentIndex);
            for (let i = start; i <= end; i++) {
                checkboxes[i].checked = e.target.checked;
            }
        }
        lastCheckedIndex = currentIndex;
    }

    function updateUI() {
        const checkedItems = checkboxes.filter(cb => cb.checked);
        const count = checkedItems.length;

        if (count > 0) {
            actionBar.style.display = 'block';
            setTimeout(() => actionBar.classList.add('show'), 10);
            document.querySelectorAll('.segment-row').forEach(row => row.classList.remove('selected'));
            checkedItems.forEach(cb => cb.closest('.segment-row').classList.add('selected'));
        } else {
            actionBar.classList.remove('show');
            setTimeout(() => actionBar.style.display = 'none', 300);
            document.querySelectorAll('.segment-row').forEach(row => row.classList.remove('selected'));
            createPointBtn.disabled = true;
            pointSelectionInfo.textContent = tr('js.choose_point_segments', 'Select continuous segments before creating point annotation');
            pointSelectionInfo.className = 'alert alert-info py-2';
            selectedCountSpan.textContent = '0';
            selectedRangeSpan.textContent = tr('js.start_end_time', 'Time range');
            return;
        }

        const checkedIndices = checkboxes
            .map((cb, idx) => cb.checked ? idx : -1)
            .filter(idx => idx !== -1);

        const isContinuous = checkContinuity(checkedIndices);
        const first = checkboxes[checkedIndices[0]];
        const last = checkboxes[checkedIndices[checkedIndices.length - 1]];

        selectedCountSpan.textContent = count;
        selectedRangeSpan.textContent = `${first.dataset.time} - ${last.dataset.time}`;

        if (isContinuous) {
            createPointBtn.disabled = false;
            pointStartIdInput.value = first.dataset.id;
            pointEndIdInput.value = last.dataset.id;
            pointSelectionInfo.textContent = tr('js.selected_contiguous', 'Selected {count} continuous segments (start at {time})')
                .replace('{count}', count)
                .replace('{time}', first.dataset.time);
            pointSelectionInfo.className = 'alert alert-info py-2';
        } else {
            createPointBtn.disabled = true;
            pointSelectionInfo.textContent = tr('js.must_contiguous', 'Error: selected segments must be continuous');
            pointSelectionInfo.className = 'alert alert-danger py-2';
        }
    }

    function checkContinuity(indices) {
        if (indices.length <= 1) return true;
        for (let i = 0; i < indices.length - 1; i++) {
            if (indices[i + 1] !== indices[i] + 1) return false;
        }
        return true;
    }

    clearBtn.addEventListener('click', function() {
        checkboxes.forEach(cb => cb.checked = false);
        updateUI();
    });

    // Init
    actionBar.style.display = 'none';
    toggleTypeFields();
});
