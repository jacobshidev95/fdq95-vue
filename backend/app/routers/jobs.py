"""Job listings API — filtered by country and category."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class Job(BaseModel):
    id: str
    title: str
    category: str      # tech | management | sales
    country: str       # ISO-3166 alpha-2
    location: str
    requirements: str
    description: str


# In production this would come from a database. Sample seed data
# covers the three categories across the most common countries.
JOBS: List[Job] = [
    # ---------------- Technology ----------------
    Job(
        id="T001",
        title="Senior Backend Engineer",
        category="tech",
        country="US",
        location="San Francisco, CA (Hybrid)",
        requirements=(
            "• 5+ years Python (FastAPI / Django) or Go\n"
            "• Strong SQL and PostgreSQL experience\n"
            "• Distributed systems, REST/gRPC API design\n"
            "• Familiarity with Docker & Kubernetes"
        ),
        description="Design and scale our core service platform.",
    ),
    Job(
        id="T002",
        title="Frontend Engineer (Vue 3)",
        category="tech",
        country="US",
        location="Remote (US)",
        requirements=(
            "• 3+ years Vue.js 3 / TypeScript\n"
            "• Pinia or Vuex state management\n"
            "• Responsive UI, accessibility (a11y) standards\n"
            "• Vite, ESLint, unit testing"
        ),
        description="Build customer-facing dashboards and portals.",
    ),
    Job(
        id="T003",
        title="DevOps Engineer",
        category="tech",
        country="GB",
        location="London, UK",
        requirements=(
            "• Kubernetes, Terraform, Helm\n"
            "• AWS or GCP in production\n"
            "• CI/CD pipeline design\n"
            "• Monitoring (Prometheus, Grafana)"
        ),
        description="Own our infrastructure and deployment automation.",
    ),
    Job(
        id="T004",
        title="Full Stack Developer",
        category="tech",
        country="CN",
        location="Shanghai, China",
        requirements=(
            "• Node.js + Vue.js 3, 3+ years\n"
            "• PostgreSQL or MySQL\n"
            "• RESTful API design\n"
            "• Git workflow, code review culture"
        ),
        description="End-to-end feature delivery on our web platform.",
    ),
    Job(
        id="T005",
        title="Data Engineer",
        category="tech",
        country="DE",
        location="Berlin, Germany",
        requirements=(
            "• Python, SQL, Spark, Kafka\n"
            "• Data warehouse modelling (dbt, Airflow)\n"
            "• Cloud storage (S3, BigQuery)\n"
            "• 4+ years relevant experience"
        ),
        description="Build the data pipeline powering analytics & ML.",
    ),
    Job(
        id="T006",
        title="Mobile Developer (iOS)",
        category="tech",
        country="JP",
        location="Tokyo, Japan",
        requirements=(
            "• Swift, SwiftUI, 3+ years\n"
            "• App Store release experience\n"
            "• REST/GraphQL integration\n"
            "• Japanese N2 or above preferred"
        ),
        description="Develop and maintain our iOS application.",
    ),

    # ---------------- Management ----------------
    Job(
        id="M001",
        title="Product Manager",
        category="management",
        country="US",
        location="New York, NY",
        requirements=(
            "• 5+ years B2B SaaS product management\n"
            "• Strong analytical and communication skills\n"
            "• Experience with Agile / Scrum\n"
            "• Data-driven decision making"
        ),
        description="Own the roadmap for our provider platform.",
    ),
    Job(
        id="M002",
        title="Engineering Manager",
        category="management",
        country="US",
        location="Remote (US)",
        requirements=(
            "• 8+ years software engineering\n"
            "• 3+ years managing engineers\n"
            "• Hiring and mentoring experience\n"
            "• Deep technical background"
        ),
        description="Lead and grow a distributed engineering team.",
    ),
    Job(
        id="M003",
        title="Operations Manager",
        category="management",
        country="GB",
        location="London, UK",
        requirements=(
            "• 5+ years operations management\n"
            "• Supply chain / logistics exposure\n"
            "• Process optimization mindset\n"
            "• Excellent stakeholder management"
        ),
        description="Streamline marketplace operations across EMEA.",
    ),
    Job(
        id="M004",
        title="Project Manager",
        category="management",
        country="CN",
        location="Beijing, China",
        requirements=(
            "• PMP or equivalent certification\n"
            "• 4+ years managing IT projects\n"
            "• Fluent Mandarin and English\n"
            "• Vendor coordination experience"
        ),
        description="Drive cross-functional projects end to end.",
    ),

    # ---------------- Sales ----------------
    Job(
        id="S001",
        title="Enterprise Sales Executive",
        category="sales",
        country="US",
        location="New York, NY",
        requirements=(
            "• 5+ years enterprise B2B sales\n"
            "• Track record closing $500k+ deals\n"
            "• Salesforce / HubSpot proficiency\n"
            "• Excellent negotiation skills"
        ),
        description="Own strategic enterprise accounts in North America.",
    ),
    Job(
        id="S002",
        title="Sales Development Representative",
        category="sales",
        country="US",
        location="Austin, TX",
        requirements=(
            "• 1+ years SaaS SDR experience\n"
            "• Strong written and verbal English\n"
            "• CRM data hygiene\n"
            "• Coachable and target-driven"
        ),
        description="Generate and qualify outbound leads.",
    ),
    Job(
        id="S003",
        title="Account Manager",
        category="sales",
        country="GB",
        location="Manchester, UK",
        requirements=(
            "• 3+ years account management\n"
            "• B2B SaaS background\n"
            "• Strong relationship building\n"
            "• Upsell / renewal experience"
        ),
        description="Retain and grow existing UK customer base.",
    ),
    Job(
        id="S004",
        title="Regional Sales Manager",
        category="sales",
        country="CN",
        location="Shenzhen, China",
        requirements=(
            "• 5+ years sales team management\n"
            "• B2B tech sales background\n"
            "• Fluent Mandarin; English preferred\n"
            "• Channel partner management"
        ),
        description="Lead the South China sales team.",
    ),
    Job(
        id="S005",
        title="Sales Engineer",
        category="sales",
        country="DE",
        location="Munich, Germany",
        requirements=(
            "• Technical background + sales exposure\n"
            "• 3+ years in pre-sales / solutions\n"
            "• Fluent German and English\n"
            "• API and integration knowledge"
        ),
        description="Support DACH sales with technical expertise.",
    ),
]


@router.get("")
async def list_jobs(
    country: str = Query(..., min_length=2, max_length=2),
    category: str = Query(...),
) -> dict:
    """Return jobs filtered by country (ISO-2) and category."""
    country = country.upper()
    category = category.lower()

    filtered = [
        j for j in JOBS
        if j.country.upper() == country and j.category == category
    ]
    return {"jobs": [j.model_dump() for j in filtered]}


@router.get("/{job_id}")
async def get_job(job_id: str) -> dict:
    for j in JOBS:
        if j.id == job_id:
            return j.model_dump()
    raise HTTPException(status_code=404, detail="Job not found")