require_relative 'test_init'
require_relative '../lib/variable_unknown'

class TestVariableUnknown < Minitest::Test
    def test_variable_unknown1
        x = -1
        expected = 1
        actual = variable_unknown(x)
        assert_equal expected, actual
    end

    def test_variable_unknown2
        x = 0
        expected = 0
        actual = variable_unknown(x)
        assert_equal expected, actual
    end

    def test_variable_unknown3
        x = 1
        expected = 1
        actual = variable_unknown(x)
        assert_equal expected, actual
    end
end
