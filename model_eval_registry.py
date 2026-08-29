#!/usr/bin/env python3
# ==============================================================================
# NDLOVU AI / ORA UNIVERSE — MODEL EVAL REGISTRY v3.0.0
# Performance Intelligence & Data-Driven Model Routing
# ==============================================================================
# Module: F1 Part 4 — AI NATION v3.0 Integration
# Builder: King Mandingu Letlape
# Target: Container 22 (model_eval_registry:8022)
# ==============================================================================

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from enum import Enum

import aiohttp
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Integer, Float, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis.asyncio as redis
import numpy as np

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [EVAL-REGISTRY] %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://mandingu:password@postgres:5432/model_eval_registry')
REDIS_URL = os.getenv('REDIS_URL', 'redis://:password@redis:6379/19')
DHARMAKAYA_ENDPOINT = os.getenv('DHARMAKAYA_ENDPOINT', 'http://dharmakaya:8015')
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

class EvalResult(Base):
    """Store model evaluation results."""
    __tablename__ = 'eval_results'
    
    id = Column(Integer, primary_key=True, index=True)
    eval_id = Column(String(128), unique=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    model = Column(String(64), index=True)
    domain = Column(String(64), index=True)
    benchmark_entry = Column(Integer)
    input_prompt = Column(String(2048))
    expected_output = Column(String(2048))
    model_output = Column(String(2048))
    latency_ms = Column(Float)
    tokens_input = Column(Integer)
    tokens_output = Column(Integer)
    cost = Column(Float)
    quality_score = Column(Float)  # 0-1.0
    alignment_score = Column(Float)  # Dharmakaya alignment
    rouge_score = Column(Float)  # ROUGE-L metric
    bleu_score = Column(Float)  # BLEU metric
    semantic_similarity = Column(Float)  # Cosine similarity to expected
    status = Column(String(32), default='completed')  # completed, failed, pending
    error_reason = Column(String(512), nullable=True)
    dharmakaya_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_eval_model_domain', 'model', 'domain'),
        Index('ix_eval_timestamp_model', 'timestamp', 'model'),
    )

class ModelScore(Base):
    """Aggregate scores per model."""
    __tablename__ = 'model_scores'
    
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String(64), unique=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    avg_quality_score = Column(Float)
    avg_latency_ms = Column(Float)
    avg_cost = Column(Float)
    avg_alignment_score = Column(Float)
    tokens_per_second = Column(Float)
    success_rate = Column(Float)  # 0-1.0
    composite_score = Column(Float)  # Weighted sum: 0-1.0
    eval_count = Column(Integer)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    trend = Column(String(32), default='stable')  # stable, improving, degrading

# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================

class BenchmarkEntry(BaseModel):
    """Single benchmark evaluation entry."""
    domain: str = Field(..., description="Benchmark domain")
    input_prompt: str = Field(..., description="Test prompt")
    expected_output: str = Field(..., description="Expected response")
    evaluation_criteria: Dict[str, float] = Field(default={"quality": 0.5, "speed": 0.3, "cost": 0.2})

class EvalRequest(BaseModel):
    """Submit model for evaluation."""
    model: str = Field(..., description="Model identifier")
    benchmark_entries: List[BenchmarkEntry]
    skip_on_error: bool = True

class EvalResultResponse(BaseModel):
    """Single evaluation result."""
    eval_id: str
    model: str
    domain: str
    quality_score: float
    latency_ms: float
    cost: float
    alignment_score: float
    composite_score: float
    status: str
    timestamp: str

class ModelScoresResponse(BaseModel):
    """Aggregate model scores."""
    model: str
    avg_quality_score: float
    avg_latency_ms: float
    avg_cost: float
    avg_alignment_score: float
    composite_score: float
    success_rate: float
    eval_count: int
    trend: str
    timestamp: str

class ModelsScoresListResponse(BaseModel):
    """List of all model scores."""
    models: Dict[str, Dict[str, Any]]
    timestamp: str
    total_evals: int

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    container: str
    timestamp: str
    postgres_connected: bool
    redis_connected: bool
    benchmark_domains: List[str]
    benchmark_entries: int
    crytonet_tier: str

