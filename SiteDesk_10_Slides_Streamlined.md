# SITEDESK — 10-SLIDE EXECUTIVE PRESENTATION DECK
**Competition:** Netcompany & Code Mely · IT Consultant Challenge 2026 (Round 1)  
**Topic:** SiteDesk — An AI Counter Assistant for Company A across Denmark, Norway, and Sweden  
**Format:** 10 Slides · Streamlined for Visual Impact & Zero Text-Bloat  

---

## SLIDE 1: EXECUTIVE SUMMARY
**Header Category:** EXECUTIVE SUMMARY  
**Action Title:** **SiteDesk: From Customer Material List to Confirmed Order in <2 Minutes**  
**Subtitle:** An AI counter assistant unifying store intake across Denmark, Norway, and Sweden  

### Top Highlight Metrics (3 Big Number Cards):
* **12 → <2 min** per material list (<30s human review)
* **≥30%** out-of-stock order lines rescued
* **~€14.0M/yr** total value at full rollout (€6.5M hard cash savings)

### 4 Strategic Pillars (4 Grid Cards):
* **PROBLEM:** Counter staff manually re-key 20–35 line material lists into legacy POS/ERP. Stockout advice depends on who is on shift—slow, inconsistent, and loses high-margin sales.
* **STRATEGIC CHOICE:** Fix the counter first. It is the common root where Denmark’s manual work, Norway’s store variance, and Sweden’s delivery errors originate (Rule of 1-10-100).
* **THE SOLUTION:** **SiteDesk** reads any list (PDF, Excel, email), matches SKUs via semantic AI, checks stock, and suggests equivalent substitutes in one click. Browser-only, non-invasive, EU-hosted AI.
* **THE ASK TODAY:** **€0.6M** for a 12-week MVP across 10 Norwegian stores with a firm Go/No-go gate in Week 12.

*Footnote: Team estimates; detailed assumptions A1–A7 on slide 9. 12-minute baseline measured in discovery.*

---

## SLIDE 2: PROBLEM CONTEXT & STRATEGIC RELEVANCE
**Header Category:** 01 · IDENTIFY  
**Action Title:** **Three Markets, Three Priorities — They All Converge at the Store Counter**  

### 3 Market Context Cards:
* **NORWAY · Store Operations:** High associate variance. Product advice and substitution depend entirely on who is on shift.
* **SWEDEN · Delivery & Fulfilment:** Lists mis-keyed at the counter cascade into wrong warehouse picks and expensive job-site re-deliveries.
* **DENMARK · Manual Processes:** Labor-heavy routine. Every line is read, searched, and re-keyed by hand (~12 min per list).

### Center Convergence Callout:
> **THE STORE COUNTER (Where Raw Lists Become Orders)**  
> *The single operational bottleneck connecting all three market pains.*

### Stakeholder Impact & Strategic Urgency (2 Bottom Blocks):
* **Who Feels It:**
  * **Counter Associates:** Spend hours on clerical search instead of active advisory.
  * **B2B Contractors & DIYers:** Lose precious morning hours waiting for order confirmations.
  * **Yard & Logistics Staff:** Pick and deliver incorrect orders originating from counter typos.
* **Why It Matters Now:** In hyper-competitive Nordics, contractors switch merchants after 2–3 bad experiences. Counter wait times and "sorry, out of stock" directly erode market share.

---

## SLIDE 3: ROOT CAUSE ANALYSIS (5 WHYS)
**Header Category:** 01 · IDENTIFY  
**Action Title:** **The Real Problem: Counter Operations Run on Personal Memory, Not System Data**  

### Left Column: Today’s Broken Counter Flow (Step-by-step):
1. **Receive list:** PDF, Excel, or raw email text *(Unstructured)*
2. **Search SKU:** Manual keyword search in legacy POS/ERP *(Slow: ~12 min)*
3. **Check inventory:** Manual query per item *(Disconnected)*
4. **Handle stockout:** Seniors recommend alternatives; juniors say "sorry" *(Lost Sales)*
5. **Re-key order:** Manually re-enter 20–35 lines into POS *(5% Error Rate)*

### Right Column: 5 Whys Root-Cause Chain (Clean Arrow Diagram):
* **Symptom:** Customers wait ~12 min per list and leave with unfulfilled orders.
* **↓ Why?** Every line is manually searched, converted, and re-keyed by hand.
* **↓ Why?** Legacy POS/ERP was designed for barcode checkout, not raw list ingestion.
* **↓ Why?** Technical product equivalence lives in senior staff's heads, not in software.
* **↓ Why?** Each country developed siloed legacy tools; costs are hidden across hundreds of stores.
* **⇒ ROOT CAUSE:** **No shared, data-driven engine to convert raw customer lists into clean ERP orders.**

