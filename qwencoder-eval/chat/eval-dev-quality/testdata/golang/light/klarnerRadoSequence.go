package light

import "math"

func initialiseKlarnerRadoSequence(limit int) []int {
	result := make([]int, limit+1)
	i2, i3 := 1, 1
	m2, m3 := 1, 1

	for i := 1; i <= limit; i++ {
		minimum := int(math.Min(float64(m2), float64(m3)))
		result[i] = minimum
		if m2 == minimum {
			m2 = result[i2]*2 + 1
			i2 += 1
		}
		if m3 == minimum {
			m3 = result[i3]*3 + 1
			i3 += 1
		}
	}

	return result
}
