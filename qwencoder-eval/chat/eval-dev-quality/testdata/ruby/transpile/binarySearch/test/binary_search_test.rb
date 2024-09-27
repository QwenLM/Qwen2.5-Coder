require_relative 'test_init'
require_relative '../lib/binary_search'

class TestBinarySearch < Minitest::Test
  def test_binary_search1
      a = []
      x = 0
      expected = -1
      actual = binary_search(a, x)
      assert_equal(expected, actual)
  end

  def test_binary_search2
      a = [0]
      x = 5
      expected = -1
      actual = binary_search(a, x)
      assert_equal(expected, actual)
  end

  def test_binary_search3
      a = [1, 2, 3, 4, 5]
      x = 6
      expected = -1
      actual = binary_search(a, x)
      assert_equal(expected, actual)
  end

  def test_binary_search4
      a = [1, 2, 3, 4, 5]
      x = 3
      expected = 2
      actual = binary_search(a, x)
      assert_equal(expected, actual)
  end

  def test_binary_search5
      a = [1, 5, 10, 15, 20, 25]
      x = 25
      expected = 5
      actual = binary_search(a, x)
      assert_equal(expected, actual)
  end
end
