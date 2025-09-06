import json
import os
import logging
from typing import List, Optional, Any, Dict
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

from app import storage, parseextract_client, normalizer, config_store
from app.parseextract_client import ParseExtractError

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Enable CORS
CORS(app, origins=["*"], supports_credentials=True)

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / 'web'

# Initialize database on startup
with app.app_context():
    storage.init_db()

@app.route("/")
def index():
    """Serve the main web UI"""
    index_file = WEB_DIR / 'index.html'
    if not index_file.exists():
        return jsonify({"hint": "UI nicht gefunden. Lade das ZIP vollständig hoch."}), 404
    return send_file(str(index_file))

@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files"""
    return send_from_directory(str(WEB_DIR), filename)

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

# ---- Config endpoints ----
@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify(config_store.load_config())

@app.route('/config', methods=['POST'])
def set_config():
    """Update configuration"""
    try:
        data = config_store.load_config()
        incoming = request.get_json() or {}
        
        # Update only provided fields
        for key in ['parsextract_url', 'api_key', 'extra_params', 'stub']:
            if key in incoming:
                data[key] = incoming[key]
        
        result = config_store.save_config(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---- Ingest listing ----
@app.route("/ingests", methods=['GET'])
def api_list_ingests():
    """List recent ingests"""
    limit = request.args.get('limit', 50, type=int)
    try:
        ingests = storage.list_ingests(limit=limit)
        return jsonify(ingests)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ingests/<int:ingest_id>", methods=['GET'])
def api_get_ingest(ingest_id: int):
    """Get single ingest by ID"""
    try:
        item = storage.get_ingest(ingest_id)
        if not item:
            return jsonify({"detail": "Not found"}), 404
        return jsonify(item)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ingests/<int:ingest_id>", methods=['DELETE'])
def api_delete_ingest(ingest_id: int):
    """Delete ingest by ID"""
    try:
        ok = storage.delete_ingest(ingest_id)
        if not ok:
            return jsonify({"detail": "Not found"}), 404
        return jsonify({"deleted": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Upload ----
@app.route("/upload", methods=['POST'])
def upload_image():
    """Upload and process dart game image"""
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "No image file selected"}), 400

        # Parse form fields
        player_names_str = request.form.get('player_names', '')
        players: List[str] = []
        if player_names_str:
            players = [p.strip() for p in player_names_str.split(",") if p.strip()]

        bust_str = request.form.get('bust', 'false')
        bust_flag = bust_str.lower() in ("1", "true", "yes", "y", "on")

        meta_str = request.form.get('meta', '')
        meta_dict: Dict[str, Any] = {}
        if meta_str:
            try:
                meta_dict = json.loads(meta_str)
            except json.JSONDecodeError:
                pass

        # Read file
        contents = image_file.read()
        filename = image_file.filename or "image.jpg"
        mime = image_file.content_type or "image/jpeg"

        # Call ParseExtract
        try:
            raw = parseextract_client.call_parseextract(contents, filename, mime=mime)
        except ParseExtractError as e:
            return jsonify({"error": str(e)}), 502

        # Normalize
        normalized = normalizer.normalize_to_dartsmind(raw, players, bust_flag, meta=meta_dict)

        # Persist
        new_id = storage.insert_ingest(filename, players, bust_flag, meta_dict, raw, normalized)

        return jsonify({
            "id": new_id,
            "filename": filename,
            "raw": raw,
            "normalized": normalized,
        })

    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
