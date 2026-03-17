const ORDER_DETAIL_API = "/api/fahui_router/get_order_by_id";

export function mountFahuiDetailPage(container, options = {}) {
  const orderId = Number(options.orderId);
  const onBack = typeof options.onBack === "function" ? options.onBack : () => {};
  let uiState = {
    loading: true,
    error: "",
    detail: null,
  };

  function render() {
    container.innerHTML = `
      <section class="detail-shell">
        <div class="detail-head">
          <button class="mode-switch secondary" type="button" data-action="detail-back">返回</button>
          <h2 class="section-title">法会订单详情</h2>
        </div>

        ${
          uiState.loading
            ? `<div class="state-banner">订单详情加载中...</div>`
            : uiState.error
              ? `<div class="state-banner error">${uiState.error}</div>`
              : uiState.detail
                ? `
                  <section class="detail-panel">
                    <div class="detail-row"><strong>订单号</strong><span>${uiState.detail.id}</span></div>
                    <div class="detail-row"><strong>功德主</strong><span>${uiState.detail.customer_name || "-"}</span></div>
                    <div class="detail-row"><strong>登记名称</strong><span>${uiState.detail.name || "-"}</span></div>
                    <div class="detail-row"><strong>手机号</strong><span>${uiState.detail.phone || "-"}</span></div>
                    <div class="detail-row"><strong>状态</strong><span>${uiState.detail.status || "-"}</span></div>
                    <div class="detail-row"><strong>版本</strong><span>${uiState.detail.version || "-"}</span></div>
                    <div class="detail-row"><strong>创建时间</strong><span>${uiState.detail.created_at || "-"}</span></div>
                  </section>

                  <section class="detail-panel">
                    <h3 class="section-title">项目明细</h3>
                    <div class="local-list">
                      ${
                        (uiState.detail.order_items || []).length
                          ? uiState.detail.order_items
                              .map(
                                (item) => `
                                  <article class="local-card">
                                    <div class="local-name">${item.item_name || item.code || "未命名项目"}</div>
                                    <div class="local-meta">项目 #${item.id}</div>
                                    <div class="local-meta">价格：${item.price ?? 0}</div>
                                  </article>
                                `,
                              )
                              .join("")
                          : `<div class="state-banner">这笔订单还没有项目明细</div>`
                      }
                    </div>
                  </section>
                `
                : ""
        }
      </section>
    `;

    const backButton = container.querySelector('[data-action="detail-back"]');
    if (backButton) {
      backButton.addEventListener("click", onBack);
    }
  }

  async function load() {
    render();

    try {
      const response = await fetch(`${ORDER_DETAIL_API}?id=${orderId}`, {
        credentials: "include",
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || payload?.status !== "success") {
        throw new Error(payload?.message || "加载订单详情失败");
      }

      uiState.loading = false;
      uiState.detail = payload.data || null;
      uiState.error = "";
      render();
    } catch (error) {
      uiState.loading = false;
      uiState.detail = null;
      uiState.error = error.message || "加载订单详情失败";
      render();
    }
  }

  load();
  return () => {
    container.innerHTML = "";
  };
}
