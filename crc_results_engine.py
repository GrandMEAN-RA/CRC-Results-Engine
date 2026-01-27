# -*- coding: utf-8 -*-
"""
Created on Wed Nov 12 23:06:58 2025

@author: EBUNOLUWASIMI

Document Splitter & Mailer GUI
Now with Email Sending Progress Bar
"""

import os
import re
import threading
import pandas as pd
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from email.message import EmailMessage
import smtplib
from licenser import bootstrap_license, ensure_license, get_branding, check_license
from licenser import show_expiry_warning, apply_license_renewal
from admin_override import validate_admin_key
from audit_logger import log_event
from dashboard_ui import open_dashboard
from usage_analytics import track
from dropbox_service import auto_uploader
from whatsapp_service import send_whatsapp
from message_template import email_template, whatsapp_template

# =====================================================
# Auto-generate license
# =====================================================
BASE_PATH =  Path(__file__).resolve().parent
fernet = bootstrap_license(BASE_PATH) # Generate license on first run
license_status = ensure_license(fernet, BASE_PATH) #Only validate existing license on subsequent runs

# =====================================================
# Output folder handling
# =====================================================
def ensure_output_folder(base_dir, academic_session, term):
    output_dir = Path(base_dir) / academic_session / term
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

# =====================================================
# PDF Split function
# =====================================================
def split_pdfs(input_dir, chunk_var, progress_bar, status_label, academic_session, term):
    output_dir = ensure_output_folder(input_dir, academic_session, term)

    chunk = int(chunk_var) if chunk_var != 'chunk size'  else 2
    
    total_files = 0
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    progress_bar["maximum"] = len(pdf_files)

    for idx, file_name in enumerate(pdf_files, start=1):
        pdf_path = os.path.join(input_dir, file_name)
        reader = PdfReader(pdf_path)
        for i in range(0, len(reader.pages), chunk):
            writer = PdfWriter()
            for j in range(chunk):
                if i+j < len(reader.pages):
                    writer.add_page(reader.pages[i+j])
            page_text = reader.pages[i].extract_text().splitlines()
            student_name = page_text[3].strip().replace(" ", "_") if len(page_text) > 3 else f"student_{i//2 + 1}"
            
            output_pdf = output_dir / f"{student_name}.pdf"
            output_pdf.parent.mkdir(parents=True, exist_ok=True)
        
            if output_pdf.exists():
                output_pdf.unlink()
            with open(output_pdf, "wb") as f:
                writer.write(f)
            total_files += 1

        progress_bar["value"] = idx
        status_label.config(text=f"Processing PDFs: {file_name} ({idx}/{len(pdf_files)})")
        progress_bar.update_idletasks()

    status_label.config(text=f"Splitting complete: {total_files} files created.")
    messagebox.showinfo("Done", f"Total files created: {total_files}")
    log_event(event="PDF_SPLIT", detail=f"Input folder: {input_dir}", base_path=BASE_PATH)
    track("PDF_SPLIT")

