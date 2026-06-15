# AI Nexus Solutions — Your AI-Powered IT Company

You are the **CEO**. Every other role — Sales, Marketing, HR, Developers, QA, Finance — is handled by AI agents that work together automatically from client discovery through delivery and payment into your account.

## Company Workflow

```
Marketing finds leads → Sales gathers requirements → Finance creates quotation
        ↓
   YOU (CEO) approve quotation
        ↓
PM assigns developers → Devs build software → PM reviews → QA tests
        ↓
Client Success hands over → Finance collects payment → YOUR account
```

### The 11 AI Team Members

| Role | Name | Department |
|------|------|------------|
| Sales Executive | Alex Rivera | Sales |
| Marketing Manager | Priya Sharma | Marketing |
| HR Manager | Jordan Lee | Human Resources |
| Business Analyst | Sam Okafor | Business Analysis |
| Project Manager | Morgan Chen | Project Management |
| Frontend Developer | Riya Patel | Engineering |
| Backend Developer | David Kim | Engineering |
| Full-Stack Developer | Elena Vasquez | Engineering |
| QA Tester | Chris Taylor | Quality Assurance |
| Finance Manager | Nina Brooks | Finance |
| Client Success | Taylor Wright | Client Success |

## Quick Start

### 1. Install dependencies

```bash
cd f:\AI-Company
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure (optional)

Copy `.env.example` to `.env` and set your details:

```bash
copy .env.example .env
```

| Variable | Description |
|----------|-------------|
| `CEO_NAME` | Your name (shown as CEO) |
| `CEO_EMAIL` | Your business email |
| `COMPANY_NAME` | Your company name |
| `OPENAI_API_KEY` | For real AI responses (optional) |
| `DEMO_MODE` | `true` = simulated AI (works without API key) |

### 3. Run the CEO Dashboard

```bash
python run.py
```

Open **http://localhost:8765** in your browser.

## How to Use (As CEO)

1. **Dashboard** — See revenue, active projects, and pending approvals.
2. **Simulate New Client** — Marketing + Sales automatically find a client and start the pipeline.
3. **Create New Project** — Manually add a client project with requirements.
4. **Approve Quotations** — When a project reaches "CEO Approval", review the quote and approve or reject.
5. **Run Stages** — Advance projects step-by-step or run all remaining stages at once.
6. **Track Payments** — All payments are recorded to your CEO business account.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | CEO dashboard stats |
| GET | `/api/team` | AI team roster |
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create project + auto-run pipeline |
| POST | `/api/simulate-lead` | Simulate marketing finding a client |
| POST | `/api/projects/{id}/run-stage` | Run next workflow stage |
| POST | `/api/projects/{id}/run-all` | Run all remaining stages |
| POST | `/api/projects/{id}/ceo-approve` | Approve/reject quotation |

## Project Structure

```
AI-Company/
├── run.py                  # Start the server
├── requirements.txt
├── src/
│   ├── agents/             # AI team members & prompts
│   ├── workflow/           # Pipeline engine
│   ├── database/           # SQLite storage
│   ├── services/           # LLM integration
│   ├── api/                # FastAPI routes
│   └── config.py
└── static/                 # CEO dashboard UI
```

## Upgrading to Real AI

Set `OPENAI_API_KEY` in `.env` and set `DEMO_MODE=false`. Each agent will use GPT to generate real, contextual responses for every stage.

## Next Steps You Can Add

- Connect real email/CRM for lead intake
- Add Stripe/PayPal for live payment processing
- Wire agents to actually generate code in a repo
- Add Slack/Discord notifications when CEO approval is needed
- Multi-project parallel execution with team capacity limits
