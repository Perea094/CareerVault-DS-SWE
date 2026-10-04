/**
 * Career Vault — Preference Manager Web UI
 * Interactive Weekly Availability Grid & Obsidian Vault Synchronization
 */

// ============================================================================
// Constants & Configuration
// ============================================================================

const DAYS = [
  { id: 'monday', label: 'Mon', fullLabel: 'Monday' },
  { id: 'tuesday', label: 'Tue', fullLabel: 'Tuesday' },
  { id: 'wednesday', label: 'Wed', fullLabel: 'Wednesday' },
  { id: 'thursday', label: 'Thu', fullLabel: 'Thursday' },
  { id: 'friday', label: 'Fri', fullLabel: 'Friday' },
  { id: 'saturday', label: 'Sat', fullLabel: 'Saturday' },
  { id: 'sunday', label: 'Sun', fullLabel: 'Sunday' }
];

// 30-minute time slots spanning 06:00 to 22:00 (32 slots per day, 0.5 hours each)
const TIME_SLOTS = [];
for (let h = 6; h < 22; h++) {
  const hPad = String(h).padStart(2, '0');
  const hNext = String(h + 1).padStart(2, '0');
  TIME_SLOTS.push({
    id: `${hPad}_00`,
    label: `${hPad}:00 - ${hPad}:30`,
    time: `${hPad}:00`,
    hours: 0.5
  });
  TIME_SLOTS.push({
    id: `${hPad}_30`,
    label: `${hPad}:30 - ${hNext}:00`,
    time: `${hPad}:30`,
    hours: 0.5
  });
}

// Pre-seeded domain options
const PRESET_DOMAINS = [
  "GenAI/LLMs",
  "RL",
  "Computer Vision",
  "NLP",
  "MLOps",
  "Research",
  "Applied ML",
  "Quant/Trading",
  "Data Engineering",
  "Distributed Systems"
];

// Pre-seeded avoided industries
const PRESET_AVOID = [
  "Crypto",
  "Web3",
  "Gambling",
  "Defense / Military",
  "Tobacco / Weapons"
];

// Pre-seeded target skills
const PRESET_SKILLS = [
  "Cloud ML",
  "LLM fine-tuning",
  "Triton",
  "CUDA / Kernel Dev",
  "Distributed Training",
  "vLLM / TensorRT-LLM"
];

// ============================================================================
// Security & Formatting Utilities
// ============================================================================

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function isValidUrl(url) {
  if (!url || typeof url !== 'string') return false;
  const trimmed = url.trim().toLowerCase();
  return trimmed.startsWith('http://') || trimmed.startsWith('https://');
}

function normalizeWorkAuth(authStr) {
  if (!authStr) return 'None';
  const s = String(authStr).trim().toLowerCase();
  if (s.includes('citizen') || s.includes('green card') || s.includes('permanent resident') || s === 'pr') {
    return 'Citizen / Green Card';
  }
  if (s.includes('tn visa') || s.includes('tn-visa') || s.includes('tn status') || s.includes('usmca') || s.includes('nafta') || s === 'tn') {
    return 'TN Visa Eligible';
  }
  if (s.includes('opt') || s.includes('cpt') || s.includes('f-1') || s.includes('f1')) {
    return 'OPT/CPT Eligible';
  }
  return 'None';
}

// ============================================================================
// Application State
// ============================================================================

let currentBrush = 'available'; // 'available' | 'classes' | 'busy'
let dragAction = 'available';
let isMouseDown = false;
let auditData = null;
let currentAuditTab = 'matches';

let state = {
  version: "1.1",
  updated: new Date().toISOString().slice(0, 10),
  status: "active",
  candidate: {
    name: "Candidate",
    university: "University",
    degree: "B.S. in Computer Science / Data Science",
    current_semester: "Junior",
    expected_graduation: "May 2027",
    email_contact: "candidate@example.com"
  },
  metadata: {
    created: "2026-10-02",
    updated: new Date().toISOString().slice(0, 10),
    type: "preferences",
    tags: ["background", "preferences", "constraints"],
    status: "active",
    version: "1.1",
    source: "Career Vault Onboarding / Preference Manager",
    privacy: "Configure with your personal preferences"
  },
  academic_context: {
    university: "University",
    program: "B.S. in Computer Science / Data Science",
    term: "Junior",
    expected_graduation: "May 2027",
    class_schedule_status: "Coursework in progress",
    focus_areas: ["Machine Learning", "Software Engineering", "Data Systems"]
  },
  availability_calendar: {
    time_slots: TIME_SLOTS,
    weekly_grid: {},
    target_weekly_hours_min: 20,
    target_weekly_hours_max: 30,
    max_manageable_hours: 40,
    schedule_notes: "Available weekday afternoons and evenings."
  },
  work_arrangement: {
    preference_rank: ["Remote", "Hybrid", "Onsite"],
    hours_per_week: "20-30 (40 manageable but not preferred)",
    hours_flexibility: true,
    timezone_overlap: "Flexible; prefers morning availability for classes",
    communication_style: "Both async and sync acceptable",
    scheduling_constraints: "Morning classes likely; schedule TBD"
  },
  location_visa: {
    current_location: "City, Country",
    us_work_authorization: "None",
    relocation_willingness: "Remote preferred; open to international relocation if visa sponsored",
    travel_willingness: true
  },
  compensation_benefits: {
    minimum_hourly: 20,
    equity_importance: "Don't care",
    benefits_priorities: [
      "PTO",
      "Health insurance",
      "Learning budget",
      "Hardware stipend",
      "401k"
    ],
    negotiation_flexibility: "Flexible"
  },
  industry_domain: {
    target_industries: ["Any (no strong preference)"],
    domains_of_interest: [
      "GenAI/LLMs",
      "RL",
      "Computer Vision",
      "NLP",
      "MLOps",
      "Research",
      "Applied ML"
    ],
    industries_to_avoid: ["Crypto"]
  },
  learning_growth: {
    mentorship: "Nice to have",
    tech_depth_vs_breadth: "No preference",
    conference_training_budget_expectation: "None",
    career_trajectory: "Open",
    skills_to_develop: ["Cloud ML", "LLM fine-tuning"]
  },
  deal_breakers: {
    hard_constraints: [
      "No onsite 5 days/week",
      "No unpaid overtime culture",
      "Must sponsor visa for relocation"
    ],
    toxic_signals: [
      "Vague equity promises",
      "Hero culture"
    ],
    automatic_disqualifiers: [
      "Full-time only (no part-time/internship)",
      "Onsite required",
      "No remote option"
    ]
  },
  role_responsibilities: {
    ic_vs_lead: "IC preferred (not ready for lead)",
    research_vs_engineering: "No preference",
    team_size: "No preference"
  }
};

