import { slideOutContainer } from "./slideOutContainer.js";
import { onHomeClick } from "./init_home.js";
import { open_fahui_detail_modal } from "../fahui/generate_fahui_detail.js";
import { get_twilio_success } from "../tools/get_twilio_success.js";

export function onRegisteredClick(container) {
  console.log("[home] 我曾经注册");

  slideOutContainer(container, "right", () => {
    // 这里写：渲染「我曾经注册」页面
    renderRegisteredSearch(container);
  });
}
function renderRegisteredSearch(container) {
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
    maxWidth: "100%",
    margin: "0 auto",
    padding: "48px 28px",
    height: "100vh",
    overflow: "scroll",

    /* ⭐ 多层背景：上层渐变 + 下层佛像 SVG */
    backgroundImage: `

    url("/static/images/bg/buddha_bg2.svg")
  `,
    backgroundRepeat: "no-repeat, no-repeat",
    backgroundPosition: "center center, center center",
    backgroundSize: "cover, 520px",
    opacity: "0",
    animation: "fadeInBackground 1.2s ease-out forwards",
    boxShadow:
      "0 24px 60px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.6)",

    backdropFilter: "blur(6px)",
  });

  /* =========================
     搜索区
  ========================= */
  const searchBar = document.createElement("div");
  Object.assign(searchBar.style, {
    display: "flex",
    gap: "14px",
    flexWrap: "wrap",
    marginBottom: "36px",
    alignItems: "center",
  });

  // version select
  const versionSelect = document.createElement("select");
  ["2025", "2024"].forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    versionSelect.appendChild(opt);
  });

  Object.assign(versionSelect.style, {
    padding: "12px 16px",
    borderRadius: "12px",
    border: "1px solid rgba(0,0,0,0.15)",
    backgroundColor: "rgba(255,255,255,0.9)",
    fontSize: "15px",
    color: "#5a4a30",
    outline: "none",
  });

  // search input
  const input = document.createElement("input");
  input.placeholder = "请输入姓名 / 电话 / 关键字";
  Object.assign(input.style, {
    flex: "1",
    padding: "14px 18px",
    borderRadius: "18px",
    border: "1px solid rgba(0,0,0,0.15)",
    fontSize: "16px",
    color: "#4a3b22",
    outline: "none",
    transition: "all 0.4s ease",
    backgroundColor: "rgba(255,255,255,0.95)",
  });
  input.onfocus = () => {
    input.style.boxShadow = "0 0 0 4px rgba(139,111,61,0.25)";
    input.style.borderColor = "#8b6f3d";
  };

  input.onblur = () => {
    input.style.boxShadow = "none";
    input.style.borderColor = "rgba(0,0,0,0.15)";
  };

  searchBar.appendChild(versionSelect);
  searchBar.appendChild(input);
  /* =========================
   Back Button
========================= */
  const backBtn = document.createElement("button");
  backBtn.textContent = "返回首页>>>";

  Object.assign(backBtn.style, {
    border: "none",
    background: "rgba(255,255,255,0.85)",
    color: "#5a4a30",
    fontSize: "14px",
    padding: "10px 18px",
    borderRadius: "999px",
    cursor: "pointer",
    boxShadow: "0 6px 16px rgba(0,0,0,0.12)",
    transition: "all 0.35s ease",
    backdropFilter: "blur(4px)",
  });

  backBtn.onmouseenter = () => {
    backBtn.style.transform = "translateX(-4px)";
    backBtn.style.boxShadow = "0 10px 24px rgba(0,0,0,0.18)";
  };

  backBtn.onmouseleave = () => {
    backBtn.style.transform = "translateX(0)";
    backBtn.style.boxShadow = "0 6px 16px rgba(0,0,0,0.12)";
  };

  backBtn.onclick = () => {
    slideOutContainer(container, "left", () => {
      onHomeClick(container, "register");
    });
  };

  /* =========================
     结果区
  ========================= */
  const list = document.createElement("div");
  Object.assign(list.style, {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
    gap: "24px",

    transition: "opacity 0.5s ease, transform 0.5s ease",
  });
  searchBar.appendChild(backBtn);
  wrapper.appendChild(searchBar);
  wrapper.appendChild(list);
  container.appendChild(wrapper);

  /* =========================
     搜索逻辑（防抖）
  ========================= */
  let timer = null;

  function triggerSearch() {
    const value = input.value.trim();

    // 空输入时可选择清空或不查
    if (!value) {
      list.innerHTML = `
            <div style="
            grid-column: 1 / -1;
            text-align: center;
            opacity: .6;
            font-size: 15px;
            padding: 40px 0;
            ">
            请静心输入姓名或电话，缘起自现
            </div>
        `;
      return;
    }

    // 结果区淡出
    list.style.opacity = "0";
    list.style.transform = "translateY(6px)";

    fetchOrders({
      version: versionSelect.value,
      value,
      page: 1,
      perPage: 10,
      listEl: list,
      container,
    });
  }

  input.oninput = () => {
    clearTimeout(timer);
    timer = setTimeout(triggerSearch, 400); // 👈 防抖 400ms
  };

  versionSelect.onchange = () => {
    if (input.value.trim()) {
      triggerSearch();
    }
  };
}

