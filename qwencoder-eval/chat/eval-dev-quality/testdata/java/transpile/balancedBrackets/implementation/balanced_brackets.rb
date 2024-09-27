def has_balanced_brackets(char_array)
    brackets = 0
    char_array.each_char do |ch|
        if ch == '['
            brackets += 1
        elsif ch == ']'
            brackets -= 1
        else
            return false # Non-bracket characters.
        end
    end

    if brackets < 0 # Closing bracket before opening bracket.
        return false
    end

    return brackets == 0
end
