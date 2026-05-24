import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import DateTimePickerField from "./components/DateTimePickerField";
import {
  Appointment,
  Customer,
  Resource,
  SeedSummary,
  Service,
  cancelAppointment,
  createAppointment,
  getOrCreateBookingRequestId,
  listAppointments,
  listCustomers,
  listResources,
  listServices,
  seed,
} from "./api/client";
import { useAutoDismiss } from "./hooks/useAutoDismiss";

function toUtcIso(localDatetime: string): string {
  return new Date(localDatetime).toISOString();
}

function addMinutes(localDatetime: string, minutes: number): string {
  const d = new Date(localDatetime);
  d.setMinutes(d.getMinutes() + minutes);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatRange(start: string, end: string) {
  const s = new Date(start);
  const e = new Date(end);
  return `${s.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })} · ${s.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })} – ${e.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}`;
}

export default function App() {
  const [summary, setSummary] = useState<SeedSummary | null>(null);
  const [resources, setResources] = useState<Resource[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [resourceId, setResourceId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [draftStart, setDraftStart] = useState("");
  const [draftEnd, setDraftEnd] = useState("");
  const [startLocal, setStartLocal] = useState("");
  const [endLocal, setEndLocal] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const clearMessage = useCallback(() => setMessage(null), []);
  const clearError = useCallback(() => setError(null), []);

  useAutoDismiss(message, clearMessage);
  useAutoDismiss(error, clearError);

  const resourceById = useMemo(
    () => Object.fromEntries(resources.map((r) => [r.id, r])),
    [resources],
  );
  const customerById = useMemo(
    () => Object.fromEntries(customers.map((c) => [c.id, c])),
    [customers],
  );
  const serviceById = useMemo(
    () => Object.fromEntries(services.map((s) => [s.id, s])),
    [services],
  );

  const refresh = useCallback(async (bizId: string) => {
    const [r, c, s, a] = await Promise.all([
      listResources(bizId),
      listCustomers(bizId),
      listServices(bizId),
      listAppointments(bizId),
    ]);
    setResources(r);
    setCustomers(c);
    setServices(s);
    setAppointments(a);
    return { r, c, s };
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const s = await seed();
        setSummary(s);
        const { r, c, s: services } = await refresh(s.business_id);
        if (r.length) setResourceId(r[0].id);
        if (c.length) setCustomerId(c[0].id);
        if (services.length) setServiceId(services[0].id);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load the shop schedule.");
      }
    })();
  }, [refresh]);

  function confirmStart() {
    if (!draftStart) return;
    setStartLocal(draftStart);
    const svc = serviceId ? serviceById[serviceId] : undefined;
    if (svc) {
      const suggestedEnd = addMinutes(draftStart, svc.duration_minutes);
      setDraftEnd(suggestedEnd);
      setEndLocal(suggestedEnd);
    }
  }

  function confirmEnd() {
    if (!draftEnd) return;
    setEndLocal(draftEnd);
  }

  useEffect(() => {
    if (!serviceId || !startLocal) return;
    const svc = serviceById[serviceId];
    if (!svc) return;
    const suggested = addMinutes(startLocal, svc.duration_minutes);
    setDraftEnd(suggested);
    setEndLocal(suggested);
  }, [serviceId, startLocal, serviceById]);

  async function onBook(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    if (!resourceId || !customerId) {
      setError("Please choose a workstation and customer.");
      return;
    }
    if (!startLocal || !endLocal) {
      setError("Press Okay on start and end times before confirming the appointment.");
      return;
    }
    if (draftStart !== startLocal || draftEnd !== endLocal) {
      setError("You have unconfirmed time changes — press Okay on start and end times.");
      return;
    }
    setLoading(true);
    try {
      await createAppointment({
        resource_id: resourceId,
        customer_id: customerId,
        service_id: serviceId || undefined,
        start_utc: toUtcIso(startLocal),
        end_utc: toUtcIso(endLocal),
        client_request_id: getOrCreateBookingRequestId(),
      });
      const svc = serviceId ? serviceById[serviceId]?.name : "Repair slot";
      setMessage(`Confirmed: ${svc} for ${customerById[customerId]?.name ?? "customer"}.`);
      if (summary) await refresh(summary.business_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Booking failed");
    } finally {
      setLoading(false);
    }
  }

  async function onCancel(id: string) {
    setError(null);
    setMessage(null);
    try {
      await cancelAppointment(id);
      setMessage("The appointment was cancelled and the time slot is available again.");
      if (summary) await refresh(summary.business_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cancel failed");
    }
  }

  const selectedResource = resourceById[resourceId];

  return (
    <>
      <header className="hero">
        <span className="hero-badge">Fictional case study · single location</span>
        <h1>Northside Repair Desk</h1>
        <p className="hero-lead">
          Appointment scheduling for phones, tablets, and laptops — one shared calendar for the whole shop.
        </p>
        <p className="hero-desc">
          Northside Repair Desk is a neighbourhood electronics repair shop. Staff book repair workstations
          and customer drop-offs in one place, so WhatsApp messages and paper notes cannot disagree about who
          owns a time slot. The system refuses overlapping bookings when two people confirm the same window,
          even if they click at the same moment.
        </p>
        <div className="hero-pills">
          <span>Concurrency-safe booking</span>
          <span>UTC time storage</span>
          <span>Email reminders (mock)</span>
        </div>
      </header>

      {error && (
        <div className="error" role="alert">
          {error}
          <span className="toast-dismiss">This message will close in 30 seconds.</span>
        </div>
      )}
      {message && (
        <div className="success" role="status">
          {message}
          <span className="toast-dismiss">This message will close in 30 seconds.</span>
        </div>
      )}

      <section className="card">
        <h2 className="section-title">Our services</h2>
        <p className="section-sub">
          Typical jobs we schedule. Duration guides the end time when you pick a service below.
        </p>
        <div className="services-grid">
          {services.length === 0 && (
            <p className="empty-state">
              Loading shop services… If this stays empty, check that the API is running and try{" "}
              <button
                type="button"
                className="btn-ghost"
                onClick={async () => {
                  try {
                    const s = await seed();
                    setSummary(s);
                    await refresh(s.business_id);
                  } catch (e) {
                    setError(e instanceof Error ? e.message : "Could not load services.");
                  }
                }}
              >
                reload demo data
              </button>
              .
            </p>
          )}
          {services.map((svc) => (
            <article key={svc.id} className="service-card">
              <h3>{svc.name}</h3>
              <p>{svc.description ?? "Professional repair with test before handover."}</p>
              <span className="duration">About {svc.duration_minutes} minutes</span>
            </article>
          ))}
        </div>
      </section>

      <section className="card">
        <h2 className="section-title">Schedule a repair</h2>
        <p className="section-sub">
          Choose a workstation, customer, and service. Press Okay to lock in each date and time.
        </p>
        <form onSubmit={onBook}>
          <label htmlFor="resource">Workstation</label>
          <p className="hint">
            {selectedResource?.description ??
              "Where the device will be worked on during this visit."}
          </p>
          <select
            id="resource"
            value={resourceId}
            onChange={(e) => setResourceId(e.target.value)}
          >
            {resources.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>

          <label htmlFor="service">Service</label>
          <select
            id="service"
            value={serviceId}
            onChange={(e) => setServiceId(e.target.value)}
          >
            {services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.duration_minutes} min)
              </option>
            ))}
          </select>

          <label htmlFor="customer">Customer</label>
          <select
            id="customer"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
          >
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
                {c.email ? ` — ${c.email}` : ""}
              </option>
            ))}
          </select>

          <DateTimePickerField
            id="start"
            label="Start time"
            draft={draftStart}
            confirmed={startLocal}
            onDraftChange={setDraftStart}
            onConfirm={confirmStart}
          />

          <DateTimePickerField
            id="end"
            label="End time"
            hint="Suggested from service duration when you confirm start; adjust and press Okay."
            draft={draftEnd}
            confirmed={endLocal}
            onDraftChange={setDraftEnd}
            onConfirm={confirmEnd}
          />

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Reserving slot…" : "Confirm appointment"}
          </button>
        </form>
      </section>

      <section className="card">
        <h2 className="section-title">Upcoming appointments</h2>
        <p className="section-sub">Everything stored in the shop database — cancel to free a slot.</p>
        <ul className="appointments">
          {appointments.length === 0 && (
            <li className="empty-state">No appointments yet. Book the first repair above.</li>
          )}
          {appointments.map((a) => (
            <li key={a.id} className="appointment-item">
              <div className="appointment-meta">
                <strong>{customerById[a.customer_id]?.name ?? "Customer"}</strong>
                {resourceById[a.resource_id]?.name ?? "Workstation"}
                <br />
                {formatRange(a.start_utc, a.end_utc)}
              </div>
              <div>
                <span
                  className={`status ${a.status === "CONFIRMED" ? "status-confirmed" : "status-cancelled"}`}
                >
                  {a.status === "CONFIRMED" ? "Confirmed" : "Cancelled"}
                </span>
                {a.status === "CONFIRMED" && (
                  <>
                    {" "}
                    <button type="button" className="btn-ghost" onClick={() => onCancel(a.id)}>
                      Cancel
                    </button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
