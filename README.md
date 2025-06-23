# 🤖 WordPress AI Image Optimizer Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Deploy](https://img.shields.io/badge/deploy-ready-green.svg)](https://github.com/yourusername/wordpress-ai-agent)

> Agent autonome qui optimise automatiquement les images WordPress avec une IA gratuite. Parfait pour les agences et développeurs qui veulent offrir ce service à leurs clients !

![Demo](https://via.placeholder.com/800x400?text=WordPress+AI+Image+Optimizer+Demo)

## ✨ Fonctionnalités

- 🆓 **100% Gratuit** - Utilise des IA gratuites (HuggingFace, Mistral)
- 🔄 **Totalement Autonome** - Traitement automatique programmé
- 🌐 **Multi-clients** - Gérez des centaines de sites WordPress
- 📊 **Dashboard Intuitif** - Interface web pour tout contrôler
- 🚀 **Déployable Partout** - GitHub, Vercel, Render, Railway...
- 🔌 **API REST Complète** - Intégration facile avec vos outils
- 🪝 **Webhooks** - Automatisation avec n8n, Zapier, Make
- 🎯 **SEO Optimisé** - Métadonnées parfaites pour le référencement

## 🚀 Installation Rapide

### Option 1 : Installation en 1 clic

```bash
curl -fsSL https://raw.githubusercontent.com/yourusername/wordpress-ai-agent/main/install.sh | bash
```

### Option 2 : Déploiement Cloud (Gratuit)

#### Deploy on Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/wordpress-ai-agent)

#### Deploy on Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/yourusername/wordpress-ai-agent)

#### Deploy on Vercel
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/wordpress-ai-agent)

### Option 3 : Installation Manuelle

```bash
# Cloner le repo
git clone https://github.com/yourusername/wordpress-ai-agent
cd wordpress-ai-agent

# Installer
pip install -r requirements.txt

# Configurer
cp .env.example .env
# Éditer .env avec vos clés

# Lancer
python agent.py
```

## 🔧 Configuration

### 1. Choisir votre IA

| IA | Coût | Performance | Configuration |
|---|---|---|---|
| **HuggingFace** | Gratuit | ⭐⭐⭐⭐ | Token gratuit sur [huggingface.co](https://huggingface.co) |
| **Mistral AI** | Freemium | ⭐⭐⭐⭐⭐ | Clé API sur [mistral.ai](https://mistral.ai) |
| **LLM Local** | Gratuit | ⭐⭐⭐ | Installer [Ollama](https://ollama.ai) |

### 2. Configuration WordPress

Dans WordPress, créez un mot de passe d'application :
1. Utilisateurs → Profil
2. Mots de passe d'application
3. Générer un nouveau mot de passe

### 3. Variables d'environnement

```env
# Mode IA (huggingface, mistral, ou local)
AI_MODE=huggingface

# Clés API
HF_API_KEY=hf_xxxxxxxxxxxxx
MISTRAL_API_KEY=sk-xxxxxxxxxxxxx

# Serveur
PORT=5000
```

## 📱 Utilisation

### Interface Web

Accédez à `http://localhost:5000` pour :
- Ajouter des sites WordPress
- Voir les statistiques en temps réel
- Gérer vos clients
- Déclencher des optimisations

![Dashboard](https://via.placeholder.com/600x400?text=Dashboard+Preview)

### API REST

```bash
# Ajouter un site
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "client123",
    "wp_url": "https://site.com",
    "wp_user": "admin",
    "wp_password": "xxxx xxxx xxxx"
  }'

# Statistiques
curl http://localhost:5000/api/stats

# Webhook
curl -X POST http://localhost:5000/api/webhook/client123
```

## 🔄 Automatisation

### n8n Workflow
```json
{
  "nodes": [
    {
      "name": "Schedule",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": { "interval": [{ "field": "hours", "hoursInterval": 24 }] }
      }
    },
    {
      "name": "Optimize WordPress",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://your-agent.com/api/webhook/all",
        "method": "POST"
      }
    }
  ]
}
```

### GitHub Actions
```yaml
name: Daily Optimization
on:
  schedule:
    - cron: '0 2 * * *'
jobs:
  optimize:
    runs-on: ubuntu-latest
    steps:
      - run: curl -X POST ${{ secrets.AGENT_URL }}/api/webhook/all
```

## 💰 Monétisation

Transformez cet agent en service SaaS :

| Plan | Prix | Fonctionnalités |
|---|---|---|
| **Starter** | 9€/mois | 100 images/mois, 1 site |
| **Pro** | 29€/mois | 1000 images/mois, 5 sites |
| **Agence** | 99€/mois | Illimité, API, Support |

## 📊 Performance

- ⚡ **Vitesse** : 5-10 secondes par image
- 📈 **Capacité** : 1000+ images/heure
- 💾 **Mémoire** : < 256MB RAM
- 🔧 **CPU** : Minimal (< 10%)

## 🛡️ Sécurité

- ✅ Mots de passe chiffrés
- ✅ HTTPS obligatoire
- ✅ Rate limiting
- ✅ Validation des entrées
- ✅ Logs d'audit

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📚 Documentation

- [Guide d'installation](docs/installation.md)
- [Configuration avancée](docs/configuration.md)
- [API Reference](docs/api.md)
- [Exemples](docs/examples.md)
- [FAQ](docs/faq.md)

## 🐛 Support

- 💬 [Discord](https://discord.gg/xxxxx)
- 📧 Email : support@yourdomain.com
- 🐛 [Issues](https://github.com/yourusername/wordpress-ai-agent/issues)

## 📈 Roadmap

- [x] Agent de base
- [x] Interface web
- [x] API REST
- [x] Webhooks
- [ ] Plugin WordPress natif
- [ ] Support multilingue
- [ ] Analyse d'images par vision IA
- [ ] Intégration WooCommerce
- [ ] App mobile

## 📝 Licence

Ce projet est sous licence MIT - voir [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- [HuggingFace](https://huggingface.co) pour l'IA gratuite
- [Mistral AI](https://mistral.ai) pour leur modèle performant
- [WordPress](https://wordpress.org) pour l'API REST
- La communauté open source

---

<p align="center">
  Fait avec ❤️ pour la communauté WordPress
  <br>
  <a href="https://github.com/yourusername/wordpress-ai-agent">⭐ Star ce projet si vous l'aimez !</a>
</p>
