package com.eval;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class TypeUnknownTest {
	@Test
	public void typeIsWrong1() {
		int x = -1;
		int expected = -1;
		int actual = TypeUnknown.typeUnknown(x);

		assertEquals(expected, actual);
	}

	@Test
	public void typeIsWrong2() {
		int x = 0;
		int expected = 0;
		int actual = TypeUnknown.typeUnknown(x);

		assertEquals(expected, actual);
	}

	@Test
	public void typeIsWrong3() {
		int x = 1;
		int expected = 1;
		int actual = TypeUnknown.typeUnknown(x);

		assertEquals(expected, actual);
	}
}
