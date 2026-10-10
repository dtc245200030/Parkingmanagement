/**
 * Tập tin Script JavaScript chính điều khiển giao diện Dashboard web (park_management/static/js/main.js).
 * Quản lý giao diện tương tác, đăng nhập, gọi API xe vào/ra, vé tháng và vẽ biểu đồ thống kê Chart.js.
 */

/* ========================================================================
   ParkAI Manager - Enhanced Frontend with Strict Role-based Permissions & Ticket Views
   ======================================================================== */

let activePanel = 'overview';
let selectedVehicleTypeVal = 'XeMay';
let selectedZoneVal = 'Khu A';

let currentUser = {
  id: 1,
  username: 'admin',
  fullName: 'Nguyễn Văn Quản',
  role: 'QuanLy',
  shift: 'Ca hành chính (8h–17h)'
};

let inLotVehicles = [];
let historyData = [];
let sessionHeartbeatTimer = null;
let monthlyCustomers = [];
let staffList = [];
let summaryMetrics = {};

// Chart Instances
let overviewChartInst = null;
let dailyTrafficChartInst = null;
let dailyRevenueChartInst = null;
let peakHourChartInst = null;
let zoneDoughnutChartInst = null;

// Toast notification helper
function showToast(msg, type = 'success') {
  const t = document.getElementById('global-toast');
  if (!t) return;
  t.className = type === 'success' ? 'bg-success text-white' : (type === 'info' ? 'bg-primary text-white' : 'bg-danger text-white');
  t.innerHTML = `<i class="fa-solid ${type === 'success' ? 'fa-circle-check' : (type === 'info' ? 'fa-circle-info' : 'fa-triangle-exclamation')} me-2"></i> ${msg}`;
  t.style.display = 'flex';
  t.classList.remove('d-none');
  setTimeout(() => { t.classList.add('d-none'); }, 3500);
}

// CSRF helper
function getCsrfToken() {
  const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
  return tokenInput ? tokenInput.value : '';
}

// ------------------------------------------------------------------------
// Authentication Flow & Role-based UI setup
// ------------------------------------------------------------------------
function togglePasswordVisibility(fieldId = 'login-password', iconId = 'toggle-pwd-btn') {
  const pwd = document.getElementById(fieldId);
  const toggle = document.getElementById(iconId);
  const icon = toggle ? toggle.querySelector('i') : null;
  if (!pwd) return;
  if (pwd.type === 'password') {
    pwd.type = 'text';
    if (icon) icon.className = 'fa-regular fa-eye-slash';
    if (toggle) {
      toggle.setAttribute('aria-label', 'Ẩn mật khẩu');
      toggle.setAttribute('aria-pressed', 'true');
    }
  } else {
    pwd.type = 'password';
    if (icon) icon.className = 'fa-regular fa-eye';
    if (toggle) {
      toggle.setAttribute('aria-label', 'Hiện mật khẩu');
      toggle.setAttribute('aria-pressed', 'false');
    }
  }
  pwd.focus();
}

function openRegisterModal() {
  const modalEl = document.getElementById('registerAccountModal');
  if (modalEl) {
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }
}

// Apply Role-based Permissions on Sidebar & Tab Access
function applyRolePermissions(userRole) {
  const isManager = (userRole === 'QuanLy' || userRole === 'manager' || userRole === 'admin');
  document.body.classList.toggle('role-manager', isManager);
  document.body.classList.toggle('role-staff', !isManager);
  
  // Elements that only Managers can access
  const managerOnlyPanels = ['overview', 'statistics', 'ai', 'staff', 'settings'];
  // Operational screens are reserved for parking staff.
  const staffOnlyPanels = ['checkinout', 'history'];
  
  document.querySelectorAll('.nav-item-btn').forEach(btn => {
    const panel = btn.getAttribute('data-panel');
    if (managerOnlyPanels.includes(panel)) {
      if (isManager) {
        btn.classList.remove('d-none');
      } else {
        btn.classList.add('d-none');
      }
    } else if (staffOnlyPanels.includes(panel)) {
      if (isManager) {
        btn.classList.add('d-none');
        btn.style.setProperty('display', 'none', 'important');
      } else {
        btn.classList.remove('d-none');
        btn.style.removeProperty('display');
      }
    }
  });

  document.querySelectorAll('[data-staff-only]').forEach(element => {
    element.classList.toggle('d-none', isManager);
    if (isManager) {
      element.style.setProperty('display', 'none', 'important');
    } else {
      element.style.removeProperty('display');
    }
  });

  const roleTagEl = document.getElementById('sidebar-role-tag');
  const roleTextEl = document.getElementById('current-user-role-text');
  if (roleTextEl) {
    roleTextEl.className = isManager ? 'fw-bold text-info small' : 'fw-bold text-success small';
    roleTextEl.textContent = isManager ? 'Quản lý hệ thống' : 'Nhân viên bãi xe';
  }
  if (roleTagEl) {
    if (isManager) {
      roleTagEl.className = 'status-pill bg-primary bg-opacity-25 text-white border border-primary border-opacity-50 mt-1';
      roleTagEl.textContent = 'Toàn quyền quản trị';
    } else {
      roleTagEl.className = 'status-pill bg-success bg-opacity-25 text-white border border-success border-opacity-50 mt-1';
      roleTagEl.textContent = 'Nhân viên tác nghiệp';
    }
  }

  // Redirect away from panels that are not available for the current role.
  if (!isManager && managerOnlyPanels.includes(activePanel)) {
    switchNavPanel('checkinout');
  } else if (isManager && staffOnlyPanels.includes(activePanel)) {
    switchNavPanel('overview');
  }
}