function initDefaultGrid() {
  const grid = {};
  const classSlots = [];
  for (let h = 8; h < 12; h++) {
    const hp = String(h).padStart(2, '0');
    classSlots.push(`${hp}_00`, `${hp}_30`);
  }
  const workSlots = [];
  for (let h = 14; h < 20; h++) {
    const hp = String(h).padStart(2, '0');
    workSlots.push(`${hp}_00`, `${hp}_30`);
  }

  DAYS.forEach(day => {
    grid[day.id] = {};
    TIME_SLOTS.forEach(slot => {
      if (['monday', 'tuesday', 'wednesday', 'thursday'].includes(day.id) && classSlots.includes(slot.id)) {
        grid[day.id][slot.id] = 'classes';
      } else if (['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].includes(day.id) && workSlots.includes(slot.id)) {
        grid[day.id][slot.id] = 'available';
      } else {
        grid[day.id][slot.id] = 'busy';
      }
    });
  });
  return grid;
}

// ============================================================================
// UI Initialization & Event Listeners
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Global mouse and touch handlers for drag-painting
  window.addEventListener('mouseup', () => { isMouseDown = false; });
  window.addEventListener('touchend', () => { isMouseDown = false; });
  window.addEventListener('touchcancel', () => { isMouseDown = false; });

  // Mobile touchmove drag painting support via elementFromPoint
  const calendarWrapper = document.getElementById('calendar-wrapper');
  if (calendarWrapper) {
    calendarWrapper.addEventListener('touchmove', (e) => {
      if (!isMouseDown) return;
      const touch = e.touches[0];
      if (!touch) return;
      const target = document.elementFromPoint(touch.clientX, touch.clientY);
      if (target && target.classList && target.classList.contains('grid-slot-cell')) {
        const dayId = target.dataset.day;
        const slotId = target.dataset.slot;
        if (dayId && slotId) {
          paintSlot(target, dayId, slotId, dragAction);
        }
      }
    }, { passive: true });

    calendarWrapper.addEventListener('mouseleave', () => {
      const bar = document.getElementById('calendar-hover-info');
      if (bar) {
        bar.textContent = "Click and drag across time slots to paint availability (When2meet style)";
      }
    });
  }

  // Brush toolbar buttons
  setupBrushButtons();

  // Presets
  setupPresetButtons();

  // Action Bar Buttons
  const resetBtn = document.getElementById('btn-reset-defaults');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      loadPreferences(true);
    });
  }

  const saveBtn = document.getElementById('btn-save-preferences');
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      savePreferences(true, false);
    });
  }

  const quitBtn = document.getElementById('btn-save-quit');
  if (quitBtn) {
    quitBtn.addEventListener('click', () => {
      saveAndQuit();
    });
  }

  const auditBtn = document.getElementById('btn-save-audit');
  if (auditBtn) {
    auditBtn.addEventListener('click', () => {
      runAudit();
    });
  }

  // Modal handlers
  setupModalHandlers();

  // Add tag inputs handlers
  setupTagInputHandlers();

  // Load preferences from API
  loadPreferences(false);
});

// ============================================================================
// Weekly Availability Grid Rendering & Interactions
// ============================================================================

function formatHourLabel(slotId) {
  const h = parseInt(slotId.slice(0, 2), 10);
  const period = h >= 12 ? 'PM' : 'AM';
  const displayHour = h % 12 === 0 ? 12 : h % 12;
  return `${displayHour}:00 ${period}`;
}

function updateHoverBar(dayName, timeLabel, status) {
  const bar = document.getElementById('calendar-hover-info');
  if (!bar) return;
  let statusBadge = '<span style="color: #cbd5e1; font-weight: 600;">Busy / Personal</span>';
  if (status === 'available') {
    statusBadge = '<span style="color: #2ecc71; font-weight: 600;">Available for Work</span>';
  } else if (status === 'classes') {
    statusBadge = '<span style="color: #3498db; font-weight: 600;">University Classes</span>';
  }
  bar.innerHTML = `<strong>${escapeHtml(dayName)}</strong>, ${escapeHtml(timeLabel)} &nbsp;&bull;&nbsp; Status: ${statusBadge}`;
}

function renderAvailabilityGrid() {
  const container = document.getElementById('availability-grid');
  container.innerHTML = '';

  const grid = state.availability_calendar.weekly_grid || {};

  // Top-left corner header (When2meet style empty cell)
  const cornerHeader = document.createElement('div');
  cornerHeader.className = 'grid-header-cell time-col-header';
  cornerHeader.textContent = '';
  container.appendChild(cornerHeader);

  // Day columns headers
  DAYS.forEach(day => {
    const dayHeader = document.createElement('div');
    dayHeader.className = 'grid-header-cell';
    dayHeader.textContent = day.label;
    container.appendChild(dayHeader);
  });

  // Rows for each time slot
  TIME_SLOTS.forEach(slot => {
    // Time label cell
    const timeCell = document.createElement('div');
    const isHour = slot.id.endsWith('_00');
    timeCell.className = `grid-time-cell ${isHour ? 'hour-start' : 'half-hour'}`;
    timeCell.innerHTML = isHour ? `<span class="time-main">${formatHourLabel(slot.id)}</span>` : '';
    container.appendChild(timeCell);

    // 7 day slot cells
    DAYS.forEach(day => {
      const slotCell = document.createElement('div');
      slotCell.className = `grid-slot-cell ${isHour ? 'hour-start' : 'half-hour'}`;
      slotCell.dataset.day = day.id;
      slotCell.dataset.slot = slot.id;
      slotCell.title = `${day.fullLabel} ${slot.label}`;

      const currentStatus = (grid[day.id] && grid[day.id][slot.id]) ? grid[day.id][slot.id] : 'busy';
      applySlotStyle(slotCell, currentStatus);

      // Mouse drag-and-click events (When2meet style click-to-toggle & drag)
      slotCell.addEventListener('mousedown', (e) => {
        e.preventDefault();
        isMouseDown = true;
        const currentVal = (state.availability_calendar.weekly_grid && state.availability_calendar.weekly_grid[day.id] && state.availability_calendar.weekly_grid[day.id][slot.id]) ? state.availability_calendar.weekly_grid[day.id][slot.id] : 'busy';
        dragAction = (currentVal === currentBrush) ? 'busy' : currentBrush;
        paintSlot(slotCell, day.id, slot.id, dragAction);
        updateHoverBar(day.fullLabel, slot.label, dragAction);
      });

      slotCell.addEventListener('mouseenter', () => {
        if (isMouseDown) {
          paintSlot(slotCell, day.id, slot.id, dragAction);
        }
        const activeVal = (state.availability_calendar.weekly_grid && state.availability_calendar.weekly_grid[day.id] && state.availability_calendar.weekly_grid[day.id][slot.id]) ? state.availability_calendar.weekly_grid[day.id][slot.id] : 'busy';
        updateHoverBar(day.fullLabel, slot.label, isMouseDown ? dragAction : activeVal);
      });

      // Touch events
      slotCell.addEventListener('touchstart', (e) => {
        isMouseDown = true;
        const currentVal = (state.availability_calendar.weekly_grid && state.availability_calendar.weekly_grid[day.id] && state.availability_calendar.weekly_grid[day.id][slot.id]) ? state.availability_calendar.weekly_grid[day.id][slot.id] : 'busy';
        dragAction = (currentVal === currentBrush) ? 'busy' : currentBrush;
        paintSlot(slotCell, day.id, slot.id, dragAction);
        updateHoverBar(day.fullLabel, slot.label, dragAction);
      }, { passive: true });

      container.appendChild(slotCell);
    });
  });

  updateKPICalculations();
}

