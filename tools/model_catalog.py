"""Account-scoped model discovery; catalog presence is not a capability guarantee."""
import json
import re
import urllib.request
from urllib.parse import urlencode


def discover_models(provider: str, api_key: str = '', base_url: str | None = None) -> tuple[list[str], str]:
    if provider == 'chatgpt_oauth':
        return [], 'Browser-login model discovery is unavailable. Suggestions are unverified; enter a model supported by your account.'
    headers = {'Accept': 'application/json'}
    if provider == 'anthropic':
        endpoint = 'https://api.anthropic.com/v1/models'
        headers.update({'x-api-key': api_key, 'anthropic-version': '2023-06-01'})
    elif provider == 'gemini':
        endpoint = 'https://generativelanguage.googleapis.com/v1beta/models'
        headers['x-goog-api-key'] = api_key
    else:
        endpoint = (base_url or 'https://api.openai.com/v1').rstrip('/') + '/models'
        if api_key:
            headers['Authorization'] = 'Bearer ' + api_key
    names = []
    try:
        for _ in range(10):
            request = urllib.request.Request(endpoint, headers=headers)
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.load(response)
            if provider == 'gemini':
                names.extend(item['name'].removeprefix('models/') for item in data.get('models', [])
                             if 'generateContent' in item.get('supportedGenerationMethods', []))
                token = data.get('nextPageToken')
                if not token:
                    break
                endpoint = 'https://generativelanguage.googleapis.com/v1beta/models?' + urlencode({'pageToken': token})
            else:
                names.extend(item['id'] for item in data.get('data', []) if isinstance(item.get('id'), str))
                if provider != 'anthropic' or not data.get('has_more') or not data.get('last_id'):
                    break
                endpoint = 'https://api.anthropic.com/v1/models?' + urlencode({'after_id': data['last_id']})
        return sorted(set(names)), 'Models returned by this connection; tool and structured-output support still depend on the selected model.'
    except Exception:
        # Never expose request URLs, headers, or credentials through exception text.
        return [], 'Model discovery failed. Suggestions are unverified; check authentication, endpoint, and connectivity.'


def pick_model(models, current, label, ask, display):
    """Numbered, filterable picker shared by setup and run-time lead selection."""
    choices = list(dict.fromkeys([current, *models]))
    choices = [value for value in choices if value]
    while True:
        display(f"\n{label} — Enter keeps {current or 'the first model'}. /text filters; m enters a custom ID; q cancels.")
        for number, model in enumerate(choices, 1):
            display(f"  [{number}] {model}")
        answer = ask("Choose model", default="").strip()
        if not answer:
            if current:
                return current
            if choices:
                return choices[0]
        elif answer.lower() == 'q':
            raise KeyboardInterrupt
        elif answer.startswith('/'):
            choices = [value for value in dict.fromkeys([current, *models]) if answer[1:].lower() in value.lower()]
        elif answer.lower() == 'm':
            custom = ask("Custom model ID (availability unverified)", default="").strip()
            if custom:
                return custom
        elif answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1]
        display("Choose a listed number, press Enter, or use /text, m, or q.")


def qualify_model(model: str, provider: str) -> str:
    """Separate adapter prefixes from colons that belong to native model IDs."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@+-]*', model):
        raise ValueError('Invalid model ID; whitespace and configuration delimiters are not allowed.')
    expected = {'anthropic': 'anthropic', 'gemini': 'google'}.get(provider, 'openai')
    prefix, separator, _ = model.partition(':')
    if separator and prefix in ('openai', 'anthropic', 'google', 'gemini', 'ollama', 'local'):
        if prefix != expected:
            raise ValueError('Model provider differs from the selected connection. Run buildrelay config to switch providers.')
        return model
    return expected + ':' + model
