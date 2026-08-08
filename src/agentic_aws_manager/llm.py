import os
from typing import Optional

class LLMInterface:
    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError()

class LlamaCppLLM(LLMInterface):
    def __init__(self, model_path: Optional[str] = None):
        model_path = model_path or os.getenv('LLAMA_MODEL_PATH')
        if not model_path:
            raise RuntimeError('LLAMA_MODEL_PATH not set')
        from llama_cpp import Llama
        self._llm = Llama(model_path=model_path)

    def generate(self, prompt: str, **kwargs) -> str:
        resp = self._llm.create(prompt=prompt, **{k: v for k, v in kwargs.items() if v is not None})
        try:
            return resp['choices'][0]['text']
        except Exception:
            return str(resp)

class TransformersLLM(LLMInterface):
    def __init__(self, model_name: Optional[str] = None):
        try:
            from transformers import pipeline
            self._pipe = pipeline('text-generation', model=model_name or 'gpt2')
        except Exception:
            self._pipe = None

    def generate(self, prompt: str, **kwargs) -> str:
        if self._pipe is None:
            return f'[LLM not configured] would respond to: {prompt}'
        out = self._pipe(prompt, max_length=kwargs.get('max_length', 256), do_sample=kwargs.get('do_sample', True))
        return out[0]['generated_text']

class EchoLLM(LLMInterface):
    def generate(self, prompt: str, **kwargs) -> str:
        return f'[LLM not available locally] prompt: {prompt}'

def load_local_llm(model_path: Optional[str] = None, model_name: Optional[str] = None):
    try:
        mp = model_path or os.getenv('LLAMA_MODEL_PATH')
        if mp:
            return LlamaCppLLM(model_path=mp)
    except Exception:
        pass
    try:
        return TransformersLLM(model_name=model_name)
    except Exception:
        pass
    return EchoLLM()
