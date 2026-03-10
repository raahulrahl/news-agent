# |---------------------------------------------------------|
# |                                                         |
# |                 Give Feedback / Get Help                |
# | https://github.com/getbindu/Bindu/issues/new/choose    |
# |                                                         |
# |---------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""news-agent - An Bindu Agent.
"""

from news_agent.__version__ import __version__
from news_agent.main import (
    handler,
    initialize_agent,
    initialize_all,
    main,
)

__all__ = [
    "__version__",
    "handler",
    "initialize_agent",
    "initialize_all",
    "main",
]
