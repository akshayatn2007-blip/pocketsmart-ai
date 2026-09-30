/**
 * PocketSmart AI - Home Interior Planner Client Script
 */

document.addEventListener('DOMContentLoaded', () => {
  const budgetInput = document.getElementById('budget');
  const budgetPreview = document.getElementById('budget-preview');

  if (budgetInput && budgetPreview) {
    const updatePreview = () => {
      const val = parseFloat(budgetInput.value) || 0;
      budgetPreview.textContent = formatINR(val);
    };
    budgetInput.addEventListener('input', updatePreview);
    updatePreview();
  }

  // Quick preset pills for room types
  document.querySelectorAll('.preset-room-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const roomSelect = document.getElementById('room_type');
      if (roomSelect) {
        roomSelect.value = btn.dataset.room;
      }
    });
  });
});
