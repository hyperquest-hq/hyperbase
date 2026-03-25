class Processor:
    def __init__(self, hg, sequence=None):
        self.hg = hg
        self.sequence = sequence

    def process_edge(self, edge):
        pass

    def on_end(self):
        pass

    def report(self):
        return ''

    def run(self):
        if self.sequence is None:
            for edge in self.hg.all():
                self.process_edge(edge)
        else:
            for edge in self.hg.sequence(self.sequence):
                self.process_edge(edge)
        self.on_end()
        print(self.report())
