import { onAccountingClick } from "./account/init_account.js";
import { onFahuiDataClick } from "./fahui/init_fahui.js";
import { onHomeClick } from "./home/init_home.js";
import { onProfileClick } from "./profile/init_profile.js";
import { onUserControlClick } from "./user_control/init_user_control.js";
import { generate_login_modal } from "./login/generate_login_modal.js";
import { onScanBarcodeClick } from "./barcode/init_barcode.js";

console.log("init.js loaded");

const app = document.getElementById("app");
const mobileStyle = document.createElement("style");
mobileStyle.textContent = `
@media (max-width: 600px) {
  nav {
    position: fixed !important;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 999;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
    padding: 6px 0;
    height: 5vh;
  }

  #nav_select_list {
    overflow-x: auto;
    max-width: 100%;
    padding: 0 10px;
    gap: 10px;
    -webkit-overflow-scrolling: touch;
  }

  #nav_select_list > li > div {
    width: 40px !important;
    height: 40px !important;
  }

  #nav_select_list i {
    font-size: 18px !important;
  }

  #base_container {
    box-sizing: border-box;
    height: 95vh;
    overflow: scroll;
  }
}
`;
document.head.appendChild(mobileStyle);

/* =========================
   nav 容器
========================= */
const nav = document.createElement("nav");

Object.assign(nav.style, {
  overflow: "hidden",
  display: "flex",
  justifyContent: "center",
  width: "100%",
  backgroundColor: "#f7f3eb", // 宣纸色
});

/* =========================
   ul 容器
========================= */
const navUl = document.createElement("ul");
navUl.id = "nav_select_list";

Object.assign(navUl.style, {
  overflow: "hidden",
  display: "flex",
  gap: "10px",
  listStyle: "none",
  margin: "0",
  overflowX: "auto", // ⬅ 横向滚动支持
  WebkitOverflowScrolling: "touch",
  maxWidth: "100%",
});

nav.appendChild(navUl);

/* =========================
   base container（新增）
========================= */
const baseContainer = document.createElement("div");
baseContainer.id = "base_container";

Object.assign(baseContainer.style, {
  minHeight: "200px",
  textAlign: "center",
  color: "#6b5a3a",
  boxSizing: "border-box",
});

/* =========================
   挂载结构
========================= */
app.appendChild(nav);
app.appendChild(baseContainer);

/* =========================
   DOM 工具
========================= */

function createIcon(className) {
  const i = document.createElement("i");
  i.className = className;

  Object.assign(i.style, {
    fontSize: "clamp(16px, 4vw, 20px)",
    color: "#8b6f3d",
  });

  return i;
}

function createNavItem(iconClass, onClick, title, container) {
  const li = document.createElement("li");
  const btn = document.createElement("div");

  btn.title = title;
  btn.onclick = () => onClick(container);

  Object.assign(btn.style, {
    width: "clamp(36px, 10vw, 44px)",
    height: "clamp(36px, 10vw, 44px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "50%",
    cursor: "pointer",
    transition: "all 0.25s ease",
    backgroundColor: "rgba(139, 111, 61, 0.08)",
  });

  btn.appendChild(createIcon(iconClass));

  // hover（佛系）
  btn.onmouseenter = () => {
    Object.assign(btn.style, {
      backgroundColor: "rgba(139, 111, 61, 0.18)",
      transform: "scale(1.08)",
      boxShadow: "0 0 8px rgba(139, 111, 61, 0.25)",
    });
  };

  btn.onmouseleave = () => {
    Object.assign(btn.style, {
      backgroundColor: "rgba(139, 111, 61, 0.08)",
      transform: "scale(1)",
      boxShadow: "none",
    });
  };

  li.appendChild(btn);
  return li;
}

/* =========================
   渲染
========================= */

export function renderHome(container) {
  navUl.appendChild(
    createNavItem("fa-solid fa-house", onHomeClick, "首页", container),
  );
}

function renderAuthButtons(container) {
  navUl.appendChild(
    createNavItem(
      "fa-solid fa-file-lines",
      onFahuiDataClick,
      "法会数据",
      container,
    ),
  );

  navUl.appendChild(
    createNavItem("fa-solid fa-book", onAccountingClick, "做账", container),
  );

  navUl.appendChild(
    createNavItem("fa-solid fa-user", onProfileClick, "个人资料", container),
  );

  navUl.appendChild(
    createNavItem(
      "fa-solid fa-users-gear",
      onUserControlClick,
      "用户管理",
      container,
    ),
  );

  navUl.appendChild(
    createNavItem("fa-solid fa-qrcode", onScanBarcodeClick, "扫码", container),
  );
}

function renderLoginButton(container) {
  navUl.appendChild(
    createNavItem(
      "fa-solid fa-right-to-bracket",
      generate_login_modal,
      "登录",
      container,
    ),
  );
}

function getUrlParam(key) {
  const params = new URLSearchParams(window.location.search);
  return params.get(key);
}

async function handleRoute(container) {
  const page = getUrlParam("page");

  if (!page || page === "home") {
    onHomeClick(container);
    return;
  }

  if (page === "fahui") {
    try {
      const res = await fetch("/api/user_control/get_user_data", {
        method: "GET",
        credentials: "include",
      });

      if (!res.ok) {
        console.warn("[auth] http error:", res.status);
        generate_login_modal(container);
        return;
      }

      const data = await res.json();

      if (data.status === "success") {
        onFahuiDataClick(container);
      } else {
        generate_login_modal(container);
      }
    } catch (err) {
      console.warn("[auth] fetch failed:", err);
      generate_login_modal(container);
    }
    return;
  }

  // 👉 其它未知 page fallback 到首页
  onHomeClick(container);
}

export function updateNavbarAfterLogin(container) {
  console.log("[nav] updateNavbarAfterLogin");

  navUl.innerHTML = "";

  renderHome(container);
  renderAuthButtons(container);
}

/* =========================
   主流程
========================= */
async function fetchUserData(container) {
  navUl.innerHTML = "";
  renderHome(container);

  try {
    const res = await fetch("/api/user_control/get_user_data", {
      method: "GET",
      credentials: "include",
    });

    if (!res.ok) {
      console.warn("[auth] http error:", res.status);
      renderLoginButton(container);
      return;
    }

    const data = await res.json();

    if (data.status === "success") {
      renderAuthButtons(container);
    } else {
      renderLoginButton(container);
    }
  } catch (err) {
    console.warn("[auth] fetch failed:", err);
    renderLoginButton(container);
  } finally {
    handleRoute(container); // ✅ 用 URL 参数决定初始页面
  }
}

/* =========================
   启动
========================= */
fetchUserData(baseContainer);