### Key Takeaway Banner:
> **So What:** Software alone won't fix it. The counter needs **One Nordic Standard**, shared product data, and a lightweight tool that makes clean entry the default.

---

## SLIDE 4: STRATEGIC PRIORITISATION & COMPARISON
**Header Category:** 02 · PRIORITISE  
**Action Title:** **Why the Counter First: Highest Business Impact Deliverable in One Quarter**  

### Strategic Evaluation Matrix:
| Proposed Initiative | Impact (30%) | Cross-Market (20%) | Time-to-Market (25%) | Feasibility (15%) | Root Cause (10%) | Weighted Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **SiteDesk (Counter AI Layer)** | **4** | **5** | **4** | **4** | **4** | **4.20** |
| Harmonised Group ERP | 5 | 5 | 1 | 1 | 5 | 3.40 |
| Store Routine & Task App (NO) | 3 | 3 | 4 | 4 | 2 | 3.30 |
| Back-Office RPA (DK) | 3 | 2 | 4 | 4 | 1 | 3.00 |
| Delivery Management System (SE)| 4 | 3 | 2 | 3 | 2 | 2.95 |

### Crisp Rejection Rationales (Why Not The Others?):
* **Harmonised ERP:** Right destination, wrong first step. 2–3 years before business impact. SiteDesk builds its first data brick.
* **Delivery System (SE):** Optimizes delivery of orders that were *already wrong at the counter*. Fix the input first.
* **Store Routine App (NO):** Standardizes checklists, but doesn't fix the moment the customer is waiting.
* **Back-Office RPA (DK):** Automates broken steps in one country; brittle to UI changes; zero AI innovation.

### Robustness Stress-Test:
> **Score 4.20 vs 3.90:** Even shifting 50% of the Time-to-Market weight to Impact, SiteDesk still beats the ERP option.

---

## SLIDE 5: SITEDESK CORE SOLUTION WORKFLOW
**Header Category:** 03 · SOLVE  
**Action Title:** **SiteDesk: AI Accelerates Data Processing, Humans Retain the Final Call**  

### 4-Step Operational Pipeline:
```
[ 1. READ (AI) ] ──────► [ 2. MATCH (AI) ] ──────► [ 3. SUBSTITUTE (AI) ] ──► [ 4. CONFIRM (HUMAN) ]
  Upload PDF/Excel/Text    Semantic search maps      Real-time stock check.     Associate 1-click review.
  Extracts items, units    messy text to SKUs with   Suggests equal/better      Direct push to POS/ERP
  in DA, NO, SV, EN.       confidence score.         spec alternatives.         (CSV fallback if offline).
```

### Before vs. After Operational Shift:
* **Lookup Time:** ~12 min manual search $\to$ **<2 min total (<30s human review)**
* **Stockout Handling:** "Sorry, we don't have it" $\to$ **"Not on shelf, but here is an approved equivalent"**
* **Service Quality:** Depends on who is on shift $\to$ **100% consistent technical advice at every counter**

### Beyond Software (Operational Enablers):
* **Nordic Counter Standard:** Associates measured on accuracy & rescued sales, not just volume.
* **Product Data Stewardship:** Named data owners maintaining Master Catalog specifications.
* **People-Centric:** Co-designed with counter staff; zero headcount cuts (time returned to customer advisory).

---

## SLIDE 6: DAILY STORE REALITY & UI MOCKUP
**Header Category:** 03 · SOLVE  
**Action Title:** **One Counter, Five Moments: Eliminating Chaos from the Working Day**  

### Left Column: 5 Operational Touchpoints:
* **07:00 · Pre-Pick:** 35-line contractor email $\to$ Auto-saved quote, pick-list printed for yard before customer arrives.
* **09:30 · List Intake:** 20-line PDF dropped $\to$ 90% auto-matched in seconds.
* **09:31 · Stockout Salvage:** Out-of-stock line flagged $\to$ AI recommends equal-spec substitute $\to$ Customer accepts.
* **11:00 · Unit Conversion:** "120m lumber" $\to$ 25 lengths (4.8m); slang "trykimp" resolved via top 3 candidates.
* **Anytime · 1-Click Push:** Final human review $\to$ Instant sync into POS/ERP without re-typing.