function applySlotStyle(element, status) {
  element.classList.remove('slot-available', 'slot-classes', 'slot-busy');
  if (status === 'available') {
    element.classList.add('slot-available');
  } else if (status === 'classes') {
    element.classList.add('slot-classes');
  } else {
    element.classList.add('slot-busy');
  }
}

function paintSlot(element, dayId, slotId, action = currentBrush) {
  if (!state.availability_calendar.weekly_grid) {
    state.availability_calendar.weekly_grid = {};
  }
  if (!state.availability_calendar.weekly_grid[dayId]) {
    state.availability_calendar.weekly_grid[dayId] = {};
  }

  state.availability_calendar.weekly_grid[dayId][slotId] = action;
  applySlotStyle(element, action);
  updateKPICalculations();
}

function updateKPICalculations() {
  const grid = state.availability_calendar.weekly_grid || {};
  let totalWorkHours = 0;
  let totalClassHours = 0;

  DAYS.forEach(day => {
    if (grid[day.id]) {
      TIME_SLOTS.forEach(slot => {
        const stat = grid[day.id][slot.id];
        if (stat === 'available') {
          totalWorkHours += slot.hours;
        } else if (stat === 'classes') {
          totalClassHours += slot.hours;
        }
      });
    }
  });

  // Read target thresholds
  const minTarget = parseInt(document.getElementById('target-hours-min').value, 10) || 20;
  const maxTarget = parseInt(document.getElementById('target-hours-max').value, 10) || 30;
  const maxManageable = parseInt(document.getElementById('max-manageable-hours').value, 10) || 40;

  state.availability_calendar.target_weekly_hours_min = minTarget;
  state.availability_calendar.target_weekly_hours_max = maxTarget;
  state.availability_calendar.max_manageable_hours = maxManageable;

  // Update DOM values
  document.getElementById('kpi-work-hours').innerHTML = `${totalWorkHours} <span class="unit">hrs/wk</span>`;
  document.getElementById('kpi-class-hours').innerHTML = `${totalClassHours} <span class="unit">hrs/wk</span>`;

  // Status Badge Evaluation
  const statusBadge = document.getElementById('kpi-status-badge');
  statusBadge.className = 'kpi-chip';

  if (totalWorkHours >= minTarget && totalWorkHours <= maxTarget) {
    statusBadge.textContent = `Optimal (${minTarget}-${maxTarget}h)`;
    statusBadge.classList.add('optimal');
  } else if (totalWorkHours < minTarget) {
    statusBadge.textContent = `Under Target (<${minTarget}h)`;
    statusBadge.classList.add('under');
  } else if (totalWorkHours > maxManageable) {
    statusBadge.textContent = `Warning (>${maxManageable}h)`;
    statusBadge.classList.add('warning');
  } else {
    statusBadge.textContent = `Over Target (>${maxTarget}h)`;
    statusBadge.classList.add('over');
  }
}

// Brush selector management
function setupBrushButtons() {
  const buttons = document.querySelectorAll('.brush-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentBrush = btn.dataset.brush;
    });
  });
}

