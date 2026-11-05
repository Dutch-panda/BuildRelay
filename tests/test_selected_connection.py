"""Explicit connection selection must win over stale credentials and tier defaults."""
import asyncio
import io
import json
import os
from unittest.mock import Mock

import pytest

from tools.model_catalog import discover_models
from tools.model_tiers import resolve_pipeline_models
from tools.chatgpt_auth import get_model
from tools.onboarding import run_onboarding_wizard, check_credentials_configured


@pytest.fixture(autouse=True)
def connection_env(monkeypatch):
    before = dict(os.environ)
    for name in ('BUILDRELAY_PROVIDER', 'BUILDRELAY_MODEL', 'BUILDRELAY_MODEL_MODE', 'USE_CHATGPT_OAUTH',
                 'MODEL_NATASHA', 'MODEL_ODIN', 'MODEL_TAGHI', 'MODEL_DIBA', 'MODEL_METI'):
        monkeypatch.delenv(name, raising=False)
    yield
    os.environ.clear()
    os.environ.update(before)


def test_selected_model_survives_tiers_and_stale_keys(monkeypatch):
    monkeypatch.setenv('BUILDRELAY_PROVIDER', 'anthropic')
    monkeypatch.setenv('BUILDRELAY_MODEL_MODE', 'selected')
    monkeypatch.setenv('BUILDRELAY_MODEL', 'anthropic:chosen-model')
    monkeypatch.setenv('DEFAULT_TIER', 'powerful')
    monkeypatch.setenv('OPENAI_API_KEY', 'stale-key')
    lineup = resolve_pipeline_models(overrides={'taghi': 'anthropic:architect-model'})
    assert lineup['taghi'] == 'anthropic:architect-model'
    assert {v for k, v in lineup.items() if k != 'taghi'} == {'anthropic:chosen-model'}


def test_explicit_api_choice_ignores_old_browser_flag(monkeypatch):
    monkeypatch.setenv('BUILDRELAY_PROVIDER', 'openai')
    monkeypatch.setenv('BUILDRELAY_MODEL', 'openai:chosen-model')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://old-gateway.invalid/v1')
    monkeypatch.setenv('USE_CHATGPT_OAUTH', '1')
    model = asyncio.run(get_model())
    assert model.model_name == 'chosen-model'
    assert str(model.client.base_url) == 'https://api.openai.com/v1/'


def test_missing_selected_key_does_not_use_other_provider(monkeypatch):
    monkeypatch.setenv('BUILDRELAY_PROVIDER', 'anthropic')
    monkeypatch.setenv('BUILDRELAY_MODEL', 'anthropic:chosen-model')
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'stale')
    assert not check_credentials_configured()
    with pytest.raises(ValueError, match='credentials are missing'):
        asyncio.run(get_model())


def test_cross_provider_model_rejected(monkeypatch):
    monkeypatch.setenv('BUILDRELAY_PROVIDER', 'openai')
    with pytest.raises(ValueError, match='differs'):
        asyncio.run(get_model('anthropic:other-model'))


def test_browser_choice_does_not_use_api_key(monkeypatch, tmp_path):
    monkeypatch.setenv('BUILDRELAY_PROVIDER', 'chatgpt_oauth')
    monkeypatch.setenv('BUILDRELAY_MODEL', 'openai:chosen-model')
    monkeypatch.setenv('OPENAI_API_KEY', 'stale')
    monkeypatch.setenv('CHATGPT_AUTH_FILE', str(tmp_path / 'absent.json'))
    flow = Mock(side_effect=RuntimeError('browser path reached'))
    monkeypatch.setattr('tools.chatgpt_auth.OpenAIChatGPTOAuthFlow', flow)
    with pytest.raises(RuntimeError, match='browser path reached'):
        asyncio.run(get_model())


def test_discovery_uses_selected_key_and_returns_live_catalog(monkeypatch):
    response = Mock()
    response.__enter__ = lambda self: io.StringIO(json.dumps({'data': [{'id': 'account-specific-model'}]}))
    response.__exit__ = lambda *a: None
    request = Mock(return_value=response)
    monkeypatch.setattr('urllib.request.urlopen', request)
    models, _ = discover_models('openai', 'test-key')
    assert models == ['account-specific-model']
    assert request.call_args.args[0].get_header('Authorization') == 'Bearer test-key'