# =====================================================
# Send Emails function with progress
# =====================================================
def send_emails(password_var, email_var, input_dir, halfterm_var, whatsapp_var, sfa_file_path, category_var, cr_file_path, msg_text, progress_bar, status_label, term, academic_session):
    
    sfa = sfa_file_path
    category = category_var
    cr_path = cr_file_path
    email = email_var if email_var else 'results@crcchristhill.org'
    app_password = password_var

    output_dir = ensure_output_folder(input_dir, academic_session, term) if not sfa else sfa_file_path

    if whatsapp_var:
         media_link = auto_uploader(output_dir, term, academic_session, sfa, status_label)
    
    try: 
        # Connect to the mail server
        smtp = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        
        smtp.login(email, app_password)
        status_label.config(text=f"✅ Logged in successfully!")
        print("✅ Logged in successfully!")
        
        sent_count = whatsapp_count = mail_count = 0
        
        if not sfa:
            pdf_files = [f for f in os.listdir(output_dir) if f.lower().endswith(".pdf")]
            
            session = str(term) + " " + str(academic_session) if not halfterm_var else str(term) + " " + str(academic_session) + " Half-term"
            session = session.replace('_',' ')
            
            maximum = len(pdf_files)
            progress_bar["maximum"] = maximum
            status_label.config(text=f"Processing {maximum} files >>>")
            
            for idx, pdf_file in enumerate(pdf_files, start=1):
                try:
                    msg = EmailMessage()
                    msg["From"] = email
                    
                    student_name = pdf_file.replace(".pdf", "")
                    surname, firstname = student_name.split("_", 1)
                    student_name = student_name.replace('_',' ')
                    surname = surname.title()
                    firstname = firstname.title()
                    
                    recipient = phone = None
                    
                    if category == "Students":
                        whatsapp_var.set(0)
                        
                        recipient = f"{firstname.lower()}.{surname.lower()}@crcchristhill.org"
                        msg["Subject"] = f"Your {session} Results Document"
                        msg_body = email_template(student_name, firstname, surname, session, category, halfterm_var)
                        
                    elif category == "Recipients":
                        if cr_path.endswith(".xlsx"):
                            df = pd.read_excel(cr_path)
                        elif cr_path.endswith(".csv"):
                            df = pd.read_csv(cr_path)
                        else:
                            raise ValueError("Recipients file must be CSV or XLSX")
                    
                        student_col = email_col = phone_col = None
                        
                        for col in df.columns:
                            if col.lower() in ("students","students name","student name","wards","child","wards' name","child's name","students' name","student's name"):
                                student_col = col
                            elif col.lower() in ("email","emails","mails","e-mails", "parent mail","parents email","recipient email","parents or guardians e-mail",
                                                 "parent or guardian e-mail", "parent or guardian email", "parents or guardians email"):
                                email_col = col
                            elif col.lower() in ("phone number","phone_number","phone no","phone_no","contact number","contact_no", "whatsapp number", "whatsapp no"):
                                phone_col = col

                        if not student_col or not email_col:
                            raise ValueError("Required columns missing in recipients file")
                        
                        row = df[df[student_col].astype(str).str.lower() == student_name.lower()]
                        
                        if row.empty:
                            continue
                        
                        recipient = row.iloc[0][email_col] if email_col in row else None
                        phone = row.iloc[0][phone_col] if phone_col in row else None
                       
                        msg["Subject"] = f"{session} Results Document for {student_name}"
                        msg_body = email_template(student_name, firstname, surname, session, category, halfterm_var)
                        
                    if recipient:
                        msg["To"] = recipient
                        msg.set_content(msg_text if msg_text else msg_body)
                         
                        with open(os.path.join(output_dir, pdf_file), "rb") as f:
                            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=pdf_file)
                         
                        status_label.config(text=f"Sending {pdf_file} to {recipient} >>> ")
                        smtp.send_message(msg)
                        status_label.config(text=f"Dispatched {pdf_file} to {recipient}")
                        print("Mail Service executed")

                        mail_count += 1
                        
                    if whatsapp_var and phone:
                        media_url = media_link[pdf_file]
                        message = whatsapp_template(student_name, firstname, surname, session, halfterm_var, msg_text, media_url)

                        status_label.config(text=f"Sending {pdf_file} to +{phone} >>> ")
                        send_whatsapp(phone, message)
                        status_label.config(text=f"Dispatched {pdf_file} to +{phone}")
                        print("whatsapp service executed")

                        whatsapp_count += 1
                    
                    if recipient or phone:
                        sent_count += 1
                        progress_bar["value"] = sent_count
                        status_label.config(text=f"Sent {sent_count}/{len(pdf_files)}: {pdf_file} to mail-{recipient} & phone-+{phone}")
                        log_event(event="EMAIL_SENT", detail=f"File: {pdf_file} | Recipient: {recipient} & +{phone}", base_path=BASE_PATH)
                        track("EMAIL_SENT")
                        track("MULTI-FILE SPLIT OPERATION")

                except Exception as e:
                    status_label.config(text=f"Send failed! | {pdf_file} to {recipient}")
                    log_event(
                        event="SEND_FAILED",
                        detail=f"{pdf_file} | {e}",
                        base_path=BASE_PATH
                    )
                    continue
                    
        elif sfa:
            file_name = sfa.split('/')[-1]
            msg_body = f"Please refer to the attached {file_name} document. \n Regards."
            
            if cr_path.endswith(".xlsx"):
                df = pd.read_excel(cr_path)
            elif cr_path.endswith(".csv"):
                df = pd.read_csv(cr_path)
            else:
                raise ValueError("Recipients file must be CSV or XLSX")

            mail_col = phone_col = None
            for col in df.columns:
                if col.lower() in ("email","emails","mails","e-mails", "parent mail","parents email","recipient email","parents or guardians e-mail",
                                   "parent or guardian e-mail", "parent or guardian email", "parents or guardians email"):
                    mail_col = col
                    maximum = df[mail_col].shape[0]
                    progress_bar["maximum"] = maximum
                    status_label.config(text=f"Processing {maximum} files >>>")
                    
                elif col.lower() in ("phone number","phone_number","phone no","phone_no","contact number","contact_no", "whatsapp number", "whatsapp no"):
                    phone_col = col
                    
            for item in df[mail_col]:
                msg = EmailMessage()
                msg["From"] = email
                recipient = item
                phone = df.loc[df[mail_col] == item, phone_col].values[0]
                msg["Subject"] = f"{file_name} document attached"
                msg.set_content(msg_text if msg_text else msg_body)
                      
                if recipient:
                    msg["To"] = recipient
                
                    with open(sfa, "rb") as f:
                        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=file_name)
                
                    status_label.config(text=f"Sending {file_name} to {recipient} >>> ")
                    smtp.send_message(msg)
                    status_label.config(text=f"Dispatched {file_name} to {recipient}")
                    print("Mail Service executed")

                    mail_count += 1
                    
                if whatsapp_var and phone:
                    media_url = media_link[file_name]
                    message = msg_text + " " + f"\n{file_name} link here: {media_url}" if msg_text else msg_body + " " + f"\n{file_name} link here: {media_url}" 

                    status_label.config(text=f"Sending {file_name} to +{phone} >>> ")
                    send_whatsapp(phone, message)
                    status_label.config(text=f"Dispatched {file_name} to +{phonr}")
                    print("whatsapp service executed")

                    whatsapp_count += 1
                
                sent_count += 1
                progress_bar["value"] = sent_count
                status_label.config(text=f"Sent {sent_count}/{maximum}: {file_name} to mail-{recipient} & phone-{phone}")
                log_event(event="EMAIL_SENT", detail=f"File: {file_name} | Recipient: {recipient} & +{phone}", base_path=BASE_PATH)
                track("EMAIL_SENT")
                track("SINGLE_FILE_ATTACHMENT")                   
               
        smtp.quit()
        status_label.config(text=f"All {sent_count} files dispatched successfully!")
        messagebox.showinfo("Done", f"All {sent_count} files dispatched successfully! \nEmail: {mail_count} \nWhatsapp: {whatsapp_count}")
        print("The service is up and running")
    
    except smtplib.SMTPAuthenticationError: 
        status_label.config(text="❌ Authentication failed — please check your email or app password.")
        print("❌ Authentication failed — please check your email or app password.") 
    except Exception as e: 
        status_label.config(text=f"❌ An error occurred! — {e} . Please check your internet connection.")
        print(f"⚠️ An error occurred: {e}")
    
