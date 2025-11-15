# 🚗 Vehicle Damage Detection System

## 📋 Overview

Professional AI-powered vehicle damage detection system for car rental inspection. Uses Roboflow YOLOv11 custom model to identify 23 types of vehicle damages with cost estimation.

---

## Project Structure

```
Hiring-Sprint-2025/
├── main.py              # Application launcher
├── detector.py          # Core detection logic (clean, modular)
├── config.py            # Configuration settings
├── ui.py                # Gradio web interface
├── api.py               # FastAPI REST endpoints
├── test_suite.py        # Comprehensive tests
├── requirements.txt     # Python dependencies
├── README.md            # This file
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.12** (recommended)
- Git

### 1. Clone & Setup Environment

```bash
# Clone repository
git clone https://github.com/Mhammad2022Ibrahim/Hiring-Sprint-2025.git
cd Hiring-Sprint-2025

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Make sure virtual environment is activated
python main.py
```

Choose from:
1. UI Only (Web Interface)
2. API Only (REST Server)
3. Both (Recommended)
4. Run Tests

### 4. Access the System

- **Web UI:** http://127.0.0.1:7860
- **API Docs:** http://127.0.0.1:8000/api/docs
- **API Endpoint:** http://127.0.0.1:8000/api/detect

---

## 📱 Using the Web UI

### Single Image Analysis

1. Go to "Single Image Analysis" tab
2. Upload vehicle image or use camera
3. Click "Analyze Damages"
4. View:
   - Annotated image with bounding boxes
   - Detailed damage report
   - Cost breakdown
   - JSON export

### Comparison Mode

1. Go to "Comparison Mode" tab
2. Upload pickup image (before rental)
3. Upload return image (after rental)
4. Click "Compare & Analyze"
5. View:
   - Side-by-side comparison
   - New damages highlighted
   - Differential cost analysis
   - JSON export

---

## 🔌 Using the REST API

### Health Check

```bash
curl http://127.0.0.1:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-15T07:30:00",
  "model": "car-damage-detection-5ioys-4z3z4/2",
  "damage_classes": 23
}
```

### Detect Damages

```bash
curl -X POST http://127.0.0.1:8000/api/detect \
  -F "file=@vehicle.jpg"
```

Response:
```json
{
  "success": true,
  "summary": {
    "total_damages": 3,
    "total_estimated_cost": 850,
    "severity_breakdown": {
      "minor": 1,
      "moderate": 1,
      "severe": 1
    }
  },
  "detections": [
    {
      "class": "front-bumper-dent",
      "confidence": 0.942,
      "severity": "moderate",
      "estimated_cost": 300,
      "bbox": {"x1": 450, "y1": 320, "x2": 570, "y2": 405}
    }
  ],
  "annotated_image": "data:image/jpeg;base64,..."
}
```

### Compare Images

```bash
curl -X POST http://127.0.0.1:8000/api/compare \
  -F "pickup_image=@pickup.jpg" \
  -F "return_image=@return.jpg"
```

### Get Damage Classes

```bash
curl http://127.0.0.1:8000/api/damage-classes
```

### Get Repair Costs

```bash
curl http://127.0.0.1:8000/api/repair-costs
```

---

## 🎯 Damage Classes (23 Types)

### Dents (11)
- bonnet-dent
- doorouter-dent
- fender-dent
- front-bumper-dent
- pillar-dent
- quaterpanel-dent
- rear-bumper-dent
- roof-dent
- medium-Bodypanel-Dent
- Major-Rear-Bumper-Dent
- RunningBoard-Dent

### Scratches (3)
- doorouter-scratch
- front-bumper-scratch
- rear-bumper-scratch

### Paint Damage (3)
- doorouter-paint-trace
- paint-chip
- paint-trace

### Glass & Lights (6)
- Front-Windscreen-Damage
- Rear-windscreen-Damage
- Headlight-Damage
- Taillight-Damage
- Signlight-Damage
- Sidemirror-Damage

---

## 💰 Cost Estimation

Sample costs (USD):

| Damage Type | Minor | Moderate | Severe |
|-------------|-------|----------|--------|
| bonnet-dent | $150 | $400 | $800 |
| doorouter-scratch | $50 | $150 | $400 |
| Front-Windscreen-Damage | $200 | $500 | $1000 |
| Major-Rear-Bumper-Dent | $300 | $700 | $1500 |

*Full cost matrix in `detector.py`*

---

## 🧪 Testing

### Run Test Suite

```bash
python test_suite.py
```

Tests include:
1. Detector initialization
2. Damage detection
3. Image annotation
4. Image comparison
5. API health check
6. API detection endpoint
7. Cost estimation
8. Damage class configuration


---

## 🔧 Configuration

Edit `config.py` for custom settings:

```python
# Roboflow API
ROBOFLOW_API_KEY = "your-api-key"
ROBOFLOW_MODEL_ID = "your-model-id"

# Server Settings
HOST = "127.0.0.1"
PORT = 7860
FASTAPI_PORT = 8000

# Detection Settings
CONFIDENCE_THRESHOLD = 0.25
```

---

## 🔧 Troubleshooting

### Common Issues

**1. ModuleNotFoundError**
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

**2. Unicode/Encoding Errors (Windows)**
```bash
# Set UTF-8 encoding
chcp 65001
python main.py
```

**3. Gradio TypeError**
- Fixed in latest version
- Uses `gr.Textbox` instead of `gr.Code` for JSON output

**4. Port Already in Use**
```bash
# Kill process using port 7860 or 8000
netstat -ano | findstr :7860
taskkill /PID <process_id> /F
```

---

## 📚 Additional Resources

- **Roboflow Docs:** https://docs.roboflow.com
- **Gradio Docs:** https://gradio.app/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com

---

## 📄 License

Proprietary - For Hiring Sprint 2025

---

## 👤 Author

Vehicle Damage Detection System
Built with Roboflow, Gradio, and FastAPI

---
