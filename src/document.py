class Document:

    def __init__(self, d):
        self.doc = d

    def retain_keys(self, keys):
        self.doc = {k: self.doc[k] for k in keys}

    def rename_keys(self, renamings):
        for old, new in renamings.items():
            self.doc[new] = self.doc.pop(old)

    def put(self, key, value):
        self.doc[key] = value

    def json(self):
        return self.doc
