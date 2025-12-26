# -*- coding: utf-8 -*-
"""
Created on Wed Nov 12 23:06:58 2025

@author: EBUNOLUWASIMI
"""
# -*- coding: utf-8 -*-
"""
Document Splitter & Mailer GUI
Now with Email Sending Progress Bar
"""

import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from email.message import EmailMessage
import smtplib

# =====================================================
# 📁 Output folder handling
# =====================================================
def ensure_output_folder(base_dir, academic_session, term):
    output_dir = Path(base_dir) / academic_session / term
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

# =====================================================
# 🧾 PDF Split function
# =====================================================
def split_pdfs(input_dir, progress_bar, status_label, academic_session, term):
    output_dir = ensure_output_folder(input_dir, academic_session, term)
    total_files = 0
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    progress_bar["maximum"] = len(pdf_files)

    for idx, file_name in enumerate(pdf_files, start=1):
        pdf_path = os.path.join(input_dir, file_name)
        reader = PdfReader(pdf_path)
        for i in range(0, len(reader.pages), 2):
            writer = PdfWriter()
            for j in range(2):
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

# =====================================================
# 🧾 Send Emails function with progress
# =====================================================
def send_emails(password_var, email_var, input_dir, msg_text, progress_bar, status_label, term, academic_session):
    
    output_dir = ensure_output_folder(input_dir, academic_session, term)
    
    email = email_var if email_var else 'opeyemi.sadiku@crcchristhill.org'
    app_password = password_var
    
    try: 
        # Connect to the mail server
        smtp = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        
        smtp.login(email, app_password) 
        print("✅ Logged in successfully!")
    
        pdf_files = [f for f in os.listdir(output_dir) if f.lower().endswith(".pdf")]
        maximum = len(pdf_files)
        progress_bar["maximum"] = maximum
        status_label.config(text=f"Processing {maximum} files >>>")
        
        session = str(term) + str(academic_session)
        
        sent_count = 0
        for idx, pdf_file in enumerate(pdf_files, start=1):
            student_name = pdf_file.replace(".pdf", "")
            surname = student_name.split("_")[0].lower()
            firstname = student_name.split("_")[1].lower()
            
            msg_body = f"Dear {student_name},\n the entire management and staff of Christ  The Redeemer's College-Christhill warmly appreciate your efforts this term towards achieving good academic performance this term. We ubiquitously encourage you to push harder next term for better results. \n Please, find attached your results for {session} academic session"
            
            msg = EmailMessage()
            msg["From"] = email
            msg.set_content(msg_text) if msg_text else msg.set_content(msg_body)
            recipient = firstname + "." + surname + "@crcchristhill.org"
            msg["To"] = recipient
            msg["Subject"] = "Your Results Document"
            
            status_label.config(text=f"Sending {pdf_file} to {recipient}")
            smtp.send_message(msg)
            sent_count += 1
            progress_bar["value"] = idx
            status_label.config(text=f"Sent {idx}/{len(pdf_files)}: {pdf_file} to {recipient}")

        smtp.quit()
        status_label.config(text=f"All {sent_count} files mailed successfully!")
        messagebox.showinfo("Done", f"All {sent_count} files mailed successfully!")
    
    except smtplib.SMTPAuthenticationError: 
        status_label.config(text="❌ Authentication failed — please check your email or app password.")
        print("❌ Authentication failed — please check your email or app password.") 
    except Exception as e: 
        status_label.config(text=f"❌ An error occurred! — {e} . Please check your internet connection.")
        print(f"⚠️ An error occurred: {e}")
    
