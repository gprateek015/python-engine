import os
import sys
from apps.www.core.config import config as www_config

basename = os.path.basename(sys.argv[0])
print(basename)

# if (
#     basename == "run_www.py"
# ):
#     from apps.www.core.config import config as www_config
# else:
#     raise Exception(
#         f"""Unknown basename: {basename} or sys.argv: {sys.argv}
#     This occurs when common/core/config.py is was executed in a non-expected way.
#     Allowed ways:
#     Run run_www.py
#     """
#     )


def get_config():
    return www_config


config = get_config()