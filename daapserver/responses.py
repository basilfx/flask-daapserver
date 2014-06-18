from daapserver.daap import DAAPObject

def diff(new, old):
    added = deleted = None

    # Take either added or deleted, but not both
    if new and old:
        update = 1
        deleted = new.deleted(old)

        if not deleted:
            added = new.added(old)
    else:
        update = 0
        added = new

    # It should not be possible that both added and deleted are set.
    assert (not added and not deleted) or (not added and deleted) or (added and not deleted)

    return added, deleted, update

def database(database):
    data = [
        DAAPObject("dmap.itemid", database.id),
        DAAPObject("dmap.itemname", database.name),
        DAAPObject("dmap.itemcount", len(database.items)),
        DAAPObject("dmap.containercount", len(database.containers))
    ]

    if database.persistent_id:
        data.append(DAAPObject("dmap.persistentid", database.persistent_id))

    return DAAPObject("dmap.listingitem", data)

def databases(new, old=None):
    added, deleted, update = diff(new, old)

    if added is not None:
        return DAAPObject("daap.serverdatabases", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", update),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(added)),
            DAAPObject("dmap.listing", ( database(v) for v in added.itervalues() ))
        ])
    else:
        return DAAPObject("daap.serverdatabases", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", update),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(deleted)),
            DAAPObject("dmap.deletedidlisting", ( DAAPObject("dmap.itemid", k) for k in deleted.iterkeys() ))
        ])

def container(container, index):
    data = [
        DAAPObject("dmap.itemid", container.id),
        DAAPObject("dmap.itemname", container.name),
        DAAPObject("dmap.itemcount", len(container.container_items)),
        DAAPObject("dmap.containeritemid", index),
        DAAPObject("dmap.parentcontainerid", container.parent.id if container.parent else 0)
    ]

    if container.persistent_id:
        data.append(DAAPObject("dmap.persistentid", container.persistent_id))
    if container.is_base:
        data.append(DAAPObject("daap.baseplaylist", 1))
    if container.is_smart:
        data.append(DAAPObject("com.apple.itunes.smart-playlist", 1))

    return DAAPObject("dmap.listingitem", data)

def containers(new, old=None):
    added, deleted, update = diff(new, old)

    if added is not None:
        return DAAPObject("daap.databaseplaylists", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", update),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(added)),
            DAAPObject("dmap.listing", ( container(v, i) for i, v in enumerate(added.itervalues(), start=1) ))
        ])
    else:
        return DAAPObject("daap.databaseplaylists", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", update),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(deleted)),
            DAAPObject("dmap.deletedidlisting", ( DAAPObject("dmap.itemid", k) for k in deleted.iterkeys() ))
        ])

def item(item, index):
    data = [
        DAAPObject("dmap.itemid", item.id),
        DAAPObject("dmap.itemkind", 2),
        DAAPObject("dmap.containeritemid", index),
    ]

    if item.persistent_id:
        data.append(DAAPObject("dmap.persistentid", item.persistent_id))
    if item.name:
        data.append(DAAPObject("dmap.itemname", item.name))
    if item.track:
        data.append(DAAPObject("daap.songtracknumber", item.track))
    if item.artist:
        data.append(DAAPObject("daap.songartist", item.artist))
    if item.album:
        data.append(DAAPObject("daap.songalbum", item.album))
    if item.year:
        data.append(DAAPObject("daap.songyear", item.year))
    if item.bitrate:
        data.append(DAAPObject("daap.songbitrate", item.bitrate))
    if item.duration:
        data.append(DAAPObject("daap.songtime", item.duration))
    if item.file_size:
        data.append(DAAPObject("daap.songsize", item.file_size))
    if item.file_suffix:
        data.append(DAAPObject("daap.songformat", item.file_suffix))
    if item.album_art:
        data.append(DAAPObject("daap.songartworkcount", 1))
        data.append(DAAPObject("daap.songextradata", 1))

    return DAAPObject("dmap.listingitem", data)

def items(new, old=None):
    added, deleted, update = diff(new, old)

    if added is not None:
        return DAAPObject("daap.databasesongs", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", update),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(added)),
            DAAPObject("dmap.listing", ( item(v, i) for i, v in enumerate(added.itervalues()) ))
        ])
    else:
        return DAAPObject("daap.databasesongs", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", update),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(deleted)),
            DAAPObject("dmap.deletedidlisting", ( DAAPObject("dmap.itemid", k) for k in deleted.iterkeys() ))
        ])

def container_item(container_item, index):
    item = container_item.item

    data = [
        DAAPObject("dmap.itemid", item.id),
        DAAPObject("dmap.itemkind", 2),
        DAAPObject("dmap.containeritemid", index),
    ]

    if container_item.persistent_id:
        data.append(DAAPObject("dmap.persistentid", container_item.persistent_id))
    if item.name:
        data.append(DAAPObject("daap.sortname", item.name))
    if item.album:
        data.append(DAAPObject("daap.sortalbum", item.album))
    if item.artist:
        data.append(DAAPObject("daap.sortartist", item.artist))
        data.append(DAAPObject("daap.sortalbumartist", item.artist))

    return DAAPObject("dmap.listingitem", data)

def container_items(new, old=None):
    added, deleted, update = diff(new, old)

    if added is not None:
        return DAAPObject("daap.playlistsongs", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", update),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(added)),
            DAAPObject("dmap.listing", ( container_item(v, i) for i, v in enumerate(added.itervalues()) ))
        ])
    else:
        return DAAPObject("daap.playlistsongs", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", update),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(deleted)),
            DAAPObject("dmap.deletedidlisting", ( DAAPObject("dmap.itemid", k) for k in deleted.iterkeys() ))
        ])