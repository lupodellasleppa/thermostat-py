#!/usr/bin/python3

import sys


script = sys.argv[1]

with open(script) as f:
    to_be_linted = f.readlines()

wrong_lines = False


def replace_spaces(line):
    line = list(line)
    res = []
    if line:
        for i in range(len(line)):
            if line[i] == " ":
                res.append("•")
                # line.insert(0, "•")
            else:
                res += line[i:]
                break
    return ''.join(res)

for i, line in enumerate(to_be_linted):
    line = line.strip("\n")
    if len(line) > 79:
        print("\n{} exceeds char limit @ {} ({})\n\n {:<7}{}\n".format(
            script, i+1, len(line), i+1, replace_spaces(line))
        )
        wrong_lines = True

if not wrong_lines:
    print("{} looks OK. Good job!".format(script))