// Preset availability schedules
function setupPresetButtons() {
  document.getElementById('preset-standard').addEventListener('click', () => {
    state.availability_calendar.weekly_grid = initDefaultGrid();
    renderAvailabilityGrid();
    showToast("Standard university week schedule applied!", "info");
  });

  document.getElementById('preset-afternoons').addEventListener('click', () => {
    const grid = {};
    DAYS.forEach(day => {
      grid[day.id] = {};
      TIME_SLOTS.forEach(slot => {
        const hour = parseInt(slot.id.slice(0, 2), 10);
        if (['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].includes(day.id) && hour >= 12 && hour < 20) {
          grid[day.id][slot.id] = 'available';
        } else {
          grid[day.id][slot.id] = 'busy';
        }
      });
    });
    state.availability_calendar.weekly_grid = grid;
    renderAvailabilityGrid();
    showToast("All weekday afternoons (12:00-20:00) set to available!", "info");
  });

  document.getElementById('preset-clear').addEventListener('click', () => {
    const grid = {};
    DAYS.forEach(day => {
      grid[day.id] = {};
      TIME_SLOTS.forEach(slot => {
        grid[day.id][slot.id] = 'busy';
      });
    });
    state.availability_calendar.weekly_grid = grid;
    renderAvailabilityGrid();
    showToast("Calendar cleared. All slots set to busy.", "info");
  });

  // Target inputs reactive listeners
  ['target-hours-min', 'target-hours-max', 'max-manageable-hours'].forEach(id => {
    document.getElementById(id).addEventListener('input', () => {
      updateKPICalculations();
    });
  });
}

// ============================================================================
// Section 2: Work Modality & Priority Ranking
// ============================================================================

function renderModalityRanking() {
  const container = document.getElementById('modality-rank-list');
  container.innerHTML = '';

  const ranks = state.work_arrangement.preference_rank || ["Remote", "Hybrid", "Onsite"];

  ranks.forEach((modality, index) => {
    const item = document.createElement('div');
    item.className = 'rank-item';
    item.innerHTML = `
      <div class="rank-item-info">
        <span class="rank-number">${index + 1}</span>
        <span class="rank-title">${escapeHtml(modality)}</span>
      </div>
      <div class="rank-actions">
        <button type="button" class="btn-icon-tiny btn-rank-up" title="Move Up" ${index === 0 ? 'disabled' : ''}>▲</button>
        <button type="button" class="btn-icon-tiny btn-rank-down" title="Move Down" ${index === ranks.length - 1 ? 'disabled' : ''}>▼</button>
      </div>
    `;

    item.querySelector('.btn-rank-up').addEventListener('click', () => {
      if (index > 0) {
        const temp = ranks[index - 1];
        ranks[index - 1] = ranks[index];
        ranks[index] = temp;
        renderModalityRanking();
      }
    });

    item.querySelector('.btn-rank-down').addEventListener('click', () => {
      if (index < ranks.length - 1) {
        const temp = ranks[index + 1];
        ranks[index + 1] = ranks[index];
        ranks[index] = temp;
        renderModalityRanking();
      }
    });

    container.appendChild(item);
  });
}

// ============================================================================
// Section 3: Compensation & Benefits Tags
// ============================================================================

function renderBenefitsTags() {
  const container = document.getElementById('benefits-tags-container');
  container.innerHTML = '';

  const benefits = state.compensation_benefits.benefits_priorities || [];

  benefits.forEach((benefit, index) => {
    const pill = document.createElement('div');
    pill.className = 'tag-pill active emerald';
    pill.innerHTML = `
      <span>${index + 1}. ${escapeHtml(benefit)}</span>
      <span class="remove-tag" title="Remove">&times;</span>
    `;

    pill.querySelector('.remove-tag').addEventListener('click', (e) => {
      e.stopPropagation();
      state.compensation_benefits.benefits_priorities.splice(index, 1);
      renderBenefitsTags();
    });

    container.appendChild(pill);
  });
}

// ============================================================================
// Section 4: Technical Focus & Domain Tag Pills
// ============================================================================

function renderDomainPills() {
  const container = document.getElementById('domains-tags-container');
  container.innerHTML = '';

  const activeDomains = new Set(state.industry_domain.domains_of_interest || []);
  const allDomains = Array.from(new Set([...PRESET_DOMAINS, ...activeDomains]));

  allDomains.forEach(domain => {
    const isActive = activeDomains.has(domain);
    const pill = document.createElement('div');
    pill.className = `tag-pill ${isActive ? 'active' : ''}`;
    pill.innerHTML = `
      <span>${escapeHtml(domain)}</span>
      <span class="remove-tag" title="Delete tag">&times;</span>
    `;

    // Toggle active state
    pill.addEventListener('click', (e) => {
      if (e.target.classList.contains('remove-tag')) return;
      if (activeDomains.has(domain)) {
        activeDomains.delete(domain);
      } else {
        activeDomains.add(domain);
      }
      state.industry_domain.domains_of_interest = Array.from(activeDomains);
      renderDomainPills();
    });

    // Remove tag permanently
    pill.querySelector('.remove-tag').addEventListener('click', (e) => {
      e.stopPropagation();
      activeDomains.delete(domain);
      state.industry_domain.domains_of_interest = Array.from(activeDomains);
      const presetIdx = PRESET_DOMAINS.indexOf(domain);
      if (presetIdx !== -1) PRESET_DOMAINS.splice(presetIdx, 1);
      renderDomainPills();
    });

    container.appendChild(pill);
  });
}

function renderAvoidPills() {
  const container = document.getElementById('avoid-tags-container');
  container.innerHTML = '';

  const activeAvoid = new Set(state.industry_domain.industries_to_avoid || []);
  const allAvoid = Array.from(new Set([...PRESET_AVOID, ...activeAvoid]));

  allAvoid.forEach(item => {
    const isActive = activeAvoid.has(item);
    const pill = document.createElement('div');
    pill.className = `tag-pill ${isActive ? 'active coral' : ''}`;
    pill.innerHTML = `
      <span>${escapeHtml(item)}</span>
      <span class="remove-tag" title="Delete">&times;</span>
    `;

    pill.addEventListener('click', (e) => {
      if (e.target.classList.contains('remove-tag')) return;
      if (activeAvoid.has(item)) {
        activeAvoid.delete(item);
      } else {
        activeAvoid.add(item);
      }
      state.industry_domain.industries_to_avoid = Array.from(activeAvoid);
      renderAvoidPills();
    });

    pill.querySelector('.remove-tag').addEventListener('click', (e) => {
      e.stopPropagation();
      activeAvoid.delete(item);
      state.industry_domain.industries_to_avoid = Array.from(activeAvoid);
      const idx = PRESET_AVOID.indexOf(item);
      if (idx !== -1) PRESET_AVOID.splice(idx, 1);
      renderAvoidPills();
    });

    container.appendChild(pill);
  });
}

function renderSkillsPills() {
  const container = document.getElementById('skills-tags-container');
  container.innerHTML = '';

  const activeSkills = new Set(state.learning_growth.skills_to_develop || []);
  const allSkills = Array.from(new Set([...PRESET_SKILLS, ...activeSkills]));

  allSkills.forEach(skill => {
    const isActive = activeSkills.has(skill);
    const pill = document.createElement('div');
    pill.className = `tag-pill ${isActive ? 'active emerald' : ''}`;
    pill.innerHTML = `
      <span>${escapeHtml(skill)}</span>
      <span class="remove-tag" title="Delete">&times;</span>
    `;

    pill.addEventListener('click', (e) => {
      if (e.target.classList.contains('remove-tag')) return;
      if (activeSkills.has(skill)) {
        activeSkills.delete(skill);
      } else {
        activeSkills.add(skill);
      }
      state.learning_growth.skills_to_develop = Array.from(activeSkills);
      renderSkillsPills();
    });

    pill.querySelector('.remove-tag').addEventListener('click', (e) => {
      e.stopPropagation();
      activeSkills.delete(skill);
      state.learning_growth.skills_to_develop = Array.from(activeSkills);
      const idx = PRESET_SKILLS.indexOf(skill);
      if (idx !== -1) PRESET_SKILLS.splice(idx, 1);
      renderSkillsPills();
    });

    container.appendChild(pill);
  });
}

// ============================================================================
// Section 6: Hard Dealbreakers & Disqualifiers Lists
// ============================================================================

function renderDealbreakersLists() {
  renderListItems(
    'hard-constraints-list',
    state.deal_breakers.hard_constraints || [],
    (index) => {
      state.deal_breakers.hard_constraints.splice(index, 1);
      renderDealbreakersLists();
    }
  );

  renderListItems(
    'auto-disqualifiers-list',
    state.deal_breakers.automatic_disqualifiers || [],
    (index) => {
      state.deal_breakers.automatic_disqualifiers.splice(index, 1);
      renderDealbreakersLists();
    }
  );

  renderListItems(
    'toxic-signals-list',
    state.deal_breakers.toxic_signals || [],
    (index) => {
      state.deal_breakers.toxic_signals.splice(index, 1);
      renderDealbreakersLists();
    },
    'warning'
  );
}

function renderListItems(containerId, items, onRemove, extraClass = '') {
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  items.forEach((item, index) => {
    const row = document.createElement('div');
    row.className = `dealbreaker-item ${extraClass}`;
    row.innerHTML = `
      <span>${escapeHtml(item)}</span>
      <button type="button" class="remove-item-btn" title="Remove">&times;</button>
    `;

    row.querySelector('.remove-item-btn').addEventListener('click', () => {
      onRemove(index);
    });

    container.appendChild(row);
  });
}

// ============================================================================
// Tag Inputs Handlers
// ============================================================================

function setupTagInputHandlers() {
  // Add Domain
  const addDomainBtn = document.getElementById('add-domain-btn');
  const addDomainInput = document.getElementById('new-domain-input');
  const handleAddDomain = () => {
    const val = addDomainInput.value.trim();
    if (val) {
      if (!state.industry_domain.domains_of_interest) state.industry_domain.domains_of_interest = [];
      if (!state.industry_domain.domains_of_interest.includes(val)) {
        state.industry_domain.domains_of_interest.push(val);
      }
      if (!PRESET_DOMAINS.includes(val)) PRESET_DOMAINS.push(val);
      addDomainInput.value = '';
      renderDomainPills();
    }
  };
  addDomainBtn.addEventListener('click', handleAddDomain);
  addDomainInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleAddDomain(); });

  // Add Avoid Industry
  const addAvoidBtn = document.getElementById('add-avoid-btn');
  const addAvoidInput = document.getElementById('new-avoid-input');
  const handleAddAvoid = () => {
    const val = addAvoidInput.value.trim();
    if (val) {
      if (!state.industry_domain.industries_to_avoid) state.industry_domain.industries_to_avoid = [];
      if (!state.industry_domain.industries_to_avoid.includes(val)) {
        state.industry_domain.industries_to_avoid.push(val);
      }
      if (!PRESET_AVOID.includes(val)) PRESET_AVOID.push(val);
      addAvoidInput.value = '';
      renderAvoidPills();
    }
  };
  addAvoidBtn.addEventListener('click', handleAddAvoid);
  addAvoidInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleAddAvoid(); });

  // Add Skill
  const addSkillBtn = document.getElementById('add-skill-btn');
  const addSkillInput = document.getElementById('new-skill-input');
  const handleAddSkill = () => {
    const val = addSkillInput.value.trim();
    if (val) {
      if (!state.learning_growth.skills_to_develop) state.learning_growth.skills_to_develop = [];
      if (!state.learning_growth.skills_to_develop.includes(val)) {
        state.learning_growth.skills_to_develop.push(val);
      }
      if (!PRESET_SKILLS.includes(val)) PRESET_SKILLS.push(val);
      addSkillInput.value = '';
      renderSkillsPills();
    }
  };
  addSkillBtn.addEventListener('click', handleAddSkill);
  addSkillInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleAddSkill(); });

  // Add Benefit
  const addBenefitBtn = document.getElementById('add-benefit-btn');
  const addBenefitInput = document.getElementById('new-benefit-input');
  const handleAddBenefit = () => {
    const val = addBenefitInput.value.trim();
    if (val) {
      if (!state.compensation_benefits.benefits_priorities) state.compensation_benefits.benefits_priorities = [];
      if (!state.compensation_benefits.benefits_priorities.includes(val)) {
        state.compensation_benefits.benefits_priorities.push(val);
      }
      addBenefitInput.value = '';
      renderBenefitsTags();
    }
  };
  addBenefitBtn.addEventListener('click', handleAddBenefit);
  addBenefitInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleAddBenefit(); });

  // Add Hard Constraint
  const addConstraintBtn = document.getElementById('add-constraint-btn');
  const addConstraintInput = document.getElementById('new-constraint-input');
  const handleAddConstraint = () => {
    const val = addConstraintInput.value.trim();
    if (val) {
      if (!state.deal_breakers.hard_constraints) state.deal_breakers.hard_constraints = [];
      state.deal_breakers.hard_constraints.push(val);
      addConstraintInput.value = '';
      renderDealbreakersLists();
    }
  };
  addConstraintBtn.addEventListener('click', handleAddConstraint);
  addConstraintInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleAddConstraint(); });

  // Add Auto Disqualifier
  const addDisqBtn = document.getElementById('add-disqualifier-btn');
  const addDisqInput = document.getElementById('new-disqualifier-input');
  const handleAddDisq = () => {
    const val = addDisqInput.value.trim();
    if (val) {
      if (!state.deal_breakers.automatic_disqualifiers) state.deal_breakers.automatic_disqualifiers = [];
      state.deal_breakers.automatic_disqualifiers.push(val);
      addDisqInput.value = '';
      renderDealbreakersLists();
    }
  };
  addDisqBtn.addEventListener('click', handleAddDisq);
  addDisqInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleAddDisq(); });

  // Add Toxic Signal
  const addToxicBtn = document.getElementById('add-toxic-btn');
  const addToxicInput = document.getElementById('new-toxic-input');
  const handleAddToxic = () => {
    const val = addToxicInput.value.trim();
    if (val) {
      if (!state.deal_breakers.toxic_signals) state.deal_breakers.toxic_signals = [];
      state.deal_breakers.toxic_signals.push(val);
      addToxicInput.value = '';
      renderDealbreakersLists();
    }
  };
  addToxicBtn.addEventListener('click', handleAddToxic);
  addToxicInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleAddToxic(); });
}

