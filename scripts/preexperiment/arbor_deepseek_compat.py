"""Opt-in outbound compaction-message compatibility for Arbor + DeepSeek.

Keep native compaction/history unchanged. Omit only its synthetic acknowledgement
from API requests: it has no provider-issued reasoning_content to replay.
"""
ACK = ('Understood. I have the full context from the summary above. '
       'Continuing from where we left off.')


def outbound_messages(messages):
    return [message for i, message in enumerate(messages)
            if not (i > 0 and messages[i-1].get('_internal') == 'context_summary'
                    and messages[i-1].get('role') == 'user'
                    and message == {'role': 'assistant', 'content': ACK})]


def install():
    from arbor.core.llm.openai_compat import OpenAICompatProvider
    original = OpenAICompatProvider._convert_messages
    if getattr(original, '_arbor_deepseek_compaction', False):
        return

    def convert(self, system, messages):
        if self.model in ('deepseek-flash', 'openai/deepseek-flash'):
            messages = outbound_messages(messages)
        return original(self, system, messages)

    convert._arbor_deepseek_compaction = True
    OpenAICompatProvider._convert_messages = convert
