// === 全局变量 ===
let order_data = null;
let socket = null;

import { show_alert } from "../tools/show_alert.js";
import { io } from "socket.io-client";

export async function open_fahui_detail_modal(container, order) {
  // 清空容器
  container.innerHTML = "";

  // 设置背景样式
  Object.assign(container.style, {
    background:
      'url("/static/images/bg/buddha_bg4.svg") center / cover no-repeat',
    minHeight: "100vh",
    boxSizing: "border-box",
  });

  // 插入 detail 容器（用于渲染具体内容）
  const detailContainer = document.createElement("div");
  detailContainer.id = "fahui-detail-container";
  container.appendChild(detailContainer);

  // 初始化 socket
  init_order_socket();

  // 拉数据并渲染
  const data = await reload_order(order.id);
  if (data) {
    generate_fahui_detail();
  }
}

// ✅ 拉取订单数据（并处理未登录 + 未 owner 验证）
async function reload_order(order_id) {
  try {
    const res = await fetch(
      `/api/fahui_router/get_order_by_id?order_id=${order_id}`,
    );
    const result = await res.json();

    if (result.status !== "success") {
      show_alert("error", result.message || "订单加载失败");
      return null;
    }

    const order = result.data;

    // ✅ 如果未 login 且无 owner，触发验证码流程
    if (!order.login && !order.owner) {
      const verified = await get_twilio_success(order);
      if (verified?.status !== "success") {
        show_alert("error", "验证未通过");
        return null;
      }

      // 再次拉取订单（已验证身份）
      return await reload_order(order_id);
    }

    // ✅ 保存 order_data
    order_data = order;
    return order;
  } catch (err) {
    console.error("订单刷新失败", err);
    show_alert("error", "网络错误，无法刷新订单");
    return null;
  }
}

// ✅ 初始化 socket
function init_order_socket() {
  if (socket) socket.disconnect();
  socket = io();

  socket.on("order_update", async (data) => {
    if (!order_data) return;
    if (data.order_id === order_data.id) {
      console.log("监听到订单更新，自动刷新");
      const new_data = await reload_order(order_data.id);
      if (new_data) generate_fahui_detail();
    }
  });
}

// ✅ 渲染供奉登记详情（直接用 ID 选择容器）
function generate_fahui_detail() {
  const container = document.getElementById("fahui-detail-container");
  if (!container || !order_data) return;
  container.innerHTML = "";

  // 外层主容器，column布局
  const main_container = document.createElement("div");
  Object.assign(main_container.style, {
    maxWidth: "900px",
    margin: "auto",
    width: "100%",
    padding: "40px",
    boxSizing: "border-box",
    display: "block", // 不使用 flex，采用上下排布
  });

  // ✅ 顶部：基本信息卡片
  const baseCard = document.createElement("div");
  Object.assign(baseCard.style, {
    width: "100%",
    maxWidth: "680px",
    margin: "0 auto 32px auto",
    background: "rgba(255,255,255,0.98)",
    borderRadius: "20px",
    padding: "32px",
    fontSize: "16px",
    color: "#4a3b22",
    lineHeight: "1.8",
    boxShadow: "0 10px 40px rgba(0,0,0,0.08)",
  });

  const title = document.createElement("div");
  title.textContent = "供奉登记详情";
  Object.assign(title.style, {
    fontSize: "24px",
    fontWeight: "600",
    color: "#8b6f3d",
    textAlign: "center",
    marginBottom: "24px",
  });
  baseCard.appendChild(title);

  const table = document.createElement("table");
  Object.assign(table.style, {
    width: "100%",
    borderCollapse: "collapse",
  });

  const addRow = (label, value) => {
    const tr = document.createElement("tr");

    const td1 = document.createElement("td");
    td1.textContent = label;
    Object.assign(td1.style, {
      padding: "8px",
      color: "#666",
      whiteSpace: "nowrap",
    });

    const td2 = document.createElement("td");
    td2.textContent = value || "-";
    Object.assign(td2.style, {
      padding: "8px",
      fontWeight: "500",
      color: "#333",
    });

    tr.appendChild(td1);
    tr.appendChild(td2);
    table.appendChild(tr);
  };

  addRow("姓名", order_data.customer_name);
  addRow("电话", order_data.phone);
  addRow("状态", order_data.status);
  addRow("版本", order_data.version);
  addRow("报名时间", order_data.created_at);

  baseCard.appendChild(table);
  main_container.appendChild(baseCard);

  // ✅ 下方：牌位卡片 + 新增按钮，横向排布
  const card_container = document.createElement("div");
  Object.assign(card_container.style, {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: "20px",
    width: "100%",
    boxSizing: "border-box",
  });

  order_data.order_items.forEach((item) => {
    const itemCard = document.createElement("div");
    Object.assign(itemCard.style, {
      flex: "1 1 260px",
      minWidth: "240px",
      padding: "20px",
      background: "rgba(247,243,235,0.6)",
      borderRadius: "16px",
      boxSizing: "border-box",
    });

    const itemTitle = document.createElement("div");
    itemTitle.textContent = item.item_name;
    Object.assign(itemTitle.style, {
      fontWeight: "600",
      fontSize: "16px",
      marginBottom: "10px",
      color: "#6a532f",
    });
    itemCard.appendChild(itemTitle);

    const formData = item.item_form_data || {};
    for (const [key, entries] of Object.entries(formData)) {
      entries.forEach(({ val }) => {
        const field = document.createElement("div");
        field.textContent = `${key}：${val}`;
        Object.assign(field.style, {
          marginBottom: "6px",
          fontSize: "15px",
        });
        itemCard.appendChild(field);
      });
    }

    itemCard.onclick = () => console.log("牌位项目", item);
    card_container.appendChild(itemCard);
  });

  const addCard = document.createElement("div");
  Object.assign(addCard.style, {
    flex: "1 1 260px",
    minWidth: "240px",
    padding: "20px",
    border: "2px dashed #bca97a",
    borderRadius: "16px",
    textAlign: "center",
    cursor: "pointer",
    background: "rgba(255,255,255,0.6)",
    fontSize: "16px",
    color: "#7a5c33",
    transition: "all 0.3s ease",
  });

  addCard.textContent = "+ 新增一位牌位供奉";
  addCard.onmouseenter = () => {
    addCard.style.background = "rgba(250, 245, 230, 0.9)";
    addCard.style.transform = "scale(1.02)";
    addCard.style.boxShadow = "0 4px 18px rgba(0,0,0,0.1)";
  };
  addCard.onmouseleave = () => {
    addCard.style.background = "rgba(255,255,255,0.6)";
    addCard.style.transform = "scale(1)";
    addCard.style.boxShadow = "none";
  };
  addCard.onclick = () => {
    console.log("新增牌位");
    // open_create_item_modal(order_data);
  };

  card_container.appendChild(addCard);
  main_container.appendChild(card_container);

  container.appendChild(main_container);
}