// ============================================================================
// Sync UI with State
// ============================================================================

function updateCandidateHeader() {
  const cand = state.candidate || {};
  const acad = state.academic_context || {};
  const name = cand.name || 'Candidate';
  const school = cand.school || cand.university || acad.university || 'University';

  const badgeEl = document.getElementById('header-candidate-badge');
  const nameEl = document.getElementById('header-candidate-name');
  const schoolEl = document.getElementById('header-candidate-school');

  if (nameEl) nameEl.textContent = name;
  if (schoolEl) schoolEl.textContent = school;

  if (badgeEl && name && name !== 'Candidate') {
    badgeEl.title = `Active Candidate: ${name} (${school})`;
  }

  const titleEl = document.getElementById('header-vault-title');
  if (titleEl && name && name !== 'Candidate') {
    titleEl.textContent = `⚡ Career Vault — ${name}`;
  }
}

function syncFormFieldsFromState() {
  // Last Updated
  const updatedDate = state.updated || (state.metadata && state.metadata.updated) || new Date().toISOString().slice(0, 10);
  document.getElementById('last-updated-display').textContent = `Updated: ${updatedDate}`;

  const cand = state.candidate || {};

  // Availability calendar targets & notes
  const cal = state.availability_calendar || {};
  document.getElementById('target-hours-min').value = cal.target_weekly_hours_min || 20;
  document.getElementById('target-hours-max').value = cal.target_weekly_hours_max || 30;
  document.getElementById('max-manageable-hours').value = cal.max_manageable_hours || 40;
  document.getElementById('schedule-notes-input').value = cal.schedule_notes || '';

  // Work arrangement
  const work = state.work_arrangement || {};
  document.getElementById('hours-flexibility').checked = work.hours_flexibility !== false;
  document.getElementById('communication-style').value = work.communication_style || 'Both async and sync acceptable';
  document.getElementById('timezone-overlap').value = work.timezone_overlap || 'Flexible; prefers morning availability for classes';

  // Location & Visa
  const loc = state.location_visa || {};
  const isDefaultLoc = !loc.current_location || loc.current_location === 'City, Country';
  document.getElementById('current-location').value = (isDefaultLoc && cand.location)
    ? cand.location
    : (loc.current_location || cand.location || 'City, Country');

  const rawWorkAuth = (loc.us_work_authorization && loc.us_work_authorization !== 'None')
    ? loc.us_work_authorization
    : (cand.work_authorization || loc.us_work_authorization || 'None');
  const mappedWorkAuth = normalizeWorkAuth(rawWorkAuth);
  const usAuthSelect = document.getElementById('us-work-auth');
  if (usAuthSelect) {
    usAuthSelect.value = mappedWorkAuth;
  }

  document.getElementById('relocation-willingness').value = loc.relocation_willingness || 'Remote preferred; open to international relocation if visa sponsored';
  document.getElementById('travel-willingness').checked = loc.travel_willingness !== false;

  // Compensation
  const comp = state.compensation_benefits || {};
  document.getElementById('minimum-hourly').value = comp.minimum_hourly || comp.minimum_hourly_usd || 20;
  document.getElementById('equity-importance').value = comp.equity_importance || "Don't care";
  document.getElementById('negotiation-flexibility').value = comp.negotiation_flexibility || "Flexible";

  // Academic Context
  const acad = state.academic_context || {};
  const isDefaultUniv = !acad.university || acad.university === 'University';
  document.getElementById('academic-university').value = (isDefaultUniv && (cand.school || cand.university))
    ? (cand.school || cand.university)
    : (acad.university || cand.school || cand.university || 'University');

  const isDefaultProg = !acad.program || acad.program === 'B.S. in Computer Science / Data Science';
  document.getElementById('academic-degree').value = (isDefaultProg && (acad.degree || cand.degree))
    ? (acad.degree || cand.degree)
    : (acad.program || acad.degree || cand.degree || 'B.S. in Computer Science / Data Science');

  const isDefaultTerm = !acad.term || acad.term === 'Junior';
  document.getElementById('academic-semester').value = (isDefaultTerm && (acad.current_semester || cand.current_semester))
    ? (acad.current_semester || cand.current_semester)
    : (acad.term || acad.current_semester || cand.current_semester || 'Junior');

  const isDefaultGrad = !acad.expected_graduation || acad.expected_graduation === 'May 2027';
  document.getElementById('academic-graduation').value = (isDefaultGrad && (cand.graduation || cand.expected_graduation))
    ? (cand.graduation || cand.expected_graduation)
    : (acad.expected_graduation || cand.graduation || cand.expected_graduation || 'May 2027');

  // Learning & Growth
  const learn = state.learning_growth || {};
  document.getElementById('career-trajectory').value = learn.career_trajectory || 'Open';
  document.getElementById('mentorship-pref').value = learn.mentorship || 'Nice to have';

  // Role Responsibilities
  const role = state.role_responsibilities || {};
  document.getElementById('role-focus-ic').value = role.ic_vs_lead || 'IC preferred (not ready for lead)';

  // Update header candidate display
  updateCandidateHeader();

  // Render dynamic collections
  renderAvailabilityGrid();
  renderModalityRanking();
  renderBenefitsTags();
  renderDomainPills();
  renderAvoidPills();
  renderSkillsPills();
  renderDealbreakersLists();
}

