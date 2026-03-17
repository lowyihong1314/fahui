import { getSavedCustomers, hasPhone, saveCustomer } from "../state/guestCustomerStore.js";

const NEW_CUSTOMER_API = "/api/fahui_router/new_customer";

export function mountHomePage(container) {
  let formState = {
    loading: false,
    error: "",
    success: "",
  };

  function render() {
    const savedCustomers = getSavedCustomers();

    container.innerHTML = `
      <section class="guest-home">
        <header class="guest-home-head">
          <h2 class="section-title">游客登记</h2>
          <p class="section-subtitle">先登记功德主资料，再用手机号继续后续验证流程。</p>
        </header>

        <div class="guest-home-grid">
          <form class="guest-form" data-role="guest-form">
            <label class="field">
              <span>功德主姓名</span>
              <input name="customer_name" type="text" placeholder="请输入姓名" />
            </label>

            <label class="field">
              <span>联络手机号码</span>
              <input name="phone" type="tel" placeholder="必填" required />
            </label>

            <label class="field">
              <span>登记名称</span>
              <input name="name" type="text" placeholder="可与功德主姓名相同" />
            </label>

            ${
              formState.error
                ? `<div class="form-error">${formState.error}</div>`
                : ""
            }
            ${
              formState.success
                ? `<div class="form-success">${formState.success}</div>`
                : ""
            }

            <button class="submit-btn" type="submit" ${formState.loading ? "disabled" : ""}>
              ${formState.loading ? "提交中..." : "创建登记"}
            </button>
          </form>

          <section class="guest-local-panel">
            <h3>本机已登记手机号</h3>
            <div class="local-list">
              ${
                savedCustomers.length
                  ? savedCustomers
                      .map(
                        (item) => `
                          <article class="local-card">
                            <div class="local-name">${item.customer_name || item.name || "未命名"}</div>
                            <div class="local-meta">${item.phone}</div>
                            <div class="local-meta">订单 #${item.order_id}</div>
                          </article>
                        `,
                      )
                      .join("")
                  : `<div class="state-banner">本机还没有保存的游客登记</div>`
              }
            </div>
          </section>
        </div>
      </section>
    `;

    bind();
  }

  function bind() {
    const form = container.querySelector('[data-role="guest-form"]');
    if (!form) {
      return;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      formState.error = "";
      formState.success = "";

      const formData = new FormData(form);
      const customerName = String(formData.get("customer_name") || "").trim();
      const name = String(formData.get("name") || customerName).trim();
      const phone = String(formData.get("phone") || "").trim();

      if (!phone) {
        formState.error = "手机号码必填";
        render();
        return;
      }

      if (hasPhone(phone)) {
        formState.error = "这个浏览器已经保存过这个手机号码，不能重复登记";
        render();
        return;
      }

      formState.loading = true;
      render();

      try {
        const response = await fetch(NEW_CUSTOMER_API, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            name,
            customer_name: customerName || name,
            phone,
          }),
        });

        const payload = await response.json().catch(() => ({}));
        if (!response.ok || payload?.success !== true) {
          throw new Error(payload?.message || payload?.error || "创建失败");
        }

        const order = payload.order || {};
        saveCustomer({
          customer_name: order.customer_name || customerName || name,
          name: order.name || name,
          phone,
          order_id: order.id,
        });

        formState.loading = false;
        formState.success = payload?.duplicated
          ? "后台已有同名登记，已把订单和手机号保存到本机"
          : "登记成功，后台已推送实时更新，手机号已保存到本机";
        render();
      } catch (error) {
        formState.loading = false;
        formState.error = error.message || "提交失败";
        render();
      }
    });
  }

  render();
  return () => {
    container.innerHTML = "";
  };
}
