import { updateNavbarAfterLogin } from "../init.js";

export function generate_login_modal(container) {
  console.log("[modal] generate_login_modal");

  // 如果已存在 modal，先移除
  const oldModal = document.getElementById("login_modal_overlay");
  if (oldModal) {
    oldModal.remove();
  }

  /* =========================
     overlay
  ========================= */
  const overlay = document.createElement("div");
  overlay.id = "login_modal_overlay";

  Object.assign(overlay.style, {
    position: "fixed",
    top: "0",
    left: "0",
    width: "100%",
    height: "100vh",
    backgroundColor: "rgba(0, 0, 0, 0.35)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: "9999",
  });

  /* =========================
     modal
  ========================= */
  const modal = document.createElement("div");

  Object.assign(modal.style, {
    width: "320px",
    padding: "24px",
    backgroundColor: "#f7f3eb", // 宣纸色
    borderRadius: "14px",
    boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    color: "#5c4b2f",
  });

  /* =========================
     title
  ========================= */
  const title = document.createElement("div");
  title.textContent = "用户登录";

  Object.assign(title.style, {
    fontSize: "18px",
    fontWeight: "600",
    textAlign: "center",
    letterSpacing: "1px",
  });

  /* =========================
     username
  ========================= */
  const usernameInput = document.createElement("input");
  usernameInput.placeholder = "用户名";

  Object.assign(usernameInput.style, {
    padding: "10px 12px",
    borderRadius: "8px",
    border: "1px solid #d6c7a1",
    fontSize: "14px",
    outline: "none",
  });

  /* =========================
     password
  ========================= */
  const passwordInput = document.createElement("input");
  passwordInput.type = "password";
  passwordInput.placeholder = "密码";

  Object.assign(passwordInput.style, {
    padding: "10px 12px",
    borderRadius: "8px",
    border: "1px solid #d6c7a1",
    fontSize: "14px",
    outline: "none",
  });

  /* =========================
     login button
  ========================= */
  const loginBtn = document.createElement("button");
  loginBtn.textContent = "登录";

  Object.assign(loginBtn.style, {
    marginTop: "8px",
    padding: "10px",
    borderRadius: "10px",
    border: "none",
    backgroundColor: "#8b6f3d", // 檀金
    color: "#fff",
    fontSize: "15px",
    cursor: "pointer",
    transition: "all 0.25s ease",
  });
  loginBtn.onclick = async () => {
    const payload = {
      username: usernameInput.value,
      password: passwordInput.value,
    };

    console.log("[login] submit", payload);

    try {
      const res = await fetch("/api/user_control/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok || data.status !== "success") {
        console.warn("[login] failed", data);
        // 现在先 console.log，以后这里可以显示错误提示
        return;
      }

      console.log("[login] success", data.user);

      // ✅ 更新 navbar（关键）
      updateNavbarAfterLogin(container, data.user);

      // 关闭 modal
      overlay.remove();
    } catch (err) {
      console.error("[login] request error", err);
    }
  };

  loginBtn.onmouseenter = () => {
    loginBtn.style.backgroundColor = "#7a6136";
  };

  loginBtn.onmouseleave = () => {
    loginBtn.style.backgroundColor = "#8b6f3d";
  };

  /* =========================
     close btn
  ========================= */
  const closeBtn = document.createElement("div");
  closeBtn.innerHTML = "&times;";

  Object.assign(closeBtn.style, {
    position: "absolute",
    top: "12px",
    right: "16px",
    fontSize: "22px",
    cursor: "pointer",
    color: "#8b6f3d",
  });

  closeBtn.onclick = () => {
    overlay.remove();
  };

  /* =========================
     assemble
  ========================= */
  modal.appendChild(closeBtn);
  modal.appendChild(title);
  modal.appendChild(usernameInput);
  modal.appendChild(passwordInput);
  modal.appendChild(loginBtn);

  overlay.appendChild(modal);

  // 点击遮罩关闭
  overlay.onclick = (e) => {
    if (e.target === overlay) {
      overlay.remove();
    }
  };

  document.body.appendChild(overlay);
}
