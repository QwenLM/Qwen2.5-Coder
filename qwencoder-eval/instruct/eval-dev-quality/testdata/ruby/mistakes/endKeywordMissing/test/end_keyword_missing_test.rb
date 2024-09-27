require_relative 'test_init'
require_relative '../lib/end_keyword_missing'

class TestEndKeywordMissing < Minitest::Test
    def test_end_keyword_missing1
        x = -1
        expected = -1
        actual = end_keyword_missing(x)
        assert_equal expected, actual
    end

    def test_end_keyword_missing2
        x = 0
        expected = 0
        actual = end_keyword_missing(x)
        assert_equal expected, actual
    end

    def test_end_keyword_missing3
        x = 1
        expected = 1
        actual = end_keyword_missing(x)
        assert_equal expected, actual
    end
end