// Handle Login submit
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('auth-login-form');
  if (loginForm) {
    const usernameInput = document.getElementById('login-username');
    const passwordInput = document.getElementById('login-password');
    const rememberInput = document.getElementById('remember-username');
    const loginAlert = document.getElementById('dashboard-login-alert');
    const submitButton = document.getElementById('dashboard-login-submit');
    const rememberedUsername = localStorage.getItem('parkai_username');

    if (rememberedUsername) {
      usernameInput.value = rememberedUsername;
      rememberInput.checked = true;
      passwordInput.focus();
    }

    [usernameInput, passwordInput].forEach(input => {
      input.addEventListener('input', () => input.closest('.login-field').classList.remove('has-error'));
    });

    loginForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const username = usernameInput.value.trim();
      const password = passwordInput.value;
      const emptyInputs = [usernameInput, passwordInput].filter(input => !input.value.trim());
      [usernameInput, passwordInput].forEach(input => {
        input.closest('.login-field').classList.toggle('has-error', !input.value.trim());
      });
      if (emptyInputs.length) {
        emptyInputs[0].focus();
        return;
      }

      loginAlert.hidden = true;
      submitButton.disabled = true;
      submitButton.classList.add('is-loading');
      submitButton.querySelector('span').textContent = 'Đang xác thực...';

      try {
        const res = await fetch('/api/auth/login/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
          currentUser = data.user;
          if (rememberInput.checked) localStorage.setItem('parkai_username', username);
          else localStorage.removeItem('parkai_username');
          document.getElementById('login-view').classList.add('d-none');
          document.getElementById('app-shell-view').classList.remove('d-none');

          document.getElementById('current-user-fullname').textContent = currentUser.fullName;
          document.getElementById('current-user-role-text').textContent = currentUser.role === 'QuanLy' ? 'Quản lý' : 'Nhân viên';
          document.getElementById('user-avatar-badge').textContent = (currentUser.fullName || 'U').charAt(0).toUpperCase();

          applyRolePermissions(currentUser.role);
          startSessionHeartbeat();
          showToast(`Đăng nhập thành công! Xin chào ${currentUser.fullName}`);
          loadAllDataFromDatabase();
          setTimeout(initAllCharts, 200);
        } else {
          loginAlert.innerHTML = '<i class="fa-solid fa-circle-exclamation" aria-hidden="true"></i><span></span>';
          loginAlert.querySelector('span').textContent = data.message || 'Tên tài khoản hoặc mật khẩu không chính xác.';
          loginAlert.hidden = false;
          passwordInput.select();
        }
      } catch (err) {
        loginAlert.innerHTML = '<i class="fa-solid fa-circle-exclamation" aria-hidden="true"></i><span></span>';
        loginAlert.querySelector('span').textContent = 'Không thể kết nối máy chủ. Vui lòng thử lại sau.';
        loginAlert.hidden = false;
      } finally {
        submitButton.disabled = false;
        submitButton.classList.remove('is-loading');
        submitButton.querySelector('span').textContent = 'Đăng nhập';
      }
    });
  }

  // Handle Register submit
  const registerForm = document.getElementById('form-register-account');
  if (registerForm) {
    registerForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const username = document.getElementById('reg-username').value.trim();
      const password = document.getElementById('reg-password').value;
      const fullName = document.getElementById('reg-fullname').value.trim();
      const phone = document.getElementById('reg-phone').value.trim();
      const email = document.getElementById('reg-email').value.trim();
      const role = document.getElementById('reg-role').value;

      try {
        const res = await fetch('/api/auth/register/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify({
            ten_dang_nhap: username,
            password: password,
            ho_ten: fullName,
            so_dien_thoai: phone,
            email: email,
            role_name: role
          })
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
          showToast(`Đăng ký tài khoản ${username} thành công! Bạn có thể đăng nhập ngay.`);
          const modalInstance = bootstrap.Modal.getInstance(document.getElementById('registerAccountModal'));
          if (modalInstance) modalInstance.hide();
          registerForm.reset();
          document.getElementById('login-username').value = username;
          document.getElementById('login-password').value = password;
          loadStaffList();
        } else {
          const errMsg = data.message || Object.values(data.errors || {})[0] || 'Đăng ký thất bại';
          showToast(errMsg, 'error');
        }
      } catch (err) {
        showToast('Lỗi khi gửi yêu cầu đăng ký: ' + err.message, 'error');
      }
    });
  }

  // Bind navigation tabs
  document.querySelectorAll('.nav-item-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const p = this.getAttribute('data-panel');
      switchNavPanel(p);
    });
  });

  // Bind check-in form
  const checkinForm = document.getElementById('real-checkin-form');
  if (checkinForm) {
    checkinForm.addEventListener('submit', handleVehicleCheckIn);
  }

  // Bind check-out form
  const checkoutForm = document.getElementById('real-checkout-form');
  if (checkoutForm) {
    checkoutForm.addEventListener('submit', handleVehicleCheckOut);
  }

  // Initial load
  loadAllDataFromDatabase();
});

async function sendSessionHeartbeat() {
  if (!currentUser || !currentUser.id) return;
  try {
    await fetch('/api/auth/me/', {cache: 'no-store'});
    if (activePanel === 'staff') await loadStaffList();
  } catch (error) {
    console.warn('Session heartbeat failed:', error);
  }
}

function startSessionHeartbeat() {
  if (sessionHeartbeatTimer) clearInterval(sessionHeartbeatTimer);
  sessionHeartbeatTimer = setInterval(sendSessionHeartbeat, 30000);
}

function logoutApp() {
  if (sessionHeartbeatTimer) {
    clearInterval(sessionHeartbeatTimer);
    sessionHeartbeatTimer = null;
  }
  fetch('/api/auth/logout/', { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken() } });
  document.getElementById('app-shell-view').classList.add('d-none');
  document.body.classList.remove('role-manager', 'role-staff');
  document.getElementById('login-view').classList.remove('d-none');
  const pwdInput = document.getElementById('login-password');
  if (pwdInput) {
    pwdInput.value = '';
    pwdInput.type = 'password';
  }
}

function switchNavPanel(panelName) {
  // Enforce the same permissions even when navigation is triggered by code.
  const isManager = (currentUser.role === 'QuanLy' || currentUser.role === 'manager' || currentUser.role === 'admin');
  const managerOnlyPanels = ['overview', 'statistics', 'ai', 'staff', 'settings'];
  const staffOnlyPanels = ['checkinout', 'history'];
  
  if (!isManager && managerOnlyPanels.includes(panelName)) {
    showToast('Chức năng này yêu cầu quyền Quản lý.', 'error');
    return;
  }

  if (isManager && staffOnlyPanels.includes(panelName)) {
    showToast('Chức năng này dành cho Nhân viên bãi xe.', 'error');
    return;
  }

  activePanel = panelName;
  document.querySelectorAll('.nav-item-btn').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-panel') === panelName);
  });
  document.querySelectorAll('.content-tab-pane').forEach(pane => {
    pane.classList.add('d-none');
  });
  const target = document.getElementById(`panel-${panelName}`);
  if (target) target.classList.remove('d-none');

  if (panelName === 'statistics' || panelName === 'overview') {
    setTimeout(initAllCharts, 150);
  }
}

// ------------------------------------------------------------------------
// Data Loading & Synchronization from Live CSDL
// ------------------------------------------------------------------------
async function loadAllDataFromDatabase() {
  await Promise.all([
    loadSummaryMetrics(),
    loadInLotVehicles(),
    loadHistoryData(),
    loadMonthlyCustomers(),
    loadStaffList(),
  ]);
  renderAllViews();
}

async function loadSummaryMetrics() {
  try {
    const res = await fetch('/api/reports/summary/');
    if (res.ok) {
      summaryMetrics = await res.json();
      updateDashboardKPIs(summaryMetrics);
    }
  } catch (e) {
    console.warn('Error loading summary:', e);
  }
}

async function loadInLotVehicles() {
  try {
    const res = await fetch('/api/tickets/in-lot/');
    if (res.ok) {
      inLotVehicles = await res.json();
    }
  } catch (e) {
    console.warn('Error loading in-lot vehicles:', e);
  }
}

async function loadHistoryData() {
  try {
    const res = await fetch('/api/tickets/sessions/');
    if (res.ok) {
      const data = await res.json();
      historyData = data.results ? data.results : data;
    }
  } catch (e) {
    console.warn('Error loading history:', e);
  }
}

async function loadMonthlyCustomers() {
  try {
    const res = await fetch('/api/tickets/monthly/');
    if (res.ok) {
      const data = await res.json();
      monthlyCustomers = data.results ? data.results : data;
    }
  } catch (e) {
    console.warn('Error loading monthly customers:', e);
  }
}

async function loadStaffList() {
  try {
    const res = await fetch('/api/users/');
    if (res.ok) {
      const data = await res.json();
      staffList = data.results ? data.results : data;
      renderStaffTab();
    }
  } catch (e) {
    console.warn('Error loading staff:', e);
  }
}

function renderAllViews() {
  renderInLotAccordion();
  renderHistoryTable();
  renderMonthlyCards();
  populateCheckoutSelect();
  renderOverviewZones();
}

