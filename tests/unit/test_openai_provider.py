from secondbrain.services.llm.openai_provider import OpenAIChatProvider


def test_parses_ascii_bracket_citations():
    assert OpenAIChatProvider._parse_citations("Fact [1] and [2].", 3) == [1, 2]


def test_parses_fullwidth_bracket_citations():
    assert OpenAIChatProvider._parse_citations("Fact 【1】 and 【3】.", 3) == [1, 3]


def test_ignores_out_of_range_and_duplicates():
    assert OpenAIChatProvider._parse_citations("[1] [1] [7]", 3) == [1]


def test_no_citations_returns_empty():
    assert OpenAIChatProvider._parse_citations("No citations here.", 3) == []
