import {
  createVerifiedToken,
  getSavedCustomers,
  getVerifiedToken,
  isPhoneLocallyVerified,
} from "../state/guestCustomerStore.js";

const SEND_OTP_API = "/api/twilio/send_otp";
const VERIFY_OTP_API = "/api/twilio/verify";
const PHONE_ORDERS_API = "/api/fahui_router/get_orders_by_phone";
const PAGE_SIZE = 10;

export function mountSearchPage(container) {
  let uiState = {
    selectedPhone: "",
    manualPhone: "",
    otpCode: "",
    loading: false,
    message: "",
    error: "",
    listLoading: false,
    phoneOrders: [],
    pagedOrdersByYear: {},
    pagesByYear: {},
  };

  function getSelectedCustomer() {
    return getSavedCustomers().find((item) => item.phone === uiState.selectedPhone) || null;
  }

  function getCurrentPhone() {
    return (uiState.selectedPhone || uiState.manualPhone || "").trim();
  }

  function getYearFromVersion(version) {
    const match = String(version || "").match(/^(\d{4})/);
    return match ? match[1] : "未分类";
  }

  function buildYearGroups(items) {
    const grouped = {};
    for (const item of items) {
      const year = getYearFromVersion(item.version);
      if (!grouped[year]) {
        grouped[year] = [];
      }
      grouped[year].push(item);
    }
    return Object.keys(grouped)
      .sort((a, b) => Number(b) - Number(a))
      .map((year) => ({
        year,
        items: grouped[year],
      }));
  }

  function getPageItems(year, items) {
    const currentPage = uiState.pagesByYear[year] || 1;
    const start = (currentPage - 1) * PAGE_SIZE;
    return items.slice(start, start + PAGE_SIZE);
  }

  function openOrderDetail(orderId) {
    window.dispatchEvent(new CustomEvent("fahui:navigate", {
      detail: {
        page: "fahui_detail",
        params: {
          orderId,
          returnPage: "search",
        },
      },
    }));
  }

  function render() {
    const customers = getSavedCustomers();
    const selectedCustomer = getSelectedCustomer();
    const currentPhone = getCurrentPhone();
    const localToken = currentPhone ? getVerifiedToken(currentPhone) : "";
    const isVerified = currentPhone ? isPhoneLocallyVerified(currentPhone) : false;

    container.innerHTML = `
      <section class="guest-home">
        <header class="guest-home-head">
          <h2 class="section-title">查找订单</h2>
          <p class="section-subtitle">查看订单前，需要先通过手机验证码认证。</p>
        </header>

        <div class="search-layout">
          <section class="guest-local-panel">
            <h3>本机手机号</h3>
            <div class="local-list">
              ${
                customers.length
                  ? customers
                      .map(
                        (item) => `
                          <button
                            class="saved-phone-card ${uiState.selectedPhone === item.phone ? "active" : ""}"
                            type="button"
                            data-action="select-phone"
                            data-phone="${item.phone}"
                          >
                            <div class="local-name">${item.customer_name || item.name || "未命名"}</div>
                            <div class="local-meta">${item.phone}</div>
                            <div class="local-meta">订单 #${item.order_id}</div>
                          </button>
                        `,
                      )
                      .join("")
                  : `<div class="state-banner">请先到首页完成登记</div>`
              }
            </div>

            <form class="search-form" data-action="manual-phone-form">
              <input
                class="search-input"
                name="phone"
                placeholder="或直接输入手机号码"
                value="${uiState.manualPhone}"
              />
              <button class="mode-switch secondary" type="submit">使用手机号</button>
            </form>
          </section>

          <section class="guest-local-panel">
            <h3>手机号认证</h3>
            ${
              currentPhone
                ? `
                  <div class="verify-summary">
                    <div class="local-meta">当前手机号：${currentPhone}</div>
                    <div class="local-meta">本地 token：${localToken || "未认证"}</div>
                  </div>

                  <div class="verify-actions">
                    <button class="mode-switch secondary" type="button" data-action="send-otp">
                      发送验证码
                    </button>
                  </div>

                  ${
                    isVerified
                      ? `
                        <div class="verify-actions">
                          <button
                            class="mode-switch secondary"
                            type="button"
                            data-action="load-detail"
                          >
                            查看订单
                          </button>
                        </div>
                      `
                      : `
                        <form class="search-form" data-action="verify-form">
                          <input
                            class="search-input"
                            name="otp"
                            placeholder="输入短信验证码"
                            value="${uiState.otpCode}"
                          />
                          <button class="mode-switch secondary" type="submit">验证</button>
                          <button
                            class="mode-switch secondary"
                            type="button"
                            data-action="load-detail"
                            disabled
                          >
                            查看订单
                          </button>
                        </form>
                      `
                  }
                `
                : `<div class="state-banner">请选择或输入一个手机号</div>`
            }

            ${uiState.message ? `<div class="form-success">${uiState.message}</div>` : ""}
            ${uiState.error ? `<div class="form-error">${uiState.error}</div>` : ""}
          </section>
        </div>

        ${
          uiState.listLoading
            ? `<div class="state-banner">手机号订单加载中...</div>`
            : uiState.phoneOrders.length
              ? `
                <section class="detail-panel">
                  <div class="detail-row"><strong>手机号</strong><span>${currentPhone || "-"}</span></div>
                  <div class="detail-row"><strong>关联订单</strong><span>${uiState.phoneOrders.length} 笔</span></div>
                </section>

                ${buildYearGroups(uiState.phoneOrders)
                  .map((group) => {
                    const totalPages = Math.max(1, Math.ceil(group.items.length / PAGE_SIZE));
                    const pageItems = getPageItems(group.year, group.items);
                    return `
                      <section class="detail-panel">
                        <div class="detail-head">
                          <h3 class="section-title">${group.year} 年</h3>
                          <span class="local-meta">${group.items.length} 笔</span>
                        </div>

                        <div class="local-list">
                          ${pageItems
                            .map(
                              (order) => `
                                <button
                                  class="saved-phone-card"
                                  type="button"
                                  data-action="open-order-detail"
                                  data-order-id="${order.id}"
                                >
                                  <div class="local-name">${order.customer_name || order.name || "未命名"}</div>
                                  <div class="local-meta">订单 #${order.id}</div>
                                  <div class="local-meta">${order.created_at || "-"}</div>
                                  <div class="local-meta">${order.status || "-"}</div>
                                </button>
                              `,
                            )
                            .join("")}
                        </div>

                        ${
                          totalPages > 1
                            ? `
                              <div class="pagination-bar">
                                <button
                                  class="mode-switch secondary"
                                  type="button"
                                  data-action="change-year-page"
                                  data-year="${group.year}"
                                  data-page="${Math.max(1, (uiState.pagesByYear[group.year] || 1) - 1)}"
                                  ${(uiState.pagesByYear[group.year] || 1) <= 1 ? "disabled" : ""}
                                >
                                  上一页
                                </button>
                                <span class="local-meta">第 ${uiState.pagesByYear[group.year] || 1} / ${totalPages} 页</span>
                                <button
                                  class="mode-switch secondary"
                                  type="button"
                                  data-action="change-year-page"
                                  data-year="${group.year}"
                                  data-page="${Math.min(totalPages, (uiState.pagesByYear[group.year] || 1) + 1)}"
                                  ${(uiState.pagesByYear[group.year] || 1) >= totalPages ? "disabled" : ""}
                                >
                                  下一页
                                </button>
                              </div>
                            `
                            : ""
                        }
                      </section>
                    `;
                  })
                  .join("")}
              `
              : ""
        }
      </section>
    `;

    bind();
  }

  async function sendOtp() {
    const customer = getSelectedCustomer();
    const phone = getCurrentPhone();
    if (!phone) {
      uiState.error = "请先选择或输入手机号";
      render();
      return;
    }

    uiState.loading = true;
    uiState.error = "";
    uiState.message = "";
    render();

    try {
      const response = await fetch(SEND_OTP_API, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(customer ? {
          order_id: customer.order_id,
        } : {
          phone,
        }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !["success", "cookie_true", "login_bypass"].includes(payload?.status)) {
        throw new Error(payload?.message || "验证码发送失败");
      }

      if (payload?.status === "login_bypass") {
        createVerifiedToken(phone);
        uiState.loading = false;
        uiState.otpCode = "";
        uiState.message = "当前已登录，已直接生成本地认证 token";
        render();
        return;
      }

      uiState.loading = false;
      uiState.message = payload.message || "验证码已发送";
      render();
    } catch (error) {
      uiState.loading = false;
      uiState.error = error.message || "验证码发送失败";
      render();
    }
  }

  async function verifyOtp(code) {
    const phone = getCurrentPhone();
    if (!phone) {
      uiState.error = "请先选择或输入手机号";
      render();
      return;
    }

    if (!code) {
      uiState.error = "请输入验证码";
      render();
      return;
    }

    uiState.loading = true;
    uiState.error = "";
    uiState.message = "";
    render();

    try {
      const response = await fetch(VERIFY_OTP_API, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          otp: code,
          phone,
        }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok || payload?.status !== "success") {
        throw new Error(payload?.message || "验证码验证失败");
      }

      createVerifiedToken(phone);
      uiState.loading = false;
      uiState.message = "验证成功，本地认证 token 已保存";
      uiState.otpCode = "";
      render();
    } catch (error) {
      uiState.loading = false;
      uiState.error = error.message || "验证码验证失败";
      render();
    }
  }

  async function loadDetail() {
    const phone = getCurrentPhone();
    if (!phone) {
      uiState.error = "请先选择或输入手机号";
      render();
      return;
    }

    uiState.listLoading = true;
    uiState.phoneOrders = [];
    uiState.pagedOrdersByYear = {};
    uiState.pagesByYear = {};
    uiState.error = "";
    uiState.message = "";
    render();

    try {
      const response = await fetch(`${PHONE_ORDERS_API}?phone=${encodeURIComponent(phone)}`, {
        credentials: "include",
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok || payload?.status !== "success") {
        throw new Error(payload?.message || "查看订单失败，请重新验证手机号");
      }

      const items = payload?.data?.items || [];
      uiState.listLoading = false;
      uiState.phoneOrders = items;
      uiState.pagesByYear = buildYearGroups(items).reduce((acc, group) => {
        acc[group.year] = 1;
        return acc;
      }, {});
      uiState.message = items.length ? "手机号关联订单已同步" : "这个手机号下还没有订单";
      render();
    } catch (error) {
      uiState.listLoading = false;
      uiState.phoneOrders = [];
      uiState.pagesByYear = {};
      uiState.error = error.message || "查看订单失败";
      render();
    }
  }

  function bind() {
    container.querySelectorAll('[data-action="select-phone"]').forEach((button) => {
      button.addEventListener("click", () => {
        uiState.selectedPhone = button.dataset.phone || "";
        uiState.manualPhone = "";
        uiState.phoneOrders = [];
        uiState.pagesByYear = {};
        uiState.message = "";
        uiState.error = "";
        render();
      });
    });

    const manualPhoneForm = container.querySelector('[data-action="manual-phone-form"]');
    if (manualPhoneForm) {
      manualPhoneForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const formData = new FormData(manualPhoneForm);
        uiState.manualPhone = String(formData.get("phone") || "").trim();
        uiState.selectedPhone = "";
        uiState.phoneOrders = [];
        uiState.pagesByYear = {};
        uiState.message = "";
        uiState.error = uiState.manualPhone ? "" : "请输入手机号码";
        render();
      });
    }

    const sendButton = container.querySelector('[data-action="send-otp"]');
    if (sendButton) {
      sendButton.addEventListener("click", sendOtp);
    }

    const form = container.querySelector('[data-action="verify-form"]');
    if (form) {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        uiState.otpCode = String(formData.get("otp") || "").trim();
        verifyOtp(uiState.otpCode);
      });
    }

    const loadButton = container.querySelector('[data-action="load-detail"]');
    if (loadButton) {
      loadButton.addEventListener("click", loadDetail);
    }

    container.querySelectorAll('[data-action="open-order-detail"]').forEach((button) => {
      button.addEventListener("click", () => {
        const orderId = Number(button.dataset.orderId);
        openOrderDetail(orderId);
      });
    });

    container.querySelectorAll('[data-action="change-year-page"]').forEach((button) => {
      button.addEventListener("click", () => {
        const year = String(button.dataset.year || "");
        const page = Number(button.dataset.page || 1);
        uiState.pagesByYear = {
          ...uiState.pagesByYear,
          [year]: page,
        };
        render();
      });
    });
  }

  render();
  return () => {
    container.innerHTML = "";
  };
}
