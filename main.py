from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime, timezone
from fastapi.responses import FileResponse
import hashlib

app = FastAPI(title="SafePath Smart City System 🚀", version="3.1.0")

# =========================
# CORS — required for frontend
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DB SETUP
# =========================
DATABASE_URL = "sqlite:///./safepath.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# =========================
# HELPERS
# =========================
def normalize_city(city: str) -> str:
    return city.strip().lower()

def hash_report(username: str, location: str, issue: str) -> str:
    raw = username.strip().lower() + location.strip().lower() + issue.strip().lower()
    return hashlib.sha256(raw.encode()).hexdigest()

def coin_reward(severity: str) -> int:
    return {"High": 30, "Medium": 15, "Low": 5}.get(severity, 5)


# =========================
# DB MODELS
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    coins = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    user = Column(String, index=True)
    city = Column(String, index=True)
    location = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    issue = Column(String)
    severity = Column(String)
    status = Column(String, default="Pending")
    hash = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)


# =========================
# ENUMS
# =========================
class Severity(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


# =========================
# REQUEST MODELS
# =========================
class RegisterData(BaseModel):
    username: str = Field(min_length=3, max_length=30)

class ReportData(BaseModel):
    username: str = Field(min_length=3)
    city: str = Field(min_length=2)
    location: str = Field(min_length=3)
    latitude: float | None = None
    longitude: float | None = None
    issue: str = Field(min_length=5)
    severity: Severity

class SOSData(BaseModel):
    username: str = Field(min_length=3)
    city: str = Field(min_length=2)
    location: str = Field(min_length=3)
    latitude: float | None = None
    longitude: float | None = None
    issue: str = Field(min_length=5)


# =========================
# DB SESSION
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {"message": "SafePath API running 🚀", "version": "3.1.0"}


# =========================
# REGISTER
# =========================
@app.post("/register")
def register(data: RegisterData, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(username=data.username)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "coins": user.coins,
        "created_at": user.created_at
    }


# =========================
# USER LOOKUP
# =========================
@app.get("/user/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "coins": user.coins,
        "created_at": user.created_at
    }


# =========================
# REPORT
# =========================
@app.post("/report")
def add_report(data: ReportData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    report_hash = hash_report(data.username, data.location, data.issue)

    if db.query(Report).filter(Report.hash == report_hash).first():
        raise HTTPException(status_code=400, detail="Duplicate report detected 🚫")

    coins = coin_reward(data.severity.value)

    report = Report(
        user=data.username,
        city=normalize_city(data.city),
        location=data.location,
        latitude=data.latitude,
        longitude=data.longitude,
        issue=data.issue,
        severity=data.severity.value,
        status="Pending",
        hash=report_hash,
    )

    try:
        user.coins += coins
        db.add(report)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed, please try again")

    return {
        "message": "Report submitted 🚀",
        "coins_earned": coins,
        "total_coins": user.coins
    }


# =========================
# REPORTS LIST
# =========================
@app.get("/reports")
def get_reports(
    city: str | None = None,
    severity: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Report)
    if city:
        query = query.filter(Report.city == normalize_city(city))
    if severity:
        query = query.filter(Report.severity == severity)

    reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": r.id, "user": r.user, "city": r.city,
            "location": r.location, "latitude": r.latitude,
            "longitude": r.longitude, "issue": r.issue,
            "severity": r.severity, "status": r.status,
            "created_at": r.created_at
        }
        for r in reports
    ]


# =========================
# SINGLE REPORT
# =========================
@app.get("/report/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": r.id, "user": r.user, "city": r.city,
        "location": r.location, "latitude": r.latitude,
        "longitude": r.longitude, "issue": r.issue,
        "severity": r.severity, "status": r.status,
        "created_at": r.created_at
    }


# =========================
# SOS 🚨
# =========================
@app.post("/sos")
def sos(data: SOSData, db: Session = Depends(get_db)):
    sos_hash = hashlib.sha256(
        (data.username + data.location + data.issue + "sos").encode()
    ).hexdigest()

    r = Report(
        user=data.username,
        city=normalize_city(data.city),
        location=data.location,
        latitude=data.latitude,
        longitude=data.longitude,
        issue="🚨 SOS: " + data.issue,
        severity="High",
        status="URGENT",
        hash=sos_hash,
    )

    try:
        db.add(r)
        db.commit()
        db.refresh(r)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="SOS failed, please try again")

    return {"message": "SOS SENT 🚨", "report_id": r.id}


# =========================
# HEATMAP 🗺️
# =========================
@app.get("/heatmap")
def heatmap(city: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Report)
    if city:
        query = query.filter(Report.city == normalize_city(city))

    reports = query.all()
    result = []

    for r in reports:
        if r.latitude is None or r.longitude is None:
            continue
        try:
            result.append({
                "lat": float(r.latitude),
                "lng": float(r.longitude),
                "severity": r.severity,
                "issue": r.issue,
                "status": r.status,
            })
        except Exception:
            continue

    return result


# =========================
# SAFE ZONES
# =========================
@app.get("/safe-zones")
def safe_zones(city: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Report).filter(Report.severity == "Low")
    if city:
        query = query.filter(Report.city == normalize_city(city))

    result = []
    for r in query.all():
        if r.latitude is None or r.longitude is None:
            continue
        try:
            result.append({
                "lat": float(r.latitude),
                "lng": float(r.longitude),
                "city": r.city,
                "score": 90
            })
        except Exception:
            continue

    return result


# =========================
# CITY SCORE 📊
# =========================
@app.get("/city-score/{city}")
def city_score(city: str, db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.city == normalize_city(city)).all()

    if not reports:
        return {
            "city": city,
            "total_reports": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "safety_score": 100
        }

    high   = sum(1 for r in reports if r.severity == "High")
    medium = sum(1 for r in reports if r.severity == "Medium")
    low    = sum(1 for r in reports if r.severity == "Low")
    score  = max(100 - (high * 10) - (medium * 5) - (low * 2), 0)

    return {
        "city": city,
        "total_reports": len(reports),
        "high_count": high,
        "medium_count": medium,
        "low_count": low,
        "safety_score": score
    }


# =========================
# PRIORITY LIST 🔥
# =========================
@app.get("/priority")
def priority(limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    reports = (
        db.query(Report)
        .filter(Report.status != "Resolved")
        .order_by(Report.severity.desc(), Report.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id, "user": r.user, "city": r.city,
            "location": r.location, "latitude": r.latitude,
            "longitude": r.longitude, "issue": r.issue,
            "severity": r.severity, "status": r.status,
            "created_at": r.created_at
        }
        for r in reports
    ]


# =========================
# LEADERBOARD 🏆
# =========================
@app.get("/leaderboard")
def leaderboard(limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.coins.desc()).limit(limit).all()
    return [{"username": u.username, "coins": u.coins} for u in users]
@app.get("/")
def read_root():
    return FileResponse("index.html")
