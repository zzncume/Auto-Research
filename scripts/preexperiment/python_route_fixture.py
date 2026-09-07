"""Fixed-response local transport fixture, never a research workflow."""
import asyncio,json,os,sys,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

class Mock(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        p=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.models.append(p.get('model'))
        if p.get('model')!='qwen3.8-max':self.send_error(400);return
        body=json.dumps({'id':'fixture','object':'chat.completion','created':0,'model':'qwen3.8-max',
            'choices':[{'index':0,'message':{'role':'assistant','content':'fixture-ok'},'finish_reason':'stop'}],
            'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

s=ThreadingHTTPServer(('127.0.0.1',0),Mock);s.models=[]
t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
base=f'http://127.0.0.1:{s.server_port}/v1'
os.environ.update(AI_SCIENTIST_API_KEY='offline-synthetic',AI_SCIENTIST_BASE_URL=base,
                  AI_SCIENTIST_MODEL='qwen3.8-max',AI_SCIENTIST_OPENAI_COMPATIBLE='1',
                  TIKTOKEN_CACHE_DIR='/source/tokenizer-cache')
try:
    if sys.argv[1]=='arbor':
        from arbor.core.llm.litellm_provider import LiteLLMProvider
        p=LiteLLMProvider(model='qwen3.8-max',api_key='offline-synthetic',base_url=base,max_retries=0,reasoning_effort='none')
        result=asyncio.run(p._acompletion(model=p.model,messages=[{'role':'user','content':'offline fixture'}]))
        assert result.choices[0].message.content=='fixture-ok'
    else:
        sys.path.insert(0,'/source/engine')
        from ai_scientist.llm import create_client,get_response_from_llm
        client,model=create_client('qwen3.8-max')
        text,_=get_response_from_llm('offline fixture',client,model,'Synthetic transport fixture only.')
        assert text=='fixture-ok'
    assert s.models==['qwen3.8-max'],s.models
    print(json.dumps({'result':'pass','fixture_requests':len(s.models),'model':s.models[0],
                      'real_model_calls':0,'research_workflow_started':False}))
finally:s.shutdown();s.server_close();t.join(timeout=5)