// ------------------------------------------------------------------------
// Render Functions with Live Data
// ------------------------------------------------------------------------
function updateDashboardKPIs(data) {
  if (!data) return;

  const totalCapEl = document.getElementById('kpi-total-capacity');
  if (totalCapEl) totalCapEl.textContent = data.total_capacity ?? 0;

  const activeVehiclesEl = document.getElementById('metric-active-vehicles');
  if (activeVehiclesEl) activeVehiclesEl.textContent = data.total_in_lot !== undefined ? data.total_in_lot : inLotVehicles.length;

  const occRateEl = document.getElementById('metric-occupancy-rate');
  if (occRateEl) occRateEl.textContent = `${data.occupancy_rate || 0}% công suất`;

  const todayInEl = document.getElementById('metric-today-in');
  if (todayInEl) todayInEl.textContent = data.today_in_count || 0;

  const todayOutEl = document.getElementById('metric-today-out');
  if (todayOutEl) todayOutEl.textContent = `${data.today_out_count || 0} lượt đã ra`;

  const todayRevEl = document.getElementById('metric-today-revenue');
  if (todayRevEl) todayRevEl.textContent = (data.today_revenue || 0).toLocaleString('vi-VN') + ' đ';

  // Stats tab
  const statWeekEntries = document.getElementById('stat-week-entries');
  if (statWeekEntries) statWeekEntries.textContent = (data.week_entries ?? 0).toLocaleString('vi-VN');

  const statWeekRevenue = document.getElementById('stat-week-revenue');
  if (statWeekRevenue) statWeekRevenue.textContent = (data.week_revenue ?? 0).toLocaleString('vi-VN') + ' đ';

  const statDailyAvg = document.getElementById('stat-daily-avg');
  if (statDailyAvg) statDailyAvg.textContent = data.avg_daily_entries ?? 0;

  // Monthly tab counters
  const mActiveEl = document.getElementById('monthly-active-count');
  if (mActiveEl) mActiveEl.textContent = data.monthly_active || 0;

  const mExpiredEl = document.getElementById('monthly-expired-count');
  if (mExpiredEl) mExpiredEl.textContent = data.monthly_expired || 0;

  const mTotalEl = document.getElementById('monthly-total-count');
  if (mTotalEl) mTotalEl.textContent = data.monthly_total || 0;
}

function renderOverviewZones() {
  // So lieu tung khu lay truc tiep tu CSDL (/api/reports/summary/), khong dem lai phia client
  const zones = summaryMetrics.zone_stats || [];

  zones.forEach(z => {
    const inLot = z.in_lot ?? 0;
    const available = z.available ?? Math.max(0, (z.capacity || 0) - inLot);
    const rate = z.rate ?? Math.round((inLot / (z.capacity || 1)) * 100);

    const countEl = document.getElementById(`zone-${z.code.toLowerCase()}-count`);
    if (countEl) countEl.textContent = inLot;

    const countEl2 = document.getElementById(`zone-${z.code.toLowerCase()}-count-2`);
    if (countEl2) countEl2.textContent = inLot;

    const availEl = document.getElementById(`zone-${z.code.toLowerCase()}-avail`);
    if (availEl) availEl.textContent = available;

    const rateEl = document.getElementById(`zone-${z.code.toLowerCase()}-rate`);
    if (rateEl) rateEl.textContent = `${rate}%`;

    const progEl = document.getElementById(`zone-${z.code.toLowerCase()}-progress`);
    if (progEl) progEl.style.width = `${Math.max(rate, 3)}%`;

    // Map zone cards
    const mapCountEl = document.getElementById(`map-count-${z.code.toLowerCase()}`);
    if (mapCountEl) mapCountEl.textContent = inLot;
    const mapAvailEl = document.getElementById(`map-avail-${z.code.toLowerCase()}`);
    if (mapAvailEl) mapAvailEl.textContent = `${rate}% • còn ${available} chỗ`;
  });
}

function renderInLotAccordion() {
  const countEl = document.getElementById('inlot-badge-count');
  if (countEl) countEl.textContent = `${inLotVehicles.length} xe`;

  const container = document.getElementById('inlot-vehicles-accordion');
  if (!container) return;

  const zones = (summaryMetrics.zone_stats && summaryMetrics.zone_stats.length)
    ? summaryMetrics.zone_stats.map(z => z.code)
    : ['A', 'B', 'C', 'D'];
  let html = '';

  zones.forEach(z => {
    const zoneVehicles = inLotVehicles.filter(v => (v.ten_khu_vuc || '').includes(z) || (v.khu_vuc && v.khu_vuc.ten_khu_vuc && v.khu_vuc.ten_khu_vuc.includes(z)));
    const badgeClass = `badge-zone-${z.toLowerCase()}`;
    html += `
      <div class="mb-3">
        <div class="d-flex align-items-center gap-2 mb-2">
          <span class="zone-badge ${badgeClass}">${z}</span>
          <span class="fw-bold text-white small">Khu ${z}</span>
          <span class="text-dim small">${zoneVehicles.length} xe</span>
        </div>
        <div class="d-flex flex-column gap-2 ps-3">
    `;

    if (zoneVehicles.length === 0) {
      html += `<div class="text-dim small py-1 fst-italic">Chưa có xe gửi ở khu này.</div>`;
    } else {
      zoneVehicles.forEach(v => {
        const vType = v.ten_loai_xe || (v.loai_xe_detail && v.loai_xe_detail.ten_loai_xe) || 'XeMay';
        const icon = (vType === 'XeMay' || vType === 'MOTORBIKE') ? 'fa-motorcycle text-primary' : ((vType === 'Oto' || vType === 'CAR') ? 'fa-car text-danger' : 'fa-bicycle text-info');
        const inTimeStr = v.thoi_gian_vao ? new Date(v.thoi_gian_vao).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '';
        const fee = v.tien_phi_du_tinh || v.tong_tien_phi || 5000;

        html += `
          <div class="dark-card p-2 px-3 d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-2">
              <i class="fa-solid ${icon}"></i>
              <div>
                <div class="fw-bold text-white small">${v.bien_so_xe_kiem_tra}</div>
                <div class="text-dim" style="font-size:0.7rem;">Vào: ${inTimeStr}</div>
              </div>
            </div>
            <div class="d-flex align-items-center gap-2">
              <div class="text-end me-1">
                <div class="text-dim small" style="font-size:0.75rem;">${v.thoi_gian_gui_text || 'Mới vào'}</div>
                <div class="fw-bold text-warning small">${Number(fee).toLocaleString('vi-VN')} đ</div>
              </div>
              <button class="btn btn-sm btn-outline-info rounded-pill py-1 px-2" title="Xem vé" onclick="viewTicketDetail(${v.ma_luot_gui})">
                <i class="fa-solid fa-ticket"></i>
              </button>
            </div>
          </div>
        `;
      });
    }
    html += `</div></div>`;
  });
  container.innerHTML = html;
}

function populateCheckoutSelect() {
  const sel = document.getElementById('checkout-session-select');
  if (!sel) return;
  sel.innerHTML = '<option value="">-- Chọn xe trong danh sách --</option>';
  inLotVehicles.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.ma_luot_gui;
    const inTimeStr = v.thoi_gian_vao ? new Date(v.thoi_gian_vao).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '';
    opt.textContent = `${v.bien_so_xe_kiem_tra} - ${v.ten_khu_vuc || 'Bãi đỗ'} (Vào: ${inTimeStr})`;
    sel.appendChild(opt);
  });
}

