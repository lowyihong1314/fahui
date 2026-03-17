import {
  getState,
  loadYear,
  setQuery,
  setSelectedYear,
  subscribe,
} from "../state/fahuiDataStore.js";

export function mountFahuiPage(container) {
  function openOrderDetail(orderId) {
    window.dispatchEvent(new CustomEvent("fahui:navigate", {
      detail: {
        page: "fahui_detail",
        params: {
          orderId,
          returnPage: "fahui_data",
        },
      },
    }));
  }

  let unsubscribe = null;

  function render(snapshot) {
    const orders = snapshot.ordersByYear[snapshot.selectedYear] || [];
    const pagination = snapshot.paginationByYear[snapshot.selectedYear] || {};

    container.innerHTML = `
      <section class="fahui-shell">
        <header class="fahui-header">
          <div>
            <h2 class="section-title">法会数据</h2>
            <p class="section-subtitle">统一从 state 读取，后面方便接 socket 增量更新。</p>
          </div>
          <div class="realtime-chip ${snapshot.realtimeConnected ? "connected" : ""}">
            <span>${snapshot.realtimeStatus}</span>
            ${
              snapshot.lastEvent
                ? `<strong>最新 #${snapshot.lastEvent.orderId}</strong>`
                : ""
            }
          </div>
        </header>

        <div class="fahui-toolbar">
          <div class="year-tabs">
            ${snapshot.years
              .map(
                (year) => `
                  <button
                    class="year-tab ${year === snapshot.selectedYear ? "active" : ""}"
                    type="button"
                    data-year="${year}"
                  >
                    ${year}
                  </button>
                `,
              )
              .join("")}
          </div>

          <form class="search-form" data-role="search-form">
            <input
              class="search-input"
              name="query"
              placeholder="搜索功德主 / 电话 / 表单内容"
              value="${snapshot.query}"
            />
            <button class="mode-switch secondary" type="submit">搜索</button>
            <button class="mode-switch secondary" type="button" data-action="refresh-year">刷新</button>
          </form>
        </div>

        ${snapshot.error ? `<div class="state-banner error">${snapshot.error}</div>` : ""}

        <section class="order-list">
          ${
            snapshot.loading
              ? `<div class="state-banner">加载中...</div>`
              : orders.length
                ? orders
                    .map(
                      (order) => `
                        <button class="order-card order-card-button" type="button" data-order-id="${order.id}">
                          <div class="order-main">
                            <div class="order-name">${order.customer_name}</div>
                            <div class="order-meta">#${order.id} · ${order.created_at}</div>
                          </div>
                          <div class="order-side">
                            <span class="status-tag">${order.status}</span>
                            <span class="order-phone">${order.phone}</span>
                          </div>
                        </button>
                      `,
                    )
                    .join("")
                : `<div class="state-banner">这个年份还没有数据</div>`
          }
        </section>

        <footer class="fahui-footer">
          <span>当前年份：${snapshot.selectedYear}</span>
          <span>总数：${pagination.total ?? orders.length}</span>
        </footer>
      </section>
    `;

    bind(snapshot);
  }

  function bind(snapshot) {
    container.querySelectorAll("[data-year]").forEach((button) => {
      button.addEventListener("click", async () => {
        const year = Number(button.dataset.year);
        setSelectedYear(year);
        await loadYear(year);
      });
    });

    const form = container.querySelector('[data-role="search-form"]');
    if (form) {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        const query = String(formData.get("query") || "").trim();
        setQuery(query);
        await loadYear(snapshot.selectedYear, { query });
      });
    }

    const refreshButton = container.querySelector('[data-action="refresh-year"]');
    if (refreshButton) {
      refreshButton.addEventListener("click", async () => {
        await loadYear(snapshot.selectedYear);
      });
    }

    container.querySelectorAll("[data-order-id]").forEach((button) => {
      button.addEventListener("click", () => {
        openOrderDetail(Number(button.dataset.orderId));
      });
    });
  }

  unsubscribe = subscribe(render);
  loadYear(getState().selectedYear);

  return () => {
    if (unsubscribe) {
      unsubscribe();
    }
    container.innerHTML = "";
  };
}