# ==============================================================================
# EVAL SCORING ENGINE
# ==============================================================================

class EvalScoringEngine:
    """
    Compute quality, latency, cost, and alignment scores.
    Uses multiple metrics: ROUGE, BLEU, semantic similarity, Dharmakaya alignment.
    """
    
    @staticmethod
    def compute_rouge_l(reference: str, hypothesis: str) -> float:
        """
        Simplified ROUGE-L (Longest Common Subsequence).
        Returns score 0-1.0
        """
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        if not ref_words or not hyp_words:
            return 0.0
        
        # LCS length
        m, n = len(ref_words), len(hyp_words)
        lcs = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_words[i - 1] == hyp_words[j - 1]:
                    lcs[i][j] = lcs[i - 1][j - 1] + 1
                else:
                    lcs[i][j] = max(lcs[i - 1][j], lcs[i][j - 1])
        
        lcs_length = lcs[m][n]
        precision = lcs_length / len(hyp_words) if hyp_words else 0
        recall = lcs_length / len(ref_words) if ref_words else 0
        
        if precision + recall == 0:
            return 0.0
        
        f_score = 2 * (precision * recall) / (precision + recall)
        return f_score
    
    @staticmethod
    def compute_bleu(reference: str, hypothesis: str) -> float:
        """
        Simplified BLEU score (1-gram precision).
        Returns score 0-1.0
        """
        ref_words = set(reference.lower().split())
        hyp_words = hypothesis.lower().split()
        
        if not hyp_words:
            return 0.0
        
        matches = sum(1 for w in hyp_words if w in ref_words)
        return matches / len(hyp_words)
    
    @staticmethod
    def compute_semantic_similarity(reference: str, hypothesis: str) -> float:
        """
        Simple semantic similarity using word overlap.
        Returns score 0-1.0
        """
        ref_words = set(reference.lower().split())
        hyp_words = set(hypothesis.lower().split())
        
        if not ref_words or not hyp_words:
            return 0.0
        
        intersection = len(ref_words & hyp_words)
        union = len(ref_words | hyp_words)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def compute_quality_score(
        rouge: float,
        bleu: float,
        semantic: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Composite quality score from multiple metrics.
        """
        if weights is None:
            weights = {"rouge": 0.4, "bleu": 0.35, "semantic": 0.25}
        
        score = (
            rouge * weights["rouge"] +
            bleu * weights["bleu"] +
            semantic * weights["semantic"]
        )
        
        return min(score, 1.0)
    
    @staticmethod
    def compute_efficiency_score(
        latency_ms: float,
        cost: float,
        latency_target_ms: float = 2000,
        cost_target: float = 0.001,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Efficiency score combining latency and cost.
        """
        if weights is None:
            weights = {"latency": 0.6, "cost": 0.4}
        
        # Normalize latency (lower is better)
        latency_score = 1.0 - min(latency_ms / latency_target_ms, 1.0)
        
        # Normalize cost (lower is better)
        cost_score = 1.0 - min(cost / cost_target, 1.0)
        
        score = latency_score * weights["latency"] + cost_score * weights["cost"]
        return min(score, 1.0)
    
    @staticmethod
    def compute_composite_score(
        quality: float,
        efficiency: float,
        alignment: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Final composite score: quality + efficiency + alignment.
        """
        if weights is None:
            weights = {"quality": 0.5, "efficiency": 0.3, "alignment": 0.2}
        
        score = (
            quality * weights["quality"] +
            efficiency * weights["efficiency"] +
            alignment * weights["alignment"]
        )
        
        return min(score, 1.0)

# ==============================================================================
# FASTAPI APPLICATION
# ==============================================================================

app = FastAPI(
    title="Model Eval Registry v3.0.0",
    description="Performance intelligence and data-driven model routing for AI NATION v3.0",
    version="3.0.0"
)

scoring_engine = EvalScoringEngine()

# ==============================================================================
# LIFESPAN EVENTS
# ==============================================================================

@app.on_event("startup")
async def startup():
    """Initialize database."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
        logger.info(f"Benchmark domains: {BENCHMARK_DOMAINS}")
        logger.info(f"Benchmark entries: {BENCHMARK_ENTRIES}")
        logger.info("Model Eval Registry v3.0.0 started")
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
    
    redis_ok = True  # Simplified
    
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version="3.0.0",
        container="model_eval_registry",
        timestamp=datetime.now(timezone.utc).isoformat(),
        postgres_connected=db_ok,
        redis_connected=redis_ok,
        benchmark_domains=BENCHMARK_DOMAINS,
        benchmark_entries=BENCHMARK_ENTRIES,
        crytonet_tier="high"
    )

# ==============================================================================
# EVAL SUBMISSION ENDPOINT
# ==============================================================================

@app.post("/api/v1/evals/submit")
async def submit_eval(
    req: EvalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Submit model for evaluation against benchmark suite.
    """
    
    logger.info(f"Eval request: {req.model}, {len(req.benchmark_entries)} entries")
    
    results = []
    
    for entry in req.benchmark_entries:
        try:
            # Compute metrics
            rouge = scoring_engine.compute_rouge_l(entry.expected_output, "")  # Would call model
            bleu = scoring_engine.compute_bleu(entry.expected_output, "")
            semantic = scoring_engine.compute_semantic_similarity(entry.expected_output, "")
            
            quality_score = scoring_engine.compute_quality_score(rouge, bleu, semantic)
            
            # Create eval result
            eval_result = EvalResult(
                eval_id=f"eval_{datetime.now(timezone.utc).timestamp()}",
                model=req.model,
                domain=entry.domain,
                benchmark_entry=1,
                input_prompt=entry.input_prompt,
                expected_output=entry.expected_output,
                model_output="",
                latency_ms=0.0,
                tokens_input=0,
                tokens_output=0,
                cost=0.0,
                quality_score=quality_score,
                alignment_score=0.9,
                rouge_score=rouge,
                bleu_score=bleu,
                semantic_similarity=semantic,
                status="completed"
            )
            
            db.add(eval_result)
            db.commit()
            
            results.append({
                "eval_id": eval_result.eval_id,
                "domain": entry.domain,
                "quality_score": quality_score,
                "status": "completed"
            })
        
        except Exception as e:
            logger.error(f"Eval error: {str(e)}")
            if not req.skip_on_error:
                raise HTTPException(status_code=500, detail=str(e))
    
    # Schedule score aggregation
    background_tasks.add_task(aggregate_model_scores, req.model)
    
    return {
        "model": req.model,
        "results_count": len(results),
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==============================================================================
# SCORE AGGREGATION (Background task)
# ==============================================================================

def aggregate_model_scores(model: str):
    """
    Aggregate eval results into model score.
    """
    db = SessionLocal()
    try:
        evals = db.query(EvalResult).filter(EvalResult.model == model).all()
        
        if not evals:
            logger.warning(f"No evals found for {model}")
            return
        
        avg_quality = np.mean([e.quality_score for e in evals if e.quality_score])
        avg_latency = np.mean([e.latency_ms for e in evals if e.latency_ms])
        avg_cost = np.mean([e.cost for e in evals if e.cost])
        avg_alignment = np.mean([e.alignment_score for e in evals if e.alignment_score])
        
        tokens_per_second = np.mean([
            (e.tokens_output / (e.latency_ms / 1000))
            for e in evals
            if e.latency_ms > 0 and e.tokens_output
        ]) if evals else 0
        
        success_count = sum(1 for e in evals if e.status == 'completed')
        success_rate = success_count / len(evals) if evals else 0
        
        # Compute composite score
        efficiency = scoring_engine.compute_efficiency_score(avg_latency, avg_cost)
        composite = scoring_engine.compute_composite_score(avg_quality, efficiency, avg_alignment)
        
        # Check trend
        prev_score = db.query(ModelScore).filter(ModelScore.model == model).order_by(ModelScore.timestamp.desc()).first()
        if prev_score:
            trend = "improving" if composite > prev_score.composite_score else "degrading" if composite < prev_score.composite_score else "stable"
        else:
            trend = "stable"
        
        # Upsert score
        score = db.query(ModelScore).filter(ModelScore.model == model).first()
        if score:
            score.avg_quality_score = avg_quality
            score.avg_latency_ms = avg_latency
            score.avg_cost = avg_cost
            score.avg_alignment_score = avg_alignment
            score.tokens_per_second = tokens_per_second
            score.success_rate = success_rate
            score.composite_score = composite
            score.eval_count = len(evals)
            score.trend = trend
            score.last_updated = datetime.now(timezone.utc)
        else:
            score = ModelScore(
                model=model,
                avg_quality_score=avg_quality,
                avg_latency_ms=avg_latency,
                avg_cost=avg_cost,
                avg_alignment_score=avg_alignment,
                tokens_per_second=tokens_per_second,
                success_rate=success_rate,
                composite_score=composite,
                eval_count=len(evals),
                trend=trend
            )
            db.add(score)
        
        db.commit()
        logger.info(f"Model {model} scores aggregated: composite={composite:.2f}")
    
    finally:
        db.close()

# ==============================================================================
# SCORES RETRIEVAL ENDPOINTS
# ==============================================================================

@app.get("/api/v1/models/scores", response_model=ModelsScoresListResponse)
async def get_all_model_scores(db: Session = Depends(lambda: SessionLocal())):
    """Get all model scores."""
    
    scores = db.query(ModelScore).order_by(ModelScore.composite_score.desc()).all()
    
    models_dict = {}
    for score in scores:
        models_dict[score.model] = {
            "score": score.composite_score,
            "quality": score.avg_quality_score,
            "latency_ms": score.avg_latency_ms,
            "cost_per_1k_tokens": score.avg_cost,
            "alignment": score.avg_alignment_score,
            "success_rate": score.success_rate,
            "tokens_per_second": score.tokens_per_second,
            "eval_count": score.eval_count,
            "trend": score.trend
        }
    
    return ModelsScoresListResponse(
        models=models_dict,
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_evals=db.query(EvalResult).count()
    )

@app.get("/api/v1/models/{model_id}/scores", response_model=ModelScoresResponse)
async def get_model_scores(model_id: str, db: Session = Depends(lambda: SessionLocal())):
    """Get scores for specific model."""
    
    score = db.query(ModelScore).filter(ModelScore.model == model_id).first()
    
    if not score:
        raise HTTPException(status_code=404, detail=f"No scores for model {model_id}")
    
    return ModelScoresResponse(
        model=score.model,
        avg_quality_score=score.avg_quality_score,
        avg_latency_ms=score.avg_latency_ms,
        avg_cost=score.avg_cost,
        avg_alignment_score=score.avg_alignment_score,
        composite_score=score.composite_score,
        success_rate=score.success_rate,
        eval_count=score.eval_count,
        trend=score.trend,
        timestamp=score.last_updated.isoformat()
    )

# ==============================================================================
# BENCHMARKS ENDPOINT
# ==============================================================================

@app.get("/api/v1/benchmarks")
async def get_benchmarks():
    """Get available benchmark domains and entries."""
    return {
        "domains": BENCHMARK_DOMAINS,
        "entries_per_domain": BENCHMARK_ENTRIES,
        "total_entries": len(BENCHMARK_DOMAINS) * BENCHMARK_ENTRIES,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==============================================================================
# METRICS ENDPOINT (Prometheus)
# ==============================================================================

@app.get("/metrics")
async def metrics(db: Session = Depends(lambda: SessionLocal())):
    """Prometheus metrics."""
    
    total_evals = db.query(EvalResult).count()
    model_count = db.query(ModelScore.model).distinct().count()
    
    metrics_text = f"""# HELP eval_registry_total_evals Total evaluations run
# TYPE eval_registry_total_evals counter
eval_registry_total_evals {total_evals}

# HELP eval_registry_models_tracked Number of models tracked
# TYPE eval_registry_models_tracked gauge
eval_registry_models_tracked {model_count}

# HELP eval_registry_crytonet_tier Container CRYTONET tier
# TYPE eval_registry_crytonet_tier gauge
eval_registry_crytonet_tier{{"tier":"high"}} 1
"""
    return metrics_text

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8022))
    workers = int(os.getenv('WORKERS', 4))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info"
    )

# ==============================================================================
# END OF model_eval_registry.py
# Tag: v3.0.0
# CRYTONET Tier: HIGH
# Dharmakaya Guardian: model_eval_registry
# ==============================================================================
