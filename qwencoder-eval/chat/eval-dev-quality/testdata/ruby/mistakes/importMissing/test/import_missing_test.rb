require_relative 'test_init'
require_relative '../lib/import_missing'

class TestImportMissing < Minitest::Test
    def test_parse_csv_string_with_valid_input
        csv_string = <<~CSV
            name,age,city
            John,30,New York
            Jane,25,Los Angeles
        CSV
        result = parse_csv_string(csv_string)

        assert_equal ["name", "age", "city"], result.headers

        assert_equal ["John", "30", "New York"], result[0].fields
        assert_equal ["Jane", "25", "Los Angeles"], result[1].fields
    end

    def test_parse_csv_string_with_empty_input
        csv_string = ""
        result = parse_csv_string(csv_string)

        # Check if result is empty
        assert_equal 0, result.size
    end

    def test_parse_csv_string_with_invalid_input
        csv_string = nil
        assert_raises(ArgumentError) { parse_csv_string(csv_string) }
    end
end
