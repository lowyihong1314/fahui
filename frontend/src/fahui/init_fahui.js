import { slideOutContainer } from "../home/slideOutContainer.js";
import { open_fahui_detail_modal } from "./generate_fahui_detail.js";
import { updateUrlParam } from "../tools/updateUrlParam.js";

export function onFahuiDataClick(container) {
  console.log("[nav] Fahui Data clicked");
  updateUrlParam("page", "fahui");

  slideOutContainer(container, "right", () => {
    renderFahuiDataPage(container);
  });
}

function renderFahuiDataPage(container) {
  container.innerHTML = "";

  const wrapper = document.createElement("div");
  Object.assign(wrapper.style, {
    padding: "40px 28px",
    height: "100vh",
    overflowY: "auto",
    background:
      'url("/static/images/bg/buddha_bg2.svg") center / cover no-repeat',
    color: "#4a3b22",
  });

  // ===== 搜索区 =====
  const searchWrap = document.createElement("div");
  Object.assign(searchWrap.style, {
    marginBottom: "24px",
    display: "flex",
    gap: "16px",
    flexWrap: "wrap",
  });

  const versionSelect = document.createElement("select");
  ["2025", "2024"].forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    versionSelect.appendChild(opt);
  });
  Object.assign(versionSelect.style, {
    padding: "10px 14px",
    borderRadius: "10px",
    fontSize: "15px",
  });

  const input = document.createElement("input");
  input.placeholder = "请输入姓名 / 电话 / 项目";
  Object.assign(input.style, {
    flex: "1",
    minWidth: "220px",
    padding: "10px 16px",
    borderRadius: "10px",
    border: "1px solid #aaa",
    fontSize: "15px",
  });

  searchWrap.appendChild(versionSelect);
  searchWrap.appendChild(input);

  const pageBtnContainer = document.createElement("div");
  Object.assign(pageBtnContainer.style, {
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
    justifyContent: "center",
    marginBottom: "20px",
  });

  // ===== 表格区 =====
  const table = document.createElement("table");
  Object.assign(table.style, {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "15px",
    background: "#fff",
    boxShadow: "0 10px 24px rgba(0,0,0,0.08)",
  });

  const thead = document.createElement("thead");
  thead.innerHTML = `
    <tr style="background:#f1ede4;">
      <th style="padding:12px;">姓名</th>
      <th>电话</th>
      <th>项目</th>
      <th>状态</th>
      <th>报名时间</th>
    </tr>
  `;
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  table.appendChild(tbody);

  // 插入结构
  wrapper.appendChild(searchWrap);
  wrapper.appendChild(pageBtnContainer);
  wrapper.appendChild(table);
  container.appendChild(wrapper);

  // ===== 搜索逻辑 =====
  let timer = null;
  input.oninput = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      triggerSearch({
        input,
        versionSelect,
        tbody,
        pageBtnContainer,
        container,
      });
    }, 400);
  };

  versionSelect.onchange = () => {
    triggerSearch({ input, versionSelect, tbody, pageBtnContainer, container });
  };

  // 首次加载
  triggerSearch({ input, versionSelect, tbody, pageBtnContainer, container });
}

function triggerSearch({
  page = 1,
  input,
  versionSelect,
  tbody,
  pageBtnContainer,
  container,
}) {
  const keyword = input.value.trim();
  const version = versionSelect.value;

  const url = `/api/fahui_router/search?version=${version}&value=${encodeURIComponent(
    keyword,
  )}&page=${page}&per_page=20`;

  tbody.innerHTML = `
    <tr>
      <td colspan="5" style="text-align:center; padding:24px;">
        加载中...
      </td>
    </tr>
  `;
  pageBtnContainer.innerHTML = "";

  fetch(url)
    .then((res) => res.json())
    .then((res) => {
      if (res.status !== "success") {
        tbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align:center; padding:24px;">
            查询失败
          </td>
        </tr>
      `;
        return;
      }

      const { items, pagination } = res.data;

      renderOrderTableRows(items, tbody, container);

      renderPageButtons({
        totalPages: pagination.pages,
        currentPage: pagination.page,
        onClick: (newPage) =>
          triggerSearch({
            page: newPage,
            input,
            versionSelect,
            tbody,
            pageBtnContainer,
            container,
          }),
        pageBtnContainer,
      });
    })
    .catch(() => {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align:center; padding:24px;">
            网络错误
          </td>
        </tr>
      `;
    });
}

function renderPageButtons({
  totalPages,
  currentPage,
  onClick,
  pageBtnContainer,
}) {
  pageBtnContainer.innerHTML = "";

  if (totalPages <= 1) return;

  const wrapper = document.createElement("div");
  Object.assign(wrapper.style, {
    display: "flex",
    gap: "8px",
    justifyContent: "center",
    alignItems: "center",
    flexWrap: "wrap",
    padding: "20px 0",
  });

  const createBtn = (label, page, disabled = false) => {
    const btn = document.createElement("button");
    btn.textContent = label;

    Object.assign(btn.style, {
      padding: "8px 16px",
      borderRadius: "8px",
      border: "1px solid #ccc",
      backgroundColor: disabled ? "#f3f1eb" : "#fff",
      color: disabled ? "#aaa" : "#4a3b22",
      cursor: disabled ? "not-allowed" : "pointer",
      fontSize: "14px",
      transition: "all 0.3s ease",
    });

    if (!disabled) {
      btn.onclick = () => onClick(page);
    }

    return btn;
  };

  wrapper.appendChild(
    createBtn("« 上一页", currentPage - 1, currentPage === 1),
  );

  const pageInfo = document.createElement("span");
  pageInfo.textContent = `第 ${currentPage} / ${totalPages} 页`;
  Object.assign(pageInfo.style, {
    fontSize: "14px",
    color: "#6b5a3a",
    margin: "0 12px",
  });
  wrapper.appendChild(pageInfo);

  wrapper.appendChild(
    createBtn("下一页 »", currentPage + 1, currentPage === totalPages),
  );

  pageBtnContainer.appendChild(wrapper);
}

function renderOrderTableRows(orders, tbody, container) {
  tbody.innerHTML = "";

  if (!orders || orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:24px;">未找到记录</td></tr>`;
    return;
  }

  orders.forEach((order) => {
    const tr = document.createElement("tr");
    tr.dataset.orderId = order.id;

    Object.assign(tr.style, {
      cursor: "pointer",
      transition: "background 0.25s",
    });

    tr.onmouseenter = () => {
      tr.style.backgroundColor = "#f9f4ec";
    };

    tr.onmouseleave = () => {
      tr.style.backgroundColor = "";
    };

    tr.onclick = () => {
      console.log("[click] order", order);
      open_fahui_detail_modal(container, order);
    };

    tr.innerHTML = `
      <td style="padding:12px;">${order.customer_name || "-"}</td>
      <td>${order.phone || "-"}</td>
      <td>${(order.order_items || []).map((i) => i.item_name).join("、")}</td>
      <td>${order.status}</td>
      <td>${order.created_at}</td>
    `;

    tbody.appendChild(tr);
  });
}
