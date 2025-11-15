"""
FastAPI REST API for Vehicle Damage Detection
Provides programmatic access to damage detection functionality
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from io import BytesIO
from typing import List, Optional
from datetime import datetime
import base64

from detector import DamageDetector
from config import (
    ROBOFLOW_API_KEY, 
    ROBOFLOW_MODEL_ID, 
    APP_TITLE, 
    APP_DESCRIPTION, 
    VERSION
)

# Initialize FastAPI
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector
detector = DamageDetector(
    api_key=ROBOFLOW_API_KEY,
    model_id=ROBOFLOW_MODEL_ID
)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Vehicle Damage Detection API",
        "version": VERSION,
        "docs": "/api/docs",
        "endpoints": {
            "detect": "/api/detect",
            "compare": "/api/compare",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": ROBOFLOW_MODEL_ID,
        "damage_classes": len(DamageDetector.DAMAGE_CLASSES)
    }


@app.post("/api/detect")
async def detect_damage(file: UploadFile = File(...)):
    """
    Detect damages in a single vehicle image
    
    Args:
        file: Image file (JPEG, PNG)
        
    Returns:
        JSON with detected damages, costs, and annotated image
    """
    try:
        # Read and validate image
        contents = await file.read()
        image = Image.open(BytesIO(contents))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Detect damages
        detections = detector.detect_damages(image)
        
        # Calculate total cost
        total_cost = sum(d['estimated_cost'] for d in detections)
        
        # Generate annotated image
        annotated_img = detector.draw_detections(image, detections)
        
        # Convert annotated image to base64
        img_buffer = BytesIO()
        annotated_img.save(img_buffer, format='JPEG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # Format response
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "image_info": {
                "filename": file.filename,
                "size": f"{image.size[0]}x{image.size[1]}",
                "format": image.format
            },
            "summary": {
                "total_damages": len(detections),
                "total_estimated_cost": total_cost,
                "severity_breakdown": {
                    "minor": sum(1 for d in detections if d['severity'] == 'minor'),
                    "moderate": sum(1 for d in detections if d['severity'] == 'moderate'),
                    "severe": sum(1 for d in detections if d['severity'] == 'severe')
                }
            },
            "detections": [
                {
                    "class": d['class'],
                    "confidence": round(d['confidence'], 4),
                    "severity": d['severity'],
                    "estimated_cost": d['estimated_cost'],
                    "bbox": {
                        "x1": d['bbox'][0],
                        "y1": d['bbox'][1],
                        "x2": d['bbox'][2],
                        "y2": d['bbox'][3]
                    }
                }
                for d in detections
            ],
            "annotated_image": f"data:image/jpeg;base64,{img_base64}"
        }
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@app.post("/api/compare")
async def compare_images(
    pickup_image: UploadFile = File(...),
    return_image: UploadFile = File(...)
):
    """
    Compare pickup and return images to identify new damages
    
    Args:
        pickup_image: Vehicle image at pickup
        return_image: Vehicle image at return
        
    Returns:
        JSON with comparison results and new damages
    """
    try:
        # Read images
        pickup_contents = await pickup_image.read()
        return_contents = await return_image.read()
        
        pickup_img = Image.open(BytesIO(pickup_contents)).convert('RGB')
        return_img = Image.open(BytesIO(return_contents)).convert('RGB')
        
        # Compare images
        comparison = detector.compare_images(pickup_img, return_img)
        
        # Generate annotated comparison
        pickup_annotated = detector.draw_detections(
            pickup_img, 
            comparison['pickup_damages'],
            {'minor': 'green', 'moderate': 'green', 'severe': 'green'}
        )
        
        return_annotated = detector.draw_detections(
            return_img,
            comparison['new_damages']
        )
        
        # Convert to base64
        pickup_buffer = BytesIO()
        return_buffer = BytesIO()
        pickup_annotated.save(pickup_buffer, format='JPEG')
        return_annotated.save(return_buffer, format='JPEG')
        
        pickup_base64 = base64.b64encode(pickup_buffer.getvalue()).decode('utf-8')
        return_base64 = base64.b64encode(return_buffer.getvalue()).decode('utf-8')
        
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "comparison_summary": {
                "pickup_damages": len(comparison['pickup_damages']),
                "return_damages": len(comparison['return_damages']),
                "new_damages": len(comparison['new_damages']),
                "total_new_cost": comparison['total_new_cost']
            },
            "new_damages": [
                {
                    "class": d['class'],
                    "confidence": round(d['confidence'], 4),
                    "severity": d['severity'],
                    "estimated_cost": d['estimated_cost'],
                    "bbox": {
                        "x1": d['bbox'][0],
                        "y1": d['bbox'][1],
                        "x2": d['bbox'][2],
                        "y2": d['bbox'][3]
                    }
                }
                for d in comparison['new_damages']
            ],
            "pickup_annotated": f"data:image/jpeg;base64,{pickup_base64}",
            "return_annotated": f"data:image/jpeg;base64,{return_base64}",
            "message": comparison['summary']
        }
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing images: {str(e)}"
        )


@app.get("/api/damage-classes")
async def get_damage_classes():
    """Get list of all detectable damage classes"""
    return {
        "total_classes": len(DamageDetector.DAMAGE_CLASSES),
        "classes": DamageDetector.DAMAGE_CLASSES,
        "categories": {
            "dents": [c for c in DamageDetector.DAMAGE_CLASSES if 'dent' in c.lower()],
            "scratches": [c for c in DamageDetector.DAMAGE_CLASSES if 'scratch' in c.lower()],
            "paint": [c for c in DamageDetector.DAMAGE_CLASSES if 'paint' in c.lower()],
            "glass_lights": [c for c in DamageDetector.DAMAGE_CLASSES 
                           if any(x in c.lower() for x in ['windscreen', 'light', 'mirror'])]
        }
    }


@app.get("/api/repair-costs")
async def get_repair_costs():
    """Get repair cost estimation matrix"""
    return {
        "currency": "USD",
        "costs": DamageDetector.REPAIR_COSTS
    }


if __name__ == "__main__":
    import uvicorn
    from config import HOST, FASTAPI_PORT
    
    uvicorn.run(
        "api:app",
        host=HOST,
        port=FASTAPI_PORT,
        reload=True
    )
