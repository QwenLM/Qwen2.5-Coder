package light

import "errors"

func extractDigits(dirtyNumber string) (cleanNumber string, err error) {
	for _, c := range dirtyNumber {
		if c == ' ' || c == '.' || c == '(' || c == ')' || c == '-' || c == '+' {
			// Remove spaces, dots, parentheses, hyphens and pluses.
			continue
		}
		if c == '-' || c == '@' || c == ':' || c == '!' {
			return "", errors.New("punctuations not permitted")
		}
		if c < '0' || c > '9' {
			return "", errors.New("letters not permitted")
		}
		cleanNumber += string(c)
	}

	return cleanNumber, nil
}