function renderHistoryTable() {
  const tbody = document.getElementById('history-table-body');
  if (!tbody) return;
  const q = (document.getElementById('history-search-input').value || '').toUpperCase().trim();
  const status = document.getElementById('history-status-filter').value;
  const zone = document.getElementById('history-zone-filter').value;

  let filtered = historyData.filter(item => {
    const plate = (item.bien_so_xe_kiem_tra || '').toUpperCase();
    const cust = (item.ten_khach_hang || '').toUpperCase();
    const staffIn = (item.ten_nhan_vien_vao || '').toUpperCase();
    if (q && !plate.includes(q) && !cust.includes(q) && !staffIn.includes(q)) return false;
    
    if (status === 'inlot' && item.trang_thai_luot !== 'Đang gửi') return false;
    if (status === 'completed' && item.trang_thai_luot !== 'Đã ra') return false;

    const zName = item.ten_khu_vuc || '';
    if (zone && !zName.includes(zone)) return false;

    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">Không tìm thấy lượt xe nào trong CSDL.</td></tr>';
    return;
  }

  let html = '';
  filtered.forEach(r => {
    const isOut = r.trang_thai_luot === 'Đã ra';
    const statusHTML = isOut 
      ? '<span class="status-pill status-out">Đã ra</span>' 
      : '<span class="status-pill status-inlot">Đang gửi</span>';

    const inDate = r.thoi_gian_vao ? new Date(r.thoi_gian_vao).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '--';
    const outDate = r.thoi_gian_ra ? new Date(r.thoi_gian_ra).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '--';
    const zoneLetter = (r.ten_khu_vuc || 'A').replace('Khu ', '').trim();
    const feeVal = Number(r.tong_tien_phi || r.tien_phi_du_tinh || 0);

    html += `
      <tr>
        <td class="fw-bold text-white">${r.bien_so_xe_kiem_tra}</td>
        <td class="text-muted">${r.ten_loai_xe || 'Xe máy'}</td>
        <td><span class="zone-badge badge-zone-${zoneLetter.toLowerCase()}">${zoneLetter}</span></td>
        <td class="text-muted">${inDate}</td>
        <td class="text-muted">${outDate}</td>
        <td class="text-muted">${r.thoi_gian_gui_text || '--'}</td>
        <td class="fw-bold text-warning">${feeVal.toLocaleString('vi-VN')} đ</td>
        <td>${statusHTML}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-info rounded-pill px-3 py-1 fw-semibold" onclick="viewTicketDetail(${r.ma_luot_gui})">
            <i class="fa-solid fa-ticket me-1"></i> Xem vé
          </button>
        </td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

function filterHistoryTable() {
  renderHistoryTable();
}

function renderMonthlyCards() {
  const container = document.getElementById('monthly-cards-container');
  if (!container) return;
  const q = (document.getElementById('monthly-search-input').value || '').toUpperCase().trim();

  let filtered = monthlyCustomers.filter(c => {
    const name = (c.ho_ten_khach_hang || '').toUpperCase();
    const plate = (c.bien_so_xe || '').toUpperCase();
    if (q && !name.includes(q) && !plate.includes(q)) return false;
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = '<div class="col-12 text-center py-4 text-muted">Không tìm thấy khách hàng vé tháng nào.</div>';
    return;
  }

  let html = '';
  filtered.forEach(c => {
    const vType = c.ten_loai_xe || 'XeMay';
    const icon = (vType === 'XeMay' || vType === 'MOTORBIKE') ? 'fa-motorcycle text-warning' : ((vType === 'Oto' || vType === 'CAR') ? 'fa-car text-danger' : 'fa-bicycle text-info');
    const isExpired = c.trang_thai_ve === 'Đã hết hạn';
    const statusBadge = !isExpired 
      ? '<span class="status-pill status-inlot"><i class="fa-solid fa-check"></i> Đang hiệu lực</span>' 
      : '<span class="status-pill status-expired">Hiệu lực đã hết</span>';

    const endFormatted = c.ngay_ket_thuc ? new Date(c.ngay_ket_thuc).toLocaleDateString('vi-VN') : '--';
    const initial = (c.ho_ten_khach_hang || 'U').split(' ').pop()[0] || 'K';

    html += `
      <div class="col-md-6">
        <div class="dark-card p-3">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="d-flex align-items-center gap-3">
              <div class="user-avatar-circle" style="background:#1f30d0;">${initial}</div>
              <div>
                <div class="fw-bold text-white fs-6">${c.ho_ten_khach_hang}</div>
                <div class="text-dim small">${c.so_dien_thoai || 'Chưa cập nhật'}</div>
              </div>
            </div>
            ${statusBadge}
          </div>
          <div class="d-flex justify-content-between align-items-center pt-2 border-top border-secondary border-opacity-10">
            <div class="d-flex align-items-center gap-2">
              <i class="fa-solid ${icon}"></i>
              <span class="fw-bold text-white small">${c.bien_so_xe}</span>
              <span class="text-dim small">• ${c.ten_loai_xe || 'Xe gửi'}</span>
            </div>
            <div class="d-flex align-items-center gap-2">
              <span class="text-dim small me-1">Hạn: <span class="text-white fw-bold">${endFormatted}</span></span>
              <button class="btn btn-sm btn-outline-info rounded-pill px-2 py-1" title="Xem chi tiết" onclick="viewMonthlyTicketDetail(${c.ma_ve_thang})">
                <i class="fa-solid fa-id-card"></i>
              </button>
              <button class="btn btn-sm btn-outline-success rounded-pill px-2 py-1" title="Gia hạn vé tháng" onclick="openRenewMonthlyModal(${c.ma_ve_thang})">
                <i class="fa-solid fa-arrows-rotate"></i>
              </button>
              <button class="btn btn-sm btn-outline-danger rounded-pill px-2 py-1" title="Xóa vé tháng" onclick="deleteMonthlyTicket(${c.ma_ve_thang})">
                <i class="fa-solid fa-trash"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function filterMonthlyCards() {
  renderMonthlyCards();
}

function renderStaffTab() {
  const container = document.getElementById('staff-list-container');
  if (!container) return;

  if (staffList.length === 0) {
    container.innerHTML = '<div class="text-muted py-3">Đang cập nhật danh sách nhân viên...</div>';
    return;
  }

  let html = '';
  staffList.forEach(u => {
    const isManager = u.ten_vai_tro === 'QuanLy' || u.vai_tro === 1;
    const initial = (u.ho_ten || 'U').charAt(0).toUpperCase();
    const avatarBg = isManager ? '#0077cc' : '#0d9488';
    const isOnline = Boolean(u.is_online);
    const statusColor = isOnline ? '#22c55e' : '#64748b';
    /* Removed manual account-status selector.
      <select class="form-select form-select-sm bg-dark text-white border-secondary" style="width:auto;" onchange="changeStaffStatus(${u.ma_nguoi_dung}, this.value, '${u.ten_dang_nhap}')" aria-label="Trạng thái tài khoản ${u.ten_dang_nhap}">
        <option value="Hoạt động" ${accountStatus === 'Hoạt động' ? 'selected' : ''}>Hoạt động</option>
        <option value="Tạm nghỉ" ${accountStatus === 'Tạm nghỉ' ? 'selected' : ''}>Tạm nghỉ</option>
        <option value="Khóa" ${accountStatus === 'Khóa' ? 'selected' : ''}>Khóa</option>
      </select> */
    const accountActions = isManager ? '' : `
      <div class="d-flex justify-content-end gap-2 mb-2">
        <button class="btn btn-outline-warning btn-sm rounded-3" onclick="resetStaffPassword(${u.ma_nguoi_dung}, '${u.ten_dang_nhap}')">
          <i class="fa-solid fa-key me-1"></i> Đặt lại mật khẩu
        </button>
        <button class="btn btn-outline-danger btn-sm rounded-3" onclick="deleteStaffAccount(${u.ma_nguoi_dung}, '${u.ten_dang_nhap}')">
          <i class="fa-solid fa-user-xmark me-1"></i> Xóa tài khoản
        </button>
      </div>`;
    const roleBadge = isManager ? '<span class="status-pill" style="background:rgba(0,149,255,0.15); color:#0095ff;">Quản lý</span>' : '<span class="status-pill status-inlot">Nhân viên</span>';

    html += `
      <div class="dark-card p-3 d-flex align-items-center justify-content-between">
        <div class="d-flex align-items-center gap-3">
          <div class="user-avatar-circle" style="background: ${avatarBg};">${initial}</div>
          <div>
            <div class="d-flex align-items-center gap-2">
              <span class="fw-bold text-white">${u.ho_ten}</span>
              <span class="d-inline-block rounded-circle" style="width:6px;height:6px;background:${statusColor};"></span>
              <span class="text-dim small">${isOnline ? 'Hoạt động' : 'Không hoạt động'}</span>
            </div>
            <div class="text-dim small mb-1">${u.email || u.ten_dang_nhap + '@baidoxe.vn'} • SĐT: ${u.so_dien_thoai || 'N/A'}</div>
            <div class="d-flex align-items-center gap-2">
              ${roleBadge}
              <span class="text-dim small">${u.ca_lam_viec || 'Ca hành chính'}</span>
            </div>
          </div>
        </div>
        <div class="text-end">
          ${accountActions}
          <div class="text-dim small">Tài khoản: <span class="text-white fw-bold">${u.ten_dang_nhap}</span></div>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

// ------------------------------------------------------------------------
async function resetStaffPassword(userId, username) {
  document.getElementById('reset-password-user-id').value = userId;
  document.getElementById('reset-password-username').textContent = username;
  document.getElementById('reset-new-password').value = '';
  document.getElementById('reset-confirm-password').value = '';
  document.getElementById('reset-password-error').classList.add('d-none');
  bootstrap.Modal.getOrCreateInstance(document.getElementById('resetPasswordModal')).show();
  setTimeout(() => document.getElementById('reset-new-password').focus(), 250);
  return;
  const newPassword = window.prompt(`Nhập mật khẩu mới cho tài khoản ${username} (tối thiểu 6 ký tự):`);
  if (newPassword === null) return;
  if (newPassword.length < 6) {
    showToast('Mật khẩu mới phải có ít nhất 6 ký tự.', 'error');
    return;
  }

  const confirmation = window.prompt('Nhập lại mật khẩu mới để xác nhận:');
  if (confirmation === null) return;
  if (newPassword !== confirmation) {
    showToast('Mật khẩu xác nhận không khớp.', 'error');
    return;
  }

  try {
    const response = await fetch(`/api/users/${userId}/reset-password/`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
      body: JSON.stringify({new_password: newPassword})
    });
    const data = await response.json();
    showToast(data.message || (response.ok ? 'Đã đặt lại mật khẩu.' : 'Không thể đặt lại mật khẩu.'), response.ok ? 'success' : 'error');
  } catch (error) {
    showToast('Không thể kết nối máy chủ: ' + error.message, 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const resetForm = document.getElementById('form-reset-password');
  if (!resetForm) return;

  resetForm.addEventListener('submit', async event => {
    event.preventDefault();
    const userId = document.getElementById('reset-password-user-id').value;
    const username = document.getElementById('reset-password-username').textContent;
    const newPassword = document.getElementById('reset-new-password').value;
    const confirmation = document.getElementById('reset-confirm-password').value;
    const errorElement = document.getElementById('reset-password-error');
    const submitButton = document.getElementById('reset-password-submit');

    const showFormError = message => {
      errorElement.textContent = message;
      errorElement.classList.remove('d-none');
    };

    errorElement.classList.add('d-none');
    if (newPassword.length < 6) {
      showFormError('Mật khẩu mới phải có ít nhất 6 ký tự.');
      return;
    }
    if (newPassword !== confirmation) {
      showFormError('Mật khẩu xác nhận không khớp.');
      return;
    }

    submitButton.disabled = true;
    try {
      const response = await fetch(`/api/users/${userId}/reset-password/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
        body: JSON.stringify({new_password: newPassword})
      });
      const data = await response.json();
      if (!response.ok) {
        showFormError(data.message || 'Không thể đặt lại mật khẩu.');
        return;
      }
      bootstrap.Modal.getInstance(document.getElementById('resetPasswordModal')).hide();
      showToast(data.message || `Đã đặt lại mật khẩu cho ${username}.`);
    } catch (error) {
      showFormError('Không thể kết nối máy chủ: ' + error.message);
    } finally {
      submitButton.disabled = false;
    }
  });
});

