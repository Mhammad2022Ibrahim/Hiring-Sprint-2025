"""
Gradio Web UI for Vehicle Damage Detection
User-friendly interface for vehicle inspection
"""

import gradio as gr
import json
from datetime import datetime
from PIL import Image

from detector import DamageDetector
from config import (
    ROBOFLOW_API_KEY,
    ROBOFLOW_MODEL_ID,
    HOST,
    PORT,
    APP_TITLE,
    APP_DESCRIPTION
)

# Initialize detector
detector = DamageDetector(
    api_key=ROBOFLOW_API_KEY,
    model_id=ROBOFLOW_MODEL_ID
)


def analyze_single_image(image):
    """Analyze a single vehicle image for damages"""
    
    if image is None:
        return None, "⚠️ Please upload an image!", ""
    
    try:
        # Convert to PIL Image
        img = Image.fromarray(image).convert('RGB')
        
        # Detect damages
        detections = detector.detect_damages(img)
        
        # Draw annotations
        annotated_img = detector.draw_detections(img, detections)
        
        # Calculate statistics
        total_cost = sum(d['estimated_cost'] for d in detections)
        severity_counts = {
            'minor': sum(1 for d in detections if d['severity'] == 'minor'),
            'moderate': sum(1 for d in detections if d['severity'] == 'moderate'),
            'severe': sum(1 for d in detections if d['severity'] == 'severe')
        }
        
        # Generate report
        report_md = f"""
# 🚗 Vehicle Damage Analysis Report
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Summary
{'✅ **No damages detected!**' if len(detections) == 0 else f'⚠️ **Found {len(detections)} damage(s)**'}

## Statistics
- **Total Damages:** {len(detections)}
- **Minor:** {severity_counts['minor']} | **Moderate:** {severity_counts['moderate']} | **Severe:** {severity_counts['severe']}
- **Estimated Repair Cost:** **${total_cost}**

"""
        
        if detections:
            report_md += "## Detailed Damage List\n\n"
            report_md += "| # | Type | Severity | Confidence | Location | Cost |\n"
            report_md += "|---|------|----------|------------|----------|------|\n"
            for i, det in enumerate(detections, 1):
                x1, y1 = det['bbox'][:2]
                report_md += (
                    f"| {i} | {det['class']} | {det['severity']} | "
                    f"{det['confidence']*100:.1f}% | ({x1}, {y1}) | "
                    f"${det['estimated_cost']} |\n"
                )
        
        report_md += "\n---\n*Powered by Roboflow AI Detection*"
        
        # JSON output as string
        json_data = {
            'timestamp': datetime.now().isoformat(),
            'total_damages': len(detections),
            'estimated_cost': total_cost,
            'severity_breakdown': severity_counts,
            'damages': []
        }
        
        for d in detections:
            json_data['damages'].append({
                'class': str(d['class']),
                'severity': str(d['severity']),
                'confidence': float(round(d['confidence']*100, 1)),
                'location': {'x': int(d['bbox'][0]), 'y': int(d['bbox'][1])},
                'estimated_cost': int(d['estimated_cost'])
            })
        
        json_output = json.dumps(json_data, indent=2)
        
        return annotated_img, report_md, json_output
    
    except Exception as e:
        import traceback
        error_msg = f"❌ **Error:** {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        return None, error_msg, ""


def compare_images_fn(pickup_image, return_image):
    """Compare pickup and return images to find new damages"""
    
    if pickup_image is None or return_image is None:
        return None, "⚠️ Please upload both pickup and return images!", ""
    
    try:
        # Convert to PIL Images
        pickup_img = Image.fromarray(pickup_image).convert('RGB')
        return_img = Image.fromarray(return_image).convert('RGB')
        
        # Compare images
        comparison = detector.compare_images(pickup_img, return_img)
        
        # Draw annotations
        pickup_annotated = detector.draw_detections(
            pickup_img,
            comparison['pickup_damages'],
            {'minor': 'green', 'moderate': 'green', 'severe': 'green'}
        )
        
        return_annotated = detector.draw_detections(
            return_img,
            comparison['new_damages']
        )
        
        # Create side-by-side comparison
        w1, h1 = pickup_annotated.size
        w2, h2 = return_annotated.size
        max_h = max(h1, h2)
        
        combined = Image.new('RGB', (w1 + w2, max_h), color='white')
        combined.paste(pickup_annotated, (0, 0))
        combined.paste(return_annotated, (w1, 0))
        
        # Generate report
        new_cost = comparison['total_new_cost']
        new_damages = comparison['new_damages']
        
        report_md = f"""
# 🔄 Vehicle Comparison Report
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Summary
- **Pickup Damages:** {len(comparison['pickup_damages'])}
- **Return Damages:** {len(comparison['return_damages'])}
- **New Damages:** {len(new_damages)}
- **New Damage Cost:** **${new_cost}**

{comparison['summary']}

"""
        
        if new_damages:
            report_md += "## New Damages Detected\n\n"
            report_md += "| # | Type | Severity | Confidence | Cost |\n"
            report_md += "|---|------|----------|------------|------|\n"
            for i, det in enumerate(new_damages, 1):
                report_md += (
                    f"| {i} | {det['class']} | {det['severity']} | "
                    f"{det['confidence']*100:.1f}% | ${det['estimated_cost']} |\n"
                )
        
        report_md += "\n---\n*Green boxes = Existing | Red/Orange/Yellow = New damages*"
        
        # JSON output as string
        json_data = {
            'timestamp': datetime.now().isoformat(),
            'pickup_damages': len(comparison['pickup_damages']),
            'return_damages': len(comparison['return_damages']),
            'new_damages': len(new_damages),
            'new_damage_cost': new_cost,
            'new_damage_details': []
        }
        
        for d in new_damages:
            json_data['new_damage_details'].append({
                'class': str(d['class']),
                'severity': str(d['severity']),
                'confidence': float(round(d['confidence']*100, 1)),
                'estimated_cost': int(d['estimated_cost'])
            })
        
        json_output = json.dumps(json_data, indent=2)
        
        return combined, report_md, json_output
    
    except Exception as e:
        import traceback
        error_msg = f"❌ **Error:** {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        return None, error_msg, ""


