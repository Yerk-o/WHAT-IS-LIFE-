# app.py - Emotion Pattern API with Google Gemini AI
"""
This API connects Google Gemini AI to your cellular dots game.
It interprets emotions/text and generates movement parameters for the dots.
"""

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow requests from your HTML file

# Configure Google Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("⚠️  WARNING: No GEMINI_API_KEY found!")
    print("📝 Create a .env file with: GEMINI_API_KEY=your_api_key_here")
    print("🔗 Get your key from: https://makersuite.google.com/app/apikey")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    print("✅ Google Gemini AI connected successfully!")
except Exception as e:
    print(f"❌ Gemini AI setup failed: {e}")
    model = None

def safe_float(value, default=0.5, min_val=0.0, max_val=2.0):
    """Safely convert to float with bounds"""
    try:
        result = float(value)
        return max(min_val, min(max_val, result))
    except (ValueError, TypeError):
        return default

@app.route('/health', methods=['GET'])
def health_check():
    """Check if API is working"""
    ai_status = "connected" if model else "disconnected"
    return jsonify({
        'status': 'healthy',
        'ai_model': ai_status,
        'message': 'Emotion Pattern API is running!'
    })

@app.route('/generate-emotion-pattern', methods=['POST'])
def generate_emotion_pattern():
    """
    Main endpoint: Takes emotion/text and returns dot movement parameters
    """
    try:
        # Get the request data
        data = request.get_json()
        emotion_text = data.get('emotion', '').strip()
        
        if not emotion_text:
            return jsonify({'error': 'Please provide emotion text'}), 400
        
        print(f"🎭 Analyzing emotion: '{emotion_text}'")
        
        # Try to use AI first, fallback to simple analysis
        if model:
            try:
                # Use Google Gemini to analyze the emotion
                pattern_data = analyze_emotion_with_ai(emotion_text)
            except Exception as e:
                print(f"⚠️  AI failed, using fallback: {e}")
                pattern_data = analyze_emotion_simple(emotion_text)
        else:
            # Use simple analysis if no AI
            pattern_data = analyze_emotion_simple(emotion_text)
        
        print(f"✅ Generated pattern: {pattern_data['interpretation']}")
        
        return jsonify({
            'success': True,
            'emotion': emotion_text,
            'pattern': pattern_data['pattern'],
            'interpretation': pattern_data['interpretation'],
            'ai_used': model is not None
        })
        
    except Exception as e:
        print(f"❌ Error generating pattern: {e}")
        return jsonify({'error': f'Failed to generate pattern: {str(e)}'}), 500

def analyze_emotion_with_ai(emotion_text):
    """Use Google Gemini AI to analyze emotion and create pattern"""
    
    # Create a detailed prompt for the AI
    prompt = f"""
    Analyze this emotion/feeling: "{emotion_text}"
    
    Based on this emotion, create movement parameters for animated dots/particles that would visually represent this feeling.
    
    Consider:
    - How fast should dots move? (speed: 0.2 to 2.0)
    - How much should they cluster together? (cohesion: 0.0 to 0.3) 
    - How much should they avoid each other? (separation: 10 to 60)
    - How much random/organic movement? (curve: 0.0 to 1.0)
    
    Also suggest which behavior mode best fits:
    - "standard" - organic flowing
    - "predator" - chase/flee dynamics  
    - "swarm" - group movement
    - "spiral" - circular/spiral flow
    
    Respond ONLY with valid JSON in this exact format:
    {{
        "speed": 1.2,
        "cohesion": 0.15,
        "separation": 25,
        "curve": 0.4,
        "behavior": "standard",
        "interpretation": "brief description of how this represents the emotion"
    }}
    """
    
    # Generate response with Gemini
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    
    print(f"AI Response: {response_text}")
    
    # Extract JSON from response
    try:
        # Find JSON in the response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            ai_data = json.loads(json_str)
            
            # Validate and clean the data
            pattern = {
                'speed': safe_float(ai_data.get('speed', 1.0), 1.0, 0.2, 2.0),
                'cohesion': safe_float(ai_data.get('cohesion', 0.12), 0.12, 0.0, 0.3),
                'separation': safe_float(ai_data.get('separation', 25), 25, 10, 60),
                'curve': safe_float(ai_data.get('curve', 0.3), 0.3, 0.0, 1.0),
                'behavior': ai_data.get('behavior', 'standard')
            }
            
            # Ensure behavior is valid
            valid_behaviors = ['standard', 'predator', 'swarm', 'spiral']
            if pattern['behavior'] not in valid_behaviors:
                pattern['behavior'] = 'standard'
            
            interpretation = ai_data.get('interpretation', f'AI interpretation of "{emotion_text}"')
            
            return {
                'pattern': pattern,
                'interpretation': interpretation
            }
            
        else:
            raise ValueError("No valid JSON found in AI response")
            
    except Exception as e:
        print(f"⚠️  Failed to parse AI response: {e}")
        # Fallback to simple analysis
        return analyze_emotion_simple(emotion_text)