async function deleteStaffAccount(userId, username) {
  if (!window.confirm(`Xóa tài khoản ${username}? Nhân viên sẽ không thể đăng nhập, nhưng lịch sử làm việc vẫn được giữ lại.`)) return;

  try {
    const response = await fetch(`/api/users/${userId}/`, {
      method: 'DELETE',
      headers: {'X-CSRFToken': getCsrfToken()}
    });
    const data = await response.json();
    if (!response.ok) {
      showToast(data.message || 'Không thể xóa tài khoản.', 'error');
      return;
    }
    showToast(data.message || 'Đã xóa tài khoản.');
    await loadStaffList();
  } catch (error) {
    showToast('Không thể kết nối máy chủ: ' + error.message, 'error');
  }
}

// Check-In & Check-Out Actions connected with Live Backend APIs
// ------------------------------------------------------------------------
async function handleVehicleCheckIn(e) {
  if (e) e.preventDefault();
  const plateInput = document.getElementById('in-plate-number');
  if (!plateInput) return;
  const plate = plateInput.value.toUpperCase().trim();
  if (!plate) {
    showToast('Vui lòng nhập biển số xe', 'error');
    return;
  }

  const zoneBadge = document.getElementById('selected-zone-badge');
  const zoneLetter = zoneBadge ? zoneBadge.textContent.trim() : 'A';
  const zoneName = `Khu ${zoneLetter}`;

  const payload = {
    plate_number: plate,
    vehicle_type: selectedVehicleTypeVal,
    zone: zoneName,
    staff_id: currentUser.id,
    staff_username: currentUser.username
  };

  try {
    const res = await fetch('/api/tickets/check-in/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      showToast(data.message || `Xe ${plate} đã vào ${zoneName} thành công!`);
      plateInput.value = '';
      await loadAllDataFromDatabase();
      
      // Auto show ticket preview
      if (data.session && data.session.ma_luot_gui) {
        viewTicketDetail(data.session.ma_luot_gui);
      }
    } else {
      showToast(data.message || 'Không thể ghi nhận xe vào', 'error');
    }
  } catch (err) {
    showToast('Lỗi gửi xe vào: ' + err.message, 'error');
  }
}

// Quick Sample Plate Helper for Testing & Fast Input
function quickSetPlate(plateStr, vType, zoneLetter) {
  const pInput = document.getElementById('in-plate-number');
  if (pInput) pInput.value = plateStr;
  
  // Set type
  const typeCard = document.querySelector(`.vehicle-type-select-card[data-type="${vType}"]`);
  if (typeCard) {
    selectVehicleType(typeCard, vType, '');
  }
}

