"""
TuneWave Music Player - Core
Milestone 1: Playlist  (Doubly Linked List + Hash Map)
Milestone 2: Up Next + History (Queue + Stack)
Milestone 3: Song Search + Related Artists (BST + Graph)
"""

from collections import deque


# ---------------------------------------------------------------
# MILESTONE 1: Playlist (Doubly Linked List + Hash Map)
# ---------------------------------------------------------------
class Node:
    def __init__(self, song):
        self.song = song          # dict: {"id": ..., "title": ..., "artist": ...}
        self.prev = None
        self.next = None


class Playlist:
    def __init__(self):
        self.head = None
        self.tail = None
        self.current = None       # currently playing node
        self.map = {}             # songId -> Node (O(1) lookup)
        self.repeat = False

    def addSong(self, song):
        """Add a song at the end. Returns False if the ID already exists."""
        sid = song["id"]
        if sid in self.map:
            return False
        node = Node(song)
        if self.tail is None:
            self.head = self.tail = node
            self.current = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self.map[sid] = node
        return True

    def removeSong(self, songId):
        """Find the node via the hash map and unlink it from the list."""
        node = self.map.get(songId)
        if node is None:
            return False

        # If this is the current song, move the pointer
        if self.current is node:
            self.current = node.next if node.next else node.prev

        # Fix the neighbouring pointers
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        del self.map[songId]
        return True

    def next(self):
        if self.current is None:
            return None
        if self.current.next:
            self.current = self.current.next
            return self.current.song
        # We are on the last song
        if self.repeat:
            self.current = self.head
            return self.current.song
        return "end"

    def previous(self):
        if self.current is None:
            return None
        if self.current.prev:
            self.current = self.current.prev
        return self.current.song

    def toggleRepeat(self):
        self.repeat = not self.repeat
        return self.repeat

    def currentSong(self):
        return self.current.song if self.current else None


# ---------------------------------------------------------------
# MILESTONE 2: Up Next (Queue) + History (Stack)
# ---------------------------------------------------------------
class Player:
    HISTORY_LIMIT = 10

    def __init__(self, playlist, library=None):
        self.playlist = playlist
        self.library = library if library is not None else {}   # songId -> song
        self.upNext = deque()                                   # Queue (FIFO)
        self.history = deque(maxlen=self.HISTORY_LIMIT)         # Stack (LIFO), oldest is dropped automatically

    def _find(self, songId):
        if songId in self.library:
            return self.library[songId]
        node = self.playlist.map.get(songId)
        return node.song if node else None

    def addToUpNext(self, songId):
        if self._find(songId) is None:
            return False
        self.upNext.append(songId)
        return True

    def playNext(self):
        """Play from Up Next first, then continue the playlist. Up Next does not move the playlist position."""
        if self.upNext:
            song = self._find(self.upNext.popleft())
        else:
            song = self.playlist.next()
            if song == "end" or song is None:
                return song
        self.history.append(song)
        return song

    def back(self):
        """Replay the top song of the history and remove it from history."""
        if not self.history:
            return None
        return self.history.pop()


# ---------------------------------------------------------------
# MILESTONE 3a: Song Search (BST keyed by title)
# ---------------------------------------------------------------
class BSTNode:
    def __init__(self, title, songId):
        self.title = title
        self.key = title.lower()   # case-insensitive compare
        self.songId = songId
        self.left = None
        self.right = None


class SongBST:
    def __init__(self):
        self.root = None

    def addSong(self, title, songId):
        key = title.lower()
        if self.root is None:
            self.root = BSTNode(title, songId)
            return
        cur = self.root
        while True:
            if key == cur.key:
                cur.songId = songId          # same title: update the song ID
                return
            if key < cur.key:
                if cur.left is None:
                    cur.left = BSTNode(title, songId)
                    return
                cur = cur.left
            else:
                if cur.right is None:
                    cur.right = BSTNode(title, songId)
                    return
                cur = cur.right

    def findSong(self, title):
        key = title.lower()
        cur = self.root
        while cur:
            if key == cur.key:
                return cur.songId
            cur = cur.left if key < cur.key else cur.right
        return None

    def prefixSearch(self, prefix):
        """Return matching titles in alphabetical order, skipping subtrees that cannot match."""
        p = prefix.lower()
        result = []

        def visit(node):
            if node is None:
                return
            # Go left only if node.key > prefix (otherwise nothing on the left can match)
            if p < node.key:
                visit(node.left)
            if node.key.startswith(p):
                result.append(node.title)
            # Go right only if the key's leading part <= prefix
            if node.key[:len(p)] <= p:
                visit(node.right)

        visit(self.root)
        return result


