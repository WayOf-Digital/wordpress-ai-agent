"""
WordPress AI Image Optimizer Agent
Agent autonome pour optimiser les images WordPress avec IA gratuite
"""

import os
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import schedule
import threading
import time

# Configuration
class Config:
    # Mistral AI (gratuit)
    MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")  # Clé gratuite Mistral
    
    # Alternative : Hugging Face (100% gratuit)
    HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    HF_API_KEY = os.getenv("HF_API_KEY", "")
    
    # LLM local (si auto-hébergé)
    LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/api/generate")
    
    # Mode IA
    AI_MODE = os.getenv("AI_MODE", "huggingface")  # mistral, huggingface, ou local
    
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
        self.processing_queue = []
        self.results_cache = {}
        
    def load_clients(self) -> Dict:
        """Charge la base de données des clients."""
        if os.path.exists(self.config.DB_FILE):
            with open(self.config.DB_FILE, 'r') as f:
                return json.load(f)
        return {"clients": {}, "tasks": [], "stats": {"total_processed": 0}}
    
    def save_clients(self):
        """Sauvegarde la base de données."""
        with open(self.config.DB_FILE, 'w') as f:
            json.dump(self.clients, f, indent=2)
    
    async def generate_with_ai(self, prompt: str) -> Optional[Dict]:
        """Génère les métadonnées avec l'IA gratuite."""
        
        if self.config.AI_MODE == "huggingface":
            return await self.generate_with_huggingface(prompt)
        elif self.config.AI_MODE == "mistral":
            return await self.generate_with_mistral(prompt)
        elif self.config.AI_MODE == "local":
            return await self.generate_with_local_llm(prompt)
        else:
            # Fallback : génération basique sans IA
            return self.generate_basic_metadata(prompt)
    
    async def generate_with_huggingface(self, prompt: str) -> Optional[Dict]:
        """Utilise Hugging Face (100% gratuit)."""
        headers = {"Authorization": f"Bearer {self.config.HF_API_KEY}"}
        
        payload = {
            "inputs": prompt + "\n\nRéponds uniquement avec un JSON valide.",
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.config.HF_API_URL,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        text = result[0]['generated_text']
                        
                        # Extraire le JSON
                        json_start = text.find('{')
                        json_end = text.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = text[json_start:json_end]
                            return json.loads(json_str)
                    else:
                        print(f"Erreur HF: {response.status}")
            except Exception as e:
                print(f"Erreur HF: {e}")
        
        return None
    
    async def generate_with_mistral(self, prompt: str) -> Optional[Dict]:
        """Utilise Mistral AI."""
        headers = {
            "Authorization": f"Bearer {self.config.MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistral-tiny",  # Modèle gratuit
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.config.MISTRAL_API_URL,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # Parser le JSON
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        if json_start >= 0:
                            return json.loads(content[json_start:json_end])
            except Exception as e:
                print(f"Erreur Mistral: {e}")
        
        return None
    
    async def generate_with_local_llm(self, prompt: str) -> Optional[Dict]:
        """Utilise un LLM local (Ollama, LlamaCpp, etc.)."""
        payload = {
            "model": "mistral",
            "prompt": prompt + "\n\nRéponds uniquement avec un JSON valide.",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 200
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.config.LOCAL_LLM_URL,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        text = result.get('response', '')
                        
                        # Extraire le JSON
                        json_start = text.find('{')
                        json_end = text.rfind('}') + 1
                        if json_start >= 0:
                            return json.loads(text[json_start:json_end])
            except Exception as e:
                print(f"Erreur LLM local: {e}")
        
        return None
    
    def generate_basic_metadata(self, context: str) -> Dict:
        """Génération basique sans IA (fallback)."""
        # Extraire les mots-clés du contexte
        words = context.split()[:20]
        title_words = ' '.join(words[:5])
        
        return {
            "alt_text": f"Image liée à {title_words}",
            "title": title_words[:60],
            "caption": f"Illustration pour {title_words}",
            "description": f"Cette image illustre le contenu relatif à {title_words}"
        }
    
    async def process_wordpress_site(self, client_id: str, wp_data: Dict):
        """Traite un site WordPress complet."""
        wp_url = wp_data['url']
        wp_user = wp_data['user']
        wp_password = wp_data['password']
        
        print(f"🤖 Traitement du site {wp_url} pour le client {client_id}")
        
        # Récupérer les images via l'API WordPress
        images = await self.fetch_wordpress_images(wp_url, wp_user, wp_password)
        
        processed = 0
        errors = 0
        
        for image in images:
            if not image.get('alt_text'):
                # Récupérer le contexte
                context = await self.get_image_context(wp_url, wp_user, wp_password, image)
                
                # Générer avec l'IA
                prompt = self.create_prompt(context)
                metadata = await self.generate_with_ai(prompt)
                
                if metadata:
                    # Mettre à jour WordPress
                    success = await self.update_wordpress_image(
                        wp_url, wp_user, wp_password, 
                        image['id'], metadata
                    )
                    
                    if success:
                        processed += 1
                    else:
                        errors += 1
                else:
                    errors += 1
                
                # Pause pour éviter la surcharge
                await asyncio.sleep(1)
        
        # Mettre à jour les stats
        self.update_client_stats(client_id, processed, errors)
        
        return {
            "processed": processed,
            "errors": errors,
            "total": len(images)
        }
    
    async def fetch_wordpress_images(self, wp_url: str, user: str, password: str) -> List[Dict]:
        """Récupère toutes les images d'un site WordPress."""
        images = []
        page = 1
        
        auth = aiohttp.BasicAuth(user, password)
        
        async with aiohttp.ClientSession(auth=auth) as session:
            while True:
                try:
                    async with session.get(
                        f"{wp_url}/wp-json/wp/v2/media",
                        params={'per_page': 100, 'page': page}
                    ) as response:
                        if response.status == 200:
                            batch = await response.json()
                            if not batch:
                                break
                            images.extend(batch)
                            page += 1
                        else:
                            break
                except:
                    break
        
        return images
    
    async def get_image_context(self, wp_url: str, user: str, password: str, image: Dict) -> Dict:
        """Récupère le contexte d'une image."""
        context = {
            'image_url': image.get('source_url', ''),
            'image_title': image.get('title', {}).get('rendered', ''),
            'page_title': '',
            'page_content': ''
        }
        
        post_id = image.get('post')
        if not post_id:
            return context
        
        auth = aiohttp.BasicAuth(user, password)
        
        async with aiohttp.ClientSession(auth=auth) as session:
            # Essayer posts puis pages
            for endpoint in ['posts', 'pages']:
                try:
                    async with session.get(
                        f"{wp_url}/wp-json/wp/v2/{endpoint}/{post_id}"
                    ) as response:
                        if response.status == 200:
                            post = await response.json()
                            context['page_title'] = post.get('title', {}).get('rendered', '')
                            content = post.get('content', {}).get('rendered', '')
                            # Nettoyer le HTML
                            context['page_content'] = self.strip_html(content)[:300]
                            break
                except:
                    continue
        
        return context
    
    def strip_html(self, html: str) -> str:
        """Supprime les balises HTML."""
        import re
        return re.sub('<.*?>', '', html)
    
    def create_prompt(self, context: Dict) -> str:
        """Crée le prompt pour l'IA."""
        return f"""Génère des métadonnées SEO pour cette image WordPress.

Contexte:
- Titre de la page: {context['page_title']}
- Contenu: {context['page_content']}
- URL de l'image: {context['image_url']}

Génère en français un JSON avec:
- alt_text: description précise (max 125 car)
- title: titre SEO (max 60 car)
- caption: légende engageante (max 160 car)
- description: description détaillée (max 300 car)

Format JSON uniquement:
{{
    "alt_text": "...",
    "title": "...",
    "caption": "...",
    "description": "..."
}}"""
    
    async def update_wordpress_image(self, wp_url: str, user: str, password: str, 
                                   image_id: int, metadata: Dict) -> bool:
        """Met à jour une image dans WordPress."""
        auth = aiohttp.BasicAuth(user, password)
        
        async with aiohttp.ClientSession(auth=auth) as session:
            try:
                async with session.post(
                    f"{wp_url}/wp-json/wp/v2/media/{image_id}",
                    json=metadata
                ) as response:
                    return response.status == 200
            except:
                return False
    
    def update_client_stats(self, client_id: str, processed: int, errors: int):
        """Met à jour les statistiques client."""
        if client_id not in self.clients['clients']:
            self.clients['clients'][client_id] = {
                'stats': {'total_processed': 0, 'total_errors': 0}
            }
        
        self.clients['clients'][client_id]['stats']['total_processed'] += processed
        self.clients['clients'][client_id]['stats']['total_errors'] += errors
        self.clients['stats']['total_processed'] += processed
        
        self.save_clients()

# Instance globale de l'agent
agent = WordPressAIAgent()

# Routes Flask
@app.route('/')
def home():
    """Page d'accueil avec interface."""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>WordPress AI Image Optimizer</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
        input, button { padding: 10px; margin: 5px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .processing { background: #cce5ff; color: #004085; }
        h1 { color: #333; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .stat-box { background: white; padding: 15px; border-radius: 5px; text-align: center; }
    </style>
</head>
<body>
    <h1>🤖 WordPress AI Image Optimizer Agent</h1>
    
    <div class="container">
        <h2>➕ Ajouter un site WordPress</h2>
        <form id="addSite">
            <input type="text" id="clientId" placeholder="ID Client" required><br>
            <input type="url" id="wpUrl" placeholder="https://site-wordpress.com" required><br>
            <input type="text" id="wpUser" placeholder="Utilisateur WordPress" required><br>
            <input type="password" id="wpPassword" placeholder="Mot de passe application" required><br>
            <button type="submit">Ajouter et traiter</button>
        </form>
        <div id="status"></div>
    </div>
    
    <div class="container">
        <h2>📊 Statistiques globales</h2>
        <div class="stats">
            <div class="stat-box">
                <h3>Total traité</h3>
                <p id="totalProcessed">0</p>
            </div>
            <div class="stat-box">
                <h3>Clients actifs</h3>
                <p id="activeClients">0</p>
            </div>
            <div class="stat-box">
                <h3>En cours</h3>
                <p id="processing">0</p>
            </div>
        </div>
    </div>
    
    <div class="container">
        <h2>👥 Clients</h2>
        <div id="clientsList"></div>
    </div>
    
    <script>
        async function addSite(e) {
            e.preventDefault();
            const status = document.getElementById('status');
            status.className = 'status processing';
            status.textContent = 'Traitement en cours...';
            
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
                document.getElementById('activeClients').textContent = stats.active_clients;
                document.getElementById('processing').textContent = stats.processing;
                
                // Afficher les clients
                const clientsList = document.getElementById('clientsList');
                clientsList.innerHTML = '';
                
                for (const [clientId, data] of Object.entries(stats.clients)) {
                    const div = document.createElement('div');
                    div.className = 'stat-box';
                    div.innerHTML = `
                        <h4>${clientId}</h4>
                        <p>Images traitées: ${data.stats.total_processed}</p>
                        <p>Erreurs: ${data.stats.total_errors}</p>
                    `;
                    clientsList.appendChild(div);
                }
            } catch (error) {
                console.error('Erreur stats:', error);
            }
        }
        
        document.getElementById('addSite').addEventListener('submit', addSite);
        
        // Charger les stats au démarrage
        loadStats();
        
        // Actualiser toutes les 10 secondes
        setInterval(loadStats, 10000);
    </script>
</body>
</html>
    ''')

@app.route('/api/process', methods=['POST'])
async def process_site():
    """Endpoint pour traiter un site WordPress."""
    data = request.json
    
    client_id = data.get('client_id')
    wp_data = {
        'url': data.get('wp_url'),
        'user': data.get('wp_user'),
        'password': data.get('wp_password')
    }
    
    # Valider les données
    if not all([client_id, wp_data['url'], wp_data['user'], wp_data['password']]):
        return jsonify({'error': 'Données manquantes'}), 400
    
    # Ajouter le client
    if client_id not in agent.clients['clients']:
        agent.clients['clients'][client_id] = {
            'sites': [],
            'stats': {'total_processed': 0, 'total_errors': 0}
        }
    
    agent.clients['clients'][client_id]['sites'].append(wp_data)
    agent.save_clients()
    
    # Lancer le traitement en arrière-plan
    asyncio.create_task(agent.process_wordpress_site(client_id, wp_data))
    
    return jsonify({
        'status': 'processing',
        'message': 'Traitement lancé en arrière-plan'
    })

@app.route('/api/stats')
def get_stats():
    """Récupère les statistiques."""
    return jsonify({
        'total_processed': agent.clients['stats']['total_processed'],
        'active_clients': len(agent.clients['clients']),
        'processing': len(agent.processing_queue),
        'clients': agent.clients['clients']
    })

@app.route('/api/webhook/<client_id>', methods=['POST'])
async def webhook(client_id):
    """Webhook pour traitement automatique."""
    # Traiter tous les sites du client
    if client_id in agent.clients['clients']:
        for site in agent.clients['clients'][client_id].get('sites', []):
            await agent.process_wordpress_site(client_id, site)
        
        return jsonify({'status': 'success'})
    
    return jsonify({'error': 'Client non trouvé'}), 404

# Tâche planifiée pour traitement automatique
def scheduled_processing():
    """Traite tous les sites toutes les 24h."""
    while True:
        time.sleep(86400)  # 24 heures
        
        print("🔄 Traitement planifié lancé...")
        for client_id, client_data in agent.clients['clients'].items():
            for site in client_data.get('sites', []):
                asyncio.run(agent.process_wordpress_site(client_id, site))

# Lancer le thread de planification
if __name__ == '__main__':
    # Créer le thread pour les tâches planifiées
    scheduler_thread = threading.Thread(target=scheduled_processing, daemon=True)
    scheduler_thread.start()
    
    # Lancer le serveur Flask
    app.run(host='0.0.0.0', port=agent.config.PORT)
