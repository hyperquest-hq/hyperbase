import json

from sqlite3 import connect

from hyperbase.hyperedge import hedge
from hyperbase.memory.keyvalue import KeyValue
from hyperbase.memory.permutations import str_plus_1


def _encode_attributes(attributes):
    return json.dumps(attributes, ensure_ascii=False, check_circular=False, separators=(',', ':'))


def _decode_attributes(value):
    return json.loads(value)


class SQLite(KeyValue):
    """Implements SQLite hypergraph storage."""

    def __init__(self, locator_string):
        super().__init__(locator_string)

        self.conn = connect(self.locator_string, isolation_level=None)
        self.cur = None

        # self.conn.execute('PRAGMA synchronous = OFF')
        # self.conn.execute('PRAGMA journal_mode = MEMORY')

        self.conn.execute('CREATE TABLE IF NOT EXISTS v (key TEXT PRIMARY KEY, value TEXT)')
        self.conn.execute('CREATE TABLE IF NOT EXISTS p (key TEXT PRIMARY KEY)')

    # ===================================
    # Implementation of interface methods
    # ===================================

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def destroy(self):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM v')
        cur.execute('DELETE FROM p')

    def all(self):
        cur = self.conn.cursor()
        for key, _ in cur.execute('SELECT * FROM v'):
            edge = hedge(key)
            if edge is not None:
                yield edge

    def all_attributes(self):
        cur = self.conn.cursor()
        for key, value in cur.execute('SELECT * FROM v'):
            edge = hedge(key)
            if edge is not None:
                attributes = _decode_attributes(value)
                yield edge, attributes

    def begin_transaction(self):
        if self.batch_mode:
            return
        self.cur = self.conn.cursor()
        self.cur.execute('BEGIN TRANSACTION')

    def end_transaction(self):
        if self.batch_mode:
            return
        self.conn.commit()
        self.cur = None

    # ==========================================
    # Implementation of private abstract methods
    # ==========================================

    def _edge2key(self, edge):
        return edge.to_str()

    def _exists_key(self, key):
        """Checks if the given key exists."""
        cur = self.conn.cursor()
        for key, _ in cur.execute('SELECT * FROM v WHERE key = ?', (key, )):
            return True
        return False

    def _add_key(self, key, attributes):
        """Adds the given edge, given its key."""
        value = _encode_attributes(attributes)
        self.cur.execute('INSERT OR REPLACE INTO v (key, value) VALUES(?, ?)', (key, value))

    def _attribute_key(self, key):
        cur = self.conn.cursor()
        for key, value in cur.execute('SELECT * FROM v WHERE key = ?', (key,)):
            return _decode_attributes(value)
        return None

    def _write_edge_permutation(self, perm):
        """Writes a given permutation."""
        self.cur.execute('INSERT OR IGNORE INTO p (key) VALUES(?)', (perm,))

    def _remove_edge_permutation(self, perm):
        """Removes a given permutation."""
        self.cur.execute('DELETE FROM p WHERE key = ?', (perm,))

    def _remove_key(self, key):
        """Removes an edge, given its key."""
        self.cur.execute('DELETE FROM v WHERE key = ?', (key,))

    def _permutations_with_prefix(self, prefix):
        end_str = str_plus_1(prefix)
        cur = self.conn.cursor()
        for row in cur.execute('SELECT * FROM p WHERE key >= ? AND key < ?', (prefix, end_str)):
            yield row[0]

    def _edges_with_prefix(self, prefix):
        end_str = str_plus_1(prefix)
        cur = self.conn.cursor()
        for key, _ in cur.execute('SELECT * FROM v WHERE key >= ? AND key < ?', (prefix, end_str)):
            yield hedge(key)
