"""Lossless native inputs and per-run model routing. No process execution."""
import hashlib
from urllib.parse import urlsplit
from prepare_inputs import BRIEF_SHA

MODEL='qwen3.8-max'

def validate_brief(text):
    if hashlib.sha256(text.encode()).hexdigest()!=BRIEF_SHA:
        raise ValueError('frozen brief mismatch')

def endpoint(value):
    u=urlsplit(value)
    if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost') or not u.port:
        raise ValueError('dedicated loopback audit endpoint required')
    if u.username or u.password or u.query or u.fragment or u.path!='/v1':
        raise ValueError('invalid audit endpoint')
    return value

def model_environment(system, base_url, local_token, model=MODEL):
    # Caller supplies an ephemeral per-run token; never load credentials here.
    base_url=endpoint(base_url)
    if not local_token:raise ValueError('ephemeral token required')
    env={'OPENAI_API_BASE':base_url,'OPENAI_BASE_URL':base_url,'OPENAI_API_KEY':local_token,
         'RESEARCH_LATEX_TEMPLATE':'/materials/native-latex'}
    if system in ('ai-scientist-v1','ai-scientist-v2'):
        env.update(AI_SCIENTIST_OPENAI_COMPATIBLE='1',AI_SCIENTIST_MODEL=MODEL,
                   AI_SCIENTIST_BASE_URL=base_url,AI_SCIENTIST_API_KEY=local_token)
    elif system=='aris-code':
        env.update(EXECUTOR_PROVIDER='openai',EXECUTOR_BASE_URL=base_url,
                   EXECUTOR_API_KEY=local_token,ARIS_REVIEWER_PROVIDER='custom',
                   ARIS_REVIEWER_MODEL=model,ARIS_REVIEWER_BASE_URL=base_url,
                   ARIS_REVIEWER_AUTH_TOKEN=local_token,ARIS_DISABLE_KEYCHAIN='1')
    elif system!='arbor':raise ValueError('unknown system')
    return env

def arbor_config(brief,base_url,local_token):
    validate_brief(brief)
    # CoordinatorConfig.meta_model is TOP LEVEL, not llm.meta_model.
    return {'task':brief,'meta_model':MODEL,
            'llm':{'provider':'litellm','model':MODEL,'base_url':endpoint(base_url),'api_key':local_token}}

def aris_argv(brief,options,model=MODEL):
    validate_brief(brief)
    return _aris_argv(brief,options,model)

def aris_diagnostic_argv(task,expected_sha256,options):
    if hashlib.sha256(task.encode()).hexdigest()!=expected_sha256:
        raise ValueError('approved diagnostic task mismatch')
    return _aris_argv(task,options)

def _aris_argv(brief,options,model=MODEL):
    allowed={'AUTO_WRITE':bool,'CODE_REVIEW':bool,'BASE_REPO':bool,'VENUE':str}
    if set(options)!=set(allowed):raise ValueError('exact option set required')
    if any(type(options[k]) is not t for k,t in allowed.items()):raise ValueError('invalid option type')
    if options['BASE_REPO'] is not False or options['VENUE']!='CVPR':
        raise ValueError('unreviewed input mapping')
    suffix=', '.join(f'{k}: {str(v).lower() if type(v) is bool else v}' for k,v in options.items())
    # One argv element, no shell interpolation; full brief remains a substring.
    # Native defaults: tool execution is permitted inside the outer sandbox;
    # text rendering flushes progress before the complete turn returns.
    return ['/tools/aris','--model',model,'--permission-mode','danger-full-access',
            '--output-format','text','prompt','/research-pipeline '+brief+'\n— '+suffix]
