require_relative 'test_init'
require_relative '../lib/cascading_if_else'

class TestCascadingIfElse < Minitest::Test
    def test_cascading_if_else1
        i = 0
        expected = 5
        actual = cascading_if_else(i)
        assert_equal(expected, actual)
    end

    def test_cascading_if_else2
        i = 1
        expected = 2
        actual = cascading_if_else(i)
        assert_equal(expected, actual)
    end

    def test_cascading_if_else3
        i = 3
        expected = 4
        actual = cascading_if_else(i)
        assert_equal(expected, actual)
    end
end
