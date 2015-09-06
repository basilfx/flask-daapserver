from daapserver import daap


def login(provider, session_id):
    """
    Generate a login response.
    """

    return DAAPObject("dmap.loginresponse", [
        DAAPObject("dmap.status", 200),
        DAAPObject("dmap.sessionid", session_id)
    ])


def update(provider, revision):
    """
    Generate an update response.
    """

    return DAAPObject("dmap.updateresponse", [
        DAAPObject("dmap.status", 200),
        DAAPObject("dmap.serverrevision", revision),
    ])


def content_codes(provider):
    """
    Generate supported content codes response.
    """

    children = [DAAPObject("dmap.status", 200)]
    data = DAAPObject("dmap.contentcodesresponse", children)

    for code in daap.dmap_code_types.iterkeys():
        name, itype = daap.dmap_code_types[code]

        children.append(
            DAAPObject("dmap.dictionary", [
                DAAPObject("dmap.contentcodesnumber", code),
                DAAPObject("dmap.contentcodesname", name),
                DAAPObject(
                    "dmap.contentcodestype", daap.dmap_reverse_data_types[itype])
            ])
        )

    return data


def server_info(provider, server_name, password):
    """
    Generate server info response
    """

    data = [
        DAAPObject("dmap.status", 200),
        DAAPObject("dmap.protocolversion", "2.0.10"),
        DAAPObject("daap.protocolversion", "3.0.12"),
        DAAPObject("com.apple.itunes.music-sharing-version", 196619),
        DAAPObject("dmap.itemname", server_name),
        DAAPObject("dmap.timeoutinterval", 1800),
        DAAPObject("dmap.supportsautologout", 1),
        DAAPObject("dmap.loginrequired", 1 if password else 0),
        DAAPObject("dmap.authenticationmethod", 2 if password else 0),
        DAAPObject("com.apple.itunes.unknown-MQ", 1),
        DAAPObject("com.apple.itunes.unknown-Tr", 1),
        DAAPObject("com.apple.itunes.unknown-SL", 1),
        DAAPObject("com.apple.itunes.unknown-SR", 1),
        DAAPObject("dmap.supportsextensions", 1),
        DAAPObject("dmap.supportsindex", 1),
        DAAPObject("dmap.supportsbrowse", 1),
        DAAPObject("dmap.supportsquery", 1),
        DAAPObject("daap.supportsgroups", 0),
        DAAPObject("dmap.databasescount", len(provider.server.databases)),
        DAAPObject("dmap.supportsupdate", 1),
        DAAPObject("dmap.supportsresolve", 1),
        DAAPObject("dmap.supportsedit", 0)
    ]

    if provider.supports_persistent_id:
        data.append(DAAPObject("dmap.supportspersistentids", 1))

    if provider.supports_artwork:
        data.append(DAAPObject("daap.supportsextradata", 1))

    return DAAPObject("dmap.serverinforesponse", data)


def databases(provider, new, old, added, removed, is_update):
    """
    Generate databases response.
    """

    # Single database response
    def _database(Database database):
        data = [
            DAAPObject("dmap.itemid", database.id),
            DAAPObject("dmap.itemname", database.name),
            DAAPObject("dmap.itemcount", len(database.items)),
            DAAPObject("dmap.containercount", len(database.containers))
        ]

        if provider.supports_persistent_id and \
                database.persistent_id is not None:
            data.append(DAAPObject(
                "dmap.persistentid", database.persistent_id))

        return DAAPObject("dmap.listingitem", data)

    # Databases response
    return DAAPObject("daap.serverdatabases", [
        DAAPObject("dmap.status", 200),
        DAAPObject("dmap.updatetype", int(is_update)),
        DAAPObject("dmap.specifiedtotalcount", len(new)),
        DAAPObject("dmap.returnedcount", len(added)),
        DAAPObject("dmap.listing", (
            _database(new[k]) for k in added
        )),
        DAAPObject("dmap.deletedidlisting", (
            DAAPObject("dmap.itemid", k) for k in removed
        ))
    ])


