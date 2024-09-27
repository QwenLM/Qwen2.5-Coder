package pascalsTriangle

import "errors"

func pascalsTriangle(rows int) ([][]int, error) {
	if rows < 0 {
		return nil, errors.New("Rows can't be negative!")
	}

	triangle := make([][]int, rows)

	for i := 0; i < rows; i++ {
		triangle[i] = make([]int, i+1)
		triangle[i][0] = 1
		for j := 1; j < i; j++ {
			triangle[i][j] = triangle[i-1][j-1] + triangle[i-1][j]
		}
		triangle[i][i] = 1
	}
	return triangle, nil
}
