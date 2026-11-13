import unittest
from session_performance import fingerprint, reuse, clear_private


class SessionPerformanceTests(unittest.TestCase):
    def test_fingerprint_stable_and_sensitive(self):
        self.assertEqual(fingerprint(b'abc', ['a', 1]), fingerprint(b'abc', ['a', 1]))
        self.assertNotEqual(fingerprint(b'abc'), fingerprint(b'abd'))

    def test_reuse_and_invalidate(self):
        state = {}
        called = []
        def build():
            called.append(1)
            return {'count': len(called)}
        self.assertEqual(reuse(state, 'parsed', 'a', build), {'count': 1})
        self.assertEqual(reuse(state, 'parsed', 'a', build), {'count': 1})
        self.assertEqual(reuse(state, 'parsed', 'b', build), {'count': 2})
        self.assertEqual(len(called), 2)
        self.assertEqual(len(state), 1)

    def test_separate_sessions_do_not_share(self):
        a, b = {}, {}
        reuse(a, 'x', 'input', lambda: 'first')
        self.assertEqual(reuse(b, 'x', 'input', lambda: 'second'), 'second')

    def test_clear_only_private_keys(self):
        state = {'other': 5}
        reuse(state, 'data', 'k', lambda: [1, 2, 3])
        clear_private(state)
        self.assertEqual(state, {'other': 5})


if __name__ == '__main__':
    unittest.main()
