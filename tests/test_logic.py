import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from logic import parse_amount


class TestParseAmount:
    def test_parse_valid_number(self):
        assert parse_amount("10.5") == 10.5
        assert parse_amount("0.99") == 0.99
        assert parse_amount("32") == 32

    def test_parse_comma_separator(self):
        assert parse_amount("10,5") == 10.5
        assert parse_amount("4,56") == 4.56

    def test_parse_invalid_input(self):
        assert parse_amount("dsklgnsldkg") is None
        assert parse_amount("12@$") is None
        assert parse_amount("11.24.2") is None
        assert parse_amount("54,24,1") is None
        assert parse_amount("") is None

    def test_parse_negative_numbers(self):
        assert parse_amount("-0.2") is None

    def test_parse_large_numbers(self):
        assert parse_amount("99999999999") == 99999999999.0