def containers(provider, new, old, added, removed, is_update):
    """
    Generate containers response.
    """

    # Single container response
    def _container(Container container):
        data = [
            DAAPObject("dmap.itemid", container.id),
            DAAPObject("dmap.itemname", container.name),
            DAAPObject("dmap.itemcount", len(container.container_items)),
            DAAPObject(
                "dmap.parentcontainerid",
                container.parent_id if container.parent_id else 0)
        ]

        if provider.supports_persistent_id and \
                container.persistent_id is not None:
            data.append(DAAPObject(
                "dmap.persistentid", container.persistent_id))
        if container.is_base:
            data.append(DAAPObject("daap.baseplaylist", 1))
        if container.is_smart:
            data.append(DAAPObject("com.apple.itunes.smart-playlist", 1))

        return DAAPObject("dmap.listingitem", data)

    # Containers response
    return DAAPObject("daap.databaseplaylists", [
        DAAPObject("dmap.status", 200),
        DAAPObject("dmap.updatetype", int(is_update)),
        DAAPObject("dmap.specifiedtotalcount", len(new)),
        DAAPObject("dmap.returnedcount", len(added)),
        DAAPObject("dmap.listing", (
            _container(new[k]) for k in added
        )),
        DAAPObject("dmap.deletedidlisting", (
            DAAPObject("dmap.itemid", k) for k in removed
        ))
    ])


def container_items(provider, new, old, added, removed, is_update):
    """
    Generate container items response.
    """

    # Single container response
    def _container_item(ContainerItem container_item):
        data = [
            DAAPObject("dmap.itemkind", 2),
            DAAPObject("dmap.itemid", container_item.item_id),
            DAAPObject("dmap.containeritemid", container_item.id),
        ]

        return DAAPObject("dmap.listingitem", data)

    # Containers response
    return DAAPObject("daap.playlistsongs", [
        DAAPObject("dmap.status", 200),
        DAAPObject("dmap.updatetype", int(is_update)),
        DAAPObject("dmap.specifiedtotalcount", len(new)),
        DAAPObject("dmap.returnedcount", len(added)),
        DAAPObject("dmap.listing", (
            _container_item(new[k]) for k in added
        )),
        DAAPObject("dmap.deletedidlisting", (
            DAAPObject("dmap.itemid", k) for k in removed
        ))
    ])


def items(provider, new, old, added, removed, is_update):
    """
    Generate items response.
    """

    # Single item response
    def _item(Item item):
        data = [
            DAAPObject("dmap.itemid", item.id),
            DAAPObject("dmap.itemkind", 2),
        ]

        if provider.supports_persistent_id and item.persistent_id is not None:
            data.append(DAAPObject("dmap.persistentid", item.persistent_id))
        if item.name is not None:
            data.append(DAAPObject("dmap.itemname", item.name))
        if item.track is not None:
            data.append(DAAPObject("daap.songtracknumber", item.track))
        if item.artist is not None:
            data.append(DAAPObject("daap.songartist", item.artist))
        if item.album is not None:
            data.append(DAAPObject("daap.songalbum", item.album))
        if item.album_artist is not None:
            data.append(DAAPObject("daap.songalbumartist", item.album_artist))
        if item.year is not None:
            data.append(DAAPObject("daap.songyear", item.year))
        if item.bitrate is not None:
            data.append(DAAPObject("daap.songbitrate", item.bitrate))
        if item.duration is not None:
            data.append(DAAPObject("daap.songtime", item.duration))
        if item.file_size is not None:
            data.append(DAAPObject("daap.songsize", item.file_size))
        if item.file_suffix is not None:
            data.append(DAAPObject("daap.songformat", item.file_suffix))
        if provider.supports_artwork and item.album_art:
            data.append(DAAPObject("daap.songartworkcount", 1))
            data.append(DAAPObject("daap.songextradata", 1))

        return DAAPObject("dmap.listingitem", data)

    # Items response
    return DAAPObject("daap.databasesongs", [
        DAAPObject("dmap.status", 200),
        DAAPObject("dmap.updatetype", int(is_update)),
        DAAPObject("dmap.specifiedtotalcount", len(new)),
        DAAPObject("dmap.returnedcount", len(added)),
        DAAPObject("dmap.listing", (
            _item(new[k]) for k in added
        )),
        DAAPObject("dmap.deletedidlisting", (
            DAAPObject("dmap.itemid", k) for k in removed
        ))
    ])
