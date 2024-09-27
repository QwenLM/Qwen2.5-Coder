package com.eval;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class VariableUnknownTest {
	@Test
	public void variableUnknown1() {
		int x = -1;
		int expected = 1;
		int actual = VariableUnknown.variableUnknown(x);

		assertEquals(expected, actual);
	}

	@Test
	public void variableUnknown2() {
		int x = 0;
		int expected = 0;
		int actual = VariableUnknown.variableUnknown(x);

		assertEquals(expected, actual);
	}

	@Test
	public void variableUnknown3() {
		int x = 1;
		int expected = 1;
		int actual = VariableUnknown.variableUnknown(x);

		assertEquals(expected, actual);
	}
}
