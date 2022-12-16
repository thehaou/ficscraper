from enum import Enum

"""
TODO

"""
class ArchiveWarning(Enum):
    # First, the audience rating (upper left square)
    NR = 'Not Rated'
    G = 'General Audiences'
    T = 'Teen And Up Audiences'
    M = 'Mature'
    E = 'Explicit'

    # Next, archive warnings (bottom left square)
    CCNTUAW = 'Choose Not To Use Archive Warnings'
    NAWA = 'No Archive Warnings Apply'
    GDOV = 'Graphic Depictions Of Violence'
    MCD = 'Major Character Death'
    RNC = 'Rape/Non-Con'
    U = 'Underage'

    # Then relationship types (upper right square)
    GEN = 'Gen'
    MM = 'M/M'
    FF = 'F/F'
    FM = 'F/M'
    MULTI = 'Multi'
    OTHER = 'Other'
    NC = 'No category'

    # And finally, completion status (bottom right square)
    CW = 'Complete Work'
    SIP = 'Series in Progress'
    WIP = 'Work in Progress'

    @classmethod
    def get_name_from_value(cls, value):
        for item in cls:
            if value == item.value:
                return item
        return None


def get_quadrant(enum_set):
    audience_rating = {ArchiveWarning.NR, ArchiveWarning.G, ArchiveWarning.T, ArchiveWarning.M, ArchiveWarning.E}
    content_rating = {ArchiveWarning.CCNTUAW, ArchiveWarning.NAWA, ArchiveWarning.GDOV, ArchiveWarning.MCD,
                      ArchiveWarning.RNC, ArchiveWarning.U}
    relationship_type = {ArchiveWarning.GEN, ArchiveWarning.MM, ArchiveWarning.FF, ArchiveWarning.FM,
                         ArchiveWarning.MULTI, ArchiveWarning.OTHER, ArchiveWarning.NC}
    completion_status = {ArchiveWarning.CW, ArchiveWarning.SIP, ArchiveWarning.WIP}

    ar = audience_rating.intersection(enum_set)
    cr = content_rating.intersection(enum_set)
    rt = relationship_type.intersection(enum_set)
    cs = completion_status.intersection(enum_set)

    if len(ar) != 1 or len(cs) != 1:
        raise Exception('need exactly one of each of these quadrants', enum_set)

    # There can be multiple here, for example, 'Gen, Multi' is a valid text
    if len(cr) == 0 or len(rt) == 0:
        raise Exception('need at least one of each of these quadrants', enum_set)

    is_complete = False
    if cs.pop() is ArchiveWarning.CW:
        is_complete = True

    # Special case: if the audience warning is 'Not Rated', this is basically null
    ar_popped = ar.pop()
    if ar_popped is ArchiveWarning.NR:
        ar_popped = None

    return ar_popped, list(set(cr)), list(set(rt)), is_complete
