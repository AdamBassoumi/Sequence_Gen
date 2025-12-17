# 📸 AI Photo Sequence Generator

Generate consistent photo sequences from text prompts using AI. This project uses Groq for prompt generation and Pollinations.ai for image generation.

## ✨ Features

*   AI-Powered Story Generation: Create detailed, multi-scene narratives from simple prompts

*   Easy Deployment: Docker Compose setup with one-command 

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- UV package manager
- Groq API key (get one at https://console.groq.com/keys)

### Production Setup with Docker

1. Configure environment:

```bash
cp .env.example .env
```
### Edit the .env file with your actual API key

2. Deploy with Docker Compose:

bash
docker-compose up --build

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

### Development Setup

#### 1. Clone and Setup

bash
git clone <your-repository-url>
cd sequence_gen_project

# Create and activate virtual environment with UV
uv venv

# Install dependencies
uv sync

# Configure environment
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
# Edit the .env file with your actual API key

#### 2. Running the Application

Start the FastAPI Server:

```bash
uv run -m app.main
```
Or with uvicorn directly:

```bash
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```
The server will start at http://localhost:8000

#### 3. Running the Frontend

In a new terminal:

``` bash
cd frontend
npm install
npm run dev
```

## 🗺️ Future Roadmap

- Enhanced Frontend: Comic/storyboard interface
- Watermarking Script: Automatic image watermarking
- MLOps Pipeline: CI/CD for model updates
- Image Captioning: Generate descriptive captions
- Prompt Builder UI: Interactive prompt crafting

## ⚠️ Important Notes

- API Keys: Never commit .env file or expose API keys
- Ethical Use: Respect copyright and content policies
- Cost Management: Monitor usage of external AI APIs

## 🤝 Contributing

Contributions welcome! Submit a Pull Request.

## 📄 License

MIT License.