def test_discovery_failure_does_not_leak_secrets(monkeypatch):
    monkeypatch.setattr('urllib.request.urlopen', Mock(side_effect=RuntimeError('secret-key')))
    models, note = discover_models('openai', 'secret-key')
    assert models == []
    assert 'secret-key' not in note
    assert 'unverified' in note


def test_onboarding_selected_catalog_model_reaches_all_leads(monkeypatch, tmp_path):
    monkeypatch.setattr('tools.onboarding.discover_models', lambda *a, **k: (['account-model'], 'Account catalog'))
    monkeypatch.setattr('tools.onboarding.ping_provider_connectivity', lambda *a, **k: (True, 'OK'))
    inputs = iter(['2', 'sk-' + 'x'*30, '1', '', '', '', ''])
    assert run_onboarding_wizard(console=Mock(), env_path=tmp_path / '.env',
                                 prompt_ask=lambda *a, **k: next(inputs), confirm_ask=lambda *a, **k: False)
    assert set(resolve_pipeline_models().values()) == {'openai:account-model'}
    assert all(asyncio.run(get_model(m)).model_name == 'account-model' for m in resolve_pipeline_models().values())


def test_failed_browser_login_cannot_finish_setup(tmp_path):
    inputs = iter(['1'])
    assert not run_onboarding_wizard(console=Mock(), env_path=tmp_path / '.env',
        prompt_ask=lambda *a, **k: next(inputs), login_func=lambda **k: (False, 'cancelled'))
    assert not (tmp_path / '.env').exists()


def test_picker_filters_and_reprompts_invalid_selection():
    from tools.model_catalog import pick_model
    answers = iter(['99', '/beta', '1'])
    result = pick_model(['alpha', 'beta'], 'alpha', 'Natasha',
                        lambda *a, **k: next(answers), lambda *a: None)
    assert result == 'beta'


def test_run_changes_saved_only_when_requested(monkeypatch):
    from tools.ui import prompt_model_approval_gate
    monkeypatch.setattr('tools.model_tiers.get_available_models_for_active_provider',
                        lambda: ('OpenAI', ['openai:first', 'openai:second']))
    save = Mock()
    monkeypatch.setattr('tools.onboarding.save_env_configuration', save)
    models = dict.fromkeys(('natasha', 'odin', 'taghi', 'meti'), 'openai:first')
    answers = iter(['c', '3', '2', '', 'y'])
    action, changed = prompt_model_approval_gate(models, input_func=lambda _: next(answers))
    assert action == 'change'
    assert changed['taghi'] == 'openai:second'
    assert changed['meti'] == 'openai:first'
    assert save.call_args.args[0]['MODEL_TAGHI'] == 'openai:second'


def test_cancelling_model_changes_does_not_save(monkeypatch):
    from tools.ui import prompt_model_approval_gate
    monkeypatch.setattr('tools.model_tiers.get_available_models_for_active_provider',
                        lambda: ('OpenAI', ['openai:first']))
    save = Mock()
    monkeypatch.setattr('tools.onboarding.save_env_configuration', save)
    answers = iter(['c', '1', 'q'])
    action, models = prompt_model_approval_gate({'natasha': 'openai:first'}, input_func=lambda _: next(answers))
    assert (action, models) == ('quit', None)
    save.assert_not_called()


def test_native_model_colons_work_in_local_adapter(monkeypatch):
    from tools.model_catalog import qualify_model
    monkeypatch.setenv('BUILDRELAY_PROVIDER', 'ollama')
    monkeypatch.setenv('BUILDRELAY_MODEL', 'openai:llama3:latest')
    monkeypatch.setenv('OPENAI_API_KEY', 'ollama')
    monkeypatch.setenv('OPENAI_BASE_URL', 'http://localhost:11434/v1')
    assert qualify_model('llama3:latest', 'ollama') == 'openai:llama3:latest'
    assert asyncio.run(get_model('llama3:latest')).model_name == 'llama3:latest'


