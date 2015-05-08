# *****************************************************************************
# Group class used for Group-tree creation
# *****************************************************************************


class Group(object):
    """ A tree of scheduling groups. Leaf nodes are groups where jobs are
        actually submitted, mid-level nodes set limits on the surplus-sharing
        abilities of this tree of groups.
    """

    def __init__(self, name, weight=1, surplus=False, threshold=0, running=0):
        # These variables define the nature of the group, and are explicitly set
        self.name = name
        self.accept_surplus = surplus
        self.running = running
        self.threshold = threshold
        self.weight = weight

        self.parent = None
        self.children = {}
        self.demand = 0

    def add_child(self, new_grp):
        """ Add a child node to this one, setting it's parent pointer """

        new_grp.parent = self
        self.children[new_grp.name] = new_grp

    def walk(self):
        """ Recursively iterate through all lower nodes in the tree """
        if not self.children:
            return
        for x in self.get_children():
            yield x
            for y in x.walk():
                yield y

    def walk_dfs(self):
        """ Iterate through tree in a depth-first order """
        for child in self.get_children():
            for sub in child.walk_dfs():
                yield sub
            yield child

    @property
    def full_name(self):
        names = list()
        parent = self
        while parent is not None:
            names.append(parent.name)
            parent = parent.parent
        return ".".join(reversed(names[:-1]))

    @property
    def is_leaf(self):
        return (not self.children)

    def get_children(self):
        """ Return list of all children group-objects """
        return self.children.itervalues()

    def find(self, name):
        """ Find a group named @name below self -- raise Exception """
        if self.name == name:
            return self
        for x in self.walk():
            if name == x.name:
                return x
        raise Exception("No group %s found" % name)

    def leaf_nodes(self):
        return (x for x in self if not x.children)

    def print_dfs(self, n=0):
        for x in self:
            print x.full_name

    def print_tree(self, n=0):
        print '|' + '--'*(n) + str(self)
        for child in sorted(self.get_children(), key=lambda x: x.name):
            child.print_tree(n + 1)

    def __getitem__(self, key):
        return self.children[key]

    def __repr__(self):
        return '<0x%x> %s' % (id(self), self.full_name)

    def __iter__(self):
        return iter(self.walk())

    def __contains__(self, key):
        return (len([x.name for x in self if x.name == key]) > 0)

    def __str__(self):
        return '%s: surplus %s, weight %f, threshold %d demand %d' % \
               (self.name, self.accept_surplus, self.weight, self.threshold,
                self.demand)