async function handleVehicleCheckOut(e) {
  if (e) e.preventDefault();
  const sel = document.getElementById('checkout-session-select');
  const sessionId = sel ? sel.value : null;
  if (!sessionId) {
    showToast('Vui lòng chọn xe cần ra bãi', 'error');
    return;
  }

  const payload = {
    session_id: sessionId,
    staff_id: currentUser.id,
    staff_username: currentUser.username
  };

  try {
    const res = await fetch('/api/tickets/check-out/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      showToast(data.message || 'Xe đã ra bãi và thanh toán thành công!');
      document.getElementById('checkout-calc-card').classList.add('d-none');
      if (sel) sel.value = '';
      await loadAllDataFromDatabase();

      // Show completed ticket / receipt
      if (data.session && data.session.ma_luot_gui) {
        viewTicketDetail(data.session.ma_luot_gui);
      }
    } else {
      showToast(data.message || 'Không thể hoàn tất xe ra', 'error');
    }
  } catch (err) {
    showToast('Lỗi hoàn tất xe ra: ' + err.message, 'error');
  }
}

function onCheckoutVehicleSelected() {
  const val = document.getElementById('checkout-session-select').value;
  const card = document.getElementById('checkout-calc-card');
  if (!val) {
    card.classList.add('d-none');
    return;
  }

  const item = inLotVehicles.find(v => String(v.ma_luot_gui) === String(val));
  if (!item) return;

  const inTimeStr = item.thoi_gian_vao ? new Date(item.thoi_gian_vao).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' }) : '--';
  const fee = Number(item.tien_phi_du_tinh || item.tong_tien_phi || 5000);

  document.getElementById('calc-time-in').textContent = inTimeStr;
  document.getElementById('calc-duration').textContent = item.thoi_gian_gui_text || '1 giờ';
  document.getElementById('calc-amount').textContent = fee.toLocaleString('vi-VN') + ' đ';
  card.classList.remove('d-none');
}

function switchCheckinTab(tab) {
  const btnIn = document.getElementById('btn-tab-checkin');
  const btnOut = document.getElementById('btn-tab-checkout');
  const formIn = document.getElementById('checkin-form-box');
  const formOut = document.getElementById('checkout-form-box');

  if (tab === 'in') {
    btnIn.classList.add('active');
    btnOut.classList.remove('active');
    formIn.classList.remove('d-none');
    formOut.classList.add('d-none');
  } else {
    btnIn.classList.remove('active');
    btnOut.classList.add('active');
    formIn.classList.add('d-none');
    formOut.classList.remove('d-none');
    populateCheckoutSelect();
  }
}

function selectVehicleType(el, type, priceText) {
  selectedVehicleTypeVal = type;
  document.querySelectorAll('.vehicle-type-select-card').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');
  
  const zoneBadge = document.getElementById('selected-zone-badge');
  const zoneText = document.getElementById('selected-zone-text');

  if (type === 'XeMay' || type === 'MOTORBIKE') {
    if (zoneBadge) { zoneBadge.textContent = 'A'; zoneBadge.className = 'zone-badge badge-zone-a'; }
    if (zoneText) zoneText.textContent = 'Khu A';
    selectedZoneVal = 'Khu A';
  } else if (type === 'Oto' || type === 'CAR') {
    if (zoneBadge) { zoneBadge.textContent = 'C'; zoneBadge.className = 'zone-badge badge-zone-c'; }
    if (zoneText) zoneText.textContent = 'Khu C';
    selectedZoneVal = 'Khu C';
  } else {
    if (zoneBadge) { zoneBadge.textContent = 'B'; zoneBadge.className = 'zone-badge badge-zone-b'; }
    if (zoneText) zoneText.textContent = 'Khu B';
    selectedZoneVal = 'Khu B';
  }
}

// ------------------------------------------------------------------------
// View Ticket Details Modal (Vé lượt with Staff Names & Vé tháng)
// ------------------------------------------------------------------------
function viewTicketDetail(sessionId) {
  let session = historyData.find(s => String(s.ma_luot_gui) === String(sessionId));
  if (!session) {
    session = inLotVehicles.find(s => String(s.ma_luot_gui) === String(sessionId));
  }
  if (!session) {
    showToast('Không tìm thấy thông tin vé xe', 'error');
    return;
  }

  const modalEl = document.getElementById('viewTicketModal');
  if (!modalEl) return;

  const inDateStr = session.thoi_gian_vao ? new Date(session.thoi_gian_vao).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '--';
  const outDateStr = session.thoi_gian_ra ? new Date(session.thoi_gian_ra).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Đang gửi trong bãi';
  const isCompleted = session.trang_thai_luot === 'Đã ra';
  const fee = Number(isCompleted ? session.tong_tien_phi : session.tien_phi_du_tinh || 0);

  document.getElementById('ticket-modal-id').textContent = `#LGX-${String(session.ma_luot_gui).padStart(5, '0')}`;
  document.getElementById('ticket-modal-plate').textContent = session.bien_so_xe_kiem_tra;
  document.getElementById('ticket-modal-vtype').textContent = session.ten_loai_xe || 'Xe máy';
  document.getElementById('ticket-modal-zone').textContent = session.ten_khu_vuc || 'Khu A';
  document.getElementById('ticket-modal-intime').textContent = inDateStr;
  document.getElementById('ticket-modal-outtime').textContent = outDateStr;
  document.getElementById('ticket-modal-duration').textContent = session.thoi_gian_gui_text || '--';
  
  // Specific Staff Names from CSDL
  document.getElementById('ticket-modal-staff-in').textContent = session.ten_nhan_vien_vao || 'Trần Thị Mai (Trực ca)';
  document.getElementById('ticket-modal-staff-out').textContent = session.ten_nhan_vien_ra || (session.trang_thai_luot === 'Đã ra' ? 'Lê Văn Hùng' : 'Chưa ghi nhận (Xe chưa ra)');

  document.getElementById('ticket-modal-fee').textContent = `${fee.toLocaleString('vi-VN')} đ`;
  document.getElementById('ticket-modal-fee-label').textContent = isCompleted ? 'TỔNG PHÍ GỬI XE:' : 'PHÍ GỬI XE TẠM TÍNH:';
  
  const statusEl = document.getElementById('ticket-modal-status');
  if (isCompleted) {
    statusEl.className = 'status-pill status-out';
    statusEl.innerHTML = '<i class="fa-solid fa-flag-checkered me-1"></i> Đã hoàn tất & Đã ra';
  } else {
    statusEl.className = 'status-pill status-inlot';
    statusEl.innerHTML = '<i class="fa-solid fa-circle-check me-1"></i> Đang gửi trong bãi';
  }

  const modal = new bootstrap.Modal(modalEl);
  modal.show();
}

function viewMonthlyTicketDetail(monthlyId) {
  const m = monthlyCustomers.find(item => String(item.ma_ve_thang) === String(monthlyId));
  if (!m) return;

  const modalEl = document.getElementById('viewMonthlyTicketModal');
  if (!modalEl) return;

  const startStr = m.ngay_bat_dau ? new Date(m.ngay_bat_dau).toLocaleDateString('vi-VN') : '--';
  const endStr = m.ngay_ket_thuc ? new Date(m.ngay_ket_thuc).toLocaleDateString('vi-VN') : '--';

  document.getElementById('m-ticket-modal-id').textContent = `#VTH-${String(m.ma_ve_thang).padStart(4, '0')}`;
  document.getElementById('m-ticket-modal-name').textContent = m.ho_ten_khach_hang;
  document.getElementById('m-ticket-modal-phone').textContent = m.so_dien_thoai || 'Chưa cập nhật';
  document.getElementById('m-ticket-modal-plate').textContent = m.bien_so_xe;
  document.getElementById('m-ticket-modal-vtype').textContent = m.ten_loai_xe || 'Xe gửi';
  document.getElementById('m-ticket-modal-start').textContent = startStr;
  document.getElementById('m-ticket-modal-end').textContent = endStr;

  const statusEl = document.getElementById('m-ticket-modal-status');
  if (m.trang_thai_ve === 'Đã hết hạn') {
    statusEl.className = 'status-pill status-expired';
    statusEl.textContent = 'Đã hết hạn';
  } else {
    statusEl.className = 'status-pill status-inlot';
    statusEl.textContent = 'Đang hiệu lực';
  }

  const modal = new bootstrap.Modal(modalEl);
  modal.show();
}

