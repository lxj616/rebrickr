from mathutils import Matrix, Vector

def clamp(v, min_v, max_v): return max(min_v, min(max_v, v))

class Direction2D(Vector):
    def __init__(self, t=None):
        if t is not None: self.from_vector(t)
    def __str__(self):
        return '<Direction2D (%0.4f, %0.4f)>' % (self.x,self.y)
    def __repr__(self): return self.__str__()
    def __mul__(self, other):
        t = type(other)
        if t is float or t is int:
            return Vec2D((other * self.x, other * self.y))
        assert False, "unhandled type of other: %s (%s)" % (str(other), str(t))
    def __rmul__(self, other):
        return self.__mul__(other)

class Vec2D(Vector):
    def __init__(self, *args, **kwargs):
        Vector.__init__(*args, **kwargs)
    def __str__(self):
        return '<Vec2D (%0.4f, %0.4f)>' % (self.x,self.y)
    def __repr__(self): return self.__str__()
    def from_vector(self, v): self.x,self.y = v

class Point2D(Vector):
    def __init__(self, *args, **kwargs):
        Vector.__init__(*args, **kwargs)
    def __str__(self):
        return '<Point2D (%0.4f, %0.4f)>' % (self.x,self.y)
    def __repr__(self): return self.__str__()
    def __add__(self, other):
        t = type(other)
        if t is Direction2D:
            return Point2D((self.x+other.x,self.y+other.y))
        if t is Vector or t is Vec2D:
            return Point2D((self.x+other.x,self.y+other.y))
        assert False, "unhandled type of other: %s (%s)" % (str(other), str(t))
    def __radd__(self, other):
        return self.__add__(other)
    def __sub__(self, other):
        t = type(other)
        if t is Vector or t is Vec2D:
            return Point2D((self.x-other.x,self.y-other.y))
        elif t is Point2D:
            return Vec2D((self.x-other.x, self.y-other.y))
        assert False, "unhandled type of other: %s (%s)" % (str(other), str(t))
