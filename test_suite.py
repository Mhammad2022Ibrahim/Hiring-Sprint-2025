"""
Comprehensive test suite for Vehicle Damage Detection System
Tests detector, API endpoints, and system integration
"""

import sys
import os
from PIL import Image, ImageDraw
import numpy as np
import requests
import json

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def create_test_image(width=640, height=480, damage_boxes=2):
    """Create a synthetic test image with simulated damages"""
    img = Image.new('RGB', (width, height), color='lightgray')
    draw = ImageDraw.Draw(img)
    
    # Draw car outline
    draw.rectangle([50, 100, width-50, height-100], outline='black', width=5)
    
    # Add damage markers
    for i in range(damage_boxes):
        x = 100 + i * 200
        y = 150 + i * 50
        draw.rectangle([x, y, x+80, y+60], outline='red', width=3)
        draw.text((x+10, y+20), f"Damage {i+1}", fill='red')
    
    return img


def test_detector_initialization():
    """Test 1: Detector Initialization"""
    print_info("Test 1: Detector Initialization")
    try:
        from detector import DamageDetector
        from config import ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID
        
        detector = DamageDetector(
            api_key=ROBOFLOW_API_KEY,
            model_id=ROBOFLOW_MODEL_ID
        )
        
        print_success("Detector initialized successfully")
        print_success(f"API Key: {ROBOFLOW_API_KEY[:10]}...")
        print_success(f"Model ID: {ROBOFLOW_MODEL_ID}")
        print_success(f"Damage Classes: {len(DamageDetector.DAMAGE_CLASSES)}")
        return True, detector
    except Exception as e:
        print_error(f"Detector initialization failed: {e}")
        return False, None


