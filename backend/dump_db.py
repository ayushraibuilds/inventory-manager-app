from db import get_all_catalogs
from pprint import pprint
import json

catalogs = get_all_catalogs()
print(json.dumps(catalogs, indent=2))
