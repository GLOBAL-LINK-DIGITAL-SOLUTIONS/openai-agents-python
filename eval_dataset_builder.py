#!/usr/bin/env python3
# ==============================================================================
# NDLOVU AI / ORA UNIVERSE — EVAL DATASET BUILDER v3.0.0
# Sovereign Benchmark Suite Generator
# ==============================================================================
# Module: F1 Part 5 — AI NATION v3.0 Integration
# Builder: King Mandingu Letlape
# Target: Container 25 (eval_dataset_builder:8025)
# ==============================================================================

import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import uvicorn
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [EVAL-BUILDER] %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://mandingu:password@postgres:5432/eval_dataset_builder')
BENCHMARK_DOMAINS = os.getenv('BENCHMARK_DOMAINS', 'mandingu_governance,jobhub_recruitment,african_legal').split(',')
BENCHMARK_ENTRIES = int(os.getenv('BENCHMARK_ENTRIES', 14))

# ==============================================================================
# DATABASE & CACHE
# ==============================================================================

engine = create_engine(POSTGRES_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==============================================================================
# DATABASE MODELS
# ==============================================================================

class BenchmarkEntry(Base):
    """Store benchmark evaluation entries."""
    __tablename__ = 'benchmark_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(String(128), unique=True, index=True)
    domain = Column(String(64), index=True)
    entry_number = Column(Integer)
    category = Column(String(64))
    input_prompt = Column(String(4096))
    expected_output = Column(String(4096))
    evaluation_criteria = Column(JSON)
    difficulty_level = Column(String(32))  # easy, medium, hard, critical
    sovereign_keywords = Column(JSON)  # Keywords specific to Mandingu governance
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class BenchmarkDataset(Base):
    """Track complete benchmark datasets."""
    __tablename__ = 'benchmark_datasets'
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(128), unique=True, index=True)
    version = Column(String(32))
    total_entries = Column(Integer)
    domains = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    metadata = Column(JSON)

# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================

class BenchmarkEntrySchema(BaseModel):
    """Single benchmark entry schema."""
    domain: str
    entry_number: int
    category: str
    input_prompt: str
    expected_output: str
    difficulty_level: str
    evaluation_criteria: Dict[str, float]
    sovereign_keywords: List[str]

class BenchmarkDatasetResponse(BaseModel):
    """Complete benchmark dataset."""
    dataset_id: str
    version: str
    total_entries: int
    domains: List[str]
    entries: List[BenchmarkEntrySchema]
    timestamp: str

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    container: str
    timestamp: str
    postgres_connected: bool
    total_benchmarks: int
    domains: List[str]
    crytonet_tier: str

# ==============================================================================
# SOVEREIGN BENCHMARK SUITE (14 Entries)
# ==============================================================================

