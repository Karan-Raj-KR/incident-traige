from openenv.core.env_client import EnvClient

try:
    from .models import IncidentAction, IncidentObservation, IncidentState
except ImportError:
    from models import IncidentAction, IncidentObservation, IncidentState

class IncidentEnvClient(EnvClient[IncidentAction, IncidentObservation, IncidentState]):
    pass
