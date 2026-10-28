# 💳 Digital Pay Ops Intelligence

An enterprise-grade operational intelligence prototype demonstrating how fintech digital payment companies monitor POS terminal installations, technician field service, and SLA compliance.

> **Important Context & Concept Disclaimer:**  
> This is an **independent concept project** inspired by publicly described fintech operations. It is **NOT** an official Digital Pay product. It does not use private company data, claim company endorsement, or fabricate real company performance metrics. All data is synthetically generated and labeled.

---

## 🚀 Key Features & Required Pages

1. **Executive Overview**
   - High-level KPI cockpit: Total Tickets, Open Tickets, SLA Compliance %, Average Resolution Time, High-Risk Overdue tickets.
   - Dynamic trend visualization of ticket inflows and status distributions.
   - Regional SLA compliance benchmark.
   - Synthesized list of prioritized operational actions and expected business impact.

2. **Ticket Explorer**
   - Interactive, searchable, and multi-filter table (Region, Status, Issue Type, Priority).
   - Global keyword search covering Ticket IDs and technician names.
   - Explicit visual badges identifying Overdue, At-Risk, Within-SLA, and Breached tickets.
   - One-click CSV export of filtered records.

3. **SLA Risk Monitor**
   - Transparent, deterministic classification engine:
     - **🔴 Overdue:** Unresolved ticket whose SLA deadline has elapsed (`current_time > deadline`).
     - **🟡 At Risk:** Unresolved ticket with $\le 20\%$ of allocated SLA duration remaining.
     - **🟢 Within SLA:** Resolved ticket completed on/before deadline, or open ticket with $> 20\%$ remaining time.
     - **🟣 Breached:** Resolved ticket completed after deadline.
   - Rigorous mathematical definition of SLA compliance:
     $$\text{SLA Compliance (\%)} = \left( \frac{\text{Resolved Tickets Within SLA}}{\text{Total Resolved Tickets}} \right) \times 100$$
   - Safe zero-denominator handling without runtime exceptions.
   - Focused triage table for tickets requiring immediate technician dispatch.

4. **Regional Insights**
   - Regional operational performance metrics across five simulated operating hubs (`Riyadh Metro`, `Jeddah Coastal`, `Dammam Eastern`, `Makkah Central`, `Medina North`).
   - Resolution velocity vs. compliance correlation chart.
   - Diagnostic commentary pinpointing operational bottlenecks and route efficiencies.

5. **Methodology & Compliance Spec**
   - In-depth documentation of synthetic dataset assumptions, SLA algorithms, and architectural boundaries.
   - Self-service inspection of raw synthetic ticket records.

---

## 🛠️ Architecture & Technology Stack

- **Frontend & App Framework:** Python & Streamlit
- **Data Engineering:** Pandas & NumPy
- **Interactive Visualizations:** Plotly Express & Plotly Graph Objects
- **Testing:** Python `unittest` framework (coverage of SLA logic, edge cases, and zero denominators)
- **Zero Cost / Zero External Dependencies:** No paid APIs, external AI endpoints, or cloud database credentials required.

---

## 💻 Local Setup & Execution Guide

### 1. Prerequisites
- Python 3.9+ or Python 3.10+
- Pip package manager

### 2. Installation
Clone or navigate to the project directory:
```bash
cd "c:\Users\salin\Desktop\data science project"
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run Automated Tests
Execute the unit test suite verifying SLA calculations and edge cases:
```bash
python tests_sla.py
```
*Expected output: `Ran 9 tests in ... OK`*

### 4. Launch the Interactive Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## ☁️ Streamlit Community Cloud Deployment

This repository is pre-configured for one-click deployment on Streamlit Community Cloud:
1. Push this repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository and set the main file path to:
   ```
   app.py
   ```
4. Click **Deploy**. The synthetic data generator will automatically initialize the local dataset upon first boot.

---

## 📸 Screenshots Guidance for Portfolio

When capturing screenshots for a design portfolio or case study:
1. **Executive Cockpit:** Capture the top 5 KPI cards alongside the inflow bar chart and regional compliance bar.
2. **SLA Risk Monitor:** Highlight the 4 colored SLA status metric cards (Overdue, At Risk, Within SLA, Breached) and the high-risk focus table.
3. **Ticket Explorer:** Showcase filtering by `Critical` priority and searching for a specific technician with color-coded risk pills.
4. **Regional Insights:** Capture the bubble scatter plot comparing resolution velocity against regional compliance rates.

---

## 📄 License
MIT License. Created strictly for portfolio and educational demonstration purposes.
