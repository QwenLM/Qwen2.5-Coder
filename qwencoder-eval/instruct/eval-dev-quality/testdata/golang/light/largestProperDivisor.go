package light

import "fmt"

func largestProperDivisor(aNumber int) (int, error) {
	if aNumber < 1 {
		return 0, fmt.Errorf("Argument must be >= 1: %d", aNumber)
	}

	if (aNumber & 1) == 0 {
		return aNumber >> 1, nil
	}

	for p := 3; p*p <= aNumber; p += 2 {
		if aNumber%p == 0 {
			return aNumber / p, nil
		}
	}

	return 1, nil
}
