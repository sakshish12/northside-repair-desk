type Props = {
  id: string;
  label: string;
  hint?: string;
  draft: string;
  confirmed: string;
  onDraftChange: (value: string) => void;
  onConfirm: () => void;
};

function formatConfirmed(value: string) {
  if (!value) return "";
  const d = new Date(value);
  return d.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function DateTimePickerField({
  id,
  label,
  hint,
  draft,
  confirmed,
  onDraftChange,
  onConfirm,
}: Props) {
  const pending = draft && draft !== confirmed;

  return (
    <div className="datetime-field">
      <label htmlFor={id}>{label}</label>
      {hint && <p className="hint">{hint}</p>}
      <div className="datetime-row">
        <input
          id={id}
          type="datetime-local"
          value={draft}
          onChange={(e) => onDraftChange(e.target.value)}
        />
        <button
          type="button"
          className="btn-okay"
          onClick={onConfirm}
          disabled={!draft}
          title="Apply this date and time"
        >
          Okay
        </button>
      </div>
      {confirmed ? (
        <p className="datetime-confirmed">
          Selected: <strong>{formatConfirmed(confirmed)}</strong>
          {pending && <span className="datetime-pending"> — press Okay to update</span>}
        </p>
      ) : (
        <p className="datetime-pending">Pick a date and time, then press Okay.</p>
      )}
    </div>
  );
}
