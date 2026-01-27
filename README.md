# CRC-Results-Engine

CRC-Results-Engine is a native windows application developed, for Christ The Redeemer's College Christhill, to automate results and general documents preprocessing and dispatch

---

## 🚀 Features

- Multifile, Multipage PDF splitting
- bulk results/documents e-mail dispatching to students (default) or custom recipients

---

## 🛠️ Tech Stack

- Python / Framework
- os, threading, pathlib, tkinter, PyPDF2, datetime, email, smtplib
- Tools

---

## 📦 Installation

Clone the repository:
git clone https://github.com/GrandMEAN-RA/CRC-Results-Engine.git
cd CRC-Results-Engine

### Install dependencies:
pip install -r requirements.txt

---

## Usage
Run the project:
	python main.py
	
	Note:
	If message/email body text are is left blank, the program switch to the default in-coded message body.
---

## Project Structure
CRC-Results-Engine/
├── src/
├── tests/
├── README.md
├── requirements.txt
└── main.py

---

## Testing
	pytest

---

## Roadmap
- PDF Splitter 
- PDF Splitter + Basic automated mailing logic (predefined for students only)
- Mailing logic upgraded for custom sender-email and recipients selection (students, recipients)
- Mailing logic upgraded for custom message body 
- Mailing logic ugraded for single-file attachment 
- Mailing logic upgraded with email and password validation
- PDF Splitter upgraded with custom split chunk size.
<<<<<<< HEAD
=======
- Help menu for license information and analytics added
- License logic integration 
>>>>>>> updates

---

## Contributing
	Contributions are welcome!
	- Fork the repository
	- Create a feature branch (git checkout -b feature/my-feature)
	- Commit your changes (git commit -m "Add my feature")
	- Push to the branch (git push origin feature/my-feature)
	- Open a Pull Request

---

## Author
	GrandMEAN Research & Analytics
	GitHub: @GrandMEAN-RA

---

## Acknowledgements
	Inspiration
	Libraries or resources used