### Right Column: Working UI Mockup:
```
SiteDesk Portal | Store: NO-STORE-042 | Session: SD-NO-8821
┌───────────────────────────────┬──────────────┬─────────────┬─────┬──────────────┬────────────┐
│ Customer Wrote                │ Sold As      │ SKU Match   │ Qty │ Stock Status │ Confidence │
├───────────────────────────────┼──────────────┼─────────────┼─────┼──────────────┼────────────┤
│ 45x95 C24 – 120 m             │ Length 4.8m  │ TIM-4595-48 │ 25  │ In Stock     │ >90%       │
│ Plasterboard 13mm – 60 m²     │ Board 1.2x2.4│ GYP-13-1224 │ 21↑ │ In Stock     │ >90%       │
│ trykimp. 22x95 terr.          │ Pick 1 of 3  │ [Select...] │ --  │ Check Spec   │ 65% (Amber)│
│ Salt-resistant cement 50kg    │ Bag 50kg     │ CEM-SALT-50 │ 20  │ Out of Stock │ >90% (Red) │
│ ↳ Suggested Alternative       │ Bag 50kg     │ CEM-PRO-50  │ 20  │ In Stock     │ Equal Spec │
└───────────────────────────────┴──────────────┴─────────────┴─────┴──────────────┴────────────┘
[ Stock Updated: 09:31 ]          [ View Alternatives ]          [ Confirm & Push Order (Enter) ]
```
*Note: ↑ = Auto-rounded up to sellable packaging units.*

---

## SLIDE 7: PRAGMATIC ARCHITECTURE & SOVEREIGN AI
**Header Category:** 03 · SOLVE  
**Action Title:** **Built Once Globally, Connected Locally — Sovereign & Secure by Design**  

### 2-Tier Architecture Model:
```
┌────────────────────────────────────────────────────────────────────────┐
│               SITEDESK CORE (Shared Global Intelligence)               │
│   Parsing Engine · Semantic SKU Matcher · Spec-Safe Alternative Engine │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST API / Webhooks
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│ DENMARK CONNECTOR│        │ NORWAY CONNECTOR │        │ SWEDEN CONNECTOR │
│ Local Catalog/DKK│        │ Local Catalog/NOK│        │ Local Catalog/SEK│
│ Legacy Navision  │        │ Local Store POS  │        │ Legacy Movex WMS │
└──────────────────┘        └──────────────────┘        └──────────────────┘
```

### Clean Integration Payload (Core → Connector):
```json
{
  "session_id": "SD-NO-8821",
  "store_location": "NO-STORE-042",
  "customer": { "client_id": "NO-B2B-1092" },
  "parsed_items": [
    {
      "original_text": "Salt-resistant cement 50kg",
      "matched_sku": "CEM-SALT-50",
      "quantity": 20,
      "stock_status": "out_of_stock",
      "fulfillment_action": "substituted",
      "final_sku": "CEM-PRO-50"
    }
  ]
}
```

### Enterprise Security & Sovereign AI Guardrails:
* **Sovereign AI:** EU/EEA-hosted models (Mistral / open models); zero data sent outside Europe.
* **Privacy by Design:** PII automatically masked; only anonymous `client_id` transferred.
* **Audit-Ready:** Full decision logging compliant with EU AI Act.
* **Zero Downtime Fallback:** System operates offline via manual search & CSV export if POS API drops.

---

## SLIDE 8: FOCUSED 12-WEEK MVP IMPLEMENTATION PLAN
**Header Category:** 03 · SOLVE  
**Action Title:** **MVP Delivery: Live in 10 Norwegian Stores in 12 Weeks with Clear Gates**  

### Scope Boundary (Strict Control):
* **IN SCOPE (7 Core Features):** List intake · SKU matching · Unit conversion · Stock check · Spec alternatives · Saved quotes/pick-list · Audit logging.
* **OUT OF SCOPE (Roadmap Phase 2):** Customer self-upload portal · Delivery-slot booking · Multi-store cross-border stock pings · Complete ERP replacement.

### 12-Week Agile Delivery Roadmap:
* **WEEKS 1–2 · DISCOVER:** Shadow 3 stores · Benchmark timing baseline · Collect 2,000 real lists · Clean top 5,000 SKUs.
* **WEEKS 3–8 · BUILD:** Three 2-week sprints (Sprint 1: Intake & Match $\to$ Sprint 2: Stock & Substitutes $\to$ Sprint 3: POS Push & Quotes).
* **WEEKS 9–12 · PILOT:** Deploy across 10 pilot stores vs. 10 control stores in Norway.

### Week-12 Go/No-Go Decision Criteria (4 Bold Metrics):
* **12 → <2 min:** Time-to-serve per list
* **≥30%:** Substitution acceptance on out-of-stock lines
* **≥70%:** Zero-touch matching rate (>90% confidence)
* **≤2%:** Error rate guardrail on automated lines

