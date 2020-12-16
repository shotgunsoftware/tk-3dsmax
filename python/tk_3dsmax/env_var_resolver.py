import pymxs

rt = pymxs.runtime

callback_name = "tk_resolve_envs"
persistent_variable_name = "SGTK_storage_lookup"

def register_callbacks():
    # remove any previous tk callbacks that may have been registered.
    rt.callbacks.removeScripts(id=rt.name(callback_name))

    # now register the callbacks
    rt.callbacks.addScript(rt.Name('filePreSave'), store_env_var_lookup, id=rt.Name(callback_name))
    # remove the persistent variable from the current scene before importing
    # since persistent variables are only brought in if they don't exist already.
    rt.callbacks.addScript(rt.Name('filePreMerge'), clean_existing_peristent_data, id=rt.Name(callback_name))

    # When opening or merging files we will check if any paths can be updated to match our env vars
    rt.callbacks.addScript(rt.Name('filePostOpen'), update_and_resolve_paths, id=rt.Name(callback_name))
    rt.callbacks.addScript(rt.Name('filePostMerge'), update_and_resolve_paths, id=rt.Name(callback_name))

    print("SGTK env var callbacks registered")

def store_env_var_lookup():
    """
    Persistently stores the local storage env vars in the max scene file
    :return:
    """
    # import sgtk now just in case it has been reloaded or changed since the callback was registered
    # this may not be necessary, I haven't checked.
    print("store_env_var_lookup called")
    import sgtk

    engine = sgtk.platform.current_engine()

    if engine:

        clean_existing_peristent_data()
        rt.execute('persistent global {0} = undefined'.format(persistent_variable_name))
        rt.persistents.make(rt.name(persistent_variable_name))

        roots = []
        # get a list of storage roots in Shotgun
        for storage_root in sgtk.util.shotgun.publish_util.get_cached_local_storages(engine.sgtk):

            # get the storage root path that applies to our current OS
            local_storage_path = sgtk.util.ShotgunPath.from_shotgun_dict(storage_root).current_os

            if not local_storage_path:
                continue

            # now expand any environment variables that the path might contain
            local_storage_path_expanded = sgtk.util.ShotgunPath.expand(local_storage_path)

            print(local_storage_path, local_storage_path_expanded)
            if local_storage_path != local_storage_path_expanded:
                # the expanded root is not the same as the original so it has environment variables in it.
                # We need to store this in the map
                roots.append([local_storage_path, local_storage_path_expanded])

        # although we can store python objects directly to max script variable using pymxs
        # the persistent variables won't be able to store that. So we must store a mx array

        # This should produce something like:
        # #(#("$path1", "c:/path1"),#("$path2", "e:/path2"))
        mxs_script = ""
        for root in roots:
            mxs_script += '#("{0}", "{1}"),'.format(root[0], root[1])

        #insert all the arrays into one master array and remove the last comma so the syntax is correct
        mxs_script = "{0} = #({1})".format(persistent_variable_name, mxs_script.rstrip(","))
        rt.execute(mxs_script)

        # rt.SGTK_storage_lookup = roots

        print("persistent roots data stored")

def clean_existing_peristent_data():
    """
    Removes the persistent variable
    :return:
    """
    rt.persistents.remove(rt.name(persistent_variable_name))

def retrieve_storage_lookup():
    """
    Retrieves a previously stored env var look up from the scene persistent variables.
    :return:
    """
    try:
        roots = rt.SGTK_storage_lookup
        # return a dictionary where the root path maps to the environment variable.
        return {a_root[1]: a_root[0] for a_root in roots}
    except AttributeError:
        # the persistent variable wasn't present so no roots were returned
        return []

def update_and_resolve_paths():
    """
    Scans the scene and updates any paths that can be matched
     against the previous env var path, to the current env var path.
    :return:
    """
    storage_root_lookup = retrieve_storage_lookup()
