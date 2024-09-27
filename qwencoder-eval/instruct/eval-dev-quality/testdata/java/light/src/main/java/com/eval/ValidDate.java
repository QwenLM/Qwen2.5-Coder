package com.eval;

class ValidDate {
    static boolean validDate(int day, int month, int year) {
		int[] monthDays = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

		if (year < 1583) {
			return false;
		}
		if (month < 1 || month > 12) {
			return false;
		}
		if (day < 1) {
			return false;
		}
		if (month == 2) {
			if ((year % 400) != 0 && (year % 4) == 0) {
				if (day > 29) {
					return false;
				}
			} else {
				if (day > 28) {
					return false;
				}
			}
		} else {
			if (day > monthDays[month-1]) {
				return false;
			}
		}

		return true;
	}
}
