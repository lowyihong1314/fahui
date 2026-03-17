const STORAGE_KEY = "fahui_guest_customers";
const TOKEN_KEY = "fahui_guest_verified_tokens";

function readJson(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (error) {
    return fallback;
  }
}

function writeJson(key, value) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

function readCustomers() {
  const parsed = readJson(STORAGE_KEY, []);
  return Array.isArray(parsed) ? parsed : [];
}

function writeCustomers(customers) {
  writeJson(STORAGE_KEY, customers);
}

function readVerifiedTokens() {
  const parsed = readJson(TOKEN_KEY, {});
  return parsed && typeof parsed === "object" ? parsed : {};
}

function writeVerifiedTokens(tokens) {
  writeJson(TOKEN_KEY, tokens);
}

export function getSavedCustomers() {
  return readCustomers();
}

export function hasPhone(phone) {
  return readCustomers().some((item) => item.phone === phone);
}

export function saveCustomer(customer) {
  const customers = readCustomers();
  if (customers.some((item) => item.phone === customer.phone)) {
    return false;
  }

  customers.push(customer);
  writeCustomers(customers);
  return true;
}

export function createVerifiedToken(phone) {
  const token = `verified_${phone}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  const tokens = readVerifiedTokens();
  tokens[phone] = token;
  writeVerifiedTokens(tokens);
  return token;
}

export function getVerifiedToken(phone) {
  const tokens = readVerifiedTokens();
  return tokens[phone] || "";
}

export function isPhoneLocallyVerified(phone) {
  return Boolean(getVerifiedToken(phone));
}
