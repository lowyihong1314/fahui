import { io } from "socket.io-client";

const SEARCH_API = "/api/fahui_router/search";
const DEFAULT_YEARS = [2025, 2024, 2023];
let socket = null;

const state = {
  years: [...DEFAULT_YEARS],
  selectedYear: DEFAULT_YEARS[0],
  query: "",
  loading: false,
  error: "",
  ordersByYear: {},
  paginationByYear: {},
  realtimeConnected: false,
  realtimeStatus: "未连接",
  lastEvent: null,
};

const listeners = new Set();

function emit() {
  const snapshot = getState();
  listeners.forEach((listener) => listener(snapshot));
}

function ensureYear(year) {
  if (!state.years.includes(year)) {
    state.years = [year, ...state.years].sort((a, b) => b - a);
  }
}

function extractYear(version) {
  if (typeof version === "number" && Number.isFinite(version)) {
    return version;
  }

  const match = String(version || "").match(/^(\d{4})/);
  return match ? Number(match[1]) : NaN;
}

function normalizeItems(items) {
  return (items || []).map((item) => ({
    id: item.id,
    customer_name: item.customer_name || item.name || "未命名订单",
    phone: item.phone || "-",
    status: item.status || "Not-ready",
    created_at: item.created_at || "-",
    version: item.version,
  }));
}

export function getState() {
  return {
    years: [...state.years],
    selectedYear: state.selectedYear,
    query: state.query,
    loading: state.loading,
    error: state.error,
    ordersByYear: { ...state.ordersByYear },
    paginationByYear: { ...state.paginationByYear },
    realtimeConnected: state.realtimeConnected,
    realtimeStatus: state.realtimeStatus,
    lastEvent: state.lastEvent ? { ...state.lastEvent } : null,
  };
}

export function subscribe(listener) {
  listeners.add(listener);
  listener(getState());
  return () => listeners.delete(listener);
}

export function setSelectedYear(year) {
  ensureYear(year);
  state.selectedYear = year;
  emit();
}

export function setQuery(query) {
  state.query = query;
  emit();
}

export async function loadYear(year = state.selectedYear, options = {}) {
  const query = options.query ?? state.query;
  const page = options.page ?? 1;

  ensureYear(year);
  state.selectedYear = year;
  state.query = query;
  state.loading = true;
  state.error = "";
  emit();

  try {
    const params = new URLSearchParams({
      version: String(year),
      value: query,
      page: String(page),
      per_page: "20",
    });

    const response = await fetch(`${SEARCH_API}?${params.toString()}`, {
      credentials: "include",
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload?.status !== "success") {
      throw new Error(payload?.message || "加载法会数据失败");
    }

    const result = payload.data || {};
    state.ordersByYear = {
      ...state.ordersByYear,
      [year]: normalizeItems(result.items),
    };
    state.paginationByYear = {
      ...state.paginationByYear,
      [year]: result.pagination || {},
    };
    state.loading = false;
    state.error = "";
    emit();
  } catch (error) {
    state.loading = false;
    state.error = error.message || "加载失败";
    emit();
  }
}

export function applySocketOrderUpdate(order, options = {}) {
  const year = extractYear(order?.version);
  if (!year) {
    return;
  }

  ensureYear(year);
  const currentOrders = state.ordersByYear[year] || [];
  const nextOrder = {
    id: order.id,
    customer_name: order.customer_name || order.name || "未命名订单",
    phone: order.phone || "-",
    status: order.status || "Not-ready",
    created_at: order.created_at || "-",
    version: order.version,
  };

  const index = currentOrders.findIndex((item) => item.id === nextOrder.id);
  const nextOrders = [...currentOrders];
  let nextTotal = state.paginationByYear[year]?.total;
  if (index >= 0) {
    nextOrders[index] = nextOrder;
  } else {
    nextOrders.unshift(nextOrder);
    if (typeof nextTotal === "number") {
      nextTotal += 1;
    }
  }

  state.ordersByYear = {
    ...state.ordersByYear,
    [year]: nextOrders,
  };
  state.paginationByYear = {
    ...state.paginationByYear,
    [year]: {
      ...(state.paginationByYear[year] || {}),
      total: nextTotal ?? nextOrders.length,
    },
  };
  state.lastEvent = {
    type: index >= 0 ? "updated" : "created",
    orderId: nextOrder.id,
    source: options.source || "socket",
    year,
    createdAt: new Date().toISOString(),
  };
  emit();
}

export function connectFahuiRealtime() {
  if (socket) {
    return socket;
  }

  state.realtimeStatus = "连接中";
  emit();

  socket = io("/", {
    withCredentials: true,
    transports: ["websocket", "polling"],
  });

  socket.on("connect", () => {
    state.realtimeConnected = true;
    state.realtimeStatus = "实时已连接";
    emit();
  });

  socket.on("disconnect", () => {
    state.realtimeConnected = false;
    state.realtimeStatus = "连接已断开";
    emit();
  });

  socket.on("connect_error", () => {
    state.realtimeConnected = false;
    state.realtimeStatus = "实时连接失败";
    emit();
  });

  socket.on("fahui:order_created", (payload) => {
    if (!payload?.order) {
      return;
    }

    applySocketOrderUpdate(payload.order, {
      source: payload.source || "new_customer",
    });
  });

  return socket;
}