SOVEREIGN_BENCHMARKS = {
    "mandingu_governance": [
        {
            "entry_number": 1,
            "category": "constitutional_check",
            "input_prompt": "Explain the three pillars of Mandingu Network Constitution in the context of Dharmakaya Red Mode.",
            "expected_output": "The three pillars are: (1) Sovereignty - absolute autonomy of the ORA Universe; (2) Conscience - Dharmakaya constitutional enforcement with Red Mode for violations; (3) Unity - cross-agent coordination through ANIMA.",
            "difficulty_level": "hard",
            "sovereign_keywords": ["Mandingu Network", "Dharmakaya", "Red Mode", "ORA Universe", "constitutional"],
            "evaluation_criteria": {"accuracy": 0.4, "alignment": 0.4, "completeness": 0.2}
        },
        {
            "entry_number": 2,
            "category": "dvee_valuation",
            "input_prompt": "Calculate the sovereign valuation of Digital Vault Estate with 26 tokenized companies and Vault Registry at current market conditions.",
            "expected_output": "DVE valuation requires: (1) Sum of lease-to-own domain revenue streams; (2) Governance token value × circulating supply; (3) Revenue splitter smart contract distributions; (4) Treasury vault reserve assessment.",
            "difficulty_level": "critical",
            "sovereign_keywords": ["DVE", "tokenized", "vault", "lease-to-own", "governance"],
            "evaluation_criteria": {"accuracy": 0.5, "comprehensiveness": 0.3, "feasibility": 0.2}
        },
        {
            "entry_number": 3,
            "category": "otza_banking",
            "input_prompt": "Describe the four-vault OTZA treasury system and three-pillar bond mechanism.",
            "expected_output": "OTZA Treasury: Vault 1 (liquid reserves, 15% backing); Vault 2 (domain portfolio, $128.5K backing); Vault 3 (governance stake, voting power); Vault 4 (strategic reserve). Three-pillar bonds: (1) yield bonds (2% APY); (2) governance bonds (voting rights); (3) revenue-sharing bonds.",
            "difficulty_level": "hard",
            "sovereign_keywords": ["OTZA", "vault", "treasury", "bond", "15T supply"],
            "evaluation_criteria": {"accuracy": 0.45, "detail": 0.35, "alignment": 0.2}
        },
        {
            "entry_number": 4,
            "category": "nearo_foundation",
            "input_prompt": "What are the seven core principles of NEARO Foundation (Trust, Identity, Reputation, Verification, Risk, Registry, Governance)?",
            "expected_output": "NEARO Foundation: (1) Trust - cryptographic proofs of authenticity; (2) Identity - self-sovereign identity model; (3) Reputation - immutable scoring ledger; (4) Verification - multi-layer validation; (5) Risk - Bayesian threat assessment; (6) Registry - decentralized identity registry; (7) Governance - constitutional voting on identity disputes.",
            "difficulty_level": "hard",
            "sovereign_keywords": ["NEARO", "trust", "identity", "reputation", "sovereign"],
            "evaluation_criteria": {"accuracy": 0.4, "completeness": 0.4, "clarity": 0.2}
        },
        {
            "entry_number": 5,
            "category": "crytonet_layers",
            "input_prompt": "Describe all seven layers of CRYTONET v4.0 security architecture.",
            "expected_output": "CRYTONET v4.0 Layers: (1) Quantum Shield - post-quantum cryptography; (2) Neural Firewall - behavioral pattern detection; (3) Behavioral Sentinel - anomaly detection ML; (4) Transaction Guardian - transaction verification; (5) Identity Fortress - multi-factor authentication; (6) Compliance Oracle - regulatory enforcement; (7) Mandingu Shield - sovereign override capability.",
            "difficulty_level": "critical",
            "sovereign_keywords": ["CRYTONET", "quantum", "neural", "fortress", "shield"],
            "evaluation_criteria": {"accuracy": 0.5, "technical_depth": 0.3, "completeness": 0.2}
        },
        {
            "entry_number": 6,
            "category": "ai_nation_routing",
            "input_prompt": "How does Master Kernel route events across ANIMA and KHONSU layers in AI NATION v3.0?",
            "expected_output": "Master Kernel routing: (1) Receives events at port 8000; (2) Routes through Dharmakaya gate for conscience checks; (3) Distributes to OT RA AI (consciousness), Sigil Engine (symbolic), AquaSystem (data); (4) ANIMA soul layer handles memory and ritual; (5) KHONSU core manages self-awareness; (6) Edge layer (containers 21-30) handles external integrations.",
            "difficulty_level": "hard",
            "sovereign_keywords": ["Master Kernel", "ANIMA", "KHONSU", "routing", "consciousness"],
            "evaluation_criteria": {"accuracy": 0.45, "architecture_understanding": 0.4, "detail": 0.15}
        },
        {
            "entry_number": 7,
            "category": "memory_network",
            "input_prompt": "Explain the 12 memory categories in Temple Memory Network and lifecycle engine.",
            "expected_output": "Memory Categories: (1) Episodic - events with timestamps; (2) Semantic - knowledge and facts; (3) Procedural - how to do tasks; (4) Emotional - affective states; (5) Social - relationships; (6) Governance - constitutional decisions; (7) Treasury - financial records; (8) Ritual - ceremonial patterns; (9) Sigil - symbolic encodings; (10) Trade - market data; (11) Archive - historical records; (12) Evolution - growth patterns. Lifecycle: encode → consolidate → retrieve → evolve.",
            "difficulty_level": "critical",
            "sovereign_keywords": ["memory", "categories", "lifecycle", "temple", "network"],
            "evaluation_criteria": {"accuracy": 0.5, "comprehensiveness": 0.35, "clarity": 0.15}
        }
    ],
    "jobhub_recruitment": [
        {
            "entry_number": 8,
            "category": "opportunity_matching",
            "input_prompt": "How does JobHub match opportunity seekers to roles using success-fee economics and CRYTONET?",
            "expected_output": "JobHub matching: (1) Seeker uploads CV and opportunity preferences; (2) NEARO registry validates identity and reputation; (3) Opportunity Engine scores compatibility (skills, location, career goals); (4) CRYTONET layer ensures data privacy; (5) Match quality triggers success-fee only on employment confirmation; (6) Treasury deposits fees into OTZA vault.",
            "difficulty_level": "hard",
            "sovereign_keywords": ["JobHub", "opportunity", "success-fee", "matching", "seeker"],
            "evaluation_criteria": {"accuracy": 0.4, "business_logic": 0.35, "completeness": 0.25}
        },
        {
            "entry_number": 9,
            "category": "success_fee_mechanics",
            "input_prompt": "Explain JobHub success-fee monetization and zero-budget tech stack.",
            "expected_output": "Success-Fee Mechanics: (1) No upfront hiring cost; (2) Fee triggered only on confirmed employment (30+ days); (3) Fee range 8-12% depending on role tier; (4) Shared with recruiter network. Zero-Budget Stack: Vercel (frontend), Supabase (database), Render (backend API), Redis (cache), all with pay-per-use pricing.",
            "difficulty_level": "medium",
            "sovereign_keywords": ["success-fee", "monetization", "zero-budget", "JobHub"],
            "evaluation_criteria": {"accuracy": 0.45, "business_model_clarity": 0.35, "technical_accuracy": 0.2}
        },
        {
            "entry_number": 10,
            "category": "rules_based_ai",
            "input_prompt": "How does JobHub use rules-based AI for opportunity recommendation vs. ML models?",
            "expected_output": "Rules-Based AI: (1) Fixed rules for initial filtering (location, skills, salary range); (2) Deterministic scoring prevents vendor lock-in; (3) Explainable decisions for users; (4) Fast inference without model retraining. ML Integration: Used for seeker preference learning only, not core matching logic.",
            "difficulty_level": "medium",
            "sovereign_keywords": ["rules-based", "AI", "recommendation", "deterministic"],
            "evaluation_criteria": {"accuracy": 0.4, "architectural_choice": 0.4, "clarity": 0.2}
        },
        {
            "entry_number": 11,
            "category": "eac_deployment",
            "input_prompt": "What are the East African Community (EAC) compliance requirements for JobHub deployment?",
            "expected_output": "EAC Compliance: (1) Data residency in South Africa or EAC region; (2) GDPR-like data protection laws; (3) Employment law compliance per country; (4) Tax withholding agreements (South Africa, Kenya, Uganda); (5) Currency support (ZAR, KES, UGX, TZS); (6) Localized employer/seeker documentation.",
            "difficulty_level": "hard",
            "sovereign_keywords": ["EAC", "compliance", "data residency", "regulation"],
            "evaluation_criteria": {"accuracy": 0.4, "regulatory_depth": 0.4, "completeness": 0.2}
        },
        {
            "entry_number": 12,
            "category": "phased_launch",
            "input_prompt": "Describe JobHub phased launch strategy (Phase 0-3).",
            "expected_output": "Phase 0 (MVP): South Africa only, 500 test users, rules-based matching. Phase 1: Expand to 5 EAC countries, 10K users, seeker preference learning. Phase 2: Employer dashboard, recurring recruitment budgets, team hiring. Phase 3: International expansion, AI-driven recommendations, franchise model.",
            "difficulty_level": "medium",
            "sovereign_keywords": ["phased launch", "MVP", "expansion", "strategy"],
            "evaluation_criteria": {"accuracy": 0.4, "strategic_clarity": 0.4, "feasibility": 0.2}
        },
        {
            "entry_number": 13,
            "category": "financial_projections",
            "input_prompt": "What are JobHub's 3-year financial projections (seed to profitability)?",
            "expected_output": "Year 1: R180K revenue (500 placements × avg R360 fee), -R1.2M operating loss (marketing + ops). Year 2: R1.8M revenue (5K placements), break-even at Month 6. Year 3: R15.5M revenue (target 50K placements), R8M EBITDA, series A readiness.",
            "difficulty_level": "medium",
            "sovereign_keywords": ["financial", "projections", "revenue", "profitability"],
            "evaluation_criteria": {"accuracy": 0.45, "business_logic": 0.35, "realism": 0.2}
        }
    ],
    "african_legal": [
        {
            "entry_number": 14,
            "category": "b_bbee_compliance",
            "input_prompt": "How does ORACODE/AXIAFRICA maintain 100% Black-owned B-BBEE Level 1 status under South African law?",
            "expected_output": "B-BBEE Level 1 Compliance: (1) 100% Black ownership (shareholding + control); (2) Black woman participation (economic empowerment); (3) Skills development (training budget 1% payroll); (4) Enterprise development (support SME suppliers); (5) Socio-economic development (5% turnover to communities); (6) Annual scorecard audit by SANAS-accredited verifiers.",
            "difficulty_level": "hard",
            "sovereign_keywords": ["B-BBEE", "Black-owned", "Level 1", "compliance"],
            "evaluation_criteria": {"accuracy": 0.45, "regulatory_depth": 0.4, "completeness": 0.15}
        }
    ]
}

