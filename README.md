# ⚡ Power BI Desktop Automation

> **Automate the boring part of Power BI Desktop.**
> Discover `.pbix` reports → Open → Refresh → Save → Close → Repeat.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Power%20BI-Desktop-F2C811?logo=powerbi&logoColor=black" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/Automation-pywinauto-success" />
  <img src="https://img.shields.io/badge/Status-Active-brightgreen" />
</p>

<p align="center">
  <b>A lightweight Python automation tool for refreshing multiple Power BI Desktop reports without manually opening, refreshing, saving, and closing every PBIX file.</b>
</p>

---

## 🚀 What does it do?

Working with several Power BI Desktop reports often means repeating the same workflow:

```text
Open report → Wait → Refresh → Wait → Save → Close
```

Doing this manually for multiple reports is repetitive and time-consuming.

**Power BI Desktop Automation** turns that workflow into:

```text
Run the script → ☕ Let Python handle the rest
```

The automation automatically discovers every `.pbix` file in a configured directory and processes them sequentially.

---

## ✨ Features

| Feature                         | Description                                                           |
| ------------------------------- | --------------------------------------------------------------------- |
| 🔎 **Automatic PBIX Discovery** | Finds all `.pbix` files inside the configured directory               |
| 🚀 **Automatic Launch**         | Opens reports directly in Power BI Desktop                            |
| 🔄 **Automatic Refresh**        | Triggers Power BI's Refresh operation                                 |
| 👀 **Refresh Monitoring**       | Detects refresh progress and waits for completion                     |
| 💾 **Automatic Save**           | Saves the refreshed PBIX report                                       |
| ❌ **Automatic Close**           | Closes Power BI Desktop after processing                              |
| 📂 **Batch Processing**         | Processes multiple reports sequentially                               |
| ⏱️ **Timeout Protection**       | Prevents the automation from hanging indefinitely                     |
| 🛡️ **Error Handling**          | Handles individual report failures without silently crashing          |
| 📝 **Detailed Logging**         | Shows exactly what the automation is doing                            |
| ⌨️ **Fallback Control**         | Uses keyboard automation if the Refresh UI control cannot be detected |

---

# 🎯 The Problem

Imagine maintaining several Power BI reports:

```text
📁 BI Reports
│
├── Sales.pbix
├── Finance.pbix
├── Operations.pbix
├── Marketing.pbix
└── Executive_Dashboard.pbix
```

Every day you may need to:

1. Open `Sales.pbix`
2. Wait for Power BI to load
3. Click **Refresh**
4. Wait for the refresh
5. Save
6. Close Power BI
7. Open the next report
8. Repeat...

This project automates that entire cycle.

---

# ⚙️ Automation Workflow

```text
                START
                  │
                  ▼
        🔎 Find all PBIX files
                  │
                  ▼
       📊 Open Power BI Desktop
                  │
                  ▼
         ⏳ Wait for loading
                  │
                  ▼
           🔄 Start Refresh
                  │
                  ▼
      👀 Detect Refresh progress
                  │
                  ▼
       ⏳ Wait until completed
                  │
                  ▼
             💾 Save
                  │
                  ▼
       ❌ Close Power BI Desktop
                  │
                  ▼
          More PBIX files?
             │        │
            YES       NO
             │        │
             └────┐   ▼
                  │  END
                  ▼
             Next Report
```

---

# 🧠 How It Works

The project combines **Python**, **Windows UI Automation**, and **Power BI Desktop**.

The automation primarily uses:

```text
Python
   │
   ├── pywinauto
   │      └── Windows UI Automation
   │
   ├── pywin32
   │      └── Window management
   │
   └── Power BI Desktop
          ├── Open PBIX
          ├── Refresh
          ├── Save
          └── Close
```

### 🔄 Smart Refresh Strategy

Instead of relying entirely on keyboard shortcuts, the automation first tries to locate Power BI's actual **Refresh** ribbon control through Windows UI Automation.

```text
Find Refresh Button
        │
        ├── Found ─────► Click Refresh
        │
        └── Not Found
               │
               ▼
        Keyboard Fallback
               │
               ▼
          Alt → H → R
```

This makes the automation more resilient than a simple macro.

---

# 📁 Project Structure

```text
powerbi-desktop-automation/
│
├── 📁 src/
│   └── powerbi_automation.py
│
├── 📄 .env.example
├── 📄 .gitignore
├── 📄 LICENSE
├── 📄 README.md
├── 📄 requirements.txt
└── ⚙️ run.bat
```

---

# 🛠️ Requirements

Before running the project, make sure you have:

### Operating System

```text
Windows 10 / Windows 11
```

### Software

```text
Python 3.10+
Microsoft Power BI Desktop
```

### Python Dependencies

The project uses:

```text
pywinauto
pywin32
```

Install them using:

```bash
pip install -r requirements.txt
```

---

