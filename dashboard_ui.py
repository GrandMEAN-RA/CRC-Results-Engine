
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from dashboard_data import get_dashboard_metrics
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from usage_analytics import get_usage_summary
from licenser import check_license
from key_generator import load_fernet_key
from cryptography.fernet import Fernet

def open_dashboard():

    def fmt_ratio(x: float) -> str:
        return f"{min(max(x, 0), 1) * 100:.1f}%"
    
    BASE_PATH =  Path(__file__).resolve().parent
    key = load_fernet_key(BASE_PATH)
    fernet = Fernet(key)

    try:
        license_status = check_license(fernet, BASE_PATH)
        metrics = get_dashboard_metrics(fernet, BASE_PATH)
        usage = get_usage_summary()
    except Exception as e:
        tk.messagebox.showerror("System Error", str(e))
        return

    win = tk.Toplevel()
    win.title("Docs Engine – Analytics Dashboard")
    win.geometry("520x900")
    
    if license_status.get("expired"):
        ttk.Label(
            win,
            text="License Expired – Dashboard Access Limited",
            foreground="red",
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=5)
    
    total = max(sum(usage.values()), 1)

    # --- License Status ---
    status_text = (
        f"License Active – {license_status['days_left']} days remaining"
        if not license_status["expired"]
        else "License Expired – Restricted Mode"
    )
    ttk.Label(win, text=status_text, font=("Segoe UI", 11, "bold")).pack(pady=5)

    dss_metrics = {
        "automation_ratio": usage.get("PDF_SPLIT", 0) / total,
        "communication_ratio": usage.get("EMAIL_SENT", 0) / total,
        "fallback_ratio": usage.get("SINGLE_FILE_ATTACHMENT", 0) / total
    }

    # --- KPI Card Visuals ---
    def card(label, value):
        frame = ttk.Frame(win, padding=10, relief="ridge")
        ttk.Label(frame, text=label, font=("Segoe UI", 9)).pack()
        ttk.Label(frame, text=str(value), font=("Segoe UI", 16, "bold")).pack()
        return frame

    card("Days to License Expiry", metrics["license_days_left"]).pack(fill="x", padx=10, pady=5)
    card("Total System Actions", metrics["total_actions"]).pack(fill="x", padx=10, pady=5)
    card("Emails Sent", metrics["emails_sent"]).pack(fill="x", padx=10, pady=5)
    card("PDF Splits", metrics["pdf_splits"]).pack(fill="x", padx=10, pady=5)
    card("Audit Events Logged", metrics["audit_events"]).pack(fill="x", padx=10, pady=5)
    card("automation_ratio", fmt_ratio(dss_metrics["automation_ratio"])).pack(fill="x", padx=10, pady=5)
    card("communication_ratio", fmt_ratio(dss_metrics["communication_ratio"])).pack(fill="x", padx=10, pady=5)
    card("fallback_ratio", fmt_ratio(dss_metrics["fallback_ratio"])).pack(fill="x", padx=10, pady=5)
    
    # --- Chart Data ---
    labels = list(usage.keys())
    values = list(usage.values())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # Bar chart
    ax1.bar(labels, values)
    ax1.set_title("Feature Usage Distribution")
    ax1.set_ylabel("Frequency")
    ax1.tick_params(axis="x", rotation=30)
    
    # Pie chart  
    dss = usage.get("PDF_SPLIT", 0) + usage.get("EMAIL_SENT", 0) # --- DSS Metric ---
    fallback = usage.get("SINGLE_FILE_ATTACHMENT", 1)

    ax2.pie(
        [dss, fallback],
        labels=["DSS-supported", "Fallback Mode"],
        autopct="%1.1f%%"
    )
    ax2.set_title("Decision Support vs Manual Operations")

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)







