"""
Ollama AI Integration for Clinical Insights
Generates explanations using local Gemma model
"""

import requests
import json
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"

# Load prompts config
config_path = Path(__file__).parent / "ai_prompts_config.json"
with open(config_path, 'r') as f:
    PROMPTS_CONFIG = json.load(f)

async def generate_ai_insight(metrics):
    """Generate AI clinical insight using Ollama Gemma"""
    
    # Check if Gemma is available
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            return {
                "explanation": generate_fallback_explanation(metrics),
                "confidence": 0.0,
                "model": "fallback"
            }
        
        models = response.json().get('models', [])
        gemma_model = next((m for m in models if 'gemma' in m.get('name', '').lower()), None)
        
        if not gemma_model:
            return {
                "explanation": generate_fallback_explanation(metrics),
                "confidence": 0.0,
                "model": "fallback"
            }
        
        # Select appropriate prompt based on metrics
        prompt = create_medical_prompt(metrics)
        
        # Get model config
        model_config = PROMPTS_CONFIG["model_config"]["ollama"]
        
        # Call Ollama
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": gemma_model['name'],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": model_config["temperature"],
                    "num_predict": model_config["max_tokens"]
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            explanation = result.get("response", "").strip()
            
            return {
                "explanation": explanation,
                "confidence": 0.85,
                "model": f"Ollama-{gemma_model['name']}"
            }
        else:
            return {
                "explanation": generate_fallback_explanation(metrics),
                "confidence": 0.0,
                "model": "fallback"
            }
            
    except Exception as e:
        print(f"⚠️ AI insight generation failed: {e}")
        return {
            "explanation": generate_fallback_explanation(metrics),
            "confidence": 0.0,
            "model": "fallback"
        }

def create_medical_prompt(metrics):
    """Create medical analysis prompt for AI"""
    volume_cm3 = metrics['stroke_volume_cm3']
    percentage = metrics['brain_percentage']
    severity = metrics['severity'].lower()
    has_stroke = metrics['has_stroke']
    
    prompts = PROMPTS_CONFIG["ai_prompts"]["stroke_analysis"]
    
    if not has_stroke:
        return prompts["no_stroke_detected"]
    elif severity == "minimal":
        return prompts["minimal_stroke"].format(
            volume_cm3=volume_cm3,
            percentage=percentage
        )
    elif severity == "low":
        return prompts["minimal_stroke"].format(
            volume_cm3=volume_cm3,
            percentage=percentage
        )
    elif severity == "moderate":
        return prompts["moderate_stroke"].format(
            volume_cm3=volume_cm3,
            percentage=percentage,
            severity=severity
        )
    elif severity == "high":
        return prompts["severe_stroke"].format(
            volume_cm3=volume_cm3,
            percentage=percentage,
            severity=severity
        )
    else:
        # Default stroke detected prompt
        return prompts["stroke_detected"].format(
            volume_cm3=volume_cm3,
            percentage=percentage,
            severity=severity
        )

def generate_fallback_explanation(metrics):
    """Generate fallback explanation if AI is unavailable"""
    fallbacks = PROMPTS_CONFIG["ai_prompts"]["fallback_responses"]
    
    if not metrics['has_stroke']:
        return fallbacks["no_stroke"]
    
    volume = metrics['stroke_volume_cm3']
    percentage = metrics['brain_percentage']
    severity = metrics['severity'].lower()
    
    if severity == "minimal" or severity == "low":
        return fallbacks["minimal"].format(
            volume_cm3=volume,
            percentage=percentage
        )
    elif severity == "moderate":
        return fallbacks["moderate"].format(
            volume_cm3=volume,
            percentage=percentage
        )
    else:
        return fallbacks["severe"].format(
            volume_cm3=volume,
            percentage=percentage
        )
