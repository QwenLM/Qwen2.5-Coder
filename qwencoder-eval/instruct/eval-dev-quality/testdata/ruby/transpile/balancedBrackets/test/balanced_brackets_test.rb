require_relative 'test_init'
require_relative '../lib/balanced_brackets'

class TestBalancedBrackets < Minitest::Test
    def test_has_balanced_brackets1
        str = ""
        actual = has_balanced_brackets(str)
        assert_equal true, actual
    end

    def test_has_balanced_brackets2
        str = "["
        actual = has_balanced_brackets(str)
        assert_equal false, actual
    end

    def test_has_balanced_brackets3
        str = "[[[]]"
        actual = has_balanced_brackets(str)
        assert_equal false, actual
    end

    def test_has_balanced_brackets4
        str = "[[]]"
        actual = has_balanced_brackets(str)
        assert_equal true, actual
    end

    def test_has_balanced_brackets5
        str = "[[[[]]]]"
        actual = has_balanced_brackets(str)
        assert_equal true, actual
    end
end
