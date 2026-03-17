import "./styles.css";
import { mountHomePage } from "./home/page.js";
import { mountSearchPage } from "./search/page.js";
import { mountFahuiPage } from "./fahui/page.js";
import { mountFahuiDetailPage } from "./fahui/detailPage.js";
import { connectFahuiRealtime } from "./state/fahuiDataStore.js";

const MODE_KEY = "fahui_frontend_mode";
const MODE_GUEST = "guest";
const MODE_ADMIN = "admin";
const LOGO_SRC = "/static/images/logo/logo.png";

const USER_INFO_API = "/api/user_control/get_user_data";
const LOGIN_API = "/api/user_control/login";
const LOGOUT_API = "/api/user_control/logout";

const app = document.getElementById("app");

const modeConfig = {
  [MODE_GUEST]: {
    label: "游客模式",
    subtitle: "浏览公开入口",
    navItems: [
      { key: "home", icon: "fa-solid fa-house", title: "首页" },
      { key: "search", icon: "fa-solid fa-magnifying-glass", title: "查找订单" },
      { key: "payment", icon: "fa-solid fa-file-invoice", title: "付款与凭证" },
      { key: "scan", icon: "fa-solid fa-qrcode", title: "扫码入口" },
    ],
  },
  [MODE_ADMIN]: {
    label: "管理员模式",
    subtitle: "运营与管理",
    navItems: [
      { key: "fahui_data", icon: "fa-solid fa-file-lines", title: "法会数据" },
      { key: "accounting", icon: "fa-solid fa-book", title: "做账 / 支付" },
      { key: "scan", icon: "fa-solid fa-qrcode", title: "扫码工具" },
      { key: "user_control", icon: "fa-solid fa-users-gear", title: "用户管理" },
    ],
  },
};

const state = {
  mode: MODE_GUEST,
  page: "home",
  user: null,
  loginOpen: false,
  loginError: "",
  loginLoading: false,
  pageParams: {},
};

let unmountCurrentPage = null;

function getStoredMode() {
  const saved = window.localStorage.getItem(MODE_KEY);
  return saved === MODE_ADMIN ? MODE_ADMIN : MODE_GUEST;
}

function setStoredMode(mode) {
  window.localStorage.setItem(MODE_KEY, mode);
}

function toggleMode(mode) {
  return mode === MODE_ADMIN ? MODE_GUEST : MODE_ADMIN;
}

async function fetchCurrentUser() {
  try {
    const response = await fetch(USER_INFO_API, {
      credentials: "include",
    });
    if (!response.ok) {
      return null;
    }

    const payload = await response.json();
    if (payload?.status === "success") {
      return payload.user ?? null;
    }

    return null;
  } catch (error) {
    return null;
  }
}

async function canEnterAdminMode() {
  const user = await fetchCurrentUser();
  state.user = user;
  return Boolean(user);
}

function createNavPill(item) {
  return `
    <button
      class="nav-pill ${state.page === item.key ? "active" : ""}"
      type="button"
      data-action="set-page"
      data-page="${item.key}"
    >
      <i class="${item.icon}"></i>
      <span>${item.title}</span>
    </button>
  `;
}

function createDesktopAuth() {
  if (state.user) {
    return `
      <div class="user-chip">
        <i class="fa-solid fa-user-check"></i>
        <span>${state.user.display_name || state.user.username || "已登录"}</span>
      </div>
      <button class="mode-switch secondary" type="button" data-action="logout">
        登出
      </button>
    `;
  }

  return `
    <button class="mode-switch secondary" type="button" data-action="open-login">
      登录
    </button>
  `;
}

function createMobileAuth() {
  if (state.user) {
    return `
      <button class="mode-switch secondary" type="button" data-action="logout">
        登出
      </button>
    `;
  }

  return `
    <button class="mode-switch secondary" type="button" data-action="open-login">
      登录
    </button>
  `;
}

function createLoginModal() {
  if (!state.loginOpen) {
    return "";
  }

  return `
    <div class="modal-backdrop" data-action="close-login">
      <div class="login-modal" role="dialog" aria-modal="true" aria-label="登录">
        <div class="login-modal-head">
          <h2>管理员登录</h2>
          <button class="icon-btn" type="button" data-action="close-login" aria-label="关闭">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
        <form class="login-form" data-action="submit-login">
          <label class="field">
            <span>用户名</span>
            <input name="username" type="text" autocomplete="username" required />
          </label>
          <label class="field">
            <span>密码</span>
            <input name="password" type="password" autocomplete="current-password" required />
          </label>
          ${state.loginError ? `<div class="form-error">${state.loginError}</div>` : ""}
          <button class="submit-btn" type="submit" ${state.loginLoading ? "disabled" : ""}>
            ${state.loginLoading ? "登录中..." : "登录"}
          </button>
        </form>
      </div>
    </div>
  `;
}

