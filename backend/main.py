from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
from contextlib import asynccontextmanager
import models
from models import SessionLocal, engine
from discord_listener import start_discord_bot, set_trigger_callback
from task_runner import spawn_bot, send_input_to_bot
from dotenv import load_dotenv

load_dotenv()

# Create DB tables
models.init_db()

# Callback for when discord sees a drop
async def handle_discord_trigger(sku: str, site: str):
    db = SessionLocal()
    # Check if SKU exists or create a temporary task
    db_sku = db.query(models.SKU).filter(models.SKU.sku_id == sku, models.SKU.site == site).first()
    
    # If we don't have it in DB, we could optionally ignore or auto-add
    # Let's auto-add for now
    if not db_sku:
        db_sku = models.SKU(sku_id=sku, site=site, quantity=1, active=True)
        db.add(db_sku)
        db.commit()
        db.refresh(db_sku)
        
    if db_sku.active:
        # Create a task
        task = models.Task(sku_id=db_sku.id, status="running")
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Log it
        log = models.Log(task_id=task.id, message=f"Triggered by Discord for SKU {sku}", level="info")
        db.add(log)
        db.commit()
        
        # Spawn the bot
        try:
            spawn_bot(site=site, sku=sku, quantity=db_sku.quantity, task_id=task.id, chrome_version=db_sku.chrome_version)
        except Exception as e:
            task.status = "failed"
            db.commit()
            print(f"Failed to spawn bot: {e}")
            
    db.close()

set_trigger_callback(handle_discord_trigger)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Reset any stale tasks from previous runs
    db = SessionLocal()
    stale_tasks = db.query(models.Task).filter(models.Task.status.in_(["running", "paused"])).all()
    for t in stale_tasks:
        t.status = "failed"
    db.commit()
    db.close()
    
    # Startup: Run the discord bot in the background
    bot_task = asyncio.create_task(start_discord_bot())
    yield
    # Shutdown
    bot_task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Auto Checkout API is running"}

@app.get("/skus")
def get_skus(db: SessionLocal = Depends(get_db)):
    return db.query(models.SKU).all()

@app.post("/skus")
def add_sku(sku_id: str, site: str, quantity: int = 1, chrome_version: str = "auto", db: SessionLocal = Depends(get_db)):
    db_sku = models.SKU(sku_id=sku_id, site=site, quantity=quantity, chrome_version=chrome_version)
    db.add(db_sku)
    db.commit()
    db.refresh(db_sku)
    return db_sku

@app.delete("/skus/{id}")
def delete_sku(id: int, db: SessionLocal = Depends(get_db)):
    sku = db.query(models.SKU).filter(models.SKU.id == id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    db.delete(sku)
    db.commit()
    return {"status": "success"}

@app.get("/tasks")
def get_tasks(db: SessionLocal = Depends(get_db)):
    return db.query(models.Task).all()

@app.post("/tasks/{task_id}/log")
def add_log(task_id: int, message: str, level: str = "info", db: SessionLocal = Depends(get_db)):
    # Clean up massive stacktraces
    clean_message = message
    if "Stacktrace:" in clean_message:
        clean_message = clean_message.split("Stacktrace:")[0].strip()
    if "Message:" in clean_message:
        clean_message = clean_message.split("Message:")[0].strip()
        
    log = models.Log(task_id=task_id, message=clean_message, level=level)
    db.add(log)
    
    # Send to discord webhook
    import os
    import requests
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url:
        try:
            requests.post(webhook_url, json={"content": f"[{level.upper()}] Task {task_id}: {clean_message}"})
        except Exception as e:
            print(f"Webhook failed: {e}")
            
    db.commit()
    return {"status": "success"}

@app.post("/tasks/{task_id}/status")
def update_task_status(task_id: int, status: str, db: SessionLocal = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = status
    db.commit()
    return {"status": "success"}

@app.post("/tasks/run/{sku_id}")
def run_task_manually(sku_id: int, db: SessionLocal = Depends(get_db)):
    db_sku = db.query(models.SKU).filter(models.SKU.id == sku_id).first()
    if not db_sku:
        raise HTTPException(status_code=404, detail="SKU not found")
        
    # Create a task
    task = models.Task(sku_id=db_sku.id, status="running")
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Log it
    log = models.Log(task_id=task.id, message=f"Manual trigger from dashboard for SKU {db_sku.sku_id}", level="info")
    db.add(log)
    db.commit()
    
    # Spawn the bot
    try:
        spawn_bot(site=db_sku.site, sku=db_sku.sku_id, quantity=db_sku.quantity, task_id=task.id, chrome_version=db_sku.chrome_version)
    except Exception as e:
        task.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to spawn bot: {str(e)}")
        
    return task

@app.post("/tasks/{task_id}/input")
def send_input_endpoint(task_id: int, input_text: str = ""):
    success = send_input_to_bot(task_id, input_text)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to send input. Process might not be running or waiting.")
    return {"status": "success"}

@app.post("/tasks/{task_id}/stop")
def stop_task_endpoint(task_id: int, db: SessionLocal = Depends(get_db)):
    from task_runner import stop_bot
    success = stop_bot(task_id)
    
    # Update DB status
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        task.status = "failed"
        db.commit()
        
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop process. It might not be running.")
    return {"status": "success"}

@app.post("/tasks/clear")
def clear_tasks(db: SessionLocal = Depends(get_db)):
    try:
        db.query(models.Log).delete()
        db.query(models.Task).delete()
        db.commit()
        return {"status": "success", "message": "All tasks and logs cleared."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear tasks: {str(e)}")

@app.get("/system/chrome-version")
def get_system_chrome_version():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        return {"status": "success", "major_version": int(version.split('.')[0]), "full_version": version}
    except Exception:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome")
            version, _ = winreg.QueryValueEx(key, "DisplayVersion")
            return {"status": "success", "major_version": int(version.split('.')[0]), "full_version": version}
        except Exception:
            return {"status": "error", "message": "Chrome not found in registry", "major_version": None}

@app.get("/logs")
def get_logs(db: SessionLocal = Depends(get_db)):
    return db.query(models.Log).order_by(models.Log.timestamp.desc()).limit(50).all()
