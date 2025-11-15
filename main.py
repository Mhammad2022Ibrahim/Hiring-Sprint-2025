"""
Main application launcher
Run UI and API servers
"""

import subprocess
import sys
import time
from multiprocessing import Process

def run_ui():
    """Launch Gradio UI"""
    subprocess.run([sys.executable, "ui.py"])

def run_api():
    """Launch FastAPI server"""
    subprocess.run([sys.executable, "api.py"])

def main():
    print("=" * 60)
    print("🚗 Vehicle Damage Detection System")
    print("=" * 60)
    print()
    print("Choose launch mode:")
    print("  1. UI Only (Gradio Web Interface)")
    print("  2. API Only (REST API Server)")
    print("  3. Both (UI + API)")
    print("  4. Run Tests")
    print()
    
    choice = input("Enter choice (1-4) [3]: ").strip() or "3"
    
    print()
    
    if choice == "1":
        print("🚀 Launching UI...")
        print("   Access at: http://127.0.0.1:7860")
        run_ui()
    
    elif choice == "2":
        print("🚀 Launching API...")
        print("   Access at: http://127.0.0.1:8000")
        print("   Docs at: http://127.0.0.1:8000/api/docs")
        run_api()
    
    elif choice == "3":
        print("🚀 Launching UI + API...")
        print("   UI: http://127.0.0.1:7860")
        print("   API: http://127.0.0.1:8000/api/docs")
        print()
        
        # Start API in background
        api_process = Process(target=run_api)
        api_process.start()
        
        time.sleep(2)  # Give API time to start
        
        # Start UI in main process
        try:
            run_ui()
        finally:
            api_process.terminate()
            api_process.join()
    
    elif choice == "4":
        print("🧪 Running tests...")
        subprocess.run([sys.executable, "test_suite.py"])
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Shutting down...")