function render() {
  const config = modeConfig[state.mode];
  const nextMode = toggleMode(state.mode);
  const nextLabel = modeConfig[nextMode].label;

  app.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="topbar-inner">
          <div class="brand">
            <img class="brand-logo" src="${LOGO_SRC}" alt="地南佛学会 logo" />
            <div class="brand-copy">
              <h1 class="brand-title">地南佛学会</h1>
              <p class="brand-subtitle">法会系统</p>
            </div>
          </div>
          <div class="nav-actions">
            <div class="mode-chip">
              <i class="fa-solid fa-circle-dot"></i>
              <span>${config.label}</span>
            </div>
            ${createDesktopAuth()}
            <button class="mode-switch" type="button" data-action="toggle-mode">
              切换到${nextLabel}
            </button>
          </div>
        </div>
      </header>

      <main class="page">
      <section class="nav-grid">
          ${state.page === "fahui_detail" ? "" : config.navItems.map(createNavPill).join("")}
        </section>
        <section class="content-slot" data-role="content-slot"></section>
      </main>

      <div class="mobile-nav">
        <div class="mobile-mode">
          <strong>${config.label}</strong>
          <span>${config.subtitle}</span>
        </div>
        <div class="mobile-actions">
          ${createMobileAuth()}
          <button class="mode-switch" type="button" data-action="toggle-mode">
            切换
          </button>
        </div>
      </div>

      ${createLoginModal()}
    </div>
  `;

  bindEvents();
  mountCurrentPage();
}

function openLoginModal() {
  state.loginOpen = true;
  state.loginError = "";
  render();
}

function closeLoginModal() {
  state.loginOpen = false;
  state.loginError = "";
  state.loginLoading = false;
  render();
}

async function handleModeToggle() {
  const updatedMode = toggleMode(state.mode);
  if (updatedMode === MODE_ADMIN) {
    const allowed = await canEnterAdminMode();
    if (!allowed) {
      openLoginModal();
      return;
    }
  }

  state.mode = updatedMode;
  state.page = updatedMode === MODE_ADMIN ? "fahui_data" : "home";
  setStoredMode(updatedMode);
  render();
}

async function handleLoginSubmit(form) {
  const formData = new FormData(form);
  const username = String(formData.get("username") || "").trim();
  const password = String(formData.get("password") || "");

  if (!username || !password) {
    state.loginError = "请输入用户名和密码";
    render();
    return;
  }

  state.loginLoading = true;
  state.loginError = "";
  render();

  try {
    const response = await fetch(LOGIN_API, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload?.status !== "success") {
      state.loginLoading = false;
      state.loginError = payload?.message || "登录失败";
      render();
      return;
    }

    state.user = payload.user ?? (await fetchCurrentUser());
    state.mode = MODE_ADMIN;
    state.page = "fahui_data";
    state.loginOpen = false;
    state.loginLoading = false;
    state.loginError = "";
    setStoredMode(MODE_ADMIN);
    render();
  } catch (error) {
    state.loginLoading = false;
    state.loginError = "网络错误，请稍后重试";
    render();
  }
}

async function handleLogout() {
  try {
    await fetch(LOGOUT_API, {
      method: "GET",
      credentials: "include",
    });
  } catch (error) {
    // Keep UI reset even if transport fails.
  }

  state.user = null;
  state.mode = MODE_GUEST;
  state.page = "home";
  state.loginOpen = false;
  state.loginError = "";
  state.loginLoading = false;
  setStoredMode(MODE_GUEST);
  render();
}

function bindEvents() {
  app.querySelectorAll('[data-action="toggle-mode"]').forEach((button) => {
    button.addEventListener("click", handleModeToggle);
  });

  app.querySelectorAll('[data-action="set-page"]').forEach((button) => {
    button.addEventListener("click", () => {
      state.page = button.dataset.page || "home";
      state.pageParams = {};
      render();
    });
  });

  app.querySelectorAll('[data-action="open-login"]').forEach((button) => {
    button.addEventListener("click", openLoginModal);
  });

  app.querySelectorAll('[data-action="logout"]').forEach((button) => {
    button.addEventListener("click", handleLogout);
  });

  app.querySelectorAll('[data-action="close-login"]').forEach((element) => {
    element.addEventListener("click", (event) => {
      if (event.target === element) {
        closeLoginModal();
      }
    });
  });

  const form = app.querySelector('[data-action="submit-login"]');
  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      handleLoginSubmit(form);
    });
  }
}

function mountCurrentPage() {
  const container = app.querySelector('[data-role="content-slot"]');
  if (!container) {
    return;
  }

  if (typeof unmountCurrentPage === "function") {
    unmountCurrentPage();
    unmountCurrentPage = null;
  }

  if (state.mode === MODE_ADMIN && state.page === "fahui_data") {
    unmountCurrentPage = mountFahuiPage(container);
    return;
  }

  if (state.page === "fahui_detail") {
    unmountCurrentPage = mountFahuiDetailPage(container, {
      orderId: state.pageParams.orderId,
      onBack: () => {
        state.page = state.pageParams.returnPage || (state.mode === MODE_ADMIN ? "fahui_data" : "search");
        state.pageParams = {};
        render();
      },
    });
    return;
  }

  if (state.mode === MODE_GUEST && state.page === "home") {
    unmountCurrentPage = mountHomePage(container);
    return;
  }

  if (state.mode === MODE_GUEST && state.page === "search") {
    unmountCurrentPage = mountSearchPage(container);
    return;
  }

  container.innerHTML = "";
}

async function bootstrap() {
  state.user = await fetchCurrentUser();
  connectFahuiRealtime();
  state.mode = getStoredMode();
  state.page = state.mode === MODE_ADMIN ? "fahui_data" : "home";

  if (state.mode === MODE_ADMIN && !state.user) {
    state.mode = MODE_GUEST;
    state.page = "home";
    setStoredMode(MODE_GUEST);
  }

  render();
}

window.addEventListener("fahui:navigate", (event) => {
  const detail = event.detail || {};
  state.page = detail.page || state.page;
  state.pageParams = detail.params || {};
  render();
});

bootstrap();
