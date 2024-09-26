package com.eval;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class CascadingIfElseTest {
	@Test
	public void cascadingIfElse1() {
		int i = 0;
		int expected = 5;
		int actual = CascadingIfElse.cascadingIfElse(i);

		assertEquals(expected, actual);
	}

	@Test
	public void cascadingIfElse2() {
		int i = 1;
		int expected = 2;
		int actual = CascadingIfElse.cascadingIfElse(i);

		assertEquals(expected, actual);
	}

	@Test
	public void cascadingIfElse3() {
		int i = 3;
		int expected = 4;
		int actual = CascadingIfElse.cascadingIfElse(i);

		assertEquals(expected, actual);
	}
}
