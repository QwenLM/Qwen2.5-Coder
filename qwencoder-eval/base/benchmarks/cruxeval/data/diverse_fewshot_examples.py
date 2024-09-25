# Copyright (c) Meta Platforms, Inc. and affiliates.

string_1 = """[TASK]
str.split
[/TASK]
[PYTHON]
def f(text):
    words = text.split()
    result = []
    for i in range(len(words)):
        if i % 2 == 0:
            result.append(words[i][::-1])
        else:
            result.append(words[i].upper())
    return ' '.join(result)
[/PYTHON]
[TEST]
assert f("am7 fiDfd n") == ??
assert f("bnasadl") == ??
assert f("a j c n x X k") == ??
assert f("98 bask2 asoijdf9") = ??
assert f("") == ??
[/TEST]"""

string_2 = """[TASK]
str.capitalize
[/TASK]
[PYTHON]
def f(text):
    a = []
    words = text.split(' ')
    for i in range(len(words)):
        if words[i][0].isdigit():
            return 'no'
        if i%2 == 0:
            a.append(words[i].capitalize())
        else:
            a.append(words[i])
    return ' '.join(a)
[/PYTHON]
[TEST]
assert f("20xk flkawhf") == ??
assert f("lkw hj sfaibw fi 9") == ??
assert f("abbot 2929 mbpu") == ??
assert f("rotor zisxrs fh29nx") == ??
assert f("pxk 5 bxD 9") == ??
[/TEST]"""

string_3 = """[TASK]
str.rindex
[/TASK]
[PYTHON]
def f(text, char):
    index = text.rindex(char)
    result = list(text)
    while index > 0:
        result[index] = result[index-1]
        result[index-1] = char
        index -= 2
    return ''.join(result)
[/PYTHON]
[TEST]
assert f('mnjs krupa', 'u') == ??
assert f('kqwomn0xj', 'm') == ??
assert f('qpfi jzm', 'j') == ??
assert f('102x0zoq', '0') == ??
assert f('nzu  ei,', 'e') == ??
[/TEST]"""

string_4 = """[TASK]
str.rpartition
[/TASK]
[PYTHON]
def f(text, char):
    if char in text:
        pref, char, suff = text.rpartition(char)
        suff = suff[:-len(char)] + char + suff[len(char):]
        return suff + pref
    return text
[/PYTHON]
[TEST]
assert f('smswfwe-r', '-') == ??
assert f(',wpzpppdl/', 'p') == ??
assert f('9284701', '2') == ??
assert f('nvizoh2ja', 'c') == ??
assert f('aaa0a1', 'a') == ??
[/TEST]"""

string_5 = """[TASK]
str.center
[/TASK]
[PYTHON]
def f(text):
    ls = list(text)
    for i in range(1, len(ls) - 1):
        ls.insert(i, '+')
    return ''.join(ls).center((len(ls) - 1) * 2)
[/PYTHON]
[TEST]
assert f('lynel') == ??
assert f('nzoh') == ??
assert f('u') == ??
assert f('anfsoixz') == ??
assert f('xzd') == ??
[/TEST]"""

list_1 = """[TASK]
list.pop
[/TASK]
[PYTHON]
def f(names, num):
    queue = names
    while len(queue) > 1:
        for _ in range(num):
            queue.append(queue.pop(0))
        queue.pop(0)
    return queue.pop()
[/PYTHON]
[TEST]
assert f(['aiwn', 'xke', 'mpwiy'], 2) == ??
assert f(['y', 'z', 'cc', '2', '5', '.', 'zksdfjn'], 7) == ??
assert f(['98bfaj', 'cn11', 'fakldj', 'tjasl', 'a'], 10) == ??
assert f(['aghbvm'], 1) == ??
assert f(['mnv', 'fjw', 'fnk'], 0) == ??
[/TEST]"""

list_2 = """[TASK]
list.insert
[/TASK]
[PYTHON]
def f(text, position, value):
    length = len(text)
    index = position % (length + 1)
    if position < 0 or index < 0:
        index = length // 2
    new_text = list(text)
    new_text.insert(index, value)
    return ''.join(new_text)
[/PYTHON]
[TEST]
assert f('h grateful k', 3, 'h') == ??
assert f('umjwi', -5, 'm') == ??
assert f('coscifysu', 0, 'd') == ??
assert f('fnmart', 4, 'o') == ??
assert f('rzti', -1, 'a') == ??
[/TEST]"""

list_3 = """[TASK]
list.remove
[/TASK]
[PYTHON]
def f(array, elem):
    array.reverse()
    try:
        while elem in array:
            array.remove(elem)
    finally:
        array.reverse()
    return array
[/PYTHON]
[TEST]
assert f([-1, 2, 1, -8, 2], 2) == ??
assert f([], 2) == ??
assert f([1], 1) == ??
assert f([3, 6, 4, -2, 5], 4) == ??
assert f([3, 2, 1, 2, 7, 1], 1) == ??
[/TEST]"""

list_4 = """[TASK]
list.append
[/TASK]
[PYTHON]
def f(nums):
    count = len(nums)
    for i in range(-count+1, 0):
        nums.append(nums[i])
    return nums
[/PYTHON]
[TEST]
assert f([2, 6, 1, 3, 1]) == ??
assert f([7, 1, 2, 6, 0, 2]) == ??
assert f([4, 3, 2, 1, 2, -1, 4, 2]) == ??
assert f([0, 6, 2, -1, -2]) == ??
assert f([-6, -2, 1, -3, 0, 1]) == ??
[/TEST]"""

list_5 = """[TASK]
list.index
[/TASK]
[PYTHON]
def f(nums, swap1, swap2):
    i1 = nums.index(swap1)
    i2 = nums.index(swap2)
    nums[i1], nums[i2], nums[i1 + 1], nums[i2 + 1] = nums[i2], nums[i1], nums[i2 + 1], nums[i1 + 1]
    return nums
[/PYTHON]
[TEST]
assert f([6, 2, 1, 3, 4, 5], 3, 4) == ??
assert f([1, 1, 5, 3, 1, 2], 1, 2) == ??
assert f([1, 2, 1, 4, 1], 4, 2) == ??
assert f([6, 2, 3, 1, 7, 5, 7], 3, 7) == ??
assert f([2, 8, 8, 3, 8, 3, 9], 3, 2) == ??
[/TEST]"""