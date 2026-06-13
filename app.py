# app.py
# Pi - An AI that learns like nature
# Built on Project Instinct research

import json
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# ============================================================
# THE AI CORE
# ============================================================

class Pi:
    """Curiosity-driven AI with persistent memory"""
    
    def __init__(self, user_id="default"):
        self.user_id = user_id
        self.memory_file = f"memory_{user_id}.json"
        self.memory = self.load_memory()
        self.curiosity = 0.5
    
    def load_memory(self):
        """Load memories from JSON file"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return []
    
    def save_memory(self):
        """Save memories to JSON file"""
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=2)
    
    def tokenize(self, text):
        """Convert text to keywords"""
        words = text.lower().replace(".", "").replace("?", "").replace("!", "").split()
        return set(words)
    
    def find_best_match(self, input_text):
        """Find most similar memory using keyword overlap"""
        input_keywords = self.tokenize(input_text)
        best_match = None
        best_score = 0
        
        for mem in self.memory:
            mem_keywords = set(mem.get("keywords", []))
            overlap = len(input_keywords & mem_keywords)
            if overlap > best_score:
                best_score = overlap
                best_match = mem
        
        return best_match, best_score
    
    def update_curiosity(self, best_score):
        """Curiosity rises when no good match exists"""
        if best_score == 0:
            self.curiosity = min(0.95, self.curiosity + 0.3)
        elif best_score < 2:
            self.curiosity = min(0.7, self.curiosity + 0.1)
        else:
            self.curiosity = max(0.1, self.curiosity - 0.2)
        return self.curiosity
    
    def learn(self, fact, source="user"):
        """Store a new memory and connect to related ones"""
        new_memory = {
            "id": len(self.memory) + 1,
            "fact": fact,
            "keywords": list(self.tokenize(fact)),
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "connections": []
        }
        self.memory.append(new_memory)
        self.connect_related(new_memory["id"])
        self.save_memory()
        return f"I learned: {fact}"
    
    def connect_related(self, new_id):
        """Auto-connect new memory to existing related memories"""
        new_mem = self.memory[new_id - 1]
        new_keywords = set(new_mem["keywords"])
        
        for existing in self.memory:
            if existing["id"] == new_id:
                continue
            existing_keywords = set(existing.get("keywords", []))
            if len(new_keywords & existing_keywords) > 0:
                if new_id not in existing.get("connections", []):
                    existing.setdefault("connections", []).append(new_id)
                if existing["id"] not in new_mem["connections"]:
                    new_mem["connections"].append(existing["id"])
        
        self.save_memory()
    
    def respond(self, user_input):
        """Generate response based on memory and curiosity"""
        best_match, score = self.find_best_match(user_input)
        self.update_curiosity(score)
        
        if self.curiosity > 0.7:
            return f"I don't know about '{user_input}'. Can you teach me?", "learn"
        elif best_match:
            return f"I remember: {best_match['fact']}", "recall"
        else:
            return f"I'm not sure. Tell me more.", "probe"
    
    def get_stats(self):
        """Return current stats"""
        return {
            "memories": len(self.memory),
            "curiosity": round(self.curiosity, 2),
            "curiosity_label": self.get_curiosity_label(),
            "connections": sum(len(m.get("connections", [])) for m in self.memory) // 2
        }
    
    def get_curiosity_label(self):
        if self.curiosity > 0.7:
            return "🔥 extreme"
        elif self.curiosity > 0.4:
            return "🧠 curious"
        elif self.curiosity > 0.2:
            return "📖 calm"
        return "😌 still"
    
    def reset(self):
        """Reset memory for this user"""
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
        self.memory = []
        self.curiosity = 0.5
        return True


# ============================================================
# FLASK WEB SERVER WITH CORS
# ============================================================

app = Flask(__name__)
CORS(app)  # This allows any frontend to call this API

# Store active AI instances per user (in memory, not persistent)
active_ais = {}

def get_ai(user_id):
    """Get or create an AI instance for a user"""
    if user_id not in active_ais:
        active_ais[user_id] = Pi(user_id)
    return active_ais[user_id]

@app.route('/chat', methods=['POST'])
def chat():
    """Main endpoint for talking to Pi"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({"error": "Message is empty"}), 400
        
        ai = get_ai(user_id)
        response, action = ai.respond(message)
        
        return jsonify({
            "response": response,
            "action": action,
            "stats": ai.get_stats()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/learn', methods=['POST'])
def learn():
    """Endpoint for teaching Pi directly"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        fact = data.get('fact', '').strip()
        
        if not fact:
            return jsonify({"error": "Fact is empty"}), 400
        
        ai = get_ai(user_id)
        result = ai.learn(fact)
        
        return jsonify({
            "message": result,
            "stats": ai.get_stats()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get AI stats for a user"""
    user_id = request.args.get('user_id', 'default')
    ai = get_ai(user_id)
    return jsonify(ai.get_stats())

@app.route('/reset', methods=['POST'])
def reset():
    """Reset AI memory for a user"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default')
        ai = get_ai(user_id)
        ai.reset()
        active_ais[user_id] = Pi(user_id)
        return jsonify({"message": f"Reset complete for user {user_id}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        "name": "Pi",
        "description": "An AI that learns like nature",
        "endpoints": [
            "POST /chat - send a message",
            "POST /learn - teach directly",
            "GET /stats - get AI stats",
            "POST /reset - reset memory"
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)        if self.curiosity > 0.7:
            return "🔥 extreme"
        elif self.curiosity > 0.4:
            return "🧠 curious"
        elif self.curiosity > 0.2:
            return "📖 calm"
        return "😌 still"
    
    def reset(self):
        """Reset memory for this user"""
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
        self.memory = []
        self.curiosity = 0.5
        return True


# ============================================================
# FLASK WEB SERVER WITH CORS
# ============================================================

app = Flask(__name__)
CORS(app)  # This allows any frontend to call this API

# Store active AI instances per user (in memory, not persistent)
active_ais = {}

def get_ai(user_id):
    """Get or create an AI instance for a user"""
    if user_id not in active_ais:
        active_ais[user_id] = Pi(user_id)
    return active_ais[user_id]

@app.route('/chat', methods=['POST'])
def chat():
    """Main endpoint for talking to Pi"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({"error": "Message is empty"}), 400
        
        ai = get_ai(user_id)
        response, action = ai.respond(message)
        
        return jsonify({
            "response": response,
            "action": action,
            "stats": ai.get_stats()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/learn', methods=['POST'])
def learn():
    """Endpoint for teaching Pi directly"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        fact = data.get('fact', '').strip()
        
        if not fact:
            return jsonify({"error": "Fact is empty"}), 400
        
        ai = get_ai(user_id)
        result = ai.learn(fact)
        
        return jsonify({
            "message": result,
            "stats": ai.get_stats()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get AI stats for a user"""
    user_id = request.args.get('user_id', 'default')
    ai = get_ai(user_id)
    return jsonify(ai.get_stats())

@app.route('/reset', methods=['POST'])
def reset():
    """Reset AI memory for a user"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default')
        ai = get_ai(user_id)
        ai.reset()
        active_ais[user_id] = Pi(user_id)
        return jsonify({"message": f"Reset complete for user {user_id}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        "name": "Pi",
        "description": "An AI that learns like nature",
        "endpoints": [
            "POST /chat - send a message",
            "POST /learn - teach directly",
            "GET /stats - get AI stats",
            "POST /reset - reset memory"
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)rt=10000)
