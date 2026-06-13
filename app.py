# app.py - Pi with Supabase persistent memory

import json
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Supabase configuration - YOUR NEW PROJECT
SUPABASE_URL = "https://qhjkcrqbshnlmvmnhqzn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFoamtjcnFic2hubG12bW5ocXpuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEzNzU5NzEsImV4cCI6MjA5Njk1MTk3MX0.Ke34mKAgL2Zr8xImhhiiOKbrbAym1UAXLBo4KqPyWDo"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# PI AI CLASS WITH SUPABASE STORAGE
# ============================================================

class Pi:
    def __init__(self, user_id="default"):
        self.user_id = user_id
    
    def tokenize(self, text):
        words = text.lower().replace(".", "").replace("?", "").replace("!", "").split()
        return set(words)
    
    def get_memories(self):
        """Fetch all memories for this user from Supabase"""
        try:
            response = supabase.table("Memories").select("*").eq("user_id", self.user_id).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching memories: {e}")
            return []
    
    def save_memory(self, memory_data):
        """Save a memory to Supabase"""
        try:
            response = supabase.table("Memories").insert(memory_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error saving memory: {e}")
            return None
    
    def find_best_match(self, input_text):
        input_keywords = self.tokenize(input_text)
        memories = self.get_memories()
        best_match = None
        best_score = 0
        
        for mem in memories:
            mem_keywords = set(mem.get("keywords", []))
            overlap = len(input_keywords & mem_keywords)
            if overlap > best_score:
                best_score = overlap
                best_match = mem
        
        return best_match, best_score
    
    def update_curiosity(self, best_score):
        if best_score == 0:
            return 0.95
        elif best_score < 2:
            return 0.7
        else:
            return 0.2
    
    def learn(self, fact, source="user"):
        keywords = list(self.tokenize(fact))
        memory_data = {
            "user_id": self.user_id,
            "input": fact,
            "keywords": keywords,
            "concepts": keywords[:3],
            "timestamp": int(datetime.now().timestamp() * 1000),
            "confidence": 0.7,
            "source": source,
            "connections": []
        }
        self.save_memory(memory_data)
        return f"I learned: {fact}"
    
    def respond(self, user_input):
        best_match, score = self.find_best_match(user_input)
        curiosity = self.update_curiosity(score)
        
        if curiosity > 0.7:
            return f"I don't know about '{user_input}'. Can you teach me?", "learn"
        elif best_match:
            return f"I remember: {best_match['input']}", "recall"
        else:
            return f"I'm not sure. Tell me more.", "probe"
    
    def get_stats(self):
        memories = self.get_memories()
        return {
            "memories": len(memories),
            "curiosity": 0.5,
            "curiosity_label": "🧠 curious",
            "connections": 0
        }


# ============================================================
# FLASK ROUTES
# ============================================================

active_ais = {}

def get_ai(user_id):
    if user_id not in active_ais:
        active_ais[user_id] = Pi(user_id)
    return active_ais[user_id]

@app.route('/chat', methods=['POST'])
def chat():
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
    user_id = request.args.get('user_id', 'default')
    ai = get_ai(user_id)
    return jsonify(ai.get_stats())

@app.route('/')
def home():
    return jsonify({
        "name": "Pi",
        "description": "An AI that learns like nature",
        "endpoints": ["POST /chat", "POST /learn", "GET /stats"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
def get_ai(user_id):
    if user_id not in active_ais:
        active_ais[user_id] = Pi(user_id)
    return active_ais[user_id]

@app.route('/chat', methods=['POST'])
def chat():
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
    user_id = request.args.get('user_id', 'default')
    ai = get_ai(user_id)
    return jsonify(ai.get_stats())

@app.route('/')
def home():
    return jsonify({
        "name": "Pi",
        "description": "An AI that learns like nature",
        "endpoints": ["POST /chat", "POST /learn", "GET /stats"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)        elif best_match:
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
