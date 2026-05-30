
string = "hi"
class writer:
    def __init__(self):
        self.lines = []
        self.ind_level = 0
        pass
    def writes(self, string):
        indent = ""
        for i in range(self.ind_level):
            indent = indent + "    "
        text = indent + string
        self.lines.append(text)
    def indent(self):
       self.ind_level += 1
    def dedent(self):
        self.ind_level -= 1
w = writer()
w.indent()
w.writes("hi")
print(w.lines)
