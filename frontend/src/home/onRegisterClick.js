import { slideOutContainer } from "./slideOutContainer.js";
import { get_twilio_success } from "../tools/get_twilio_success.js";
import { open_fahui_detail_modal } from "../fahui/generate_fahui_detail.js";
import { show_alert } from "../tools/show_alert.js";

/* =========================
   localStorage helpers
========================= */
const STORAGE_KEY = "fahui_registrations";

function loadRegistrations() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveRegistrations(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

function createEmptyRecord() {
  return {
    id: crypto.randomUUID(),
    ic_name: "",
    email: "",
    nickname: "",
    referrer: "",
    phone: "",
    submitted: false,
    updated_at: Date.now(),
  };
}

/* =========================
   Entry
========================= */
export function onRegisterClick(container) {
  slideOutContainer(container, "left", () => {
    renderEntry(container);
  });
}

/* =========================
   Entry logic
========================= */
function renderEntry(container) {
  container.innerHTML = "";

  const records = loadRegistrations();

  if (records.length > 0) {
    renderSelectOrCreate(container, records);
  } else {
    const record = createEmptyRecord();
    saveRegistrations([record]);
    renderQuestionnaire(container, record);
  }
}

/* =========================
   Select / Create
========================= */
function renderSelectOrCreate(container, records) {
  container.innerHTML = "";

  const style = document.createElement("style");
  style.textContent = `
  @keyframes fadeInBackground {
    from { opacity: 0; }
    to { opacity: 1; }
  }`;
  document.head.appendChild(style);

  const wrapper = document.createElement("div");
  Object.assign(wrapper.style, {
    height: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background:
      'url("/static/images/bg/buddha_bg3.svg") center / cover no-repeat',
    opacity: "0",
    animation: "fadeInBackground 1.2s ease-out forwards",
  });
  const box = document.createElement("div");
  Object.assign(box.style, {
    width: "100%",
    maxWidth: "420px",
    background: "rgba(255,255,255,0.95)",
    borderRadius: "18px",
    padding: "28px",
    boxShadow: "0 20px 50px rgba(0,0,0,0.25)",
  });

  box.innerHTML = `<h3 style="margin-bottom:16px;">请选择报名人</h3>`;

  records.forEach((r) => {
    const item = document.createElement("div");
    item.textContent = `${r.ic_name || "未填写"} · ${r.phone || "-"}`;
    Object.assign(item.style, {
      padding: "12px",
      borderRadius: "12px",
      border: "1px solid #ccc",
      marginBottom: "10px",
      cursor: "pointer",
    });

    item.onclick = () => {
      // 如果已经填过，直接跳到最后确认页
      renderQuestionnaire(container, r, {
        startAtConfirm: true,
      });
    };

    box.appendChild(item);
  });

  const addBtn = document.createElement("div");
  addBtn.textContent = "+ 新增一位";
  Object.assign(addBtn.style, {
    marginTop: "16px",
    padding: "12px",
    textAlign: "center",
    borderRadius: "14px",
    background: "#8b6f3d",
    color: "#fff",
    cursor: "pointer",
  });

  addBtn.onclick = () => {
    const list = loadRegistrations();
    const record = createEmptyRecord();
    list.push(record);
    saveRegistrations(list);
    renderQuestionnaire(container, record);
  };

  box.appendChild(addBtn);
  wrapper.appendChild(box);
  container.appendChild(wrapper);
}

/* =========================
   Questionnaire
========================= */
function renderQuestionnaire(container, record, options = {}) {
  container.innerHTML = "";

  const formData = record;

  const wrapper = document.createElement("div");
  Object.assign(wrapper.style, {
    width: "100%",
    height: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background:
      'url("/static/images/bg/buddha_bg3.svg") center / cover no-repeat',
  });

  const modal = document.createElement("div");
  Object.assign(modal.style, {
    width: "100%",
    maxWidth: "420px",
    background: "rgba(255,255,255,0.92)",
    borderRadius: "20px",
    padding: "32px 28px",
    boxShadow: "0 20px 50px rgba(0,0,0,0.25)",
    textAlign: "center",
  });

  const title = document.createElement("div");
  Object.assign(title.style, {
    fontSize: "20px",
    marginBottom: "20px",
    color: "#5a4a30",
    fontWeight: "600",
  });

  const inputWrap = document.createElement("div");
  inputWrap.style.marginBottom = "28px";

  const nav = document.createElement("div");
  Object.assign(nav.style, {
    display: "flex",
    gap: "12px",
  });

  const btnPrev = document.createElement("button");
  btnPrev.textContent = "上一个";

  const btnNext = document.createElement("button");
  btnNext.textContent = "下一个";

  [btnPrev, btnNext].forEach((btn) => {
    Object.assign(btn.style, {
      flex: "1",
      padding: "12px",
      borderRadius: "14px",
      border: "none",
      cursor: "pointer",
      fontSize: "15px",
      background: "#8b6f3d",
      color: "#fff",
    });
  });

  nav.append(btnPrev, btnNext);
  const backBtn = document.createElement("div");
  backBtn.textContent = "← 返回选择报名人";

  Object.assign(backBtn.style, {
    textAlign: "left",
    fontSize: "14px",
    color: "#8b6f3d",
    cursor: "pointer",
    marginBottom: "12px",
  });

  backBtn.onclick = () => {
    const records = loadRegistrations();
    renderSelectOrCreate(container, records);
  };

  modal.appendChild(backBtn);
  modal.appendChild(title);
  modal.appendChild(inputWrap);
  modal.appendChild(nav);

  wrapper.appendChild(modal);
  container.appendChild(wrapper);

  const questions = [
    {
      key: "ic_name",
      text: "1. 请您提供 IC 名字",
      render: () => textInput("例如：LOW YI HONG", "ic_name"),
    },
    {
      key: "email",
      text: "2. 可以输入您的邮箱（可留空）",
      render: () => textInput("example@email.com", "email"),
    },
    {
      key: "nickname",
      text: "3. 如何称呼您？",
      render: () => textInput("您的称呼", "nickname"),
    },
    {
      key: "referrer",
      text: "4. 请问你是谁介绍的？",
      render: () =>
        selectInput(["王玉芬老师", "韩雪恩学姐", "刘佳颖学姐"], "referrer"),
    },
    {
      key: "phone",
      text: "5. 请您提供您的手机号码",
      render: () => textInput("例如：0123456789", "phone"),
    },
    { key: "confirm", text: "6. 请确认您的信息", render: renderConfirm },
  ];

  let current = options.startAtConfirm ? questions.length - 1 : 0;

  function persist() {
    const list = loadRegistrations().map((r) =>
      r.id === formData.id ? { ...formData, updated_at: Date.now() } : r,
    );
    saveRegistrations(list);
  }

  function renderStep() {
    const q = questions[current];

    /* =====================
     标题动画
  ===================== */
    title.style.opacity = "0";
    title.style.transform = "translateY(-6px)";

    setTimeout(() => {
      title.textContent = q.text;
      title.style.transition = "opacity 0.35s ease, transform 0.35s ease";
      title.style.opacity = "1";
      title.style.transform = "translateY(0)";
    }, 120);

    /* =====================
     输入区：高度动画（终极稳定版）
  ===================== */

    // 1️⃣ 记录旧高度
    const oldHeight = inputWrap.offsetHeight;

    // 2️⃣ 锁定当前高度
    inputWrap.style.height = oldHeight + "px";
    inputWrap.style.overflow = "hidden";

    // 3️⃣ 淡出旧内容
    const oldContent = inputWrap.firstChild;
    if (oldContent) {
      oldContent.style.transition = "opacity 0.25s ease, transform 0.25s ease";
      oldContent.style.opacity = "0";
      oldContent.style.transform = "translateY(-8px)";
    }

    setTimeout(
      () => {
        // 4️⃣ 替换内容
        inputWrap.innerHTML = "";

        const el = q.render();
        el.style.opacity = "0";
        el.style.transform = "translateY(10px)";
        el.style.transition = "opacity 0.35s ease, transform 0.35s ease";

        inputWrap.appendChild(el);

        // 5️⃣ 计算新高度
        const newHeight = inputWrap.scrollHeight;

        // ⭐ 关键：强制 reflow（否则缩小不会动画）
        inputWrap.offsetHeight;

        // 6️⃣ 高度动画（放大 & 缩小都生效）
        inputWrap.style.transition = "height 0.35s ease";
        inputWrap.style.height = newHeight + "px";

        // 7️⃣ 内容淡入
        requestAnimationFrame(() => {
          el.style.opacity = "1";
          el.style.transform = "translateY(0)";
        });

        // 8️⃣ 动画结束后恢复 auto
        setTimeout(() => {
          inputWrap.style.height = "auto";
          inputWrap.style.overflow = "visible";
        }, 360);
      },
      oldContent ? 180 : 0,
    );

    btnPrev.style.visibility = current === 0 ? "hidden" : "visible";

    const isLast = current === questions.length - 1;

    btnPrev.style.visibility = current === 0 ? "hidden" : "visible";
    btnNext.textContent = isLast ? "提交" : "下一个";

    if (isLast) {
      // ⭐ 提交态（成功绿）
      Object.assign(btnNext.style, {
        backgroundColor: "#4caf50",
        boxShadow: "0 6px 16px rgba(76,175,80,0.4)",
        cursor: "pointer",
        transform: "scale(0.97)",
        transition: "all 0.35s ease",
      });
    } else {
      // ⭐ 普通态（原本颜色）
      Object.assign(btnNext.style, {
        backgroundColor: "#8b6f3d",
        boxShadow: "0 10px 24px rgba(0,0,0,0.25)",
        cursor: "pointer",
        transform: "scale(1)",
        transition: "all 0.35s ease",
      });
    }
  }

  function textInput(placeholder, key) {
    const input = document.createElement("input");
    input.value = formData[key] || "";
    input.placeholder = placeholder;

    Object.assign(input.style, {
      width: "100%",
      padding: "14px 0px",
      textAlign: "center",
      borderRadius: "14px",
      border: "1px solid rgba(0,0,0,0.2)",
      fontSize: "16px",
    });

    const errorText = document.createElement("div");
    Object.assign(errorText.style, {
      marginTop: "6px",
      fontSize: "13px",
      color: "#d9534f",
      minHeight: "18px", // 保证占位不抖动
    });

    const wrapper = document.createElement("div");
    wrapper.appendChild(input);
    wrapper.appendChild(errorText);

    input.oninput = () => {
      const value = input.value.trim();
      formData[key] = value;
      persist();

      // 校验手机号格式
      if (key === "phone") {
        const formatted = formatPhoneNumber(value);
        if (!formatted) {
          errorText.textContent = "手机号格式无效，请检查";
          input.style.borderColor = "#d9534f";
        } else {
          errorText.textContent = "";
          input.style.borderColor = "rgba(0,0,0,0.2)";
        }
      }
    };

    return wrapper;
  }

  function selectInput(options, key) {
    const wrap = document.createElement("div");
    wrap.style.display = "flex";
    wrap.style.flexDirection = "column";
    wrap.style.gap = "12px";

    options.forEach((opt) => {
      const btn = document.createElement("div");
      btn.textContent = opt;

      Object.assign(btn.style, {
        padding: "12px",
        borderRadius: "12px",
        cursor: "pointer",
        border: "1px solid rgba(0,0,0,0.2)",
        background: formData[key] === opt ? "#8b6f3d" : "#fff",
        color: formData[key] === opt ? "#fff" : "#333",
      });

      btn.onclick = () => {
        formData[key] = opt;
        persist();
        renderStep();
      };

      wrap.appendChild(btn);
    });

    return wrap;
  }

  function renderConfirm() {
    const box = document.createElement("div");
    box.style.textAlign = "left";
    box.style.fontSize = "14px";
    box.style.lineHeight = "1.8";

    const formattedPhone = formatPhoneNumber(formData.phone);

    box.innerHTML = `
    <div>IC 名字：${formData.ic_name || "-"}</div>
    <div>邮箱：${formData.email || "-"}</div>
    <div>称呼：${formData.nickname || "-"}</div>
    <div>介绍人：${formData.referrer || "-"}</div>
    ${formattedPhone ? `<div>手机：${formattedPhone}</div>` : ""}
  `;

    return box;
  }

  btnPrev.onclick = () => {
    if (current > 0) {
      current--;
      renderStep();
    }
  };

  btnNext.onclick = async () => {
    if (current === questions.length - 1) {
      if (btnNext.disabled) return;

      // ⭐ 校验手机号码格式
      const formattedPhone = formatPhoneNumber(formData.phone);
      if (!formattedPhone) {
        show_alert("error","请填写有效的手机号码");
        return;
      }

      // ✅ 用格式化后的号码进行提交
      formData.phone = formattedPhone;

      // ===== loading 状态 =====
      btnNext.textContent = "提交中…";
      btnNext.disabled = true;
      Object.assign(btnNext.style, {
        backgroundColor: "#bfa76a",
        boxShadow: "0 4px 12px rgba(0,0,0,0.25)",
        transform: "scale(0.96)",
        cursor: "wait",
        transition: "all 0.3s ease",
      });

      try {
        const res = await fetch("/api/fahui_router/new_customer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: formData.ic_name,
            customer_name: formData.nickname,
            member_name: formData.referrer,
            email: formData.email,
            phone: formData.phone, // 已格式化
          }),
        });

        const result = await res.json();
        if (!result.success) throw new Error(result.error || "提交失败");

        const order = result.order;

        const verifyResult = await get_twilio_success(order);
        if (!verifyResult || verifyResult.status !== "success") {
          throw new Error(verifyResult?.message || "短信验证未完成");
        }

        const verifiedOrder = verifyResult.order;

        btnNext.textContent = "已提交";
        Object.assign(btnNext.style, {
          backgroundColor: "#4caf50",
          boxShadow: "0 6px 16px rgba(76,175,80,0.45)",
          transform: "scale(1)",
          cursor: "default",
        });

        setTimeout(() => {
          open_fahui_detail_modal(container, verifiedOrder);
        }, 300);
      } catch (err) {
        console.error(err);
        btnNext.textContent = "提交失败，重试";
        btnNext.disabled = false;
        Object.assign(btnNext.style, {
          backgroundColor: "#d9534f",
          boxShadow: "0 6px 16px rgba(217,83,79,0.45)",
          transform: "scale(1)",
          cursor: "pointer",
        });
      }

      return;
    }

    // ===== 普通下一题 =====
    current++;
    renderStep();
  };

  renderStep();
}

function formatPhoneNumber(rawPhone) {
  if (!rawPhone) return null;

  // 去掉空格、连字符、括号等，但保留开头的 +
  const phone = rawPhone.replace(/[^\d+]/g, "").trim();

  let normalized = "";

  if (phone.startsWith("+60")) {
    normalized = phone;
  } else if (phone.startsWith("60")) {
    normalized = "+" + phone;
  } else if (phone.startsWith("0")) {
    normalized = "+60" + phone.slice(1);
  } else if (phone.startsWith("1")) {
    normalized = "+60" + phone;
  } else {
    return null;
  }

  // 提取纯数字部分（去掉 + 和 60 前缀）
  const digits = normalized.replace("+60", "");

  // 至少 8 位数字（不包含国家码）
  if (digits.length < 8) return null;

  return normalized;
}