# 📥 Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/powerbi-desktop-automation.git
```

### 2️⃣ Enter the project

```bash
cd powerbi-desktop-automation
```

### 3️⃣ Create a virtual environment

```bash
python -m venv .venv
```

### 4️⃣ Activate it

```bash
.venv\Scripts\activate
```

### 5️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

You're ready. 🚀

---

# 🔧 Configuration

By default, the automation can use a directory such as:

```text
Desktop\BI
```

For example:

```text
C:\Users\YourUsername\Desktop\BI
```

You can configure your PBIX directory through the `PBIX_FOLDER` environment variable.

### PowerShell

```powershell
$env:PBIX_FOLDER="C:\Reports\PowerBI"
```

Then run:

```powershell
python src\powerbi_automation.py
```

---

## ⏱️ Advanced Configuration

Several timeout values can also be configured.

Example:

```env
PBIX_FOLDER=C:\Reports\PowerBI

POWER_BI_START_TIMEOUT_SECONDS=120
AFTER_OPEN_WAIT_SECONDS=60
REFRESH_START_TIMEOUT_SECONDS=45
REFRESH_TIMEOUT_SECONDS=7200
NO_DIALOG_SETTLE_SECONDS=30
CLOSE_TIMEOUT_SECONDS=60
POLL_INTERVAL_SECONDS=1
```

This is particularly useful for large Power BI models that require longer refresh times.

---

# ▶️ Usage

### Option 1 — Python

Run:

```bash
python src/powerbi_automation.py
```

### Option 2 — Windows

Simply run:

```text
run.bat
```

The automation will then start processing the available reports.

---

# 🖥️ Example

Suppose the configured directory contains:

```text
C:\Reports\PowerBI
│
├── Sales.pbix
├── Finance.pbix
└── Operations.pbix
```

The automation processes:

```text
Sales.pbix
    ↓
Finance.pbix
    ↓
Operations.pbix
```

without requiring you to manually repeat the workflow for every report.

---

# 📟 Example Output

```text
09:00:01 | INFO | Found 3 PBIX file(s) to process.

09:00:01 | INFO | [1/3] Sales.pbix
09:00:01 | INFO | Opening: Sales.pbix
09:01:12 | INFO | Power BI Desktop is ready
09:02:12 | INFO | Starting Refresh...
09:02:13 | INFO | Refresh progress window detected.
09:04:35 | INFO | Refresh completed.
09:04:35 | INFO | Saving PBIX...
09:04:40 | INFO | Save command completed.
09:04:40 | INFO | Closing: Sales.pbix
09:04:45 | INFO | Power BI Desktop closed.
09:04:45 | INFO | Done: Sales.pbix

...

09:15:24 | INFO | All 3 file(s) processed successfully.
```

---

# 🛡️ Error Handling

Automation should not fail silently.

If a report encounters an error, the program records the failure:

```text
ERROR | Failed on Finance.pbix
```

and attempts to restore a clean state before continuing.

At the end of the execution, failed reports are summarized.

```text
Completed with 1 failure(s):

- Finance.pbix
```

This makes troubleshooting considerably easier when processing multiple reports.

---

# 🔐 Security

### ⚠️ Never commit sensitive Power BI data.

The repository's `.gitignore` should exclude:

```text
*.pbix
*.pbit
.env
*.log
```

Never upload:

* 🔑 API keys
* 🔐 passwords
* 🗄️ database credentials
* 🏢 confidential company reports
* 📊 production datasets
* 🌐 private/internal endpoints

Use environment variables for machine-specific configuration.

---

# ⚠️ Important Notes

This project controls **Power BI Desktop through Windows UI Automation**.

It is **not an official Microsoft Power BI API integration**.

Because of this, automation may occasionally be affected by:

```text
Power BI Desktop UI updates
Authentication dialogs
Unexpected Power BI errors
Windows focus restrictions
Slow report loading
Dataset refresh failures
Power BI crashes
```

The project includes timeout handling, refresh detection, and fallback mechanisms to reduce these issues.

---

# 💡 When Is This Useful?

This project can be useful when:

* You maintain multiple local PBIX reports.
* Reports need periodic desktop refreshes.
* Reports depend on local files.
* Reports contain Python-based processing.
* Manual refresh workflows are taking too much time.
* Power BI Service refresh is not suitable for the workflow.
* You want to integrate Power BI Desktop into a larger Windows automation pipeline.

---

# 🗺️ Roadmap

Possible future improvements:

* [ ] Windows Task Scheduler integration
* [ ] Scheduled automatic execution
* [ ] Email/notification support
* [ ] Retry failed refreshes
* [ ] Config file support
* [ ] Per-report configuration
* [ ] Execution history
* [ ] Structured log files
* [ ] Screenshot capture on failure
* [ ] Power BI process monitoring
* [ ] n8n integration
* [ ] Automated report publishing workflow

---

# 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

If you find an issue, feel free to open a GitHub Issue.

For larger changes, consider opening an issue first to discuss the proposed improvement.

---

# ⭐ Support

If this project saves you time or helps automate your Power BI workflow, consider giving the repository a **⭐ Star**.

It helps others discover the project.

---

# 📜 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for details.

---

# 👩‍💻 Author

### Mona Faghfouri Azar

**Data Analytics • Python Automation • Power BI • AI & Automation**

Built to turn repetitive Power BI Desktop workflows into automated pipelines. ⚡

