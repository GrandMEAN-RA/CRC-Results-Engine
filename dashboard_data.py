
from usage_analytics import get_usage_summary
from licenser import check_license
from audit_logger import read_audit_log

def get_dashboard_metrics(fernet, BASE_PATH):
    usage = get_usage_summary()
    license_status = check_license(fernet, BASE_PATH)
    audit_entries = read_audit_log(base_path=BASE_PATH)

    return {
        "license_days_left": license_status["days_left"],
        "license_expired": license_status["expired"],
        "total_actions": sum(usage.values()),
        "emails_sent": usage.get("EMAIL_SENT", 0),
        "pdf_splits": usage.get("PDF_SPLIT", 0),
        "single_file_ops": usage.get("SINGLE_FILE_ATTACHMENT", 0),
        "audit_events": len(audit_entries)
    }
