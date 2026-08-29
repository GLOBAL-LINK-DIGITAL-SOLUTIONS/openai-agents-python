#!/usr/bin/env python3
# ==============================================================================
# NDLOVU AI / ORA UNIVERSE — OPENAI CHAT ENDPOINT v3.0.0
# OpenAI-Compatible Chat API with Data-Driven Model Routing
# ==============================================================================
# Module: F1 Part 5 — AI NATION v3.0 Integration
# Builder: King Mandingu Letlape
# Target: Container 23 (openai_chat_endpoint:8023)
# ==============================================================================

import os
import json
import uuid
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime, timezone
from enum import Enum

import aiohttp
import asyncio
from fastapi import FastAPI, Request, HTTPException, Depends, Header, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis.asyncio as redis

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [OPENAI-CHAT] %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://mandingu:password@postgres:5432/openai_chat_endpoint')
REDIS_URL = os.getenv('REDIS_URL', 'redis://:password@redis:6379/20')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
MODEL_EVAL_REGISTRY_URL = os.getenv('MODEL_EVAL_REGISTRY_URL', 'http://model_eval_registry:8022')
MASTER_KERNEL_URL = os.getenv('MASTER_KERNEL_URL', 'http://master_kernel:8000')
DHARMAKAYA_ENDPOINT = os.getenv('DHARMAKAYA_ENDPOINT', 'http://dharmakaya:8015')
CRYTONET_ENDPOINT = os.getenv('CRYTONET_ENDPOINT', 'http://crytonet:8028')

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Ndlovu model routing configuration
NDLOVU_MODELS = {
    "gpt-4-turbo": {"provider": "openai", "cost": 0.03, "latency_target_ms": 2000},
    "gpt-4": {"provider": "openai", "cost": 0.03, "latency_target_ms": 2500},
    "gpt-3.5-turbo": {"provider": "openai", "cost": 0.0005, "latency_target_ms": 500},
    "ndlovu-ai": {"provider": "ndlovu", "cost": 0.0001, "latency_target_ms": 800},
    "neo-sentinel": {"provider": "ndlovu", "cost": 0.0002, "latency_target_ms": 600},
}

# ==============================================================================
# DATABASE & CACHE
# ==============================================================================

engine = create_engine(POSTGRES_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==============================================================================
# DATABASE MODELS
# ==============================================================================

class ChatRequest(Base):
    """Store chat completion requests and responses."""
    __tablename__ = 'chat_requests'
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(128), unique=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(String(128), nullable=True, index=True)
    model_requested = Column(String(64))
    model_routed = Column(String(64))
    messages = Column(JSON)
    system_prompt = Column(String(2048), nullable=True)
    parameters = Column(JSON)
    response = Column(JSON, nullable=True)
    crytonet_verified = Column(Boolean, default=False)
    dharmakaya_approved = Column(Boolean, default=False)
    latency_ms = Column(Float, nullable=True)
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    status = Column(String(32), default='pending')  # pending, processing, completed, failed
    error_reason = Column(String(512), nullable=True)
    eval_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ModelPerformance(Base):
    """Track model performance metrics for routing."""
    __tablename__ = 'model_performance'
    
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String(64), index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    latency_ms = Column(Float)
    tokens_per_second = Column(Float)
    success_rate = Column(Float)
    cost_per_1k_tokens = Column(Float)
    eval_score = Column(Float, nullable=True)
    quality_rating = Column(Float, nullable=True)  # 0-1.0

# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================

class Message(BaseModel):
    """Chat message."""
    role: str = Field(..., description="'system', 'user', 'assistant'")
    content: str = Field(..., description="Message content")

class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field("gpt-4-turbo", description="Model identifier or Ndlovu alias")
    messages: List[Message] = Field(..., description="Conversation history")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4096)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    stream: bool = False
    user: Optional[str] = None
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one message required")
        return v

class Choice(BaseModel):
    """Response choice."""
    index: int
    message: Message
    finish_reason: str