function fetchOrders({ version, value, page, perPage, listEl, container }) {
  const url = `/api/fahui_router/search?version=${version}&value=${encodeURIComponent(
    value,
  )}&page=${page}&per_page=${perPage}`;

  fetch(url)
    .then((res) => res.json())
    .then((res) => {
      if (res.status !== "success") {
        listEl.innerHTML = "查询失败";
        return;
      }

      renderOrderCards(res.data.items, listEl, container);

      // ✅ 渲染完成后淡入
      requestAnimationFrame(() => {
        listEl.style.opacity = "1";
        listEl.style.transform = "translateY(0)";
      });
    })
    .catch(() => {
      listEl.innerHTML = "网络错误";
      listEl.style.opacity = "1";
      listEl.style.transform = "translateY(0)";
    });
}

function renderOrderCards(items, container, base_container) {
  container.innerHTML = "";

  if (!items || items.length === 0) {
    container.textContent = "未查询到记录";
    return;
  }

  items.forEach((order, index) => {
    const card = document.createElement("div");

    Object.assign(card.style, {
      padding: "20px",
      borderRadius: "14px",
      backgroundColor: "#fff",
      boxShadow: "0 10px 24px rgba(0,0,0,0.12)",
      lineHeight: "1.7",
      cursor: "pointer",
      transition: "all 0.3s ease",

      // 初始动画状态
      opacity: "0",
      transform: "translateY(12px)",
    });

    card.innerHTML = `
      <div><strong>姓名：</strong>${order.customer_name || "-"}</div>
      <div><strong>对接人：</strong>${order.member_name || "-"}</div>
      <div><strong>电话：</strong>${order.phone || "-"}</div>
      <div><strong>状态：</strong>${order.status}</div>
      <div style="font-size:12px;opacity:.7;margin-top:8px;">
        报名时间：${order.created_at}
      </div>
    `;

    // ✅ hover 效果
    card.onmouseenter = () => {
      card.style.transform = "translateY(-2px) scale(1.02)";
      card.style.boxShadow = "0 16px 32px rgba(0,0,0,0.15)";
    };

    card.onmouseleave = () => {
      card.style.transform = "translateY(0)";
      card.style.boxShadow = "0 10px 24px rgba(0,0,0,0.12)";
    };

    // ✅ 点击动画 + 调用详情
    card.onclick = () => {
      card.style.transform = "scale(0.96)";
      setTimeout(async () => {
        card.style.transform = "scale(1)";
        const verifyResult = await get_twilio_success(order);
        if (!verifyResult || verifyResult.status !== "success") {
          throw new Error(verifyResult?.message || "短信验证未完成");
        }
      
        const verifiedOrder = verifyResult.order;

        open_fahui_detail_modal(base_container, verifiedOrder);
      }, 100);
    };

    container.appendChild(card);

    // ✅ 进场动画（每个延迟 100ms）
    setTimeout(() => {
      card.style.opacity = "1";
      card.style.transform = "translateY(0)";
    }, index * 100);
  });
}
