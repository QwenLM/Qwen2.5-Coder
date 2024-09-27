package com.eval;

public class VariableUnknown {
	public static int variableUnknown(int x) {
		y = x;
		if (x > 0) {
			return y;
		}
		if (x < 0) {
			return -y;
		}

		return 0;
	}
}
