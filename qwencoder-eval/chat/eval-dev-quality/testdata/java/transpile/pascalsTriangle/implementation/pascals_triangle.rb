def pascals_triangle(rows)
    if rows < 0
        raise ArgumentError, "Rows can't be negative!"
    end

    triangle = Array.new(rows)

    for i in 0...rows
        triangle[i] = Array.new(i + 1)
        triangle[i][0] = 1
        for j in 1...i
            triangle[i][j] = triangle[i - 1][j - 1] + triangle[i - 1][j]
        end
        triangle[i][i] = 1
    end

    return triangle
end
