require_relative 'test_init'
require_relative '../lib/pascals_triangle'

class TestPascalsTriangle < Minitest::Test
    def test_pascals_triangle1
        rows = -1
        assert_raises(ArgumentError) do
            pascals_triangle(rows)
        end
    end

    def test_pascals_triangle2
        rows = 0
        expected = []
        actual = pascals_triangle(rows)
        assert_equal(expected, actual)
    end

    def test_pascals_triangle3
        rows = 1
        expected = [[1]]
        actual = pascals_triangle(rows)
        assert_equal(expected, actual)
    end

    def test_pascals_triangle4
        rows = 5
        expected = [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]
        actual = pascals_triangle(rows)
        assert_equal(expected, actual)
    end
end
