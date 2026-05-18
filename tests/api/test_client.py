from rs.api.client import _decode_response_line


def test_decode_response_line_prefers_utf8_when_valid():
    text = '{"name":"\u6253\u51fb"}\n'

    assert _decode_response_line(text.encode("utf-8")) == text


def test_decode_response_line_falls_back_to_locale_for_chinese_windows():
    text = '{"name":"\u6253\u51fb"}\n'

    assert _decode_response_line(text.encode("gbk")) == text