function syncStateFromFormFields() {
  // Calendar
  state.availability_calendar.target_weekly_hours_min = parseInt(document.getElementById('target-hours-min').value, 10) || 20;
  state.availability_calendar.target_weekly_hours_max = parseInt(document.getElementById('target-hours-max').value, 10) || 30;
  state.availability_calendar.max_manageable_hours = parseInt(document.getElementById('max-manageable-hours').value, 10) || 40;
  state.availability_calendar.schedule_notes = document.getElementById('schedule-notes-input').value.trim();

  // Work arrangement
  state.work_arrangement.hours_flexibility = document.getElementById('hours-flexibility').checked;
  state.work_arrangement.communication_style = document.getElementById('communication-style').value.trim();
  state.work_arrangement.timezone_overlap = document.getElementById('timezone-overlap').value.trim();
  state.work_arrangement.hours_per_week = `${state.availability_calendar.target_weekly_hours_min}-${state.availability_calendar.target_weekly_hours_max} (${state.availability_calendar.max_manageable_hours} manageable but not preferred)`;

  // Location & Visa
  state.location_visa.current_location = document.getElementById('current-location').value.trim();
  state.location_visa.us_work_authorization = normalizeWorkAuth(document.getElementById('us-work-auth').value);
  state.location_visa.relocation_willingness = document.getElementById('relocation-willingness').value.trim();
  state.location_visa.travel_willingness = document.getElementById('travel-willingness').checked;

  // Compensation
  state.compensation_benefits.minimum_hourly = parseFloat(document.getElementById('minimum-hourly').value) || 20;
  state.compensation_benefits.minimum_hourly_usd = state.compensation_benefits.minimum_hourly;
  state.compensation_benefits.equity_importance = document.getElementById('equity-importance').value;
  state.compensation_benefits.negotiation_flexibility = document.getElementById('negotiation-flexibility').value;

  // Academic Context
  state.academic_context.university = document.getElementById('academic-university').value.trim();
  state.academic_context.program = document.getElementById('academic-degree').value.trim();
  state.academic_context.term = document.getElementById('academic-semester').value.trim();
  state.academic_context.expected_graduation = document.getElementById('academic-graduation').value.trim();

  // Learning & Growth
  state.learning_growth.career_trajectory = document.getElementById('career-trajectory').value;
  state.learning_growth.mentorship = document.getElementById('mentorship-pref').value;

  // Role Responsibilities
  state.role_responsibilities.ic_vs_lead = document.getElementById('role-focus-ic').value;

  // Mirror updates to legacy keys if present
  if (state.compensation) {
    state.compensation.minimum_hourly_usd = state.compensation_benefits.minimum_hourly;
  }
  if (state.career_goals) {
    state.career_goals.target_domains = state.industry_domain.domains_of_interest;
    state.career_goals.disallowed_industries = state.industry_domain.industries_to_avoid;
  }
  if (state.modality) {
    state.modality.ranking = (state.work_arrangement.preference_rank || []).map(r => r.toLowerCase());
  }

  // Candidate mirror
  state.candidate = Object.assign({}, state.candidate, {
    name: state.candidate?.name || 'Candidate',
    university: state.academic_context.university,
    school: state.academic_context.university,
    degree: state.academic_context.program,
    current_semester: state.academic_context.term,
    expected_graduation: state.academic_context.expected_graduation,
    location: state.location_visa.current_location,
    work_authorization: state.location_visa.work_authorization || state.candidate?.work_authorization
  });

  const today = new Date().toISOString().slice(0, 10);
  state.updated = today;
  if (!state.metadata) state.metadata = {};
  state.metadata.updated = today;

  updateCandidateHeader();
}