def analyze_emotion_simple(emotion_text):
    """Simple fallback emotion analysis without AI"""
    
    text_lower = emotion_text.lower()
    
    # Default pattern
    pattern = {
        'speed': 0.8,
        'cohesion': 0.12,
        'separation': 25,
        'curve': 0.3,
        'behavior': 'standard'
    }
    
    interpretation = f"Simple pattern for '{emotion_text}'"
    
    # Analyze emotion keywords
    
    # High energy emotions
    if any(word in text_lower for word in ['excited', 'energetic', 'manic', 'hyper', 'frantic', 'wild']):
        pattern['speed'] = 1.8
        pattern['curve'] = 0.8
        pattern['behavior'] = 'swarm'
        interpretation = "High energy, chaotic movement"
    
    # Anger/Aggression
    elif any(word in text_lower for word in ['angry', 'rage', 'furious', 'aggressive', 'violent']):
        pattern['speed'] = 1.5
        pattern['separation'] = 45
        pattern['behavior'] = 'predator'
        interpretation = "Aggressive, confrontational movement"
    
    # Sadness/Depression
    elif any(word in text_lower for word in ['sad', 'depressed', 'melancholy', 'sorrow', 'grief']):
        pattern['speed'] = 0.4
        pattern['curve'] = 0.1
        pattern['cohesion'] = 0.05
        interpretation = "Slow, isolated, downward movement"
    
    # Anxiety/Fear
    elif any(word in text_lower for word in ['anxious', 'nervous', 'scared', 'fear', 'panic']):
        pattern['speed'] = 1.2
        pattern['separation'] = 35
        pattern['curve'] = 0.6
        pattern['behavior'] = 'predator'
        interpretation = "Nervous, erratic, avoidant movement"
    
    # Love/Affection
    elif any(word in text_lower for word in ['love', 'affection', 'romance', 'tender', 'caring']):
        pattern['speed'] = 0.9
        pattern['cohesion'] = 0.25
        pattern['separation'] = 15
        pattern['behavior'] = 'standard'
        interpretation = "Gentle, clustering, harmonious movement"
    
    # Joy/Happiness
    elif any(word in text_lower for word in ['happy', 'joy', 'cheerful', 'bliss', 'elated']):
        pattern['speed'] = 1.3
        pattern['cohesion'] = 0.18
        pattern['curve'] = 0.5
        pattern['behavior'] = 'swarm'
        interpretation = "Joyful, bouncy, grouped movement"
    
    # Calm/Peace
    elif any(word in text_lower for word in ['calm', 'peaceful', 'serene', 'tranquil', 'zen']):
        pattern['speed'] = 0.6
        pattern['curve'] = 0.2
        pattern['cohesion'] = 0.08
        interpretation = "Slow, peaceful, flowing movement"
    
    # Confusion/Chaos
    elif any(word in text_lower for word in ['confused', 'chaos', 'disorder', 'random', 'lost']):
        pattern['speed'] = 1.0
        pattern['curve'] = 0.9
        pattern['separation'] = 20
        pattern['behavior'] = 'spiral'
        interpretation = "Chaotic, unpredictable movement"
    
    return {
        'pattern': pattern,
        'interpretation': interpretation
    }

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        'message': 'Emotion Pattern API for "What is Life" Game',
        'endpoints': {
            '/generate-emotion-pattern': 'POST - Generate dot patterns from emotions',
            '/health': 'GET - Check API health'
        },
        'example_request': {
            'url': '/generate-emotion-pattern',
            'method': 'POST',
            'body': {'emotion': 'overwhelming joy mixed with nostalgia'},
            'response': {
                'success': True,
                'emotion': 'overwhelming joy mixed with nostalgia',
                'pattern': {
                    'speed': 1.3,
                    'cohesion': 0.18,
                    'separation': 20,
                    'curve': 0.5,
                    'behavior': 'swarm'
                },
                'interpretation': 'Joyful, bouncy movement with nostalgic flow'
            }
        }
    })

if __name__ == '__main__':
    print("🎨 Starting Emotion Pattern API...")
    print("🎭 This API connects emotions to visual dot patterns")
    print()
    print("📋 Setup Steps:")
    print("1. Create .env file with your Gemini API key")
    print("2. Install: pip install flask flask-cors google-generativeai python-dotenv")
    print("3. Get API key from: https://makersuite.google.com/app/apikey")
    print()
    print("🌐 Starting server on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)