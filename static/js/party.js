/**
 * PocketSmart AI - Party Planner Client Script
 */

document.addEventListener('DOMContentLoaded', () => {
  const budgetInput = document.getElementById('budget');
  const guestsInput = document.getElementById('num_guests');
  const perGuestDisplay = document.getElementById('per-guest-preview');

  function calculatePerGuest() {
    if (!budgetInput || !guestsInput || !perGuestDisplay) return;
    const budget = parseFloat(budgetInput.value) || 0;
    const guests = parseInt(guestsInput.value, 10) || 1;
    const foodEst = budget * 0.45; // 45% catering rule
    const perHead = Math.round(foodEst / Math.max(1, guests));
    perGuestDisplay.textContent = formatINR(perHead) + ' / person catering estimate';
  }

  if (budgetInput && guestsInput) {
    budgetInput.addEventListener('input', calculatePerGuest);
    guestsInput.addEventListener('input', calculatePerGuest);
    calculatePerGuest();
  }
});