// ============================================================================
// REST API Communication
// ============================================================================

async function loadPreferences(isReset = false) {
  try {
    document.getElementById('save-status-text').innerHTML = `
      <span class="save-status-indicator" style="background-color: var(--sky-blue);"></span>
      <span>Fetching preferences from Obsidian vault...</span>
    `;

    const res = await fetch('/api/preferences');
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const data = await res.json();
    if (data && typeof data === 'object') {
      state = Object.assign({}, state, data);
      if (!state.availability_calendar.weekly_grid || Object.keys(state.availability_calendar.weekly_grid).length === 0) {
        state.availability_calendar.weekly_grid = initDefaultGrid();
      }
      syncFormFieldsFromState();
      document.getElementById('save-status-text').innerHTML = `
        <span class="save-status-indicator" style="background-color: var(--emerald);"></span>
        <span>Vault synchronized</span>
      `;
      if (isReset) {
        showToast("Preferences reset to Obsidian vault defaults!", "success");
      }
    }
  } catch (err) {
    console.error("Error loading preferences:", err);
    document.getElementById('save-status-text').innerHTML = `
      <span class="save-status-indicator" style="background-color: var(--coral);"></span>
      <span>Connection error with vault server</span>
    `;
    showToast(`Error connecting to server: ${err.message}`, "error");
  }
}

async function savePreferences(showNotification = true, andQuit = false) {
  const saveBtn = document.getElementById('btn-save-preferences');
  const quitBtn = document.getElementById('btn-save-quit');
  const origSaveText = saveBtn ? saveBtn.innerHTML : '';
  const origQuitText = quitBtn ? quitBtn.innerHTML : '';

  try {
    syncStateFromFormFields();

    if (andQuit && quitBtn) {
      quitBtn.innerHTML = `<span class="spinner"></span> Saving &amp; Closing...`;
      quitBtn.disabled = true;
      if (saveBtn) saveBtn.disabled = true;
    } else if (saveBtn) {
      saveBtn.innerHTML = `<span class="spinner"></span> Saving...`;
      saveBtn.disabled = true;
    }

    document.getElementById('save-status-text').innerHTML = `
      <span class="save-status-indicator" style="background-color: var(--purple-accent);"></span>
      <span>Writing to 001-background/preferences.md & preferences.json...</span>
    `;

    const payload = Object.assign({}, state);
    if (andQuit) {
      payload.quit = true;
    }

    const res = await fetch('/api/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `HTTP ${res.status}`);
    }

    const data = await res.json();
    document.getElementById('last-updated-display').textContent = `Updated: ${state.updated}`;

    if (andQuit) {
      document.getElementById('save-status-text').innerHTML = `
        <span class="save-status-indicator" style="background-color: var(--emerald);"></span>
        <span>Saved! Server shutting down — return to your terminal to continue setup.</span>
      `;
      showToast("Preferences saved! Server stopped. Return to your terminal to continue setup.", "success", 8000);
      if (saveBtn) saveBtn.disabled = true;
      if (quitBtn) {
        quitBtn.disabled = true;
        quitBtn.innerHTML = `✅ Saved &amp; Closed`;
      }
      // Also notify quit endpoint
      fetch('/api/quit', { method: 'POST' }).catch(() => {});
      setTimeout(() => {
        try { window.close(); } catch (e) {}
      }, 1500);
    } else {
      if (saveBtn) {
        saveBtn.innerHTML = origSaveText;
        saveBtn.disabled = false;
      }
      if (quitBtn) {
        quitBtn.innerHTML = origQuitText;
        quitBtn.disabled = false;
      }
      document.getElementById('save-status-text').innerHTML = `
        <span class="save-status-indicator" style="background-color: var(--emerald);"></span>
        <span>Preferences saved & synced to Obsidian</span>
      `;
      if (showNotification) {
        showToast("Preferences successfully saved & synced to Obsidian vault!", "success");
      }
    }

    return data;
  } catch (err) {
    if (saveBtn) {
      saveBtn.innerHTML = origSaveText;
      saveBtn.disabled = false;
    }
    if (quitBtn) {
      quitBtn.innerHTML = origQuitText;
      quitBtn.disabled = false;
    }
    console.error("Error saving preferences:", err);
    document.getElementById('save-status-text').innerHTML = `
      <span class="save-status-indicator" style="background-color: var(--coral);"></span>
      <span>Failed to save preferences</span>
    `;
    showToast(`Failed to save preferences: ${err.message}`, "error");
    throw err;
  }
}

