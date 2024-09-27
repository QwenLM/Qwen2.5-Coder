package light

import "errors"

func magicSquareOdd(base int) ([][]int, error) {
	if base%2 == 0 || base < 3 {
		return nil, errors.New("base must be odd and > 2")
	}

	grid := make([][]int, base)
	for i := range grid {
		grid[i] = make([]int, base)
	}
	r, number := 0, 0
	size := base * base

	c := base / 2
	for number < size {
		number++
		grid[r][c] = number
		if r == 0 {
			if c == base-1 {
				r++
			} else {
				r = base - 1
				c++
			}
		} else {
			if c == base-1 {
				r--
				c = 0
			} else {
				if grid[r-1][c+1] == 0 {
					r--
					c++
				} else {
					r++
				}
			}
		}
	}

	return grid, nil
}
