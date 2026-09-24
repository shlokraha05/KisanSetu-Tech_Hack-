// KisanSetu Core JavaScript Utilities

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alerts after 6 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.auto-dismiss-alert');
        alerts.forEach(alert => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        });
    }, 6000);
});

// Print Token Slip function
function printToken() {
    window.print();
}

// Interactive Slot Fetcher for Booking Pages
function setupSlotFetcher(centreSelectId, dateInputId, slotSelectId, capacityInfoId) {
    const centreSelect = document.getElementById(centreSelectId);
    const dateInput = document.getElementById(dateInputId);
    const slotSelect = document.getElementById(slotSelectId);
    const capacityInfo = document.getElementById(capacityInfoId);

    if (!centreSelect || !dateInput || !slotSelect) return;

    async function loadSlots() {
        const centreId = centreSelect.value;
        const date = dateInput.value;

        if (!centreId || !date) {
            slotSelect.innerHTML = '<option value="">-- First Select Centre and Date --</option>';
            slotSelect.disabled = true;
            if (capacityInfo) capacityInfo.innerHTML = '';
            return;
        }

        slotSelect.innerHTML = '<option value="">Loading available slots... / स्लॉट लोड हो रहे हैं...</option>';
        slotSelect.disabled = true;

        try {
            const resp = await fetch(`/farmer/api/slots?centre_id=${centreId}&date=${date}`);
            const data = await resp.json();

            if (!data || data.length === 0) {
                slotSelect.innerHTML = '<option value="">No slots configured for this date / कोई स्लॉट उपलब्ध नहीं है</option>';
                slotSelect.disabled = true;
                if (capacityInfo) {
                    capacityInfo.innerHTML = '<p class="text-amber-700 text-sm">No slots found. Please select another date or contact the procurement centre.</p>';
                }
                return;
            }

            let optionsHtml = '<option value="">-- Choose a Time Slot / समय स्लॉट चुनें --</option>';
            let availableCount = 0;

            data.forEach(s => {
                if (s.is_available) {
                    availableCount++;
                    optionsHtml += `<option value="${s.id}" data-cap="${s.capacity}" data-booked="${s.booked_count}" data-rem="${s.remaining}">
                        ${s.time_range} (${s.remaining} slots remaining / शेष)
                    </option>`;
                } else {
                    optionsHtml += `<option value="${s.id}" disabled class="text-gray-400">
                        ${s.time_range} [FULL / पूर्ण]
                    </option>`;
                }
            });

            slotSelect.innerHTML = optionsHtml;
            slotSelect.disabled = false;

            if (capacityInfo) {
                capacityInfo.innerHTML = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${availableCount > 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                    ${availableCount} slot windows available on this date
                </span>`;
            }

        } catch (err) {
            console.error('Failed to load slots', err);
            slotSelect.innerHTML = '<option value="">Error loading slots</option>';
            slotSelect.disabled = true;
        }
    }

    centreSelect.addEventListener('change', loadSlots);
    dateInput.addEventListener('change', loadSlots);
}
