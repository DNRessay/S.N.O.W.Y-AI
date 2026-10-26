import { useEffect, useState } from "react";
import { ActivityIcon, MenuIcon, ReceiptIcon } from "./Icons";

const API = import.meta.env.VITE_API_URL || "";

export const iconBtn = {
    position: "relative", background: "none", border: "none", cursor: "pointer", padding: "6px",
    color: "var(--text-muted)", display: "inline-flex", alignItems: "center", justifyContent: "center", borderRadius: "8px",
};

function rand(bill) {
    return bill.zar != null
        ? `R${bill.zar.toLocaleString("en-ZA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        : `$${bill.usd.toFixed(2)}`;
}

// This month's AWS bill and Modal GPU spend: a receipt icon; tap for the amounts.
export function CostButton({ token }) {
    const [aws, setAws] = useState(null);
    const [modal, setModal] = useState(null);
    const [open, setOpen] = useState(false);
    useEffect(() => {
        if (!token) return;
        const get = (path, set) => fetch(`${API}/settings/${path}`, { headers: { Authorization: `Bearer ${token}` } })
            .then(r => (r.ok ? r.json() : null)).then(set).catch(() => {});
        get("aws-cost", setAws);
        get("modal-cost", setModal);
    }, [token]);
    if (!aws && !modal) return null;
    const small = { fontSize: "11px", color: "var(--text-muted)" };
    const big = { fontSize: "20px", fontWeight: 700, color: "var(--gold-text)" };
    return (
        <span style={{ position: "relative" }}>
            <button onClick={() => setOpen(o => !o)} aria-label="Bills this month" title="Bills this month" style={iconBtn}>
                <ReceiptIcon size={18} />
            </button>
            {open && (
                <>
                    <div onClick={() => setOpen(false)} style={{ position: "fixed", inset: 0, zIndex: 30 }} />
                    <div style={{ position: "absolute", right: 0, top: "100%", zIndex: 31, minWidth: "220px", background: "var(--surface)",
                                  border: "1px solid var(--border)", borderRadius: "12px", padding: "10px 12px", boxShadow: "0 8px 24px rgba(0,0,0,0.18)",
                                  display: "flex", flexDirection: "column", gap: "10px" }}>
                        {aws && (
                            <div>
                                <div style={small}>AWS this month (estimate)</div>
                                {aws.ok
                                    ? <div style={big}>{rand(aws)}</div>
                                    : <div style={{ fontSize: "12px", color: "var(--text)" }}>{aws.error}</div>}
                                {aws.ok && aws.zar != null && <div style={small}>${aws.usd.toFixed(2)} at R{aws.rate.toFixed(2)}/$ · {aws.rate_source}</div>}
                            </div>
                        )}
                        {modal && (
                            <div style={{ borderTop: aws ? "1px solid var(--border)" : "none", paddingTop: aws ? "10px" : 0 }}>
                                <div style={small}>Modal this month ({modal.ok ? modal.tracked : "GPU"})</div>
                                {modal.ok ? (
                                    <>
                                        <div style={big}>{rand(modal)}</div>
                                        <div style={small}>${modal.usd.toFixed(2)} of ${modal.free_usd.toFixed(0)} free · ${modal.free_left_usd.toFixed(2)} left</div>
                                        <div style={small}>Stops at ${Number(modal.cap_usd).toFixed(2)} (your cap)</div>
                                    </>
                                ) : <div style={{ fontSize: "12px", color: "var(--text)" }}>{modal.error}</div>}
                            </div>
                        )}
                    </div>
                </>
            )}
        </span>
    );
}

// The activity feed button: gold while Sem is working, red dot after an error.
export function ActivityButton({ onFeed, hasError, busy }) {
    if (!onFeed) return null;
    return (
        <button onClick={onFeed} aria-label={hasError ? "Activity (has an error)" : "Activity"} title="Activity"
            style={{ ...iconBtn, color: busy ? "var(--gold)" : "var(--text-muted)" }}>
            <ActivityIcon size={18} />
            {hasError && <span style={{ position: "absolute", top: "4px", right: "4px", width: "7px", height: "7px", borderRadius: "50%", background: "var(--danger)", border: "1.5px solid var(--bg)" }} />}
        </button>
    );
}

// Master on/off switch for the whole assistant. While off, chat and every tab refuse new requests.
export function PowerSwitch({ token }) {
    const [on, setOn] = useState(null);
    const [locked, setLocked] = useState(false);
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
    useEffect(() => {
        if (!token) return;
        fetch(`${API}/power`, { headers }).then(r => (r.ok ? r.json() : null)).then(d => { if (d) { setOn(d.on); setLocked(!!d.locked); } }).catch(() => {});
    }, [token]); // eslint-disable-line react-hooks/exhaustive-deps
    if (on === null) return null;
    const flip = async () => {
        if (locked) return;
        const next = !on;
        setOn(next);
        try {
            const r = await fetch(`${API}/power`, { method: "PUT", headers, body: JSON.stringify({ on: next }) });
            if (!r.ok) setOn(!next);
        } catch { setOn(!next); }
    };
    return (
        <button onClick={flip} role="switch" aria-checked={on} aria-label="SNOWY on/off" title={locked ? "Switched off by the deploy (SNOWY_ENABLED=false in GitHub)" : on ? "SNOWY is on" : "SNOWY is off"}
            style={{ ...iconBtn, padding: "6px 4px", opacity: locked ? 0.5 : 1, cursor: locked ? "not-allowed" : "pointer" }}>
            <span style={{ width: "34px", height: "20px", borderRadius: "10px", position: "relative", transition: "background 0.15s",
                           background: on ? "var(--gold)" : "var(--border)" }}>
                <span style={{ position: "absolute", top: "2px", left: on ? "16px" : "2px", width: "16px", height: "16px", borderRadius: "50%",
                               background: "var(--bg)", transition: "left 0.15s" }} />
            </span>
        </button>
    );
}

// Right side of every tab's header: power switch + bill + activity.
export function HeaderStatus({ token, onFeed, hasError, busy }) {
    return (
        <span style={{ display: "inline-flex", alignItems: "center" }}>
            <PowerSwitch token={token} />
            <CostButton token={token} />
            <ActivityButton onFeed={onFeed} hasError={hasError} busy={busy} />
        </span>
    );
}

export default function StatusBar({ sessionId, title, streaming, onMenu, onTitleClick, onFeed, hasError, token }) {
    return (
        <div style={{ display: "flex", flexDirection: "column", background: "var(--bg)", borderBottom: "1px solid var(--border)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 8px 2px" }}>
                <button onClick={onMenu} aria-label="Menu" style={{ ...iconBtn, color: "var(--text)" }}><MenuIcon size={20} /></button>
                <span style={{ color: "var(--text)", fontWeight: "700", fontSize: "15px" }}>SNOWY</span>
                <span style={{ flex: 1 }} />
                <HeaderStatus token={token} onFeed={onFeed} hasError={hasError} busy={streaming} />
            </div>
            <button
                onClick={onTitleClick}
                title="Start a new chat"
                style={{
                    background: "none", border: "none", cursor: "pointer", textAlign: "left",
                    padding: "0 12px 8px 44px", margin: 0, fontSize: "12px", color: "var(--text-muted)",
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                }}
            >
                {title || sessionId}
            </button>
        </div>
    );
}
