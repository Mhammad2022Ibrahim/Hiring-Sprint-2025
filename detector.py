"""
Vehicle Damage Detection System
Core detection module using Roboflow API
"""

import os
import base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import List, Dict, Tuple


class DamageDetector:
    """Vehicle damage detection using Roboflow API"""
    
    # Damage class definitions (23 custom classes)
    DAMAGE_CLASSES = [
        'bonnet-dent', 'doorouter-dent', 'doorouter-paint-trace', 'doorouter-scratch',
        'fender-dent', 'front-bumper-dent', 'front-bumper-scratch', 'Front-Windscreen-Damage',
        'Headlight-Damage', 'Major-Rear-Bumper-Dent', 'medium-Bodypanel-Dent', 'paint-chip',
        'paint-trace', 'pillar-dent', 'quaterpanel-dent', 'rear-bumper-dent',
        'rear-bumper-scratch', 'Rear-windscreen-Damage', 'roof-dent', 'RunningBoard-Dent',
        'Sidemirror-Damage', 'Signlight-Damage', 'Taillight-Damage'
    ]
    
    # Repair cost estimation matrix (USD)
    REPAIR_COSTS = {
        # Dents
        'bonnet-dent': {'minor': 150, 'moderate': 400, 'severe': 800},
        'doorouter-dent': {'minor': 100, 'moderate': 350, 'severe': 700},
        'fender-dent': {'minor': 120, 'moderate': 380, 'severe': 750},
        'front-bumper-dent': {'minor': 100, 'moderate': 300, 'severe': 600},
        'pillar-dent': {'minor': 200, 'moderate': 500, 'severe': 1000},
        'quaterpanel-dent': {'minor': 150, 'moderate': 400, 'severe': 800},
        'rear-bumper-dent': {'minor': 100, 'moderate': 300, 'severe': 600},
        'roof-dent': {'minor': 200, 'moderate': 600, 'severe': 1200},
        'medium-Bodypanel-Dent': {'minor': 150, 'moderate': 400, 'severe': 900},
        'Major-Rear-Bumper-Dent': {'minor': 300, 'moderate': 700, 'severe': 1500},
        'RunningBoard-Dent': {'minor': 80, 'moderate': 250, 'severe': 500},
        
        # Scratches
        'doorouter-scratch': {'minor': 50, 'moderate': 150, 'severe': 400},
        'front-bumper-scratch': {'minor': 50, 'moderate': 150, 'severe': 350},
        'rear-bumper-scratch': {'minor': 50, 'moderate': 150, 'severe': 350},
        
        # Paint damage
        'doorouter-paint-trace': {'minor': 60, 'moderate': 180, 'severe': 450},
        'paint-chip': {'minor': 40, 'moderate': 120, 'severe': 300},
        'paint-trace': {'minor': 50, 'moderate': 150, 'severe': 400},
        
        # Glass/Light damage
        'Front-Windscreen-Damage': {'minor': 200, 'moderate': 500, 'severe': 1000},
        'Rear-windscreen-Damage': {'minor': 200, 'moderate': 500, 'severe': 1000},
        'Headlight-Damage': {'minor': 150, 'moderate': 400, 'severe': 800},
        'Taillight-Damage': {'minor': 100, 'moderate': 300, 'severe': 600},
        'Signlight-Damage': {'minor': 80, 'moderate': 200, 'severe': 400},
        'Sidemirror-Damage': {'minor': 100, 'moderate': 300, 'severe': 600},
    }
    
    def __init__(self, api_key: str, model_id: str):
        """
        Initialize Roboflow damage detector
        
        Args:
            api_key: Roboflow API key
            model_id: Roboflow model ID (workspace/project/version)
        """
        self.api_key = api_key
        self.model_id = model_id
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Roboflow API client"""
        try:
            from inference_sdk import InferenceHTTPClient
            self.client = InferenceHTTPClient(
                api_url="https://serverless.roboflow.com",
                api_key=self.api_key
            )
            print(f"✓ Roboflow API initialized")
            print(f"  Model: {self.model_id}")
        except ImportError:
            raise ImportError(
                "inference-sdk not installed. Run: pip install inference-sdk"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Roboflow client: {e}")
    
    def detect_damages(self, image: Image.Image) -> List[Dict]:
        """
        Detect damages in an image using Roboflow API
        
        Args:
            image: PIL Image object
            
        Returns:
            List of damage detections with format:
            [{
                'bbox': [x1, y1, x2, y2],
                'confidence': float,
                'class': str,
                'severity': str,
                'estimated_cost': int
            }]
        """
        # Convert image to base64
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        # Call Roboflow API
        result = self.client.infer(img_base64, model_id=self.model_id)
        
        # Parse detections
        detections = []
        img_array = np.array(image)
        h, w = img_array.shape[:2]
        
        if 'predictions' in result:
            for pred in result['predictions']:
                # Convert from center coords to corners
                x_center, y_center = pred['x'], pred['y']
                width, height = pred['width'], pred['height']
                
                x1 = int(x_center - width / 2)
                y1 = int(y_center - height / 2)
                x2 = int(x_center + width / 2)
                y2 = int(y_center + height / 2)
                
                class_name = pred['class']
                confidence = pred['confidence']
                
                # Estimate severity
                severity = self._estimate_severity(x1, y1, x2, y2, class_name, (h, w))
                
                # Get repair cost
                cost = self.REPAIR_COSTS.get(class_name, {}).get(severity, 100)
                
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': confidence,
                    'class': class_name,
                    'severity': severity,
                    'estimated_cost': cost
                })
        
        return detections
    
    def _estimate_severity(self, x1: int, y1: int, x2: int, y2: int, 
                          damage_class: str, img_shape: Tuple[int, int]) -> str:
        """
        Estimate damage severity based on size and type
        
        Args:
            x1, y1, x2, y2: Bounding box coordinates
            damage_class: Type of damage
            img_shape: (height, width) of image
            
        Returns:
            'minor', 'moderate', or 'severe'
        """
        h, w = img_shape
        bbox_area = (x2 - x1) * (y2 - y1)
        img_area = h * w
        damage_ratio = bbox_area / img_area
        
        # Critical damage types
        critical_types = ['Major-Rear-Bumper-Dent', 'Front-Windscreen-Damage', 
                         'Rear-windscreen-Damage']
        
        if damage_class in critical_types:
            if damage_ratio > 0.05:
                return 'severe'
            elif damage_ratio > 0.02:
                return 'moderate'
            else:
                return 'minor'
        
        # Standard damage assessment
        if damage_ratio > 0.08:
            return 'severe'
        elif damage_ratio > 0.03:
            return 'moderate'
        else:
            return 'minor'
    
    def draw_detections(self, image: Image.Image, detections: List[Dict], 
                       color_map: Dict[str, str] = None) -> Image.Image:
        """
        Draw bounding boxes on image
        
        Args:
            image: PIL Image
            detections: List of detections from detect_damages()
            color_map: Optional severity color mapping
            
        Returns:
            Annotated PIL Image
        """
        if color_map is None:
            color_map = {
                'minor': 'yellow',
                'moderate': 'orange',
                'severe': 'red'
            }
        
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            severity = det['severity']
            class_name = det['class']
            confidence = det['confidence']
            
            color = color_map.get(severity, 'red')
            
            # Draw bounding box
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            
            # Draw label
            label = f"{class_name} ({confidence*100:.1f}%)"
            draw.rectangle([x1, y1-25, x1+len(label)*10, y1], fill=color)
            draw.text((x1+5, y1-22), label, fill='white', font=font)
        
        return img_copy
    
    def compare_images(self, pickup_img: Image.Image, 
                      return_img: Image.Image) -> Dict:
        """
        Compare pickup and return images to find new damages
        
        Args:
            pickup_img: Image from vehicle pickup
            return_img: Image from vehicle return
            
        Returns:
            Dictionary with comparison results
        """
        pickup_damages = self.detect_damages(pickup_img)
        return_damages = self.detect_damages(return_img)
        
        # Find new damages (simple heuristic based on class count)
        pickup_classes = [d['class'] for d in pickup_damages]
        new_damages = [d for d in return_damages 
                      if d['class'] not in pickup_classes or 
                      pickup_classes.count(d['class']) < 
                      [d['class'] for d in return_damages].count(d['class'])]
        
        total_new_cost = sum(d['estimated_cost'] for d in new_damages)
        
        return {
            'pickup_damages': pickup_damages,
            'return_damages': return_damages,
            'new_damages': new_damages,
            'total_new_cost': total_new_cost,
            'summary': f"Found {len(new_damages)} new damage(s). Estimated cost: ${total_new_cost}"
        }
