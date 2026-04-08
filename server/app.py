try:
    from openenv.core.env_server import create_app
    from ..models import InvestigatorAction, InvestigatorObservation
    from .content_integrity_environment import ContentIntegrityEnvironment
except ImportError:
    from openenv.core.env_server import create_app
    from models import InvestigatorAction, InvestigatorObservation
    from server.content_integrity_environment import ContentIntegrityEnvironment

app = create_app(
    ContentIntegrityEnvironment,
    InvestigatorAction,
    InvestigatorObservation,
    env_name="content-integrity-investigator",
)

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()