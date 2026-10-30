# RORA: Multi-Source Education Intelligence and Early Intervention System

Built for the 2026 NISR Big Data Hackathon (Open Innovation track).

RORA is a production-ready education data analysis and early intervention platform for Rwanda. It bridges macro-level statistical planning with micro-level student intervention by cross-examining multi-sectoral data across:
1. **NISR EICV7 (2023/24)**: District Primary NAR, Secondary NAR, Repetition rates, and household poverty profiles.
2. **MINEMA & Meteo Rwanda**: Disaster vulnerability indices (drought, flood, and landslide exposure).
3. **SDMS / NESA**: Student-level academic term marks, academic trajectory, and repetition history.
4. **Social Protection & Community (Ubudehe & VUP)**: Household Ubudehe categories and school feeding fee arrears.

---

## The Core Problem Addressed

Conventional monitoring treats school dropout as if it were driven purely by attendance. In practice, students face compounding multi-dimensional vulnerabilities:
- **Academic Collapse**: A student may maintain 90% attendance while their marks crash below passing levels, leading to disengagement and unmonitored dropout.
- **Socio-Economic Shocks**: Household meal fee arrears (unpaid school feeding contributions) remain a major direct cause of exclusion in rural schools.
- **Environmental Shocks (MINEMA)**: Recurrent dry spells in Eastern Province (e.g. Nyagatare, Kayonza, Bugesera) and heavy rainfall/landslides in Western and Northern Provinces (e.g. Rutsiro, Ngororero, Gicumbi) disrupt family livelihoods and school access.

RORA combines these multi-sectoral variables into a calibrated predictive model that identifies student vulnerabilities before they drop out.

---

## Role-Differentiated Experience

Each role accesses a dedicated, purpose-built console:

### 1. National Planner (`planner` / `planner123`)
- **Focus**: Strategic resource allocation and district targeting.
- **Tools**:
  - **Composite Vulnerability Ranking**: Multi-factor index combining poverty, repetition, climate hazards, and net attendance.
  - **Geographic Vulnerability Map**: Interactive map of Rwanda's 30 districts.
  - **Targeted Resource Simulator**: Simulates the impact of deploying emergency school feeding bursaries and remedial teacher packages to priority districts.

### 2. Policy & Data Analyst (`analyst` / `analyst123`)
- **Focus**: Cross-sectoral statistical diagnostics and predictive modeling.
- **Tools**:
  - **Cross-Sector Correlation Engine**: Dynamic scatter analytics comparing poverty, climate risk, and repetition.
  - **Model Diagnostics**: Detailed table of log-odds feature weights, Odds Ratios, and domain interpretations.
  - **Macro Shock Stress-Testing**: Simulates national shocks (e.g. drought in Eastern Province) to project cohort vulnerability shifts.

### 3. School Staff (`school` / `school123`)
- **Focus**: Actionable student early warning and intervention case management.
- **Tools**:
  - **School Early Warning Roster**: Multi-dimensional risk scoring with primary risk driver attribution.
  - **Student 360 Case View**: Inspects attendance, marks trajectory, Ubudehe category, and climate exposure.
  - **What-If Intervention Simulator**: Tests how specific school interventions (feeding fee waiver, remedial classes) reduce the predicted risk probability in real time.
  - **Case Management Form**: Logs follow-up actions and tracks active support cases in `data/demo/follow_up_actions.json`.

---

## Predictive Model Formulation

The predictive engine computes individual log-odds:
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

---

## How to Run

1. Activate your virtual environment:
   ```bash
   .\venv\Scripts\Activate.ps1
   ```
2. Start the application:
   ```bash
   streamlit run app.py
   ```
3. Use the sidebar account switcher or sign in using any of the evaluation accounts:
   - `planner` / `planner123`
   - `analyst` / `analyst123`
   - `school` / `school123`