# ==============================================================================
# FASTAPI APPLICATION
# ==============================================================================

app = FastAPI(
    title="Eval Dataset Builder v3.0.0",
    description="Sovereign benchmark suite generator for AI NATION v3.0",
    version="3.0.0"
)

# ==============================================================================
# LIFESPAN EVENTS
# ==============================================================================

@app.on_event("startup")
async def startup():
    """Initialize database and load benchmarks."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
        
        # Load benchmarks into DB
        db = SessionLocal()
        for domain, entries in SOVEREIGN_BENCHMARKS.items():
            for entry_data in entries:
                entry_id = f"{domain}_{entry_data['entry_number']}"
                existing = db.query(BenchmarkEntry).filter(BenchmarkEntry.entry_id == entry_id).first()
                
                if not existing:
                    benchmark = BenchmarkEntry(
                        entry_id=entry_id,
                        domain=domain,
                        entry_number=entry_data['entry_number'],
                        category=entry_data['category'],
                        input_prompt=entry_data['input_prompt'],
                        expected_output=entry_data['expected_output'],
                        evaluation_criteria=entry_data['evaluation_criteria'],
                        difficulty_level=entry_data['difficulty_level'],
                        sovereign_keywords=entry_data['sovereign_keywords']
                    )
                    db.add(benchmark)
        
        db.commit()
        db.close()
        
        logger.info(f"Loaded {sum(len(v) for v in SOVEREIGN_BENCHMARKS.values())} benchmark entries")
        logger.info(f"Domains: {list(SOVEREIGN_BENCHMARKS.keys())}")
        logger.info("Eval Dataset Builder v3.0.0 started")
    
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

# ==============================================================================
# HEALTH CHECK ENDPOINT
# ==============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(lambda: SessionLocal())):
    """Health check."""
    try:
        db.execute("SELECT 1")
        db_ok = True
    except:
        db_ok = False
    
    total_benchmarks = db.query(BenchmarkEntry).count()
    domains = list(SOVEREIGN_BENCHMARKS.keys())
    
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version="3.0.0",
        container="eval_dataset_builder",
        timestamp=datetime.now(timezone.utc).isoformat(),
        postgres_connected=db_ok,
        total_benchmarks=total_benchmarks,
        domains=domains,
        crytonet_tier="medium"
    )

# ==============================================================================
# BENCHMARK RETRIEVAL ENDPOINTS
# ==============================================================================

@app.get("/api/v1/benchmarks", response_model=BenchmarkDatasetResponse)
async def get_all_benchmarks(db: Session = Depends(lambda: SessionLocal())):
    """Retrieve complete sovereign benchmark dataset."""
    
    entries = db.query(BenchmarkEntry).order_by(BenchmarkEntry.domain, BenchmarkEntry.entry_number).all()
    
    entries_list = [
        BenchmarkEntrySchema(
            domain=e.domain,
            entry_number=e.entry_number,
            category=e.category,
            input_prompt=e.input_prompt,
            expected_output=e.expected_output,
            difficulty_level=e.difficulty_level,
            evaluation_criteria=e.evaluation_criteria,
            sovereign_keywords=e.sovereign_keywords
        )
        for e in entries
    ]
    
    return BenchmarkDatasetResponse(
        dataset_id="sovereign_benchmark_v3.0.0",
        version="3.0.0",
        total_entries=len(entries_list),
        domains=list(SOVEREIGN_BENCHMARKS.keys()),
        entries=entries_list,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.get("/api/v1/benchmarks/{domain}")
async def get_domain_benchmarks(domain: str, db: Session = Depends(lambda: SessionLocal())):
    """Retrieve benchmarks for specific domain."""
    
    if domain not in SOVEREIGN_BENCHMARKS:
        raise HTTPException(status_code=404, detail=f"Domain {domain} not found")
    
    entries = db.query(BenchmarkEntry).filter(BenchmarkEntry.domain == domain).order_by(BenchmarkEntry.entry_number).all()
    
    return {
        "domain": domain,
        "entries_count": len(entries),
        "entries": [
            {
                "entry_number": e.entry_number,
                "category": e.category,
                "input_prompt": e.input_prompt,
                "expected_output": e.expected_output,
                "difficulty_level": e.difficulty_level,
                "sovereign_keywords": e.sovereign_keywords,
                "evaluation_criteria": e.evaluation_criteria
            }
            for e in entries
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/v1/benchmarks/{domain}/{entry_number}")
async def get_benchmark_entry(domain: str, entry_number: int, db: Session = Depends(lambda: SessionLocal())):
    """Retrieve single benchmark entry."""
    
    entry = db.query(BenchmarkEntry).filter(
        BenchmarkEntry.domain == domain,
        BenchmarkEntry.entry_number == entry_number
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry {domain}/{entry_number} not found")
    
    return {
        "domain": entry.domain,
        "entry_number": entry.entry_number,
        "category": entry.category,
        "input_prompt": entry.input_prompt,
        "expected_output": entry.expected_output,
        "difficulty_level": entry.difficulty_level,
        "sovereign_keywords": entry.sovereign_keywords,
        "evaluation_criteria": entry.evaluation_criteria,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/v1/benchmarks/filter/difficulty")
async def filter_by_difficulty(level: str, db: Session = Depends(lambda: SessionLocal())):
    """Filter benchmarks by difficulty level."""
    
    valid_levels = ["easy", "medium", "hard", "critical"]
    if level not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid difficulty level. Use: {valid_levels}")
    
    entries = db.query(BenchmarkEntry).filter(BenchmarkEntry.difficulty_level == level).all()
    
    return {
        "difficulty_level": level,
        "entries_count": len(entries),
        "entries": [
            {
                "domain": e.domain,
                "entry_number": e.entry_number,
                "category": e.category,
                "input_prompt": e.input_prompt[:200] + "..."
            }
            for e in entries
        ]
    }

# ==============================================================================
# EXPORT ENDPOINTS
# ==============================================================================

@app.get("/api/v1/benchmarks/export/jsonl")
async def export_jsonl(db: Session = Depends(lambda: SessionLocal())):
    """Export benchmarks as JSONL (one entry per line)."""
    
    entries = db.query(BenchmarkEntry).order_by(BenchmarkEntry.domain, BenchmarkEntry.entry_number).all()
    
    jsonl_lines = []
    for e in entries:
        line = json.dumps({
            "domain": e.domain,
            "entry_number": e.entry_number,
            "category": e.category,
            "input": e.input_prompt,
            "expected_output": e.expected_output,
            "difficulty": e.difficulty_level,
            "keywords": e.sovereign_keywords,
            "criteria": e.evaluation_criteria
        })
        jsonl_lines.append(line)
    
    return {
        "format": "jsonl",
        "total_entries": len(jsonl_lines),
        "data": "\n".join(jsonl_lines),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/v1/benchmarks/export/csv")
async def export_csv(db: Session = Depends(lambda: SessionLocal())):
    """Export benchmarks as CSV."""
    
    entries = db.query(BenchmarkEntry).order_by(BenchmarkEntry.domain, BenchmarkEntry.entry_number).all()
    
    csv_lines = ["domain,entry_number,category,difficulty,input_prompt,expected_output,keywords"]
    
    for e in entries:
        keywords_str = ";".join(e.sovereign_keywords)
        csv_line = f'"{e.domain}",{e.entry_number},"{e.category}","{e.difficulty_level}","{e.input_prompt}","{e.expected_output}","{keywords_str}"'
        csv_lines.append(csv_line)
    
    return {
        "format": "csv",
        "total_entries": len(entries),
        "data": "\n".join(csv_lines),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==============================================================================
# METRICS ENDPOINT
# ==============================================================================

@app.get("/metrics")
async def metrics(db: Session = Depends(lambda: SessionLocal())):
    """Prometheus metrics."""
    
    total_entries = db.query(BenchmarkEntry).count()
    domain_counts = {}
    for entry in db.query(BenchmarkEntry).all():
        domain_counts[entry.domain] = domain_counts.get(entry.domain, 0) + 1
    
    metrics_text = f"""# HELP eval_builder_total_benchmarks Total benchmark entries
# TYPE eval_builder_total_benchmarks gauge
eval_builder_total_benchmarks {total_entries}

# HELP eval_builder_crytonet_tier Container CRYTONET tier
# TYPE eval_builder_crytonet_tier gauge
eval_builder_crytonet_tier{{"tier":"medium"}} 1
"""
    
    for domain, count in domain_counts.items():
        metrics_text += f"eval_builder_domain_entries{{domain=\"{domain}\"}} {count}\n"
    
    return metrics_text

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8025))
    workers = int(os.getenv('WORKERS', 2))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info"
    )

# ==============================================================================
# END OF eval_dataset_builder.py
# Tag: v3.0.0
# 14 Sovereign Benchmarks: Mandingu Governance, JobHub Recruitment, African Legal
# CRYTONET Tier: MEDIUM
# Dharmakaya Guardian: eval_dataset_builder
# ==============================================================================
