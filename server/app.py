import sys
import os

# Add the root directory to sys.path so 'models' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from openenv.core.env_server import create_app
    from models import InvestigatorAction, InvestigatorObservation
    from server.content_integrity_environment import ContentIntegrityEnvironment
except ImportError:
    # Fallback for different directory structures
    from openenv.core.env_server import create_app
    from ..models import InvestigatorAction, InvestigatorObservation
    from .content_integrity_environment import ContentIntegrityEnvironment
# Create the standard app
app = create_app(
    ContentIntegrityEnvironment,
    InvestigatorAction,
    InvestigatorObservation,
    env_name="content-integrity-investigator",
)

@app.get("/")
async def health_check():
    """Generic health check for Docker/HF Liveness probes."""
    return {"status": "healthy", "env": "content-integrity-investigator"}

@app.get("/reset")
async def reset_health_check():
    """
    Handle the GET /reset pings from the validator.
    This prevents the 405 Method Not Allowed error.
    """
    return {"message": "Environment ready for POST requests"}

# --- INJECTION END ---

def main():
    import uvicorn
    # Make sure we use the string import so reload/workers function correctly
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()