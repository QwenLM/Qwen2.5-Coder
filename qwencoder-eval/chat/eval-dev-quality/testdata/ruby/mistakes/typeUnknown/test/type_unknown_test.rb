require_relative 'test_init'
require_relative '../lib/type_unknown'  # Adjust the path according to your project structure

class TestTypeUnknown < Minitest::Test
    def test_type_unknown1
        x = -1
        expected = -1
        actual = type_unknown(x)
        assert_equal(expected, actual)
    end

    def test_type_unknown2
        x = 0
        expected = 0
        actual = type_unknown(x)
        assert_equal(expected, actual)
    end

    def test_type_unknown3
        x = 1
        expected = 1
        actual = type_unknown(x)
        assert_equal(expected, actual)
    end
end