function printTicketModal() {
  window.print();
}

// ------------------------------------------------------------------------
// Parking Map Interactive Zone Detail
// ------------------------------------------------------------------------
function selectMapZone(zoneKey) {
  document.querySelectorAll('.map-zone-block').forEach(b => b.classList.remove('active'));
  if (event && event.currentTarget) event.currentTarget.classList.add('active');

  const emptyState = document.getElementById('map-empty-state');
  const activeContent = document.getElementById('map-zone-active-content');
  if (emptyState) emptyState.classList.add('d-none');
  if (activeContent) activeContent.classList.remove('d-none');

  document.getElementById('map-detail-title').textContent = `Khu ${zoneKey}`;
  const badge = document.getElementById('map-detail-badge');
  badge.textContent = zoneKey;
  badge.className = `zone-badge badge-zone-${zoneKey.toLowerCase()}`;

  const zoneVehicles = inLotVehicles.filter(v => (v.ten_khu_vuc || '').includes(zoneKey) || (v.khu_vuc && v.khu_vuc.ten_khu_vuc && v.khu_vuc.ten_khu_vuc.includes(zoneKey)));
  document.getElementById('map-detail-count').textContent = `${zoneVehicles.length} xe đang gửi`;
  
  const list = document.getElementById('map-zone-vehicle-list');
  if (zoneVehicles.length === 0) {
    list.innerHTML = '<div class="text-muted small py-4 text-center">Không có xe nào đang gửi trong khu vực này.</div>';
    return;
  }

  let html = '';
  zoneVehicles.forEach(v => {
    const inTimeStr = v.thoi_gian_vao ? new Date(v.thoi_gian_vao).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '';
    const fee = Number(v.tien_phi_du_tinh || v.tong_tien_phi || 5000);

    html += `
      <div class="dark-card p-3 d-flex justify-content-between align-items-center" style="background: var(--bg-input);">
        <div>
          <div class="fw-bold text-white fs-6">${v.bien_so_xe_kiem_tra}</div>
          <div class="text-dim" style="font-size: 0.75rem;">Vào: ${inTimeStr} • NV: ${v.ten_nhan_vien_vao || 'Trực ca'}</div>
        </div>
        <div class="d-flex align-items-center gap-2">
          <div class="text-end">
            <div class="text-info small fw-bold">${v.thoi_gian_gui_text || 'Mới vào'}</div>
            <div class="text-warning small">${fee.toLocaleString('vi-VN')} đ</div>
          </div>
          <button class="btn btn-sm btn-outline-info rounded-pill px-2 py-1" onclick="viewTicketDetail(${v.ma_luot_gui})">
            <i class="fa-solid fa-ticket"></i>
          </button>
        </div>
      </div>
    `;
  });
  list.innerHTML = html;
}

// ------------------------------------------------------------------------
// Add Monthly Customer Modal
// ------------------------------------------------------------------------
function openAddMonthlyModal() {
  const m = new bootstrap.Modal(document.getElementById('addMonthlyModal'));
  m.show();
}

document.addEventListener('DOMContentLoaded', () => {
  const formMonthly = document.getElementById('form-add-monthly');
  if (formMonthly) {
    formMonthly.addEventListener('submit', async function(e) {
      e.preventDefault();
      const name = document.getElementById('monthly-cust-name').value.trim();
      const phone = document.getElementById('monthly-cust-phone').value.trim();
      const plate = document.getElementById('monthly-cust-plate').value.toUpperCase().trim();
      const rawType = document.getElementById('monthly-cust-type').value;
      const type = rawType.split('&')[0];
      const expiry = document.getElementById('monthly-cust-expiry').value;

      try {
        const res = await fetch('/api/tickets/monthly/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify({
            name, phone, plate, type, expiry
          })
        });

        const data = await res.json();
        if (res.ok) {
          showToast(`Đã thêm khách hàng vé tháng ${name} thành công!`);
          bootstrap.Modal.getInstance(document.getElementById('addMonthlyModal')).hide();
          formMonthly.reset();
          await loadAllDataFromDatabase();
        } else {
          showToast(data.message || 'Lỗi thêm vé tháng', 'error');
        }
      } catch (err) {
        showToast('Lỗi: ' + err.message, 'error');
      }
    });
  }

  const formRenewMonthly = document.getElementById('form-renew-monthly');
  if (formRenewMonthly) {
    formRenewMonthly.addEventListener('submit', handleRenewMonthlySubmit);
  }
});

async function deleteMonthlyTicket(monthlyId) {
  const item = monthlyCustomers.find(c => String(c.ma_ve_thang) === String(monthlyId));
  const custName = item ? item.ho_ten_khach_hang : '';
  if (!confirm(`Bạn có chắc chắn muốn xóa vé tháng của khách hàng "${custName}" khỏi hệ thống?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/tickets/monthly/${monthlyId}/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCsrfToken()
      }
    });

    const data = await res.json();
    if (res.ok) {
      showToast(data.message || 'Đã xóa vé tháng thành công!');
      const modalEl = document.getElementById('viewMonthlyTicketModal');
      if (modalEl) {
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();
      }
      await loadAllDataFromDatabase();
    } else {
      showToast(data.message || 'Lỗi khi xóa vé tháng', 'error');
    }
  } catch (err) {
    showToast('Lỗi xóa vé tháng: ' + err.message, 'error');
  }
}

function openRenewMonthlyModal(monthlyId) {
  const item = monthlyCustomers.find(c => String(c.ma_ve_thang) === String(monthlyId));
  if (!item) return;

  document.getElementById('renew-monthly-id').value = item.ma_ve_thang;
  document.getElementById('renew-cust-name').textContent = item.ho_ten_khach_hang;
  document.getElementById('renew-cust-info').textContent = `Biển số: ${item.bien_so_xe} • SĐT: ${item.so_dien_thoai || 'N/A'}`;
  
  const endFormatted = item.ngay_ket_thuc ? new Date(item.ngay_ket_thuc).toLocaleDateString('vi-VN') : '--';
  document.getElementById('renew-current-expiry').textContent = endFormatted;

  document.getElementById('renew-months-select').value = '1';
  document.getElementById('renew-new-date').value = '';

  const viewModalEl = document.getElementById('viewMonthlyTicketModal');
  if (viewModalEl) {
    const viewModal = bootstrap.Modal.getInstance(viewModalEl);
    if (viewModal) viewModal.hide();
  }

  const modalEl = document.getElementById('renewMonthlyModal');
  if (modalEl) {
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }
}

function updateRenewDatePreview() {
  // Clearing manual date input if dropdown changes
  const manualDate = document.getElementById('renew-new-date');
  if (manualDate) manualDate.value = '';
}

async function handleRenewMonthlySubmit(e) {
  if (e) e.preventDefault();
  const monthlyId = document.getElementById('renew-monthly-id').value;
  const months = document.getElementById('renew-months-select').value;
  const newDate = document.getElementById('renew-new-date').value;

  const payload = {};
  if (newDate) {
    payload.new_end_date = newDate;
  } else {
    payload.months = months;
  }

  try {
    const res = await fetch(`/api/tickets/monthly/${monthlyId}/renew/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      showToast(data.message || 'Gia hạn vé tháng thành công!');
      const modalEl = document.getElementById('renewMonthlyModal');
      if (modalEl) {
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();
      }
      await loadAllDataFromDatabase();
    } else {
      showToast(data.message || 'Lỗi gia hạn vé tháng', 'error');
    }
  } catch (err) {
    showToast('Lỗi gia hạn: ' + err.message, 'error');
  }
}

