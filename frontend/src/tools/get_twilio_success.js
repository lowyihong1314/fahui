import { show_alert } from "./show_alert.js";
import { getMaxZIndex } from "./getMaxZIndex.js";

export async function get_twilio_success(order) {
  return new Promise(async (resolve) => {
    let resolved = false;
    if (order.login === true) {
      show_alert("success", "已登录，无需验证");
      resolve({
        status: "success",
        order,
        message: "已登录，无需验证",
      });
      return;
    }

    // ===== UI Setup =====
    const overlay = document.createElement("div");
    Object.assign(overlay.style, {
      position: "fixed",
      inset: "0",
      background: "rgba(0,0,0,0.55)",
      zIndex: getMaxZIndex() + 1,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      backdropFilter: "blur(4px)",
    });

    const modal = document.createElement("div");
    Object.assign(modal.style, {
      width: "100%",
      maxWidth: "420px",
      background: "rgba(255,255,255,0.96)",
      borderRadius: "22px",
      padding: "32px 28px",
      textAlign: "center",
      boxShadow: "0 24px 60px rgba(0,0,0,0.35)",
    });

    const shield = document.createElement("div");
    shield.textContent = "🛡️";
    shield.style.fontSize = "42px";

    const title = document.createElement("div");
    title.textContent = "手机验证";
    Object.assign(title.style, {
      fontSize: "20px",
      fontWeight: "600",
      margin: "10px 0",
    });

    const msg = document.createElement("div");
    msg.textContent = `我们已经发送验证码给 ${order.phone}`;
    Object.assign(msg.style, {
      fontSize: "14px",
      opacity: "0.75",
      marginBottom: "18px",
    });

    // ===== OTP Input =====
    const input = document.createElement("input");
    input.placeholder = "请输入验证码";
    Object.assign(input.style, {
      width: "100%",
      padding: "14px",
      borderRadius: "14px",
      border: "1px solid rgba(0,0,0,0.2)",
      textAlign: "center",
      letterSpacing: "4px",
      marginBottom: "18px",
      fontSize: "16px",
    });

    // ===== Verify Button =====
    const btn = document.createElement("button");
    btn.textContent = "验证";
    Object.assign(btn.style, {
      width: "100%",
      padding: "14px",
      borderRadius: "16px",
      border: "none",
      backgroundColor: "#8b6f3d",
      color: "#fff",
      fontSize: "16px",
      cursor: "pointer",
    });

    // ===== Resend =====
    const resendWrapper = document.createElement("div");
    resendWrapper.style.marginTop = "16px";

    const resendBtn = document.createElement("button");
    resendBtn.textContent = "我没有收到验证码";
    Object.assign(resendBtn.style, {
      display: "none",
      fontSize: "13px",
      color: "#8b6f3d",
      background: "none",
      border: "none",
      cursor: "pointer",
      textDecoration: "underline",
      padding: 0,
    });

    resendWrapper.appendChild(resendBtn);

    modal.append(shield, title, msg, input, btn, resendWrapper);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    console.log(order);

    // ===== 首次发送 OTP（或 cookie 短路）=====
    if (!order.login) {
      console.log("send otp no login");
      const sendResult = await sendOTP(order.id, order.phone);

      if (sendResult.status === "cookie_true") {
        finishSuccess();
        return;
      }
    }

    // 3 分钟后显示补发
    setTimeout(() => {
      resendBtn.style.display = "inline";
    }, 180000);

    resendBtn.onclick = async () => {
      resendBtn.disabled = true;
      resendBtn.textContent = "已重新发送";
      resendBtn.style.opacity = "0.6";

      const resendResult = await sendOTP(order.id, order.phone);
      if (resendResult.status === "cookie_true") {
        finishSuccess();
        return;
      }

      setTimeout(() => {
        resendBtn.disabled = false;
        resendBtn.textContent = "我没有收到验证码";
        resendBtn.style.opacity = "1";
      }, 180000);
    };

    // ===== Verify OTP =====
    btn.onclick = async () => {
      if (resolved) return;
      const otp = input.value.trim();

      if (!otp) {
        show_alert("error", "请输入验证码");
        return;
      }

      btn.disabled = true;
      btn.textContent = "验证中...";

      try {
        const res = await fetch("/api/twilio/test_verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ otp, phone: order.phone }),
        });

        const result = await res.json();

        if (result.status === "success") {
          finishSuccess();
        } else {
          show_alert("error", result.message || "验证码错误");
          btn.disabled = false;
          btn.textContent = "验证";
        }
      } catch {
        show_alert("error", "网络错误");
        btn.disabled = false;
        btn.textContent = "验证";
      }
    };

    // ===== success helper =====
    function finishSuccess() {
      if (resolved) return;
      resolved = true;
      overlay.remove();
      show_alert("success", "验证成功");
      resolve({
        status: "success",
        order,
        message: "验证成功",
      });
    }
  });
}

// =====================================================
// OTP sender
// =====================================================
function sendOTP(order_id, phone) {
  return new Promise(async (resolve) => {
    try {
      // 发送验证码（改成 GET）
      const res = await fetch(
        `/api/twilio/test_send_otp?order_id=${order_id}`,
        {
          method: "GET",
          credentials: "include", // ✅ 关键，确保 cookie 可用
        },
      );

      const result = await res.json();

      if (result.status === "cookie_true") {
        resolve({ status: "cookie_true" });
        return;
      }

      if (result.status === "success") {
        show_alert("success", "验证码已发送");
        resolve({ status: "success" });
        return;
      }

      show_alert("error", result.message || "发送失败");
      resolve({ status: "fail" });
    } catch (e) {
      console.error("sendOTP error:", e);
      show_alert("error", "网络异常");
      resolve({ status: "fail" });
    }
  });
}