### Delivery Team & Budget:
* **Team of 7:** 1 Delivery Lead · 1 UX Designer · 2 Full-Stack Devs · 1 AI Engineer · 1 Integration Engineer · 1 Super-User Lead.
* **MVP Investment:** **€0.6M** total (assumptions A7).

---

## SLIDE 9: BUSINESS IMPACT & FINANCIAL MODEL
**Header Category:** IMPACT  
**Action Title:** **~€14.0M Annual Value at Full Rollout — Hard Cash Benefits Pay Back in Year 2**  

### Annual Value Waterfall (3 Pillars):
* **€7.5M · Time Released (Soft):** 1.125M lists $\times$ 10 min saved = 187,500 hrs. Equivalent to ~117 FTE redirected to active customer selling.
* **€3.2M · Out-of-Stock Sales Rescued (Hard):** 1.125M lists $\times$ 1 stockout line $\times$ €75 $\times$ 30% accepted $\times$ 25% margin.
* **€3.4M · Reduced Errors (Hard):** 1.125M lists $\times$ 5% error rate $\times$ €120 average cost $\times$ 50% fewer errors.
* **$\mathbf{\Rightarrow}$ TOTAL ANNUAL VALUE: ~€14.0M (including €6.5M Hard Cash Savings)**

### 3-Year Investment & Payback Horizon:
* **Total 3-Year Investment:** **€5.0M** (€0.6M MVP + €2.9M full rollout + €0.5M/yr run).
* **Hard Cash Benefits Ramp:** **€12.4M** over 3 years (20% $\to$ 70% $\to$ 100%).
* **Payback Period:** **Within Year 2** (Covers costs even if hard benefits drop by 50%).

### Model Assumptions (Structured Table):
| Code | Parameter | Assumed Value | Source / Justification |
| :---: | :--- | :--- | :--- |
| **A1** | Store Count | ~300 stores (DK 120, SE 100, NO 80) | Official Case Brief: "Hundreds of stores" |
| **A2** | Daily Volume | 15 bulk lists / store / day $\times$ 250 days | 1.125M lists/year total |
| **A3** | Processing Time | 12 min $\to$ <2 min per list | Baseline to be validated in discovery |
| **A4** | Labor Cost | €40/h fully loaded | Nordic retail benchmark (1,600 h/yr) |
| **A5** | Line Item Value | €75 per line · 25% gross margin | Standard construction materials mix |
| **A6** | Error Cost | 5% baseline error rate · €120/error | Re-delivery, credit notes & restock fees |
| **A7** | Budget Envelope | €0.6M MVP · €3.5M Total Build · €0.5M Run | Industry standard agile implementation |

---

## SLIDE 10: SCALABILITY & NORDIC ROLLOUT ROADMAP
**Header Category:** 04 · SCALE  
**Action Title:** **Prove in Norway, Scale Across the Nordics — The Foundation for Harmonisation**  

### 4-Wave Strategic Rollout Timeline:
```
           M0 – M3 (Wave 0)      M4 – M9 (Wave 1)      M10 – M15 (Wave 2)      M16 – M24 (Wave 3)
NORWAY:   [ 10-Store Pilot ] ──► [ All Norway Stores] ──────────────────────────────────────────► Live
DENMARK:                         [ Denmark Pilot ]   ──► [ All Denmark Stores] ─────────────────► Live
SWEDEN:                                                  [ Sweden Pilot + Pre-pick] ────────────► Live
```
* **Wave 0 (Norway Pilot):** Address most urgent store variance; refine core AI models.
* **Wave 1 (Norway Full + Denmark Pilot):** Expand to largest store base; eliminate Danish manual typing.
* **Wave 2 (Denmark Full + Sweden Pilot):** Add pre-pick functionality to resolve Swedish delivery delays.
* **Wave 3 (Full Nordic Harmonisation):** Shared data model established across ~300 stores; readiness for group ERP.

### Readiness Gates (Prerequisites before entering each market):
* [✓] Local POS/ERP read access confirmed.
* [✓] Top 5,000 SKUs cleansed with local unit attributes.
* [✓] Local Process Owner named & super-users trained.

### Immediate Decisions Required Today:
1. **Approve €0.6M budget** for the 12-week MVP.
2. **Designate 10 pilot + 10 control stores** in Norway.
3. **Grant data access** to product catalog and store inventory APIs.
4. **Lock in Week-12 Go/No-go criteria** with executive leadership.

*Closing Strategic Pitch:*  
**Fix the counter — and the store, the yard, and the delivery truck all get easier.**
