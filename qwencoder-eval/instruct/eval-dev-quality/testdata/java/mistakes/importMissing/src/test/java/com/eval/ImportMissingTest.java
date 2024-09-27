package com.eval;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class ImportMissingTest {
	@Test
	public void importMissing1() {
		List<Integer> input = new ArrayList<>();
		int expected = 0;
		int actual = ImportMissing.importMissing(input);

		assertEquals(expected, actual);
	}

	@Test
	public void importMissing2() {
		List<Integer> input = new ArrayList<>();
		input.add(1);
		input.add(3);
		int expected = 4;
		int actual = ImportMissing.importMissing(input);

		assertEquals(expected, actual);
	}
}