# ===================================================== # 
#🖥️ Splash Screen 
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
# 🖥 GUI
# =====================================================
def create_gui():
    
    # show splash first 
    root = tk.Tk()
    root.withdraw()  # Hide main window initially

    show_splash(root, duration=2500)

    root.title("DocuCore")
    #root.geometry("600x400")
    root.resizable(True, False)

    # Academic session
    month, year = datetime.now().month, datetime.now().year
    if month >= 9:
        academic_session = f"{year}-{year+1}"
        term = "Salvation Term"
    else:
        academic_session = f"{year-1}-{year}"
        term = "Victory Term" if month >= 4 else "Redemption Term"
    
    input_dir = tk.StringVar()
    
    def validate_butn(*args):
        split_butn.config(
            state='normal' if input_dir.get() else 'disabled'
            )
        send_butn.config(
            state='normal' if password_var.get() and email_var.get() else 'disabled'
            )
        
    input_dir.trace_add("write", validate_butn)
    
    # --- Frames ---
    pdf_frame = tk.LabelFrame(root, text="PDF Splitter", bd=3, relief="ridge")
    pdf_frame.pack(padx=20, pady=10, fill="x")
    mail_frame = tk.LabelFrame(root, text="Send Emails", bd=3, relief="ridge")
    mail_frame.pack(padx=20, pady=10, fill="x")
    status_frame = tk.LabelFrame(root, text="Status", bd=3, relief="ridge")
    status_frame.pack(padx=20, pady=10, fill="x")

    # --- PDF Splitter ---
    file_label = ttk.Label(pdf_frame, text="Select Input Folder:")
    file_label.pack(pady=5)
    file_entry = ttk.Entry(pdf_frame, textvariable=input_dir, width=55)
    file_entry.config(state="readonly")
    file_entry.pack(pady=5)
    browse_butn = ttk.Button(pdf_frame, text="Browse", command=lambda: input_dir.set(filedialog.askdirectory()))
    browse_butn.pack(pady=5)

    progress_bar = ttk.Progressbar(status_frame, orient="horizontal", length=500, mode="determinate")
    progress_bar.pack(pady=5)
    status_label = ttk.Label(status_frame, text="Status: Waiting")
    status_label.pack(pady=5)
    
    def run_split():
        threading.Thread(
            target=split_pdfs,
            args=(input_dir.get(), progress_bar, status_label, academic_session, term),
            daemon=True
        ).start()
            
    split_butn = ttk.Button(pdf_frame, text="Split PDFs",
               command=run_split, state = 'disabled')
    split_butn.pack(pady=5)
    
    # --- Sender Email & Message ---
    email_var = tk.StringVar()
    ttk.Label(mail_frame, text="Sender Email:").pack(pady=5)
    sender_entry = ttk.Entry(mail_frame, width=50, textvariable=email_var)
    sender_entry.pack(pady=5)
    ttk.Label(mail_frame, text="Message/Email Body:").pack(pady=5)
    msg_text = tk.Text(mail_frame, height=5, width=50)
    msg_text.pack(pady=5)

    # --- Password & progress ---
    password_var = tk.StringVar()
    password_label = ttk.Label(mail_frame, text="Enter Email Password:")
    password_label.pack(pady=5)
    password_entry = ttk.Entry(mail_frame, textvariable=password_var, show="*")
    password_entry.pack(pady=5)
    toggle_button = ttk.Button(mail_frame, text="Show")
    toggle_button.pack(pady=5)
    
    password_var.trace_add("write", validate_butn)
    
    def toggle_password():
        if password_entry.cget("show") == "":
            password_entry.config(show="*")
            toggle_button.config(text="Show")
        else:
            password_entry.config(show="")
            toggle_button.config(text="Hide")

    toggle_button.config(command=toggle_password)
    
    def run_mail():
        threading.Thread(
            target=send_emails,
            args=(password_var.get(), email_var.get(), input_dir.get(), msg_text, progress_bar, status_label, term, academic_session),
            daemon=True
        ).start()
    
    send_butn = ttk.Button(mail_frame, text="Dispatch Documents", command=run_mail, state = 'disabled')
    send_butn.pack(pady=5)    

    root.mainloop()

# =====================================================
if __name__ == "__main__":
    create_gui()