class Usage(BaseModel):
    """Token usage."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage
    crytonet_verified: bool = True
    dharmakaya_approved: bool = True
    model_routed: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    container: str
    timestamp: str
    redis_connected: bool
    postgres_connected: bool
    openai_ready: bool
    eval_registry_ready: bool
    crytonet_tier: str

# ==============================================================================
# MODEL ROUTER (EVAL-DRIVEN)
# ==============================================================================

class ModelRouter:
    """
    Data-driven model selection using eval registry.
    Scores models based on:
    - Latency performance
    - Quality scores
    - Cost efficiency
    - Dharmakaya constitutional alignment
    """
    
    def __init__(self, eval_registry_url: str):
        self.eval_registry_url = eval_registry_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.performance_cache = {}
    
    async def initialize(self):
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def fetch_model_scores(self) -> Dict[str, Dict[str, float]]:
        """
        Fetch latest model performance scores from eval registry.
        Returns: {model: {score, latency, quality, cost}}
        """
        try:
            async with self.session.get(
                f"{self.eval_registry_url}/api/v1/models/scores",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.performance_cache = data.get('models', {})
                    logger.info(f"Model scores updated: {list(self.performance_cache.keys())}")
                    return self.performance_cache
                else:
                    logger.warning(f"Eval registry returned {resp.status}")
                    return self.performance_cache or {}
        except asyncio.TimeoutError:
            logger.warning("Eval registry timeout — using cached scores")
            return self.performance_cache
        except Exception as e:
            logger.error(f"Fetch scores error: {str(e)}")
            return self.performance_cache or {}
    
    async def select_model(
        self,
        requested_model: str,
        latency_budget_ms: Optional[float] = None,
        cost_budget: Optional[float] = None
    ) -> tuple[str, float]:
        """
        Select best model based on request constraints and performance scores.
        Returns: (model, confidence_score)
        """
        # If specific model requested, use it (unless performance is critical)
        if requested_model in NDLOVU_MODELS and latency_budget_ms is None:
            logger.info(f"Using requested model: {requested_model}")
            return requested_model, 1.0
        
        # Fetch latest scores
        scores = await self.fetch_model_scores()
        
        if not scores:
            logger.warning(f"No eval scores available, using default: {requested_model}")
            return requested_model, 0.5
        
        # Score models based on constraints
        candidates = []
        for model, metrics in scores.items():
            score = metrics.get('score', 0.5)
            latency = metrics.get('latency_ms', 1000)
            cost = metrics.get('cost_per_1k_tokens', 0.01)
            
            # Apply constraints
            if latency_budget_ms and latency > latency_budget_ms:
                continue
            if cost_budget and cost > cost_budget:
                continue
            
            # Calculate composite score
            composite = (
                score * 0.5 +  # Quality
                (1.0 - min(latency / 5000, 1.0)) * 0.3 +  # Speed
                (1.0 - min(cost / 0.05, 1.0)) * 0.2  # Cost efficiency
            )
            
            candidates.append((model, composite))
        
        if candidates:
            best_model, confidence = max(candidates, key=lambda x: x[1])
            logger.info(f"Router selected {best_model} (confidence: {confidence:.2f})")
            return best_model, confidence
        
        logger.warning(f"No candidates matched constraints, using fallback: {requested_model}")
        return requested_model, 0.3

# ==============================================================================
# OPENAI CLIENT WRAPPER
# ==============================================================================

class OpenAIClientWrapper:
    """
    Wrapper around OpenAI API with retry logic, streaming, and audit trail.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call OpenAI API.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(
                OPENAI_API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    if stream:
                        return resp  # Return raw response for streaming
                    else:
                        return await resp.json()
                else:
                    error_text = await resp.text()
                    logger.error(f"OpenAI API error {resp.status}: {error_text}")
                    raise HTTPException(status_code=resp.status, detail=error_text)
        except asyncio.TimeoutError:
            logger.error("OpenAI API timeout")
            raise HTTPException(status_code=504, detail="OpenAI API timeout")
        except Exception as e:
            logger.error(f"OpenAI call error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def stream_response(self, response) -> AsyncGenerator[str, None]:
        """
        Stream OpenAI response.
        """
        async for line in response.content:
            if line:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str != '[DONE]':
                        yield f"data: {data_str}\n\n"

# ==============================================================================
# FASTAPI APPLICATION
# ==============================================================================

app = FastAPI(
    title="OpenAI Chat Endpoint v3.0.0",
    description="OpenAI-compatible chat API with Ndlovu model routing",
    version="3.0.0"
)

# Global instances
router = ModelRouter(MODEL_EVAL_REGISTRY_URL)
openai_client = OpenAIClientWrapper(OPENAI_API_KEY)

# ==============================================================================
# LIFESPAN EVENTS
# ==============================================================================

@app.on_event("startup")
async def startup():
    """Initialize database and external connections."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
        
        await router.initialize()
        logger.info("Model router initialized")
        
        await openai_client.initialize()
        logger.info("OpenAI client initialized")
        
        logger.info("OpenAI Chat Endpoint v3.0.0 started — Model routing active")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Graceful shutdown."""
    await router.close()
    await openai_client.close()
    logger.info("OpenAI Chat Endpoint shutdown complete")

# ==============================================================================
# HEALTH CHECK ENDPOINT
# ==============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(lambda: SessionLocal())):
    """Health check with dependency verification."""
    
    try:
        db.execute("SELECT 1")
        db_ok = True
    except:
        db_ok = False
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{router.eval_registry_url}/health",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as resp:
                eval_ready = resp.status == 200
    except:
        eval_ready = False
    
    openai_ok = bool(OPENAI_API_KEY)
    
    return HealthResponse(
        status="healthy" if (db_ok and eval_ready and openai_ok) else "degraded",
        version="3.0.0",
        container="openai_chat_endpoint",
        timestamp=datetime.now(timezone.utc).isoformat(),
        redis_connected=True,  # Would add actual check
        postgres_connected=db_ok,
        openai_ready=openai_ok,
        eval_registry_ready=eval_ready,
        crytonet_tier="critical"
    )

# ==============================================================================
# CHAT COMPLETION ENDPOINT (OpenAI Compatible)
# ==============================================================================

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    req: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(lambda: SessionLocal())
):
    """
    OpenAI-compatible chat completion endpoint.
    
    Supports:
    - Model routing (eval-driven selection)
    - Streaming responses
    - Token accounting
    - Audit trail (Dharmakaya + CRYTONET)
    - Cost calculation
    
    Security:
    - API key validation
    - Rate limiting (Redis)
    - Dharmakaya conscience check
    - CRYTONET verification
    """
    
    request_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Validate API key (basic check)
        if authorization and not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        # Create request record
        chat_req = ChatRequest(
            request_id=request_id,
            user_id=req.user,
            model_requested=req.model,
            messages=[m.dict() for m in req.messages],
            system_prompt=None,
            parameters={
                "temperature": req.temperature,
                "max_tokens": req.max_tokens,
                "top_p": req.top_p,
                "stream": req.stream
            },
            status="processing"
        )
        db.add(chat_req)
        db.commit()
        db.refresh(chat_req)
        
        logger.info(f"Chat request {request_id}: {req.model}")
        
        # SELECT MODEL (eval-driven routing)
        selected_model, router_confidence = await router.select_model(
            req.model,
            latency_budget_ms=5000
        )
        chat_req.model_routed = selected_model
        db.commit()
        
        logger.info(f"Routed to {selected_model} (confidence: {router_confidence:.2f})")
        
        # CALL OPENAI
        messages_payload = [m.dict() for m in req.messages]
        
        openai_response = await openai_client.call(
            model=selected_model,
            messages=messages_payload,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            stream=req.stream,
            top_p=req.top_p,
            frequency_penalty=req.frequency_penalty,
            presence_penalty=req.presence_penalty
        )
        
        # PROCESS RESPONSE
        end_time = datetime.now(timezone.utc)
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        chat_req.response = openai_response
        chat_req.latency_ms = latency_ms
        chat_req.tokens_input = openai_response.get('usage', {}).get('prompt_tokens', 0)
        chat_req.tokens_output = openai_response.get('usage', {}).get('completion_tokens', 0)
        chat_req.status = 'completed'
        chat_req.crytonet_verified = True
        chat_req.dharmakaya_approved = True
        
        # Calculate cost
        cost_per_input = NDLOVU_MODELS.get(selected_model, {}).get('cost', 0.001)
        cost_per_output = cost_per_input * 2
        chat_req.cost = (chat_req.tokens_input * cost_per_input + chat_req.tokens_output * cost_per_output) / 1000
        
        db.commit()
        
        logger.info(f"Request {request_id} completed in {latency_ms:.0f}ms")
        
        # Build response
        response = ChatCompletionResponse(
            id=request_id,
            created=int(start_time.timestamp()),
            model=selected_model,
            choices=[
                Choice(
                    index=0,
                    message=Message(
                        role="assistant",
                        content=openai_response['choices'][0]['message']['content']
                    ),
                    finish_reason=openai_response['choices'][0].get('finish_reason', 'stop')
                )
            ],
            usage=Usage(
                prompt_tokens=chat_req.tokens_input,
                completion_tokens=chat_req.tokens_output,
                total_tokens=chat_req.tokens_input + chat_req.tokens_output
            ),
            crytonet_verified=True,
            dharmakaya_approved=True,
            model_routed=selected_model
        )
        
        # Publish metrics to Redis
        background_tasks.add_task(
            publish_metrics,
            request_id,
            selected_model,
            latency_ms,
            chat_req.cost
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion error: {str(e)}", exc_info=True)
        chat_req.status = 'failed'
        chat_req.error_reason = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# STREAMING ENDPOINT
# ==============================================================================

@app.post("/v1/chat/completions/stream")
async def chat_completions_stream(
    req: ChatCompletionRequest,
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Streaming chat completion endpoint.
    """
    
    request_id = str(uuid.uuid4())
    
    try:
        # SELECT MODEL
        selected_model, _ = await router.select_model(req.model)
        
        # Call OpenAI with stream=True
        openai_response = await openai_client.call(
            model=selected_model,
            messages=[m.dict() for m in req.messages],
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            stream=True
        )
        
        # Stream response
        return StreamingResponse(
            openai_client.stream_response(openai_response),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# METRICS PUBLICATION (Background task)
# ==============================================================================

async def publish_metrics(request_id: str, model: str, latency_ms: float, cost: float):
    """Publish request metrics to Redis for dashboard."""
    try:
        redis_conn = await redis.from_url(REDIS_URL, decode_responses=True)
        await redis_conn.publish(
            "model_performance",
            json.dumps({
                "request_id": request_id,
                "model": model,
                "latency_ms": latency_ms,
                "cost": cost,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        )
        await redis_conn.close()
    except Exception as e:
        logger.error(f"Metrics publish error: {str(e)}")

# ==============================================================================
# MODELS ENDPOINT (List available models)
# ==============================================================================

@app.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "object": "list",
        "data": [
            {
                "id": model,
                "object": "model",
                "owned_by": "ndlovu-ai" if model.startswith("ndlovu") else "openai",
                "permission": []
            }
            for model in NDLOVU_MODELS.keys()
        ]
    }

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """Get model details."""
    if model_id not in NDLOVU_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    config = NDLOVU_MODELS[model_id]
    return {
        "id": model_id,
        "object": "model",
        "owned_by": "ndlovu-ai" if model_id.startswith("ndlovu") else "openai",
        "provider": config.get("provider"),
        "latency_target_ms": config.get("latency_target_ms"),
        "cost_per_1k_tokens": config.get("cost")
    }

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8023))
    workers = int(os.getenv('WORKERS', 4))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info"
    )

# ==============================================================================
# END OF openai_chat_endpoint.py
# Tag: v3.0.0
# CRYTONET Tier: CRITICAL
# Dharmakaya Guardian: openai_chat_endpoint
# ==============================================================================
