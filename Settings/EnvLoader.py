"""Variable provider that reads a repo-root .env file and exposes test configuration.

Variable priority: CLI (-v flag) > *** Variables *** sections > this file.
.env values therefore act as project-level defaults that CLI flags can override,
which keeps CI working without a .env file present.
"""

import os
from pathlib import Path


# Maps legacy Selenium browser names to Playwright browser names
_BROWSER_MAP = {
    'chrome': 'chromium',
    'edge': 'msedge',
    'firefox': 'firefox',
    'webkit': 'webkit',
    'chromium': 'chromium',
    'msedge': 'msedge',
}


def get_variables():
    _load_dotenv(Path(__file__).parent.parent / '.env')
    browser_raw = os.getenv('BROWSER', 'chromium').lower()
    return {
        'target_app': os.getenv('TARGET_APP', 'SwagLabs'),
        'environment': os.getenv('ENVIRONMENT', 'Staging'),
        'browser': _BROWSER_MAP.get(browser_raw, browser_raw),
        'headless': os.getenv('HEADLESS', 'False').lower() == 'true',
    }


def _load_dotenv(path):
    if not path.exists():
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            # os.environ.setdefault preserves any value already set by the environment,
            # which lets CI env vars take precedence over the .env file
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
