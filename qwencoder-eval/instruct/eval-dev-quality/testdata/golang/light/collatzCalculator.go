package light

import "errors"

func computeStepCount(start int) (int, error) {
	if start <= 0 {
		return 0, errors.New("Only positive integers are allowed")
	}
	if start == 1 {
		return 0, nil
	}
	var next int

	if start%2 == 0 {
		next = start / 2
	} else {
		next = 3*start + 1
	}

	n, err := computeStepCount(next)
	if err != nil {
		return 0, err
	}

	return 1 + n, nil
}