# =============================================================================
# BUILD GRADIO INTERFACE
# =============================================================================

with gr.Blocks(title=APP_TITLE, theme=gr.themes.Soft()) as demo:
    
    gr.Markdown(f"""
    # 🚗 {APP_TITLE}
    
    {APP_DESCRIPTION}
    """)
    
    with gr.Tabs() as tabs:
        # Tab 1: Single Image Analysis
        with gr.Tab("📸 Single Image Analysis"):
            gr.Markdown("""
            ### Quick Damage Detection
            Upload a vehicle image to detect and analyze all damages instantly.
            Supports multiple angles: front, rear, sides, roof, interior.
            """)
            
            with gr.Row():
                with gr.Column():
                    single_input = gr.Image(
                        label="📸 Upload Vehicle Image",
                        type="numpy",
                        sources=["upload", "webcam", "clipboard"]
                    )
                    analyze_btn = gr.Button(
                        "🔍 Analyze Damages",
                        variant="primary",
                        size="lg"
                    )
                
                with gr.Column():
                    single_output_image = gr.Image(
                        label="✅ Detected Damages (Annotated)"
                    )
            
            single_output_report = gr.Markdown(label="📊 Analysis Report")
            
            with gr.Accordion("📋 JSON Output (for API integration)", open=False):
                single_output_json = gr.Textbox(label="JSON Data", lines=10, max_lines=20)
            
            analyze_btn.click(
                fn=analyze_single_image,
                inputs=[single_input],
                outputs=[single_output_image, single_output_report, single_output_json]
            )
        
        # Tab 2: Comparison Mode
        with gr.Tab("🔄 Comparison Mode"):
            gr.Markdown("""
            ### Compare Pickup vs Return
            Upload vehicle photos from pickup and return to identify new damages.
            Side-by-side comparison highlights what changed during rental.
            """)
            
            with gr.Row():
                with gr.Column():
                    pickup_input = gr.Image(
                        label="📸 Pickup Photo (Before Rental)",
                        type="numpy",
                        sources=["upload", "webcam", "clipboard"]
                    )
                
                with gr.Column():
                    return_input = gr.Image(
                        label="📸 Return Photo (After Rental)",
                        type="numpy",
                        sources=["upload", "webcam", "clipboard"]
                    )
            
            compare_btn = gr.Button(
                "🔍 Compare & Analyze",
                variant="primary",
                size="lg"
            )
            
            compare_output_image = gr.Image(
                label="🔄 Side-by-Side Comparison"
            )
            
            compare_output_report = gr.Markdown(label="📊 Comparison Report")
            
            with gr.Accordion("📋 JSON Output (for API integration)", open=False):
                compare_output_json = gr.Textbox(label="JSON Data", lines=10, max_lines=20)
            
            compare_btn.click(
                fn=compare_images_fn,
                inputs=[pickup_input, return_input],
                outputs=[compare_output_image, compare_output_report, compare_output_json]
            )
    
    gr.Markdown("""
    ---
    ### 🔧 Technical Details
    
    **AI Model:** YOLOv11 custom-trained on Roboflow
    **Detection Classes:** 23 specialized vehicle damage types
    **API Integration:** REST/GraphQL endpoints available
    **Supported Formats:** JPG, PNG, JPEG
    **Camera Support:** Desktop, tablet, phone cameras via HTML5
    
    ### 📖 How It Works
    
    1. **Upload/Capture:** Use built-in cameras or upload images
    2. **AI Detection:** Roboflow API identifies damages with confidence scores
    3. **Analysis:** Severity estimation (minor/moderate/severe) and cost calculation
    4. **Report:** Visual annotations + detailed breakdown + JSON export
    
    ### 📡 API Access
    
    REST API available at port 8000. See `/api/docs` for interactive documentation.
    
    **Endpoints:**
    - `POST /api/detect` - Single image analysis
    - `POST /api/compare` - Pickup vs return comparison
    - `GET /api/damage-classes` - List all detectable damages
    - `GET /api/repair-costs` - Cost estimation matrix
    
    ---
    
    *Powered by Roboflow AI • Built with Gradio & FastAPI*
    """)


if __name__ == "__main__":
    demo.launch(
        share=False,
        server_name=HOST,
        server_port=PORT
    )
