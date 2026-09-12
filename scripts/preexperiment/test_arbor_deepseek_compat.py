import copy
import unittest
from arbor_deepseek_compat import ACK, outbound_messages

class CompactionTests(unittest.TestCase):
    def test_preserves_history_reasoning_and_tool_pairs(self):
        messages = [
            {'role':'user', '_internal':'context_summary', 'content':'summary'},
            {'role':'assistant', 'content':ACK},
            {'role':'assistant', 'content':[{'type':'thinking','thinking':'test-only'},
                {'type':'tool_use','id':'t','name':'check','input':{}}]},
            {'role':'user', 'content':[{'type':'tool_result','tool_use_id':'t','content':'OK'}]}]
        before = copy.deepcopy(messages)
        result = outbound_messages(messages)
        self.assertEqual(result, [messages[0], *messages[2:]])
        self.assertEqual(messages, before)
        self.assertIs(result[1], messages[2])

    def test_does_not_remove_real_or_unmarked_messages(self):
        messages = [{'role':'user','content':'ordinary'}, {'role':'assistant','content':ACK},
                    {'role':'user','_internal':'context_summary','content':'summary'},
                    {'role':'assistant','content':'Actual answer'}]
        self.assertEqual(outbound_messages(messages), messages)

if __name__ == '__main__': unittest.main()
