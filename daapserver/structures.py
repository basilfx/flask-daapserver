import collections
import itertools

SET = 1
DELETE = 2

class RevisionManager(object):
    """
    """

    __slots__ = ["last_operation", "revision", "last_revision", "sources"]

    def __init__(self):
        self.last_operation = (None, None, None)
        self.revision = 0
        self.last_revision = 0

        self.sources = {}

    def is_conflicting(self, operation, source, item):
        last_operation, last_source, last_item = self.last_operation

        self.last_operation = (operation, source, item)
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

        self.last_operation = (None, None, None)
        self.sources = {}

    def abort(self):
        self.revision = self.last_revision

        for source in self.sources.itervalues():
            source._abort()

        self.last_operation = (None, None, None)
        self.sources = {}

class RevisionDictView(collections.Mapping):
    """
    """

    def __init__(self, revision, base, changes, added, deleted):
        self.revision = revision
        self.base = base
        self.changes = changes
        self.added = added
        self.deleted = deleted

        # Ability to wrap items (e.g. for tree structures)
        self.wrapper = None

        self.am_slotted = True

    def __getitem__(self, key):
        # Check if key was deleted
        if key in self.deleted:
            raise KeyError

        # Try revision first, then base
        try:
            value = self.changes[key]
        except KeyError:
            value = self.base[key]

        # Wrap value (e.g. for tree structures), otherwise return
        if self.wrapper:
            return self.wrapper(value)
        else:
            return value

    def __iter__(self):
        for key in itertools.chain(self.base, self.changes):
            if key not in self.deleted:
                yield key

    def __len__(self):
        return max(0, len(self.base) - len(self.deleted)) + len(self.added)

class RevisionDict(dict):
    """
    """

    def __init__(self, manager=None):
        """
        Initialize a new revision dictionary.
        """

        self.manager = manager or RevisionManager()
        self.local_revision = 0

        # Init logging structures.
        self.reset()

    def __setitem__(self, key, value):
        """
        Wrapper for the original __setitem__, to track all changes.
        """

        # Start new revision if the operation is conflicting, or the local
        # revision does not match the managers revision
        if self.manager.is_conflicting(SET, self, (key, value)):
            self.new_revision()

        if self.local_revision != self.manager.revision:
            self.new_revision()

        # Update logging structures
        self.last_log[key] = value
        self.last_added.append(key)

        try:
            self.last_deleted.remove(key)
        except ValueError:
            pass

    def __delitem__(self, key):
        """
        Wrapper for the original __delitem__, to track all changes.
        """

        if key not in self and key not in self.last_added:
            raise KeyError

        # Start new revision if the operation is conflicting, or the local
        # revision does not match the managers revision
        if self.manager.is_conflicting(DELETE, self, (key, None)):
            self.new_revision()

        if self.local_revision != self.manager.revision:
            self.new_revision()

        # Update logging structures
        self.last_deleted.append(key)

        try:
            del self.last_log[key]
        except KeyError:
            pass

        try:
            self.last_added.remove(key)
        except ValueError:
            pass

    def set_manager(self, manager):
        """
        Set the revision manager. In case a revision manager is switched, the
        current object contents at the latest revision is added to the new
        revision manager.
        """

        # Save current state, since this will be the starting point for the next
        # version.
        if hasattr(self, "_manager"):
            state = self.get_revision()
        else:
            state = {}

        # Update manager
        self._manager = manager

        # The current items should be 'imported' to make sure it is consistent.
        self.reset()

        for key, value in state.iteritems():
            self[key] = value

    def get_manager(self):
        """
        Get the revision manager.
        """

        return self._manager

    manager = property(get_manager, set_manager)

    def new_revision(self):
        """
        Append a new revision to the log structures.
        """

        revision = self.manager.revision

        # Record new revision
        self.revisions.append(revision)

        # Create shallow copy of the dict
        self.last_log = self.log[revision] = self.last_log.copy()
        self.last_added = self.added[revision] = self.last_added[:]
        self.last_deleted = self.deleted[revision] = self.last_deleted[:]

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

    def get_revision(self, revision=None):
        """
        Return a revision of this dictionary at a particular moment in time.
        Will align the revision to the nearest older revision if no changes are
        available for the requested revision.
        """

        revision = revision or self.manager.revision
        aligned_revision = self.find_revision(revision)

        return RevisionDictView(revision, self, self.log[aligned_revision], self.added[aligned_revision], self.deleted[aligned_revision])

    def _commit(self):
        """
        Actual implementation of commit. Invoked by manager.
        """

        for key, value in self.last_log.iteritems():
            dict.__setitem__(self, key, value)

        for key in self.last_deleted:
            try:
                dict.__delitem__(self, key)
            except KeyError:
                pass

        # Reset logs
        self.reset()

    def _abort(self):
        """
        Actual implementation of abort. Invoked by manager.
        """

        self.reset()

    def commit(self):
        """
        Short-hand for `self.manager.commit()'
        """

        self.manager.commit()

    def abort(self):
        """
        Short-hand for `self.manager.abort()'
        """

        self.manager.abort()

    def reset(self):
        """
        Reset the log keeping structures.
        """

        self.revisions = []

        self.last_log = {}
        self.last_deleted = []
        self.last_added = []

        self.log = collections.defaultdict(dict)
        self.deleted = collections.defaultdict(list)
        self.added = collections.defaultdict(list)

        # Init current revision
        self.new_revision()