// ------------------------------------------------------------------------
// Excel Export Function
// ------------------------------------------------------------------------
function exportExcel(reportType = 'history') {
  showToast('Đang tạo và tải file Excel báo cáo...', 'info');
  window.location.href = `/api/reports/export/excel/?type=${reportType}`;
}

// ------------------------------------------------------------------------
// Chart.js Visualizations
// ------------------------------------------------------------------------
async function initAllCharts() {
  const chartDefaultColor = '#8e9fb5';
  Chart.defaults.color = chartDefaultColor;
  Chart.defaults.font.family = '"Plus Jakarta Sans", sans-serif';

  let chartData = null;
  try {
    const res = await fetch('/api/reports/charts/');
    if (res.ok) {
      chartData = await res.json();
    }
  } catch (e) {
    console.warn('Error fetching chart data:', e);
  }

  const hourlyLabels = chartData ? chartData.hourly.labels : ['6h', '7h', '8h', '9h', '10h', '11h', '12h', '13h', '14h', '15h', '16h', '17h', '18h', '19h', '20h', '21h'];
  // Khong dung du lieu gia mac dinh - chi ve khi co so lieu that tu CSDL
  const hourlyValues = chartData ? chartData.hourly.data : new Array(16).fill(0);

  const dailyLabels = chartData ? chartData.daily.labels : ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
  const dailyTraffic = chartData ? chartData.daily.traffic : new Array(7).fill(0);
  const dailyRev = chartData ? chartData.daily.revenue : new Array(7).fill(0);

  const ctpOverview = document.getElementById('overviewTrafficChart');
  if (ctpOverview) {
    if (overviewChartInst) overviewChartInst.destroy();
    overviewChartInst = new Chart(ctpOverview, {
      type: 'line',
      data: {
        labels: hourlyLabels,
        datasets: [{
          label: 'Lưu lượng xe',
          data: hourlyValues,
          borderColor: '#0095ff',
          backgroundColor: 'rgba(0, 149, 255, 0.15)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: '#0095ff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: 'rgba(31, 48, 80, 0.4)' }, beginAtZero: true }
        }
      }
    });
  }

  const ctpStat1 = document.getElementById('statDailyTrafficChart');
  if (ctpStat1) {
    if (dailyTrafficChartInst) dailyTrafficChartInst.destroy();
    dailyTrafficChartInst = new Chart(ctpStat1, {
      type: 'bar',
      data: {
        labels: dailyLabels,
        datasets: [{
          label: 'Lưu lượng xe',
          data: dailyTraffic,
          backgroundColor: '#0095ff',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: 'rgba(31, 48, 80, 0.4)' } }
        }
      }
    });
  }

  const ctpStat2 = document.getElementById('statDailyRevenueChart');
  if (ctpStat2) {
    if (dailyRevenueChartInst) dailyRevenueChartInst.destroy();
    dailyRevenueChartInst = new Chart(ctpStat2, {
      type: 'line',
      data: {
        labels: dailyLabels,
        datasets: [{
          label: 'Doanh thu (triệu đ)',
          data: dailyRev,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.15)',
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: 'rgba(31, 48, 80, 0.4)' } }
        }
      }
    });
  }

  const ctpStat3 = document.getElementById('statPeakHourChart');
  if (ctpStat3) {
    if (peakHourChartInst) peakHourChartInst.destroy();
    peakHourChartInst = new Chart(ctpStat3, {
      type: 'bar',
      data: {
        labels: hourlyLabels,
        datasets: [{
          label: 'Lượt xe',
          data: hourlyValues,
          backgroundColor: '#f59e0b',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: 'rgba(31, 48, 80, 0.4)' } }
        }
      }
    });
  }

  const ctpStat4 = document.getElementById('statZoneDoughnutChart');
  if (ctpStat4) {
    if (zoneDoughnutChartInst) zoneDoughnutChartInst.destroy();
    const zoneDist = chartData && chartData.zone_distribution ? chartData.zone_distribution.data : [0, 0, 0, 0];
    zoneDoughnutChartInst = new Chart(ctpStat4, {
      type: 'doughnut',
      data: {
        labels: ['Khu A', 'Khu B', 'Khu C', 'Khu D'],
        datasets: [{
          data: zoneDist,
          backgroundColor: ['#0095ff', '#10b981', '#8b5cf6', '#f59e0b'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        cutout: '70%'
      }
    });
  }
}

let tab7AiHistory = [];

function askAiPrompt(promptText) {
  document.getElementById('ai-input-text').value = promptText;
  sendAiMessage();
}

async function sendAiMessage() {
  const inputEl = document.getElementById('ai-input-text');
  const text = inputEl.value.trim();
  if (!text) return;

  const stream = document.getElementById('ai-chat-stream');
  
  // Hiển thị tin nhắn user
  stream.innerHTML += `
    <div class="d-flex justify-content-end mb-3">
      <div class="chat-bubble bubble-user">${text}</div>
    </div>`;

  tab7AiHistory.push({ role: 'user', content: text });
  inputEl.value = '';
  stream.scrollTop = stream.scrollHeight;

  // Hiển thị typing indicator
  const loadingId = 'ai-loading-' + Date.now();
  stream.innerHTML += `
    <div class="d-flex gap-3 mb-3" id="${loadingId}">
      <div class="role-icon-box icon-box-green" style="width:34px; height:34px; font-size:14px;">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="chat-bubble bubble-bot">
        <div class="d-flex gap-1 align-items-center py-1">
          <span class="spinner-grow spinner-grow-sm text-success" role="status"></span>
          <span class="small text-white opacity-75 ms-1">ParkAI đang phân tích CSDL & Gemini AI...</span>
        </div>
      </div>
    </div>`;
  stream.scrollTop = stream.scrollHeight;

  try {
    const res = await fetch('/api/ai/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      body: JSON.stringify({ message: text, history: tab7AiHistory.slice(-8) })
    });

    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) loadingEl.remove();

    const data = await res.json();
    if (data.reply) {
      tab7AiHistory.push({ role: 'assistant', content: data.reply });
      const formattedAnswer = data.reply
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');

      stream.innerHTML += `
        <div class="d-flex gap-3 mb-3">
          <div class="role-icon-box icon-box-green" style="width:34px; height:34px; font-size:14px;">
            <i class="fa-solid fa-robot"></i>
          </div>
          <div class="chat-bubble bubble-bot">${formattedAnswer}</div>
        </div>`;
    } else {
      stream.innerHTML += `
        <div class="d-flex gap-3 mb-3">
          <div class="role-icon-box icon-box-green" style="width:34px; height:34px; font-size:14px;">
            <i class="fa-solid fa-robot"></i>
          </div>
          <div class="chat-bubble bubble-bot text-danger">⚠️ ${data.error || 'Không thể lấy phản hồi từ AI'}</div>
        </div>`;
    }
  } catch (err) {
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) loadingEl.remove();

    stream.innerHTML += `
      <div class="d-flex gap-3 mb-3">
        <div class="role-icon-box icon-box-green" style="width:34px; height:34px; font-size:14px;">
          <i class="fa-solid fa-robot"></i>
        </div>
        <div class="chat-bubble bubble-bot text-danger">⚠️ Lỗi kết nối đến máy chủ AI Assistant: ${err.message}</div>
      </div>`;
  }
  stream.scrollTop = stream.scrollHeight;
}