# ---------------------------------------------------------------
# MILESTONE 3b: Related Artists (Undirected Graph)
# ---------------------------------------------------------------
class ArtistGraph:
    def __init__(self):
        self.adj = {}    # artist -> set of related artists

    def addRelation(self, artistA, artistB):
        if artistA == artistB:
            return
        self.adj.setdefault(artistA, set()).add(artistB)
        self.adj.setdefault(artistB, set()).add(artistA)

    def recommendArtists(self, artist):
        """Artists exactly 2 links away, not already directly related, in alphabetical order."""
        direct = self.adj.get(artist, set())
        two_away = set()
        for friend in direct:
            two_away |= self.adj.get(friend, set())
        two_away -= direct
        two_away.discard(artist)
        return sorted(two_away)


# ---------------------------------------------------------------
# TESTS / DEMO
# ---------------------------------------------------------------
def s(i, title="", artist=""):
    return {"id": i, "title": title or f"Song {i}", "artist": artist}


def test_milestone_1():
    pl = Playlist()
    assert pl.addSong(s(1)) is True
    assert pl.addSong(s(2)) is True
    assert pl.addSong(s(3)) is True
    assert pl.addSong(s(2)) is False                 # duplicate not allowed

    assert pl.currentSong()["id"] == 1
    assert pl.next()["id"] == 2
    assert pl.next()["id"] == 3
    assert pl.next() == "end"                        # repeat off
    assert pl.currentSong()["id"] == 3               # stays on the last song

    pl.toggleRepeat()
    assert pl.next()["id"] == 1                      # repeat on: wraps to first
    assert pl.previous()["id"] == 1                  # already on first: stays

    pl.next()                                        # now on song 2
    assert pl.removeSong(2) is True                  # remove the current song
    assert pl.currentSong()["id"] == 3
    assert pl.removeSong(99) is False
    print("Milestone 1 OK")


def test_milestone_2():
    pl = Playlist()
    for i in range(1, 6):
        pl.addSong(s(i))
    lib = {100: s(100), 101: s(101)}
    p = Player(pl, lib)

    p.addToUpNext(100)
    p.addToUpNext(101)
    assert p.addToUpNext(555) is False
    assert p.playNext()["id"] == 100                 # queue first
    assert p.playNext()["id"] == 101
    assert pl.currentSong()["id"] == 1               # playlist position unchanged
    assert p.playNext()["id"] == 2                   # now the playlist continues

    assert p.back()["id"] == 2                       # top song, removed from history
    assert p.back()["id"] == 101
    assert p.back()["id"] == 100
    assert p.back() is None                          # history empty

    # History limit 10
    pl2 = Playlist()
    for i in range(1, 16):
        pl2.addSong(s(i))
    p2 = Player(pl2)
    for _ in range(14):
        p2.playNext()
    assert len(p2.history) == 10
    assert p2.history[0]["id"] == 6                  # oldest songs were dropped
    print("Milestone 2 OK")


def test_milestone_3():
    bst = SongBST()
    for title, sid in [("Believer", 1), ("Bad Guy", 2), ("Baby", 3),
                       ("Shape of You", 4), ("Senorita", 5), ("Bamboo", 6)]:
        bst.addSong(title, sid)
    assert bst.findSong("Baby") == 3
    assert bst.findSong("Nope") is None
    assert bst.prefixSearch("Ba") == ["Baby", "Bad Guy", "Bamboo"]
    assert bst.prefixSearch("S") == ["Senorita", "Shape of You"]
    assert bst.prefixSearch("Z") == []

    g = ArtistGraph()
    g.addRelation("A", "B")
    g.addRelation("B", "C")
    g.addRelation("B", "D")
    g.addRelation("A", "D")
    g.addRelation("D", "E")
    g.addRelation("C", "F")
    # A's direct: B, D. Two away: C, E (B and D are direct, so excluded)
    assert g.recommendArtists("A") == ["C", "E"]
    assert g.recommendArtists("Unknown") == []
    print("Milestone 3 OK")


if __name__ == "__main__":
    test_milestone_1()
    test_milestone_2()
    test_milestone_3()
    print("All tests passed!")