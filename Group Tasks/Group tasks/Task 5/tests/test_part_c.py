from unittest.mock import patch
from answer_agent.formatter import format_sources, format_citations
from answer_agent.agent import answer_question
from orchestrator import run_workflow
from memory_cache import cache_key, invalidate_cache, remember, get_history, clear_session

def test_sources_deduplicate():
    evidence = [{"document":"a.pdf","page":2,"content":"one"}, {"document":"a.pdf","page":2,"content":"two"}, {"document":"b.pdf","page":4,"content":"three"}]
    assert len(format_sources(evidence)) == 2
    assert '[a.pdf, p. 2]' in format_citations(evidence)

def test_answer_grounded_prompt():
    analysis = {"analysis":"Result is 92%", "evidence":[{"document":"paper.pdf","page":3,"content":"Accuracy 92%"}], "enough_evidence":True}
    with patch('answer_agent.agent.llm.ask_llm', return_value='Accuracy is 92% [paper.pdf, p. 3]') as mock:
        result = answer_question('Accuracy?', analysis)
    assert result['sources'][0]['page'] == 3
    assert result['enough_evidence'] is True
    assert 'paper.pdf' in mock.call_args.args[1]

def test_orchestrator_order():
    calls=[]
    def retriever(*args, **kwargs):
        calls.append('retrieve'); return [{'document':'a.pdf','page':1,'content':'x'}]
    def analyst(*args, **kwargs):
        calls.append('analyze'); return {'analysis':'x', 'evidence':args[1], 'rounds':1}
    def answer(*args, **kwargs):
        calls.append('answer'); return {'answer':'x','sources':[]}
    with patch('orchestrator.retrieve',side_effect=retriever), patch('orchestrator.analyze',side_effect=analyst), patch('orchestrator.answer_question',side_effect=answer):
        assert run_workflow('question')['rounds'] == 1
    assert calls == ['retrieve','analyze','answer']

def test_memory_and_cache_revision():
    clear_session('test')
    remember('test','hello','world')
    assert len(get_history('test')) == 2
    old=cache_key('hello', [])
    invalidate_cache()
    assert old != cache_key('hello', [])
    clear_session('test')
