# RORA: Seeing Dropout Before It Happens

*Built for the 2026 NISR Big Data Hackathon (Open Innovation track).*

**Live app:** https://rora-app-ciit.onrender.com

**Watch how it works (demo video):** https://youtu.be/vTrm9Egufrc

---

## A student we would have missed

Picture a girl in Upper Primary in Nyagatare. (She's a composite, but she is real in every way that matters.) She comes to school every day. Her attendance is 90%. No register would ever flag her.

But her marks have been sliding for two terms. Her family's meal contributions are unpaid, and she sits in the room while other children eat. The dry season has been long, and her parents are quietly running out of options. One morning she doesn't come back, and nobody can say exactly when it started.

Today's monitoring looks at one number, attendance, and she passed that test right up to the day she left.

**RORA exists so that the next time this happens, someone knows months earlier.**

---

## What RORA does

RORA is an education early-intervention platform for Rwanda. It connects the national picture, which planners need, with the individual child, whom teachers can actually help.

We bring four sources together that normally never meet:

1. **NISR EICV7 (2023/24):** District Primary NAR, Secondary NAR, repetition rates, and household poverty profiles.
2. **MINEMA & Meteo Rwanda:** Disaster vulnerability indices for drought, flood, and landslide exposure.
3. **SDMS / NESA:** Student-level term marks, academic trajectory, and repetition history.
4. **Social Protection & Community (Ubudehe & VUP):** Household Ubudehe categories and school feeding fee arrears.

Then it answers the question that matters: **which child is about to fall, why, and what would help?**

---

## Why attendance alone fails

Dropout is rarely one event. It's usually several pressures stacking up quietly:

- **Academic collapse.** A child can attend 90% of days while marks fall below passing. They're present, but they've stopped believing school is for them.
- **Money.** Unpaid school feeding contributions remain a direct reason children are pushed out of rural schools.
- **Climate.** Dry spells in the Eastern Province (Nyagatare, Kayonza, Bugesera) and heavy rain and landslides in the West and North (Rutsiro, Ngororero, Gicumbi) disrupt livelihoods, and school is often the first thing a family has to give up.

RORA reads these signals together in one calibrated model, so no single missing number hides a child in trouble.

**Alignment:** This supports NST2 and Vision 2050 goals on quality education, human capital, and reducing inequality.

---

## One platform, three people who need it

Each role gets its own console, built around the decisions that person actually makes.

### The National Planner (`planner` / `planner123`)
*"Where should limited resources go first?"*
- **Composite Vulnerability Ranking:** Combines poverty, repetition, climate hazards, and net attendance.
- **Geographic Vulnerability Map:** An interactive map of Rwanda's 30 districts.
- **Targeted Resource Simulator:** Estimates the effect of emergency school feeding bursaries and remedial teacher packages in priority districts.

### The Policy & Data Analyst (`analyst` / `analyst123`)
*"What's really driving this, and what if things get worse?"*
- **Cross-Sector Correlation Engine:** Interactive scatter analysis of poverty, climate risk, and repetition.
- **Model Diagnostics:** Log-odds weights, Odds Ratios, and plain-language interpretations.
- **Macro Shock Stress-Testing:** Simulates national shocks, such as drought in the Eastern Province, and shows how cohort vulnerability shifts.

### The School Staff Member (`school` / `school123`)
*"Which child do I talk to today, and what can I do for them?"*
- **Early Warning Roster:** Multi-dimensional risk scoring, with the main risk driver named for each student.
- **Student 360 Case View:** Attendance, marks trajectory, Ubudehe category, and climate exposure on one screen.
- **What-If Intervention Simulator:** Test a feeding fee waiver or remedial classes and watch the predicted risk change in real time.
- **Case Management Form:** Logs follow-up actions and tracks active cases in `data/demo/follow_up_actions.json`.

---

## The model, kept transparent on purpose

We chose a logistic model rather than a black box because a headteacher, a district officer, and a statistician should all be able to ask *"why is this child flagged?"* and get an answer they can check.

$$\log\left(\frac{P}{1 - P}\right) = \beta_0 + \sum_{i=1}^{k} \beta_i x_i$$
$$P(\text{Dropout} \mid X) = \frac{1}{1 + e^{-z}}$$

Where:
- $\beta_0 = -2.60$ (baseline population log-odds)
- $\beta_{\text{Ubudehe Cat 1}} = 0.85$ (Odds Ratio: 2.34x)
- $\beta_{\text{Feeding Arrears}} = 0.75$ (Odds Ratio: 2.12x)
- $\beta_{\text{Climate Shock}} = 0.65$ (Odds Ratio: 1.92x)
- $\beta_{\text{Prior Repetition}} = 0.50$ (Odds Ratio: 1.65x)
- $\beta_{\text{Long Commute (>4km)}} = 0.40$ (Odds Ratio: 1.49x)
- $\beta_{\text{Consecutive Absences}} = 0.35$ per day for $\ge 3$ absences
- $\beta_{\text{Marks Deficit}} = 0.045$ per point below 55%
- $\beta_{\text{Attendance Deficit}} = 0.045$ per point below 85%

Every weight is visible, and every flag comes with its reason.

---

## How to Run

### Option 1: Use the online version (easiest)

RORA is hosted here, with nothing to install:

**https://rora-app-ciit.onrender.com**

If the app has been idle, the first load may take a short while to wake up. Give it a moment and then refresh.

### Option 2: Run it locally on your own computer

1. Activate your virtual environment:
```bash
   .\venv\Scripts\Activate.ps1
```
   (On macOS/Linux: `source venv/bin/activate`)

2. Start the application:
```bash
   streamlit run app.py
```
3. Open the local address Streamlit prints in your terminal, usually `http://localhost:8501`.

### Signing in (online or local)

Use the sidebar account switcher or any of these evaluation accounts:
- `planner` / `planner123`
- `analyst` / `analyst123`
- `school` / `school123`

---

## Disclosure of AI Tool Use

In accordance with the competition rules, we disclose that AI tools were used as assistants during this project, including for drafting and refining documentation and wording. The project design, data choices, and model formulation are our team's own work, and we accept full responsibility for everything submitted. All data sources are acknowledged above.