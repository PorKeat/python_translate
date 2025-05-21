import os
import requests
from flask import Flask, request, render_template, jsonify, send_from_directory
from deep_translator import GoogleTranslator
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MURF_API_KEY = "ap2_8d0f50e8-4bec-4257-8856-aea70a809ffc"
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_files")
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"khmer_text": "សួស្តី", "message": "", "message_type": "success"})

    try:
        # Using deep_translator to translate
        translator = GoogleTranslator(source='en', target='km')
        khmer_text = translator.translate(text)
        return jsonify({"khmer_text": khmer_text, "message": "", "message_type": "success"})
    except Exception as e:
        return jsonify({"khmer_text": "", "message": f"Translation error: {str(e)}", "message_type": "error"})

@app.route("/generate_voiceover", methods=["POST"])
def generate_voiceover():
    data = request.get_json()
    khmer_text = data.get("khmer_text", "")
    if not khmer_text:
        return jsonify({"message": "No Khmer text provided", "message_type": "error"})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"khmer_{timestamp}.mp3"
    full_audio_path = os.path.join(AUDIO_DIR, audio_filename)
    
    try:
        # Using direct Murf API request
        url = "https://api.murf.ai/v1/speech/generate-with-key"
        
        payload = {
            "voice": "en-US-ken", # Using English voice as requested
            "text": khmer_text,
            "format": "mp3",
            "bitrate": 192000,     # Using numeric value instead of string with "k"
            "sampleRate": 48000,   # Using numeric value instead of string with "k"
            "speed": 1.0,
            "pitch": 0,
            "style": "default"
        }
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": MURF_API_KEY
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            response_data = response.json()
            audio_data = response_data.get("audioFile")
            
            # If audio data is a URL
            if audio_data and audio_data.startswith('http'):
                audio_content = requests.get(audio_data).content
                with open(full_audio_path, "wb") as f:
                    f.write(audio_content)
                
                # Create an audio player HTML element
                audio_player = f'<audio controls autoplay><source src="/audio/{audio_filename}" type="audio/mpeg">Your browser does not support the audio element.</audio>'
                
                return jsonify({
                    "message": audio_player,
                    "message_type": "success",
                    "audio_file": audio_filename
                })
            # If audio data is base64
            elif audio_data:
                import base64
                audio_bytes = base64.b64decode(audio_data)
                with open(full_audio_path, "wb") as f:
                    f.write(audio_bytes)
                
                # Create an audio player HTML element
                audio_player = f'<audio controls autoplay><source src="/audio/{audio_filename}" type="audio/mpeg">Your browser does not support the audio element.</audio>'
                
                return jsonify({
                    "message": audio_player,
                    "message_type": "success",
                    "audio_file": audio_filename
                })
            else:
                return jsonify({
                    "message": f"No audio data received from Murf API: {response_data}",
                    "message_type": "error"
                })
        else:
            return jsonify({
                "message": f"Error from Murf API: {response.text}",
                "message_type": "error"
            })
            
    except Exception as e:
        return jsonify({
            "message": f"Error generating voiceover: {str(e)}",
            "message_type": "error"
        })

@app.route("/audio/<filename>", methods=["GET"])
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)