async function saveAndQuit() {
  return savePreferences(false, true);
}

async function runAudit() {
  const auditBtn = document.getElementById('btn-save-audit');
  const origContent = auditBtn.innerHTML;

  try {
    // Step 1: Save first
    await savePreferences(false);

    // Step 2: Trigger audit
    auditBtn.innerHTML = `<span class="spinner"></span> Auditing 004-work-opportunities...`;
    auditBtn.disabled = true;

    const res = await fetch('/api/audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preferences: state })
    });

    auditBtn.innerHTML = origContent;
    auditBtn.disabled = false;

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `HTTP ${res.status}`);
    }

    const result = await res.json();
    auditData = result.audit;

    // Render audit modal
    renderAuditResults();
    openAuditModal();
    showToast(`Audit complete! ${auditData.summary.direct_matches} direct matches found.`, "success");
  } catch (err) {
    console.error("Error running audit:", err);
    auditBtn.innerHTML = origContent;
    auditBtn.disabled = false;
    showToast(`Opportunity audit failed: ${err.message}`, "error");
  }
}

// ============================================================================
// Modal Management & Audit Tab Rendering
// ============================================================================

function setupModalHandlers() {
  const overlay = document.getElementById('audit-modal-overlay');
  const closeBtn = document.getElementById('modal-close-btn');
  const doneBtn = document.getElementById('modal-done-btn');

  const closeModal = () => {
    overlay.classList.remove('open');
  };

  closeBtn.addEventListener('click', closeModal);
  doneBtn.addEventListener('click', closeModal);

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('open')) {
      closeModal();
    }
  });

  // Tab switching
  ['matches', 'caution', 'disqualified'].forEach(tab => {
    const btn = document.getElementById(`tab-btn-${tab}`);
    btn.addEventListener('click', () => {
      document.querySelectorAll('.audit-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentAuditTab = tab;
      renderAuditTabContent();
    });
  });
}

function openAuditModal() {
  const overlay = document.getElementById('audit-modal-overlay');
  overlay.classList.add('open');
}

function renderAuditResults() {
  if (!auditData) return;

  const s = auditData.summary || {};
  document.getElementById('modal-total-analyzed').textContent = s.total_analyzed || 0;
  document.getElementById('modal-direct-matches').textContent = s.direct_matches || 0;
  document.getElementById('modal-caution-matches').textContent = s.caution || 0;
  document.getElementById('modal-disqualified').textContent = s.disqualified || 0;

  renderAuditTabContent();
}

function renderAuditTabContent() {
  if (!auditData) return;

  const listContainer = document.getElementById('modal-audit-list');
  listContainer.innerHTML = '';

  let items = [];
  if (currentAuditTab === 'matches') {
    items = auditData.matches || [];
  } else if (currentAuditTab === 'caution') {
    items = auditData.caution || [];
  } else {
    items = auditData.disqualified || [];
  }

  if (items.length === 0) {
    listContainer.innerHTML = `
      <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted);">
        No opportunities found in this category.
      </div>
    `;
    return;
  }

  items.forEach(opp => {
    const card = document.createElement('div');
    card.className = 'audit-opportunity-card';

    const company = escapeHtml(opp.company || 'Unknown');
    const role = escapeHtml(opp.role || 'Role');
    const tier = escapeHtml(opp.tier || 'Opportunity');
    const location = escapeHtml(opp.location || 'Location');
    const hours = escapeHtml(opp.hours_per_week || 'Hours');
    const score = escapeHtml(opp.score || 100);

    let extraBadge = '';
    if (currentAuditTab === 'matches') {
      extraBadge = `<span class="audit-opp-tag" style="border-color: var(--emerald); color: var(--emerald);">Match Score: ${score}%</span>`;
    } else if (currentAuditTab === 'caution') {
      const reason = opp.caution_reasons ? opp.caution_reasons.join(', ') : 'Caution: hours or relocation';
      extraBadge = `<div class="audit-opp-caution">⚠️ ${escapeHtml(reason)}</div>`;
    } else {
      const reason = opp.disqualify_reason || 'Deal-breaker triggered';
      extraBadge = `<div class="audit-opp-reason">🛑 ${escapeHtml(reason)}</div>`;
    }

    const applyUrl = (opp.apply_url && isValidUrl(opp.apply_url)) ? escapeHtml(opp.apply_url.trim()) : null;
    const applyBtn = applyUrl ? `
      <a href="${applyUrl}" target="_blank" rel="noopener noreferrer" class="btn-apply-link">
        Apply ↗
      </a>
    ` : '';

    card.innerHTML = `
      <div class="audit-opp-info">
        <h4>${company} — ${role}</h4>
        <div class="audit-opp-meta">
          <span class="audit-opp-tag">${tier}</span>
          <span>📍 ${location}</span>
          <span>⏱ ${hours}</span>
        </div>
        ${extraBadge}
      </div>
      <div>
        ${applyBtn}
      </div>
    `;

    listContainer.appendChild(card);
  });
}

// ============================================================================
// Toast Notification Utility
// ============================================================================

function showToast(message, type = 'info', duration = 3800) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';

  toast.innerHTML = `
    <span>${icon}</span>
    <div style="flex: 1;">${escapeHtml(message)}</div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px) scale(0.95)';
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }, duration);
}
