from .base import *
from dotenv import load_dotenv


ENVIRONMENT = os.environ.get('ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    from .prod import *
else:
    from .local import *
    dotenv_path = os.path.join(BASE_DIR, os.pardir, '.env')
    load_dotenv(dotenv_path)