def test_picker_keeps_suggestions_and_all_saved_lead_choices(monkeypatch):
    from tools.model_tiers import get_available_models_for_active_provider
    monkeypatch.setenv('BUILDRELAY_PROVIDER', 'chatgpt_oauth')
    monkeypatch.setenv('BUILDRELAY_MODEL', 'openai:first')
    monkeypatch.setenv('MODEL_METI', 'openai:custom')
    monkeypatch.setenv('BUILDRELAY_MODEL_CATALOG', '')
    monkeypatch.setenv('BUILDRELAY_MODEL_SUGGESTIONS', 'first,second')
    _, choices = get_available_models_for_active_provider()
    assert choices == ['openai:first', 'openai:custom', 'openai:second']


def test_global_cli_override_wins_over_saved_leads(monkeypatch):
    monkeypatch.setenv('BUILDRELAY_MODEL_MODE', 'selected')
    monkeypatch.setenv('BUILDRELAY_MODEL', 'openai:saved')
    monkeypatch.setenv('MODEL_NATASHA', 'openai:old')
    models = resolve_pipeline_models(global_model='openai:new', overrides={'meti': 'openai:explicit'})
    assert models['natasha'] == 'openai:new'
    assert models['meti'] == 'openai:explicit'


def test_model_ids_cannot_inject_configuration():
    from tools.model_catalog import qualify_model
    with pytest.raises(ValueError, match='Invalid model ID'):
        qualify_model('model\nOPENAI_BASE_URL=unexpected', 'openai')


def test_browser_login_is_not_bypassed_by_testing_environment(monkeypatch, tmp_path):
    from tools.chatgpt_auth import login_with_chatgpt_browser
    monkeypatch.setenv('BUILDRELAY_TESTING', '1')
    monkeypatch.setattr('tools.chatgpt_auth.OpenAIChatGPTOAuthFlow', Mock(side_effect=RuntimeError('sensitive-error')))
    success, message = login_with_chatgpt_browser(auth_path=tmp_path / 'absent.json', open_browser=False)
    assert not success
    assert 'sensitive-error' not in message


def test_first_session_requires_setup_before_running(monkeypatch):
    import main
    monkeypatch.delenv('BUILDRELAY_TESTING', raising=False)
    monkeypatch.setattr('tools.onboarding.check_credentials_configured', lambda: False)
    wizard = Mock(return_value=False)
    session = Mock()
    monkeypatch.setattr('tools.onboarding.run_onboarding_wizard', wizard)
    monkeypatch.setattr('tools.session.run_project_session', session)
    monkeypatch.setattr(main.sys.stdin, 'isatty', lambda: True)
    monkeypatch.setattr(main.sys, 'argv', ['main.py', '--session', 'demo'])
    with pytest.raises(SystemExit) as exc:
        asyncio.run(main.main())
    assert exc.value.code == 1
    wizard.assert_called_once()
    session.assert_not_called()


def test_first_run_continues_original_prompt_after_real_wizard(monkeypatch, tmp_path):
    import main
    from contracts import ImplementationResult
    monkeypatch.delenv('BUILDRELAY_TESTING', raising=False)
    monkeypatch.setattr(main.sys.stdin, 'isatty', lambda: True)
    original_prompt = 'Research CSV handling and build a validator'
    monkeypatch.setattr(main.sys, 'argv', ['main.py', original_prompt])
    monkeypatch.setattr('tools.onboarding.check_credentials_configured', lambda: False)
    monkeypatch.setattr('tools.onboarding.discover_models', lambda *a, **k: (['account-model'], 'Retrieved'))
    monkeypatch.setattr('tools.onboarding.ping_provider_connectivity', lambda *a, **k: (True, 'OK'))
    answers = iter(['2', 'sk-' + 'x'*30, '1', '', '', '', ''])
    wizard = run_onboarding_wizard
    monkeypatch.setattr('tools.onboarding.run_onboarding_wizard', lambda: wizard(
        console=Mock(), env_path=tmp_path / '.env', prompt_ask=lambda *a, **k: next(answers)))
    received = []
    async def run(record, ledger, **kwargs):
        received.append(record.prompt)
        assert set(resolve_pipeline_models().values()) == {'openai:account-model'}
        return ImplementationResult(task_id=record.task_id, status='success', summary='Checked', executed_phases=[])
    monkeypatch.setattr(main, 'run_task', run)
    asyncio.run(main.main())
    assert received == [original_prompt]
