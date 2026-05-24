import { fetchWithRetry } from "./fetchWithRetry";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const PENDING_IDEM_KEY = "northside.pending_client_request_id";

export type SeedSummary = {
  business_id: string;
  business_name: string;
  resource_ids: string[];
  customer_ids: string[];
  service_ids: string[];
};

export type Resource = {
  id: string;
  name: string;
  kind: string;
  description?: string | null;
};
export type Customer = { id: string; name: string; email: string | null };
export type Service = {
  id: string;
  name: string;
  description?: string | null;
  duration_minutes: number;
};
export type Appointment = {
  id: string;
  resource_id: string;
  customer_id: string;
  start_utc: string;
  end_utc: string;
  status: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetchWithRetry(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/** Stable id for one booking attempt; survives retries after network loss. */
export function getOrCreateBookingRequestId(): string {
  const existing = sessionStorage.getItem(PENDING_IDEM_KEY);
  if (existing) return existing;
  const id = crypto.randomUUID();
  sessionStorage.setItem(PENDING_IDEM_KEY, id);
  return id;
}

export function clearBookingRequestId(): void {
  sessionStorage.removeItem(PENDING_IDEM_KEY);
}

export async function seed(): Promise<SeedSummary> {
  return request<SeedSummary>("/admin/seed", { method: "POST" });
}

export async function listResources(businessId: string): Promise<Resource[]> {
  return request(`/businesses/${businessId}/resources`);
}

export async function listCustomers(businessId: string): Promise<Customer[]> {
  return request(`/businesses/${businessId}/customers`);
}

export async function listServices(businessId: string): Promise<Service[]> {
  return request(`/businesses/${businessId}/services`);
}

export async function listAppointments(businessId: string): Promise<Appointment[]> {
  return request(`/appointments?business_id=${businessId}`);
}

export type CreateAppointmentDTO = {
  resource_id: string;
  customer_id: string;
  start_utc: string;
  end_utc: string;
  service_id?: string;
  client_request_id?: string;
};

export async function createAppointment(body: CreateAppointmentDTO): Promise<Appointment> {
  const res = await fetchWithRetry(`${BASE}/appointments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 409) {
    clearBookingRequestId();
    throw new Error("That slot was just taken. Pick another time.");
  }
  if (!res.ok) {
    throw new Error(await res.text());
  }
  clearBookingRequestId();
  return res.json();
}

export async function cancelAppointment(id: string): Promise<Appointment> {
  return request(`/appointments/${id}/cancel`, { method: "POST" });
}
