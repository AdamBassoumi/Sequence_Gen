# Photo Sequence Generator
Generate consistent photo sequences from text prompts using AI. This project uses Groq for prompt generation and Pollinations.ai for image generation.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10 or higher
- UV package manager (fast Python package installer)
- Groq API key (get one at https://console.groq.com/keys)

### 2. Install UV (if not already installed)
pip install uv
### 3. Clone and Setup

#### Clone the repository
git clone <your-repository-url>
cd sequence_gen_project

##### Create and activate virtual environment with UV
uv venv


### 4. Install Dependencies

uv sync
### 5. Configure Environment

# Create environment file
echo "GROQ_API_KEY=your_groq_api_key_here" > .env

# Edit the .env file with your actual API key

### 🏃‍♂️ Running the Application
Start the FastAPI Server
#### Run the server
uv run -m app.main

#### Or with uvicorn directly:
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
The server will start at http://localhost:8000

### Test with the Client Script
#### In a new terminal (activate venv first)
uv run tests/test_client.py
Follow the prompts to generate a story sequence.


### Future Updates

#### Front End Dev
#### WaterMark Script
#### ML_FLOW 
#### 