"""
WordPress AI Image Optimizer Agent - Version Simplifiée
Compatible avec tous les environnements
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading

# Configuration
class Config:
    # Hugging Face (gratuit)
    HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    HF_API_KEY = os.getenv("HF_API_KEY", "")
    
    # Base de données locale (JSON)
    DB_FILE = "agent_database.json"
    
    # Port du serveur
    PORT = int(os.getenv("PORT", 5000))

# Application Flask
app = Flask(__name__)
CORS(app)

class WordPressAIAgent:
    def __init__(self):
        self.config = Config()
        self.clients = self.load_clients()
        
    def load_clients(self) -> Dict:
        """Charge la base de données des clients."""
        if os.path.exists(self.config.DB_FILE):
            with open(self.config.DB_FILE, 'r') as f:
                return json.load(f)
        return {"clients": {}, "stats": {"total_processed": 0}}
    
    def save_clients(self):
        """Sauvegarde la base de données."""
        with open(self.config.DB_FILE, 'w') as f:
            json.dump(self.clients, f, indent=2)
    
    def generate_with_ai(self, prompt: str) -> Optional[Dict]:
        """Génère les métadonnées avec HuggingFace."""
        if not self.config.HF_API_KEY:
            # Mode démo sans clé API
            return {
                "alt_text": "Image optimisée par IA",
                "title": "Titre SEO optimisé",
                "caption": "Légende engageante pour cette image",
                "description": "Description détaillée pour le référencement"
            }
        
        headers = {"Authorization": f"Bearer {self.config.HF_API_KEY}"}
        
        payload = {
            "inputs": prompt + "\n\nRéponds uniquement avec un JSON valide.",
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(
                self.config.HF_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '')
                    
                    # Extraire le JSON
                    json_start = text.find('{')
                    json_end = text.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = text[json_start:json_end]
                        return json.loads(json_str)
        except Exception as e:
            print(f"Erreur IA: {e}")
        
        # Fallback
        return {
            "alt_text": "Image du site WordPress",
            "title": "Image optimisée",
            "caption": "Image automatiquement optimisée",
            "description": "Description générée automatiquement"
        }
    
    def process_wordpress_site(self, client_id: str, wp_data: Dict):
        """Traite un site WordPress."""
        wp_url = wp_data['url']
        wp_user = wp_data['user']
        wp_password = wp_data['password']
        
        print(f"🤖 Traitement du site {wp_url} pour le client {client_id}")
        
        # Récupérer les images
        images = self.fetch_wordpress_images(wp_url, wp_user, wp_password)
        
        processed = 0
        errors = 0
        
        for image in images[:10]:  # Limiter à 10 pour le test
            if not image.get('alt_text'):
                # Générer avec l'IA
                context = self.get_image_context(wp_url, wp_user, wp_password, image)
                prompt = self.create_prompt(context)
                metadata = self.generate_with_ai(prompt)
                
                if metadata:
                    # Mettre à jour WordPress
                    success = self.update_wordpress_image(
                        wp_url, wp_user, wp_password, 
                        image['id'], metadata
                    )
                    
                    if success:
                        processed += 1
                    else:
                        errors += 1
                
                time.sleep(1)  # Pause entre chaque image
        
        # Mettre à jour les stats
        self.update_client_stats(client_id, processed, errors)
        
        return {
            "processed": processed,
            "errors": errors,
            "total": len(images)
        }
    
    def fetch_wordpress_images(self, wp_url: str, user: str, password: str) -> List[Dict]:
        """Récupère les images d'un site WordPress."""
        images = []
        page = 1
        
        auth = (user, password)
        
        while True:
            try:
                response = requests.get(
                    f"{wp_url}/wp-json/wp/v2/media",
                    params={'per_page': 100, 'page': page},
                    auth=auth,
                    timeout=30
                )
                
                if response.status_code == 200:
                    batch = response.json()
                    if not batch:
                        break
                    images.extend(batch)
                    page += 1
                else:
                    break
            except:
                break
        
        return images
    
    def get_image_context(self, wp_url: str, user: str, password: str, image: Dict) -> Dict:
        """Récupère le contexte d'une image."""
        context = {
            'image_url': image.get('source_url', ''),
            'image_title': image.get('title', {}).get('rendered', ''),
            'page_title': '',
            'page_content': ''
        }
        
        # Simplifier pour éviter les erreurs
        return context
    
    def create_prompt(self, context: Dict) -> str:
        """Crée le prompt pour l'IA."""
        return f"""Génère des métadonnées SEO pour cette image WordPress.

URL de l'image: {context['image_url']}

Génère un JSON avec:
- alt_text: description précise (max 125 car)
- title: titre SEO (max 60 car)  
- caption: légende engageante (max 160 car)
- description: description détaillée (max 300 car)

Format JSON uniquement."""
    
    def update_wordpress_image(self, wp_url: str, user: str, password: str, 
                             image_id: int, metadata: Dict) -> bool:
        """Met à jour une image dans WordPress."""
        auth = (user, password)
        
        try:
            response = requests.post(
                f"{wp_url}/wp-json/wp/v2/media/{image_id}",
                json=metadata,
                auth=auth,
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def update_client_stats(self, client_id: str, processed: int, errors: int):
        """Met à jour les statistiques."""
        if client_id not in self.clients['clients']:
            self.clients['clients'][client_id] = {
                'stats': {'total_processed': 0, 'total_errors': 0}
            }
        
        self.clients['clients'][client_id]['stats']['total_processed'] += processed
        self.clients['clients'][client_id]['stats']['total_errors'] += errors
        self.clients['stats']['total_processed'] += processed
        
        self.save_clients()

# Instance globale
agent = WordPressAIAgent()

# Routes Flask
@app.route('/')
def home():
    """Page d'accueil."""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>WordPress AI Image Optimizer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .container { 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        h1 { 
            color: #333; 
            text-align: center;
            margin-bottom: 30px;
        }
        input, button { 
            width: 100%;
            padding: 12px; 
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        button {
            background: #0066cc;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #0052a3;
        }
        .status { 
            padding: 15px; 
            margin: 15px 0; 
            border-radius: 5px;
            text-align: center;
        }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .processing { background: #cce5ff; color: #004085; }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .stat-box { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 5px; 
            text-align: center;
            border: 1px solid #dee2e6;
        }
        .stat-box h3 {
            margin: 0 0 10px 0;
            color: #495057;
        }
        .stat-box p {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
            color: #0066cc;
        }
        label {
            display: block;
            margin-top: 15px;
            color: #495057;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>🤖 WordPress AI Image Optimizer</h1>
    
    <div class="container">
        <h2>➕ Ajouter un site WordPress</h2>
        <form id="addSite">
            <label for="clientId">ID Client</label>
            <input type="text" id="clientId" placeholder="mon-client-1" required>
            
            <label for="wpUrl">URL du site WordPress</label>
            <input type="url" id="wpUrl" placeholder="https://site-wordpress.com" required>
            
            <label for="wpUser">Utilisateur WordPress</label>
            <input type="text" id="wpUser" placeholder="admin" required>
            
            <label for="wpPassword">Mot de passe application</label>
            <input type="password" id="wpPassword" placeholder="xxxx xxxx xxxx xxxx" required>
            
            <button type="submit">🚀 Lancer l'optimisation</button>
        </form>
        <div id="status"></div>
    </div>
    
    <div class="container">
        <h2>📊 Statistiques</h2>
        <div class="stats">
            <div class="stat-box">
                <h3>Total optimisé</h3>
                <p id="totalProcessed">0</p>
            </div>
            <div class="stat-box">
                <h3>Clients actifs</h3>
                <p id="activeClients">0</p>
            </div>
        </div>
    </div>
    
    <div class="container" style="text-align: center; background: #f8f9fa;">
        <p>💡 <strong>Astuce</strong> : Créez un mot de passe d'application dans WordPress<br>
        (Utilisateurs → Profil → Mots de passe d'application)</p>
    </div>
    
    <script>
        async function addSite(e) {
            e.preventDefault();
            const status = document.getElementById('status');
            status.className = 'status processing';
            status.textContent = '⏳ Traitement en cours... Cela peut prendre quelques minutes.';
            
            const data = {
                client_id: document.getElementById('clientId').value,
                wp_url: document.getElementById('wpUrl').value,
                wp_user: document.getElementById('wpUser').value,
                wp_password: document.getElementById('wpPassword').value
            };
            
            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    status.className = 'status success';
                    status.textContent = `✅ Succès! ${result.processed} images optimisées`;
                    loadStats();
                } else {
                    status.className = 'status error';
                    status.textContent = `❌ Erreur: ${result.error}`;
                }
            } catch (error) {
                status.className = 'status error';
                status.textContent = `❌ Erreur: ${error.message}`;
            }
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('totalProcessed').textContent = stats.total_processed;
                document.getElementById('activeClients').textContent = Object.keys(stats.clients).length;
            } catch (error) {
                console.error('Erreur stats:', error);
            }
        }
        
        document.getElementById('addSite').addEventListener('submit', addSite);
        
        // Charger les stats au démarrage
        loadStats();
    </script>
</body>
</html>
    ''')

@app.route('/api/process', methods=['POST'])
def process_site():
    """Traite un site WordPress."""
    data = request.json
    
    client_id = data.get('client_id')
    wp_data = {
        'url': data.get('wp_url'),
        'user': data.get('wp_user'),
        'password': data.get('wp_password')
    }
    
    if not all([client_id, wp_data['url'], wp_data['user'], wp_data['password']]):
        return jsonify({'error': 'Données manquantes'}), 400
    
    # Ajouter le client
    if client_id not in agent.clients['clients']:
        agent.clients['clients'][client_id] = {
            'sites': [],
            'stats': {'total_processed': 0, 'total_errors': 0}
        }
    
    agent.save_clients()
    
    # Traiter directement (version simplifiée)
    result = agent.process_wordpress_site(client_id, wp_data)
    
    return jsonify(result)

@app.route('/api/stats')
def get_stats():
    """Récupère les statistiques."""
    return jsonify({
        'total_processed': agent.clients['stats']['total_processed'],
        'clients': agent.clients['clients']
    })

if __name__ == '__main__':
    print("🚀 Agent démarré sur http://localhost:5000")
    app.run(host='0.0.0.0', port=agent.config.PORT)