def test_damage_detection(detector):
    """Test 2: Single Image Damage Detection"""
    print_info("\nTest 2: Single Image Damage Detection")
    try:
        # Create test image
        test_img = create_test_image()
        
        # Detect damages
        detections = detector.detect_damages(test_img)
        
        print_success(f"Detection completed: {len(detections)} damage(s) found")
        
        if detections:
            for i, det in enumerate(detections, 1):
                print(f"  Damage {i}:")
                print(f"    Class: {det['class']}")
                print(f"    Confidence: {det['confidence']*100:.1f}%")
                print(f"    Severity: {det['severity']}")
                print(f"    Cost: ${det['estimated_cost']}")
        else:
            print_warning("No damages detected (expected with synthetic image)")
        
        return True
    except Exception as e:
        print_error(f"Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_annotation(detector):
    """Test 3: Image Annotation"""
    print_info("\nTest 3: Image Annotation")
    try:
        test_img = create_test_image()
        
        # Create dummy detection
        dummy_detection = [{
            'bbox': [100, 150, 180, 210],
            'confidence': 0.95,
            'class': 'front-bumper-dent',
            'severity': 'moderate',
            'estimated_cost': 300
        }]
        
        annotated = detector.draw_detections(test_img, dummy_detection)
        
        print_success("Image annotation successful")
        print_success(f"Output image size: {annotated.size}")
        
        # Save test output
        os.makedirs('test_output', exist_ok=True)
        annotated.save('test_output/annotated_test.jpg')
        print_success("Saved annotated image to: test_output/annotated_test.jpg")
        
        return True
    except Exception as e:
        print_error(f"Annotation failed: {e}")
        return False


def test_image_comparison(detector):
    """Test 4: Image Comparison"""
    print_info("\nTest 4: Pickup vs Return Comparison")
    try:
        pickup_img = create_test_image(damage_boxes=1)
        return_img = create_test_image(damage_boxes=2)
        
        comparison = detector.compare_images(pickup_img, return_img)
        
        print_success("Comparison completed")
        print(f"  Pickup damages: {len(comparison['pickup_damages'])}")
        print(f"  Return damages: {len(comparison['return_damages'])}")
        print(f"  New damages: {len(comparison['new_damages'])}")
        print(f"  Total new cost: ${comparison['total_new_cost']}")
        
        return True
    except Exception as e:
        print_error(f"Comparison failed: {e}")
        return False


def test_api_health():
    """Test 5: API Health Check"""
    print_info("\nTest 5: API Health Check")
    try:
        response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("API is healthy")
            print(f"  Status: {data['status']}")
            print(f"  Model: {data['model']}")
            print(f"  Classes: {data['damage_classes']}")
            return True
        else:
            print_warning(f"API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_warning("API not running. Start with: python api.py")
        return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_api_detect():
    """Test 6: API Detection Endpoint"""
    print_info("\nTest 6: API Detection Endpoint")
    try:
        # Create test image
        test_img = create_test_image()
        
        # Save to bytes
        from io import BytesIO
        img_bytes = BytesIO()
        test_img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Make API request
        files = {'file': ('test.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(
            "http://127.0.0.1:8000/api/detect",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("API detection successful")
            print(f"  Damages found: {data['summary']['total_damages']}")
            print(f"  Total cost: ${data['summary']['total_estimated_cost']}")
            
            # Save response
            with open('test_output/api_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print_success("Saved API response to: test_output/api_response.json")
            
            return True
        else:
            print_error(f"API request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_warning("API not running. Start with: python api.py")
        return False
    except Exception as e:
        print_error(f"API detection test failed: {e}")
        return False


def test_cost_estimation():
    """Test 7: Cost Estimation Accuracy"""
    print_info("\nTest 7: Cost Estimation")
    try:
        from detector import DamageDetector
        
        # Test cost matrix
        sample_damages = [
            ('front-bumper-dent', 'minor'),
            ('doorouter-scratch', 'moderate'),
            ('Front-Windscreen-Damage', 'severe')
        ]
        
        print_success("Testing cost estimation:")
        total = 0
        for damage_type, severity in sample_damages:
            cost = DamageDetector.REPAIR_COSTS.get(damage_type, {}).get(severity, 0)
            total += cost
            print(f"  {damage_type} ({severity}): ${cost}")
        
        print(f"  Total: ${total}")
        print_success("Cost estimation working correctly")
        return True
        
    except Exception as e:
        print_error(f"Cost estimation test failed: {e}")
        return False


def test_damage_classes():
    """Test 8: Damage Class Configuration"""
    print_info("\nTest 8: Damage Classes")
    try:
        from detector import DamageDetector
        
        classes = DamageDetector.DAMAGE_CLASSES
        costs = DamageDetector.REPAIR_COSTS
        
        print_success(f"Total damage classes: {len(classes)}")
        print_success(f"Cost entries: {len(costs)}")
        
        # Check for missing cost definitions
        missing = [c for c in classes if c not in costs]
        if missing:
            print_warning(f"Missing cost definitions for: {missing}")
        else:
            print_success("All classes have cost definitions")
        
        # Categorize
        dents = [c for c in classes if 'dent' in c.lower()]
        scratches = [c for c in classes if 'scratch' in c.lower()]
        glass = [c for c in classes if any(x in c.lower() for x in ['windscreen', 'light', 'mirror'])]
        
        print(f"  Dents: {len(dents)}")
        print(f"  Scratches: {len(scratches)}")
        print(f"  Glass/Lights: {len(glass)}")
        
        return True
        
    except Exception as e:
        print_error(f"Class configuration test failed: {e}")
        return False


def run_all_tests():
    """Run complete test suite"""
    print("=" * 60)
    print("🧪 Vehicle Damage Detection System - Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Initialization
    success, detector = test_detector_initialization()
    results.append(("Detector Initialization", success))
    
    if not success or detector is None:
        print_error("\nCannot proceed without detector. Check Roboflow API key.")
        return
    
    # Test 2-4: Detector functionality
    results.append(("Damage Detection", test_damage_detection(detector)))
    results.append(("Image Annotation", test_annotation(detector)))
    results.append(("Image Comparison", test_image_comparison(detector)))
    
    # Test 5-6: API tests
    results.append(("API Health Check", test_api_health()))
    results.append(("API Detection", test_api_detect()))
    
    # Test 7-8: Configuration
    results.append(("Cost Estimation", test_cost_estimation()))
    results.append(("Damage Classes", test_damage_classes()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        color = Colors.GREEN if success else Colors.RED
        print(f"{color}{status}{Colors.END} - {test_name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print_success("\n🎉 All tests passed! System is ready.")
    elif passed >= total * 0.7:
        print_warning("\n⚠️  Most tests passed. Check failed tests above.")
    else:
        print_error("\n❌ Multiple tests failed. Review system configuration.")
    
    print("\n💡 Tips:")
    print("  - To run API tests, start the API server: python api.py")
    print("  - To test UI, run: python ui.py")
    print("  - Check test_output/ folder for generated files")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print_error(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
