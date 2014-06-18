import collections
import itertools

from daapserver.utils import Mapping

SET = 1
DELETE = 2
INSERT = 3

class DictBackend(dict):

    def hint(self, keys=None):
        """Hint the backend on which keys are going to be accessed. Useful for
        backends with database storage.
        """

        pass

class RevisionManager(object):
    """
    """

    __slots__ = ["last_operation", "revision", "last_revision", "sources"]

    def __init__(self):
        self.last_operation = (None, None)
        self.revision = 0
        self.last_revision = 0

        self.sources = {}

    def is_conflicting(self, operation, source, item):
        last_operation, last_source = self.last_operation

        self.last_operation = (operation, source)
        self.sources[id(source)] = source

        # Check for conflicts
        if operation == last_operation:
            if operation == SET or (operation == DELETE and source is last_source):
                return False

        # New revision required
        self.revision += 1

        # Operation is conflicting
        return True

    def commit(self):
        self.last_revision = self.revision

        for source in self.sources.itervalues():
            source._commit()

        self.last_operation = (None, None)
        self.sources = {}

class RevisionDictView(Mapping):
    """
    """

    def __init__(self, revision, backend, changes, all_keys):
        self.revision = revision
        self.backend = backend
        self.changes = changes
        self.all_keys = all_keys

        # Ability to wrap items (e.g. for tree structures)
        self.wrapper = None

    def __getitem__(self, key):
        # Try changes first, then backend
        try:
            value = self.changes[key]
        except KeyError:
            if key not in self.all_keys:
                raise KeyError

            value = self.backend[key]

        # Wrap value (e.g. for tree structures), otherwise return
        if self.wrapper:
            return self.wrapper(value)
        else:
            return value

    def __iter__(self):
        self.backend.hint(self.all_keys)
        return self.all_keys.__iter__()

    def __len__(self):
        self.backend.hint(self.all_keys)
        return self.all_keys.__len__()

    def added(self, other):
        return RevisionDictView(self.revision, self.backend, self.changes, self.all_keys - other.all_keys)

    def deleted(self, other):
        return other.added(self)

class RevisionDict(Mapping):
    """
    """

    def __init__(self, manager=None, backend=None):
        """
        Initialize a new revision dictionary.
        """

        self.backend = backend or DictBackend()
        self.manager = manager or RevisionManager()
        self.local_revision = 0

        # Init logging structures.
        self.reset(reset_full=True)

    def __setitem__(self, key, value):
        """
        Wrapper for __setitem__ to track all changes.
        """

        # Propagate to backend
        self.backend.__setitem__(key, value)

        # Start new revision if the operation is conflicting, or the local
        # revision does not match the managers revision
        if self.manager.is_conflicting(SET, self, (key, value)):
            self.new_revision()

        if self.local_revision != self.manager.revision:
            self.new_revision()

        # Update logging structures
        self.last_log[key] = value
        self.last_log_keys.add(key)

    def __delitem__(self, key):
        """
        Wrapper for __delitem__ to track all changes.
        """

        # Propagate to backend
        self.backend.__delitem__(key)

        # Start new revision if the operation is conflicting, or the local
        # revision does not match the managers revision
        if self.manager.is_conflicting(DELETE, self, (key, None)):
            self.new_revision()

        if self.local_revision != self.manager.revision:
            self.new_revision()

        # Update logging structures
        try:
            del self.last_log[key]
        except KeyError:
            pass

        self.last_log_keys.discard(key)

    def __getitem__(self, key):
        return self.backend.__getitem__(key)

    def __iter__(self):
        self.backend.hint(None)
        return self.backend.__iter__()

    def __len__(self):
        self.backend.hint(None)
        return self.backend.__len__()

    def new_revision(self):
        """
        Append a new revision to the log structures.
        """

        revision = self.manager.revision

        # Record new revision
        self.revisions.append(revision)

        # Create shallow copy of the dict
        self.last_log = self.log[revision] = self.last_log.copy()
        self.last_log_keys = self.log_keys[revision] = self.last_log_keys.copy()

        # Set local revision
        self.local_revision = revision

    def find_revision(self, target_revision):
        """
        Align a target revision to the nearest older revision.
        """

        if target_revision < self.manager.last_revision:
            raise ValueError("Cannot go back to before a commited revision")

        if target_revision in self.revisions:
            return target_revision

        for revision in reversed(self.revisions):
            if revision < target_revision:
                return revision

        # Nothing found, so we have no record of it
        return self.manager.revision

    def get_revision(self, revision):
        """
        Return a revision of this dictionary at a particular moment in time.
        Will align the revision to the nearest older revision if no changes are
        available for the requested revision.
        """

        revision = revision or self.manager.revision
        aligned = self.find_revision(revision)

        return RevisionDictView(revision, self.backend, self.log[aligned], self.log_keys[aligned])

    def reset(self, reset_full=False):
        """
        Reset the log keeping structures.
        """

        self.last_log = {}
        self.last_log_keys = set(self.backend.keys())

        if reset_full:
            self.revisions = []

            self.log = collections.defaultdict(dict)
            self.log_keys = collections.defaultdict(set)

        # Init current revision
        self.new_revision()

    def clear(self):
        """
        Clear the structure and reset the log keeping structures.
        """

        self.reset(reset_full=True)
        super(RevisionDict, self).clear()

    def _commit(self):
        """
        Actual implementation of commit. Invoked by manager.
        """

        # Reset logs
        self.reset()

    def commit(self):
        """
        Short-hand for `self.manager.commit()'
        """

        self.manager.commit()