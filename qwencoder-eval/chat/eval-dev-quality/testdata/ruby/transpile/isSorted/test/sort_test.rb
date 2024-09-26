require_relative 'test_init'
require_relative '../lib/sort'

class TestSort < Minitest::Test
    def test_is_sorted1
        a = []
        actual = is_sorted(a)
        assert_equal(false, actual)
    end

    def test_is_sorted2
        a = [5, 4, 3, 2, 1]
        actual = is_sorted(a)
        assert_equal(false, actual)
    end

    def test_is_sorted3
        a = [0]
        actual = is_sorted(a)
        assert_equal(true, actual)
    end

    def test_is_sorted4
        a = [1, 2, 3, 4, 5]
        actual = is_sorted(a)
        assert_equal(true, actual)
    end

    def test_is_sorted5
        a = [1, 2, 10, 11, 20, 21]
        actual = is_sorted(a)
        assert_equal(true, actual)
    end
end
