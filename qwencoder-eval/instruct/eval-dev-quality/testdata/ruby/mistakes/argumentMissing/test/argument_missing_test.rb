require_relative 'test_init'
require_relative '../lib/argument_missing'

class TestArgumentMissing < Minitest::Test
    def test_argument_missing1
        x = -1
        expected = -1
        actual = argument_missing(x)
        assert_equal expected, actual
    end

    def test_argument_missing2
        x = 0
        expected = 0
        actual = argument_missing(x)
        assert_equal expected, actual
    end

    def test_argument_missing3
        x = 1
        expected = 1
        actual = argument_missing(x)
        assert_equal expected, actual
    end
end
