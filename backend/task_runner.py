import subprocess
import os
import sys
import threading
import requests

# Track active subprocesses: task_id -> Popen object
active_processes = {}

def spawn_bot(site: str, sku: str, quantity: int, task_id: int, chrome_version: str = "auto"):
    """
    Spawns the appropriate bot script as a background process.
    """
    script_map = {
        "target": "target/main.py",
        "walmart": "walmart/walmart.py",
        "bestbuy": "bestbuy/main.py",
        "topps": "topps/main.py"
    }
    
    script_path = script_map.get(site.lower())
    if not script_path:
        raise ValueError(f"Unknown site: {site}")
        
    full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", script_path))
    
    cmd = [
        sys.executable, full_path,
        "--sku", str(sku),
        "--quantity", str(quantity),
        "--task_id", str(task_id)
    ]
    
    if site.lower() in ["target", "bestbuy", "topps"]:
        cmd += ["--chrome-version", str(chrome_version)]
    
    # Run detached but capture stdin so we can send "Enter" remotely
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    active_processes[task_id] = process
    
    # Spawn a background thread to wait for process exit
    def monitor_process(p, tid):
        p.wait()
        # Clean up active_processes
        if tid in active_processes:
            del active_processes[tid]
        
        # If the process exited and didn't update status, mark as failed
        try:
            # We don't have DB context here so use the API
            # Get current status
            res = requests.get(f"http://localhost:8000/tasks").json()
            task = next((t for t in res if t["id"] == tid), None)
            if task and task["status"] in ["running", "paused"]:
                requests.post(f"http://localhost:8000/tasks/{tid}/log", params={"message": f"Bot process exited unexpectedly with code {p.returncode}.", "level": "error"})
                requests.post(f"http://localhost:8000/tasks/{tid}/status", params={"status": "failed"})
        except Exception:
            pass

    threading.Thread(target=monitor_process, args=(process, task_id), daemon=True).start()
    
    return process

def send_input_to_bot(task_id: int, user_input: str):
    """
    Sends string input to the bot's standard input if running.
    """
    process = active_processes.get(task_id)
    if process and process.poll() is None:
        try:
            process.stdin.write(f"{user_input}\n".encode())
            process.stdin.flush()
            return True
        except Exception:
            return False
    return False

def stop_bot(task_id: int):
    """
    Terminates the bot's subprocess.
    """
    process = active_processes.get(task_id)
    if process and process.poll() is None:
        try:
            process.terminate()
            return True
        except Exception:
            return False
    return False
