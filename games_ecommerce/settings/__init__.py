from .base import *
from dotenv import load_dotenv


ENVIRONMENT = os.environ.get('ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    from .prod import *
    env_file = '.env.prod'
else:
    from .local import *
    env_file = '.env'

dotenv_path = os.path.join(BASE_DIR, os.pardir, env_file)
load_dotenv(dotenv_path)
