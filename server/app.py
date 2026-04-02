try:
    from ..models import IncidentAction, IncidentObservation
except ImportError:
    from models import IncidentAction, IncidentObservation

try:
    from ..server.incident_environment import IncidentEnvironment
except ImportError:
    from incident_environment import IncidentEnvironment

from openenv.core.env_server import create_fastapi_app

app = create_fastapi_app(IncidentEnvironment, IncidentAction, IncidentObservation)
