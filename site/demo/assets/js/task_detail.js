document.addEventListener('DOMContentLoaded', function() {
    const I18N = window.__I18N || {};
    const tr = (key, fallback) => I18N[key] || fallback || key;
    let lastCheckedIndex = null;
    const checkboxes = Array.from(document.querySelectorAll('.segment-selector'));
    const hourSelectors = Array.from(document.querySelectorAll('.hour-selector'));
    const quarterSelectors = Array.from(document.querySelectorAll('.quarter-selector'));
    const actionBar = document.getElementById('sticky-action-bar');
    const selectedCountSpan = document.getElementById('selected-count');
    const selectedRangeSpan = document.getElementById('selected-range');
    const createBlockBtn = document.getElementById('create-block-btn');
    const filterButtons = document.querySelectorAll('[data-filter]');
    
    // Modal inputs
    const blockStartIdInput = document.getElementById('blockStartId');
    const blockEndIdInput = document.getElementById('blockEndId');
    const blockSelectionInfo = document.getElementById('blockSelectionInfo');
    const expandAllBtn = document.getElementById('expand-all');
    const collapseAllBtn = document.getElementById('collapse-all');

    // Populate checkbox data-time using user's local timezone
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

    hourSelectors.forEach(selector => {
        selector.addEventListener('change', function(e) {
            toggleGroupByHour(e.target);
            updateUI();
        });
    });

    quarterSelectors.forEach(selector => {
        selector.addEventListener('change', function(e) {
            toggleGroupByQuarter(e.target);
            updateUI();
        });
    });

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            applyFilter(btn.dataset.filter);
        });
    });

    if (expandAllBtn && collapseAllBtn) {
        expandAllBtn.addEventListener('click', () => toggleAllCollapses(true));
        collapseAllBtn.addEventListener('click', () => toggleAllCollapses(false));
    }

    document.querySelectorAll('.asr-toggle-icon').forEach(btn => {
        btn.addEventListener('click', function() {
            const box = btn.closest('.asr-preview-box');
            if (!box) return;
            const textEl = box.querySelector('.asr-preview-text');
            if (!textEl) return;

            const expanded = btn.dataset.expanded === 'true';
            if (expanded) {
                textEl.classList.add('asr-collapsed');
                box.classList.remove('asr-is-expanded');
                box.classList.add('asr-is-collapsed');
                btn.dataset.expanded = 'false';
                btn.setAttribute('aria-expanded', 'false');
                btn.setAttribute('aria-label', tr('detail.expand_asr', 'Expand ASR text'));
                btn.innerHTML = '&#9654;';
                return;
            }

            textEl.classList.remove('asr-collapsed');
            box.classList.remove('asr-is-collapsed');
            box.classList.add('asr-is-expanded');
            btn.dataset.expanded = 'true';
            btn.setAttribute('aria-expanded', 'true');
            btn.setAttribute('aria-label', tr('detail.collapse_asr', 'Collapse ASR text'));
            btn.innerHTML = '&#9660;';
        });
    });

    function handleCheck(e, currentIndex) {
        if (e.shiftKey && lastCheckedIndex !== null) {
            const start = Math.min(lastCheckedIndex, currentIndex);
            const end = Math.max(lastCheckedIndex, currentIndex);
            
            for (let i = start; i <= end; i++) {
                if (!checkboxes[i].disabled) {
                    checkboxes[i].checked = e.target.checked;
                }
            }
        }
        lastCheckedIndex = currentIndex;
    }

    function toggleGroupByHour(hourCheckbox) {
        const hour = hourCheckbox.dataset.hour;
        checkboxes.forEach(cb => {
            if (cb.dataset.hour === hour && !cb.disabled) {
                cb.checked = hourCheckbox.checked;
            }
        });
        // Sync quarter selectors within this hour
        quarterSelectors.forEach(qc => {
            if (qc.dataset.hour === hour) {
                qc.checked = hourCheckbox.checked;
            }
        });
    }

    function toggleGroupByQuarter(quarterCheckbox) {
        const hour = quarterCheckbox.dataset.hour;
        const quarter = quarterCheckbox.dataset.quarter;
        checkboxes.forEach(cb => {
            if (cb.dataset.hour === hour && cb.dataset.quarter === quarter && !cb.disabled) {
                cb.checked = quarterCheckbox.checked;
            }
        });
        // If any quarter unchecked, uncheck hour header
        if (!quarterCheckbox.checked) {
            hourSelectors.forEach(hc => {
                if (hc.dataset.hour === hour) hc.checked = false;
            });
        }
    }

    function updateUI() {
        // Collect checked items
        const checkedItems = checkboxes.filter(cb => cb.checked);
        const count = checkedItems.length;

        syncGroupCheckboxes();

        // Toggle Action Bar
        if (count > 0) {
            actionBar.style.display = 'block';
            setTimeout(() => actionBar.classList.add('show'), 10);
            
            // Highlight Rows
            document.querySelectorAll('.segment-row').forEach(row => row.classList.remove('selected'));
            checkedItems.forEach(cb => {
                cb.closest('.segment-row').classList.add('selected');
            });
        } else {
            actionBar.classList.remove('show');
            setTimeout(() => actionBar.style.display = 'none', 300);
            document.querySelectorAll('.segment-row').forEach(row => row.classList.remove('selected'));
        }

        // Validate Continuity & Update Text
        if (count > 0) {
            // Sort by index to ensure time order check
            const checkedIndices = checkboxes
                .map((cb, idx) => cb.checked ? idx : -1)
                .filter(idx => idx !== -1);
            
            const isContinuous = checkContinuity(checkedIndices);
            
            const firstId = checkboxes[checkedIndices[0]].dataset.id;
            const lastId = checkboxes[checkedIndices[checkedIndices.length - 1]].dataset.id;
            const firstTime = checkboxes[checkedIndices[0]].dataset.time;
            const lastTime = checkboxes[checkedIndices[checkedIndices.length - 1]].dataset.time; // This logic needs to imply +1 min essentially

            selectedCountSpan.textContent = count;
            selectedRangeSpan.textContent = `${firstTime} - ...`; // Simplified

            if (isContinuous) {
                createBlockBtn.disabled = false;
                createBlockBtn.textContent = tr('js.create_block', 'Create Block');
                
                // prepare form data
                blockStartIdInput.value = firstId;
                blockEndIdInput.value = lastId;
                blockSelectionInfo.textContent = tr('js.selected_contiguous', 'Selected {count} continuous segments (start at {time})')
                    .replace('{count}', count)
                    .replace('{time}', firstTime);
                blockSelectionInfo.className = "alert alert-info py-2";
            } else {
                createBlockBtn.disabled = true;
                createBlockBtn.textContent = tr('js.non_contiguous', 'Non-contiguous (cannot create)');
                blockSelectionInfo.textContent = tr('js.must_contiguous', 'Error: selected segments must be continuous');
                blockSelectionInfo.className = "alert alert-danger py-2";
            }
        }
    }

    function syncGroupCheckboxes() {
        // quarter level
        quarterSelectors.forEach(qc => {
            const hour = qc.dataset.hour;
            const quarter = qc.dataset.quarter;
            const segs = checkboxes.filter(cb => cb.dataset.hour === hour && cb.dataset.quarter === quarter && !cb.disabled && cb.closest('.segment-row').style.display !== 'none');
            if (segs.length === 0) {
                qc.checked = false;
                return;
            }
            qc.checked = segs.every(cb => cb.checked);
        });

        hourSelectors.forEach(hc => {
            const hour = hc.dataset.hour;
            const segs = checkboxes.filter(cb => cb.dataset.hour === hour && !cb.disabled && cb.closest('.segment-row').style.display !== 'none');
            if (segs.length === 0) {
                hc.checked = false;
                return;
            }
            hc.checked = segs.every(cb => cb.checked);
        });
    }

    function checkContinuity(indices) {
        if (indices.length <= 1) return true;
        for (let i = 0; i < indices.length - 1; i++) {
            if (indices[i+1] !== indices[i] + 1) return false;
        }
        return true;
    }

    function toggleAllCollapses(expand) {
        const hourCollapses = document.querySelectorAll('.hour-collapse');
        const quarterCollapses = document.querySelectorAll('.quarter-collapse');
        hourCollapses.forEach(el => {
            const c = bootstrap.Collapse.getOrCreateInstance(el, {toggle: false});
            expand ? c.show() : c.hide();
        });
        quarterCollapses.forEach(el => {
            const c = bootstrap.Collapse.getOrCreateInstance(el, {toggle: false});
            expand ? c.show() : c.hide();
        });
    }

    function applyFilter(filter) {
        filterButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });

        document.querySelectorAll('.segment-row').forEach(row => {
            const label = row.dataset.labelStatus;
            const show = filter === 'all' || label === 'unlabeled';
            row.style.display = show ? '' : 'none';
        });

        // Clear selections that might be hidden to avoid creating invalid ranges
        checkboxes.forEach(cb => {
            if (cb.closest('.segment-row').style.display === 'none') {
                cb.checked = false;
            }
        });
        updateUI();
    }

    // Clear Selection
    document.getElementById('clear-selection-btn').addEventListener('click', function() {
        checkboxes.forEach(cb => cb.checked = false);
        updateUI();
    });

    // Init state
    actionBar.style.display = 'none';
    applyFilter('all');
});
