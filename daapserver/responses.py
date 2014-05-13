from daapserver.daap import do

def diff(new, old):
    added = deleted = None

    if new and old:
        update = 1
        deleted = list(set(old.keys()) - set(new.keys()))

        if not deleted:
            added = list(set(new.items()) - set(old.items()))
    else:
        update = 0
        added = new.items()

    assert (not added and not deleted) or (not added and deleted) or (added and not deleted)

    return added, deleted, update

def database(database):
    data = [
        do("dmap.itemid", database.id),
        do("dmap.itemname", database.name),
        do("dmap.persistentid", database.persistent_id),
        do("dmap.itemcount", len(database.items)),
        do("dmap.containercount", len(database.containers))
    ]

    return do("dmap.listingitem", data)

def databases(new, old=None):
    added, deleted, update = diff(new, old)

    if added:
        return do("daap.serverdatabases", [
            do("dmap.status", 200),
            do("dmap.updatetype", update),
            do("dmap.specifiedtotalcount", len(new)),
            do("dmap.returnedcount", len(added)),
            do("dmap.listing", [ database(v) for k, v in added ])
        ])
    else:
        return do("daap.serverdatabases", [
            do("dmap.status", 200),
            do("dmap.updatetype", update),
            do("dmap.specifiedtotalcount", len(new)),
            do("dmap.returnedcount", len(deleted)),
            do("dmap.deletedidlisting", [ do("dmap.itemid", k) for k in deleted ])
        ])

def container(container):
    data = [
        do("dmap.itemid", container.id),
        do("dmap.itemname", container.name),
        do("dmap.persistentid", container.persistent_id),
        do("dmap.itemcount", len(container.items)),
        do("dmap.containeritemid", container.id),
        do("dmap.parentcontainerid", container.parent.id
            if container.parent else 0)
    ]

    if container.is_base:
        data += [do("daap.baseplaylist", 1)]
    if container.is_smart:
        data += [do("com.apple.itunes.smart-playlist", 1)]

    return do("dmap.listingitem", data)

def containers(new, old=None):
    added, deleted, update = diff(new, old)

    if added:
        return do("daap.databaseplaylists", [
            do("dmap.status", 200),
            do("dmap.updatetype", update),
            do("dmap.specifiedtotalcount", len(new)),
            do("dmap.returnedcount", len(added)),
            do("dmap.listing", [ container(v) for k, v in added ])
        ])
    else:
        return do("daap.databaseplaylists", [
            do("dmap.status", 200),
            do("dmap.updatetype", update),
            do("dmap.specifiedtotalcount", len(new)),
            do("dmap.returnedcount", len(deleted)),
            do("dmap.deletedidlisting", [ do("dmap.itemid", k) for k in deleted ])
        ])

def item(item):
    data = [
        do("dmap.itemid", item.id),
        do("dmap.itemkind", 2),
        #do("dmap.containeritemid", index),
        do("dmap.persistentid", item.persistent_id)
    ]

    if item.album:
        data += [do("daap.songalbum", item.album)]
    if item.file_suffix:
        data += [do("daap.songformat", item.file_suffix)]
    if item.title:
        data += [do("dmap.itemname", item.title)]
    if item.track:
        data += [do("daap.songtracknumber", item.track)]
    if item.artist:
        data += [do("daap.songartist", item.artist )]
    if item.bitrate:
        data += [do("daap.songbitrate", item.bitrate)]
    if item.file_size:
        data += [do("daap.songsize", item.file_size)]
    if item.year:
        data += [do("daap.songyear", item.year)]
    if item.duration:
        data += [do("daap.songtime", item.duration )]

    return do("dmap.listingitem", data)

def items(new, old=None):
    added, deleted, update = diff(new, old)

    if added:
        return do("daap.databasesongs", [
            do("dmap.status", 200),
            do("dmap.updatetype", update),
            do("dmap.specifiedtotalcount", len(new)),
            do("dmap.returnedcount", len(added)),
            do("dmap.listing", [ item(v) for k, v in added ])
        ])
    else:
        return do("daap.databasesongs", [
            do("dmap.status", 200),
            do("dmap.updatetype", update),
            do("dmap.specifiedtotalcount", len(new)),
            do("dmap.returnedcount", len(deleted)),
            do("dmap.deletedidlisting", [ do("dmap.itemid", k) for k in deleted ])
        ])

def container_item(item):
    data = [
        do("dmap.itemid", index),
        do("dmap.itemkind", 2),
        do("dmap.containeritemid", item.id),
        do("dmap.persistentid", item.id),
    ]

    if item.title:
        data += [do("daap.sortname", item.title)]
    if item.album:
        data += [do("daap.sortalbum", item.album)]
    if item.artist:
        data += [
            do("daap.sortartist", item.artist),
            do("daap.sortalbumartist", item.artist)
        ]

    return do("dmap.listingitem", data)

def container_items(new, old=None):
    added, deleted, update = diff(new, old)

    if added:
        return do("daap.playlistsongs", [
            do("dmap.status", 200),
            do("dmap.updatetype", update),
            do("dmap.specifiedtotalcount", len(new)),
            do("dmap.returnedcount", len(added)),
            do("dmap.listing", [ item(v) for k, v in added ])
        ])
    else:
        return do("daap.playlistsongs", [
            do("dmap.status", 200),
            do("dmap.updatetype", update),
            do("dmap.specifiedtotalcount", len(new)),
            do("dmap.returnedcount", len(deleted)),
            do("dmap.deletedidlisting", [ do("dmap.itemid", k) for k in deleted ])
        ])