# ===================================================== # 
# Splash Screen 
# ===================================================== 
def show_splash(root, duration=2000):
    """
    Displays a splash screen for the given duration (ms)
    without blocking the main Tkinter app.
    """

    splash = tk.Toplevel(root)
    splash.overrideredirect(True)  # Remove title bar

    width, height = 400, 250
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    splash.geometry(f"{width}x{height}+{x}+{y}")
    splash.configure(bg="white")

    # --- Splash Content ---
    ttk.Label(
        splash,
        text="CRC Docs",
        font=("Segoe UI", 22, "bold")
    ).pack(pady=(50, 10))

    ttk.Label(
        splash,
        text="Document Processing Engine",
        font=("Segoe UI", 11)
    ).pack()

    ttk.Label(
        splash,
        text="Loading...",
        font=("Segoe UI", 10)
    ).pack(pady=15)

    progress = ttk.Progressbar(
        splash,
        orient="horizontal",
        length=250,
        mode="indeterminate"
    )
    progress.pack(pady=10)
    progress.start(10)

    # Close splash after duration
    def close_splash():
        progress.stop()
        splash.destroy()
        root.deiconify()  # Show main window

    root.after(duration, close_splash)
        
# =====================================================
# GUI
# =====================================================
def create_gui():
    # Form events handlers
    def on_entry_click(event):
        if chunk_entry.get() == 'chunk size':
            chunk_entry.delete(0, tk.END)
            chunk_entry.config(fg='black')
        chunk_entry.unbind('<FocusIn>')

    def on_focus_out(event):
        if chunk_entry.get() == '':
            chunk_entry.insert(0, 'chunk size')
            chunk_entry.config(fg='grey')
            chunk_entry.bind('<FocusIn>', on_entry_click)

    # Admin license override
    def admin_override():
        key = tk.simpledialog.askstring(
            "Admin Override",
            "Enter admin override key:",
            show="*"
        )
        if key and validate_admin_key(key):
            license_status["expired"] = False
            status_label.config(
                text="⚠ ADMIN OVERRIDE ACTIVE — All features unlocked."
            )
            messagebox.showwarning(
                "Admin Override",
                "Admin override enabled.\nUse for emergency purposes only."
            )
            log_event(event="ADMIN_OVERRIDE", detail="Admin override activated", base_path=BASE_PATH)
            track("ADMIN_OVERRIDE")
        log_event(event="ADMIN_OVERRIDE", detail="Admin override failed", base_path=BASE_PATH)
        track("ADMIN_OVERRIDE")
                         
    root = tk.Tk()

    apply_license_renewal(fernet, BASE_PATH) # Check for license renewal

    # Check license
    license_status = check_license(fernet, BASE_PATH)
    if not license_status.get("expired", True) and license_status.get("days_left") <= license_status.get("notice_days"):
        show_expiry_warning(license_status.get("days_left"))
    
    root.withdraw()  # Hide main window initially

    show_splash(root, duration=2500) # show splash first

    log_event(event="APP_START", detail="CRC Docs launched", base_path=BASE_PATH)
    track("APP_START")

    # Get licensee's brand identity
    branding = get_branding(fernet, BASE_PATH)
    print(branding)
    root.title(f"{branding.get('short_name')} – Docs Engine")
    """
    header = ttk.Label(
        root,
        text=branding.get("school_name"),
        font=("Segoe UI", 14, "bold")
    )
    header.pack(pady=3)
    """
    root.resizable(False, False)

    # Help menu bar
    menubar = tk.Menu(root) 
    help_menu = tk.Menu(menubar, tearoff=0)

    def show_license_info():
        lic = check_license(fernet, BASE_PATH)
        messagebox.showinfo(
            "License Information:",
            f"Licensed to: {lic.get('licensed_to')}\n"
            f"Days remaining: {lic.get('days_left')}\n"
            f"Status: {'Expired' if lic.get('expired') else 'Active'}"
        )

    help_menu.add_command(label="License Info", command=show_license_info)
    help_menu.add_command(label="Admin Override", command=admin_override)
    help_menu.add_command(label="Analytics Dashboard", command=open_dashboard)
    menubar.add_cascade(label="Help", menu=help_menu)
    root.config(menu=menubar)

    # Academic session
    month, year = datetime.now().month, datetime.now().year
    if month >= 9:
        academic_session = f"{year}_{year+1}"
        term = "Salvation_Term"
    else:
        academic_session = f"{year-1}_{year}"
        term = "Victory_Term" if month >= 4 else "Redemption_Term"
    
    input_dir = tk.StringVar()
    sfa_file_path = tk.StringVar()
      
    # =====================================================
    # Validation logic
    # =====================================================
    VALID_DOMAIN = "@crcchristhill.org"
    OFFICIAL_EMAIL = "results@crcchristhill.org"

    def is_valid_email(email: str) -> bool:
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        if not email:
            return False
        if not re.match(pattern, email):
            return False
        if not email.lower().endswith(VALID_DOMAIN):
            return False
        if email.lower() != OFFICIAL_EMAIL:
            return False
        return True
    
    def validate_email_ui(event=None):
        email = email_var.get().strip()
        if not email:
            status_label.config(text="", foreground="black")
            return False
        if is_valid_email(email):
            status_label.config(text="✔️ Valid email", foreground="green")
            return True
        else:
            status_label.config(text="Invalid email ❌", foreground="red")
            return False
        
    def is_valid_password(password: str) -> bool:
        if not password:
            return False
        if len(password) != 16: 
            return False
        return True

    def validate_password_ui(event=None):
        password = password_var.get().strip()
        if not password:
            status_label.config(text="", foreground="black")
            return False 
        if is_valid_password(password): 
            status_label.config(text="✔️ Password OK!", foreground="green")
            password = password.encode("utf-8").decode("utf-8")
            return password
        else:
            status_label.config(text=f"You have entered {len(password)} characters. App password MUST be 16 characters long.", foreground="red")
            return False

    def validate_butn(*args):
        if custom_var.get() == 'sfa':
            split_butn.config(state='disabled')
        if custom_var.get() == 'chunk' and input_dir.get():
            split_butn.config(state='normal')
        else:
            split_butn.config(state='disabled')

        if msg_body_var.get()==1 and validate_email_ui() and validate_password_ui():
            if (custom_var.get() == 'sfa' and sfa_file_path.get()) or (custom_var.get() == 'chunk' and input_dir.get()):
                if category_var.get()=="Students":
                    send_butn.config(state='normal' if msg_text.get("1.0", "end").strip() else 'disabled')
                elif category_var.get()=="Recipients" and cr_file_path.get():
                    send_butn.config(state='normal' if msg_text.get("1.0", "end").strip() else 'disabled')
                else:
                    send_butn.config(state='disabled')
            else:
                send_butn.config(state='disabled')
        elif validate_email_ui() and validate_password_ui():
            if (custom_var.get() == 'sfa' and sfa_file_path.get()) or (custom_var.get() == 'chunk' and input_dir.get()):
                if category_var.get()=="Students":
                    send_butn.config(state='normal')
                elif category_var.get()=="Recipients" and cr_file_path.get():
                    send_butn.config(state='normal')
                else:
                    send_butn.config(state='disabled')
            else:
                send_butn.config(state='disabled')
        else:
            send_butn.config(state='disabled')
                 
    input_dir.trace_add("write", validate_butn)
    sfa_file_path.trace_add("write", validate_butn)
    
    # --- Frames ---
    pdf_frame = tk.LabelFrame(root, text="PDF Splitter", bd=3, relief="ridge")
    pdf_frame.pack(padx=20, pady=3, fill="x")
    check_frame = tk.LabelFrame(pdf_frame, text="custom settings", bd=1, relief="solid")
    check_frame.pack(pady=2)
    mail_frame = tk.LabelFrame(root, text="Email Dispatcher", bd=3, relief="ridge")
    mail_frame.columnconfigure(0, weight=1)  # left spacer
    mail_frame.columnconfigure(1, weight=0)  # content
    mail_frame.columnconfigure(2, weight=1)  # right spacer
    mail_frame.pack(padx=20, pady=3, fill="x")
    recipient_frame = tk.LabelFrame(mail_frame, text="Recipient Category", bd=1, relief="solid")
    recipient_frame.grid(row=0, column=1, pady=2)
    status_frame = tk.LabelFrame(root, text="Status", bd=3, relief="ridge")
    status_frame.pack(padx=20, pady=3, fill="x")

    # --- PDF Splitter ---
    def update_label_text():
        if license_status["expired"]:  #Check license
            custom_var.set('sfa')
            sfa_butn.config(state="disabled")
            chunk_butn.config(state="disabled")
            split_butn.config(state="disabled")
            student_check.config(state="disabled")
            recipient_check.config(state="disabled")
            whatsapp.config(state="disabled")

            file_label.config(text="Select file to attach:")
            file_entry.config(textvariable=sfa_file_path)

            status_label.config(
                text="⚠ License expired — Only Single File Attachment is available."
            )
            return

        # Normal behaviour
        if custom_var.get() == 'sfa':
            file_label.config(text="Select file to attach:")
            file_entry.config(textvariable=sfa_file_path)
            student_check.config(text="",state='disable')
        else:
            file_label.config(text="Select input folder:")
            file_entry.config(textvariable=input_dir)
            student_check.config(text="Students",state='normal')
        
    # --- User Parameters ---
    custom_var = tk.StringVar(value="None")
    custom_var.trace_add("write", validate_butn)
    
    sfa_butn = ttk.Radiobutton(check_frame, value="sfa", variable=custom_var, command=update_label_text)
    sfa_butn.config(text='Single file attachment', state='normal')
    sfa_butn.grid(row=0, column=0, pady=2)
    chunk_butn = ttk.Radiobutton(check_frame, text="Process files", value="chunk", variable=custom_var)
    chunk_butn.grid(row=0, column=1, padx=2, pady=2)

    chunk_var = tk.StringVar(value="chunk size")
    chunk_entry = tk.Entry(check_frame, width=10, textvariable=chunk_var, fg='grey')
    chunk_entry.bind('<FocusIn>', on_entry_click)
    chunk_entry.bind('<FocusOut>', on_focus_out)
    chunk_entry.grid(row=0, column=2, pady=2, padx=1)
    chunk_entry.grid_remove()
    custom_var.trace_add("write", lambda *args: chunk_entry.grid() if custom_var.get()=='chunk' else chunk_entry.grid_remove())
    custom_var.trace_add("write", lambda *args: update_label_text())
    
    file_label = ttk.Label(pdf_frame, text="Select input folder")
    file_label.pack(pady=2)
    file_entry = ttk.Entry(pdf_frame, width=55, state="readonly")
    file_entry.pack(pady=2)
    file_entry.config(textvariable=input_dir)
    
    browse_butn = ttk.Button(pdf_frame, text="Browse", command=lambda: input_dir.set(filedialog.askdirectory()) if custom_var.get() == 'chunk' else sfa_file_path.set(filedialog.askopenfilename()))
    browse_butn.pack(pady=2)

    progress_bar = ttk.Progressbar(status_frame, orient="horizontal", length=500, mode="determinate")
    progress_bar.pack(pady=2)
    status_label = ttk.Label(status_frame, text="Status: Waiting", wraplength=150)
    status_label.pack(pady=12)
    brand_label = ttk.Label(status_frame, text=branding["footer_text"])
    brand_label.pack(pady=2)

    #Split thread
    def run_split():
        if license_status["expired"]:  #Check license
            messagebox.showerror(
                "License Expired",
                "PDF splitting is disabled.\n\nOnly Single File Attachment is permitted."
            )
            return
         #Normal behaviour
        threading.Thread(
            target=split_pdfs,
            args=(input_dir.get(), chunk_var.get(), progress_bar, status_label, academic_session, term),
            daemon=True
        ).start()
            
    split_butn = ttk.Button(pdf_frame, text="Split PDFs",
               command=run_split, state = 'disabled')
    split_butn.pack(pady=2)
    
    category_var = tk.StringVar(value="None")
    cr_file_path = tk.StringVar()

    #Upload recipient file
    def validate_cr():
        messagebox.showinfo("Attention!", "Please select a CSV or XLSX file")
        cr_ok = category_var.get() == "Recipients"
        
        cr_file_path.set(filedialog.askopenfilename(
            filetypes=[("CSV/Excel files","*.csv *.xlsx")]))
        
        # Validate file if PG is selected 
        if cr_ok:
            file_path = cr_file_path.get() 
            if file_path: 
                ext = os.path.splitext(file_path)[1].lower() 
                if ext in [".csv", ".xlsx"]: 
                    messagebox.showinfo("Recipients File Loaded", f"Recipients file loaded:\n{file_path}") 
                    return file_path
                elif ext not in [".csv", ".xlsx"]: 
                    messagebox.showinfo("Invalid file type!", "Ensure the selected file is a CSV or XLSX file")
                    return False
            elif not file_path:
                messagebox.showinfo("Attention!", "Select a file and ensure the selected file is a CSV or XLSX file")
                return False
    
    cr_frame = ttk.Frame(recipient_frame)
    upload_butn = ttk.Button(cr_frame, text="Browse",
                            command=validate_cr )
    upload_butn.pack(pady=2)
    cr_frame.grid(row=1, column=0, columnspan=2)
    cr_frame.grid_remove()
    category_var.trace_add("write", lambda *args: cr_frame.grid() if category_var.get()=="Recipients" else cr_frame.grid_remove())
    category_var.trace_add("write", lambda *args: validate_butn())
    
    # --- Sender Email & Message body ---
    email_var = tk.StringVar()
    ttk.Label(mail_frame, text="Sender Email:").grid(row=3, column=1, pady=2)
    sender_entry = ttk.Entry(mail_frame, width=50, textvariable=email_var)
    sender_entry.grid(row=4, column=1, pady=2)
    sender_entry.bind("<FocusOut>", validate_email_ui)
    sender_entry.bind("<KeyRelease>", validate_butn)
    
    msg_body_var = tk.IntVar()
    msg_body = ttk.Checkbutton(mail_frame, text="Set message body text", variable=msg_body_var)
    msg_body.grid(row=5, column=1, pady=2)
    whatsapp_var = tk.IntVar()
    whatsapp = ttk.Checkbutton(mail_frame, text="Dispatch to Whatsapp", variable=whatsapp_var)
    whatsapp.grid(row=6, column=1, pady=2)
    halfterm_var = tk.IntVar()
    halfterm = ttk.Checkbutton(mail_frame, text="Half-term", variable=halfterm_var)
    halfterm.grid(row=7, column=1, pady=2)
    
    text_frame = ttk.Frame(mail_frame)
    text_frame.grid(row=8, column=1, sticky="ew", pady=5)
    text_frame.columnconfigure(0, weight=1)  # left spacer
    text_frame.columnconfigure(1, weight=0)  # content
    text_frame.columnconfigure(2, weight=1)  # right spacer
    text_frame.grid_remove()
    msg_label = ttk.Label(text_frame, text="Message / Email Body text:")
    msg_label.grid(row=0, column=1, sticky="w")
    msg_text = tk.Text(text_frame, height=2, width=50, wrap="word")
    msg_text.grid(row=1, column=1)
    msg_text.bind("<KeyRelease>", validate_butn)
    msg_body_var.trace_add("write", lambda *args: text_frame.grid() if msg_body_var.get()==1 else text_frame.grid_remove())
    msg_body_var.trace_add("write", validate_butn)
    
    # --- Recipient Selection ---
    student_check = ttk.Radiobutton(recipient_frame, value="Students", variable=category_var)
    student_check.config(text='Students', state='normal')
    student_check.grid(row=0, column=0, padx=20)
    recipient_check = ttk.Radiobutton(recipient_frame, text="Upload Recipients file", value="Recipients", variable=category_var)
    recipient_check.grid(row=0, column=1, padx=20)

    # --- Password & progress ---
    password_var = tk.StringVar()
    password_label = ttk.Label(mail_frame, text="Enter 16-character Email App Password:")
    password_label.grid(row=9, column=1, pady=2)
    password_entry = ttk.Entry(mail_frame, width=50, textvariable=password_var, show="*")
    password_entry.grid(row=10, column=1, pady=2)
    password_entry.bind("<FocusOut>", validate_password_ui)
    password_entry.bind("<KeyRelease>", validate_butn)
    toggle_button = ttk.Button(mail_frame, text="Show")
    toggle_button.grid(row=11, column=1, pady=2)
    
    def toggle_password():
        if password_entry.cget("show") == "":
            password_entry.config(show="*")
            toggle_button.config(text="Show")
        else:
            password_entry.config(show="")
            toggle_button.config(text="Hide")

    toggle_button.config(command=toggle_password)

    #Email dispath thread
    def run_mail():
        threading.Thread(
            target=lambda: send_emails(password_var.get(), email_var.get(), input_dir.get(), halfterm_var.get(), whatsapp_var.get(), sfa_file_path.get(), category_var.get(), cr_file_path.get(), msg_text.get("1.0","end-1c"), progress_bar, status_label, term, academic_session),
            daemon=True
        ).start()
    
    send_butn = ttk.Button(mail_frame, text="Dispatch Documents", command=run_mail, state = 'disabled')
    send_butn.grid(row=12, column=1, pady=2)

    root.mainloop()

# =====================================================
if __name__ == "__main__":
    create_gui()
