import os
import hashlib
import pymxs

rt = pymxs.runtime

callback_name = "tk_resolve_envs"
persistent_variable_name = "SGTK_storage_lookup_"

def register_callbacks():
    # remove any previous tk callbacks that may have been registered.
    rt.callbacks.removeScripts(id=rt.name(callback_name))

    # now register the callbacks
    rt.callbacks.addScript(rt.Name('filePreSave'), store_env_var_lookup, id=rt.Name(callback_name))

    # When opening or merging files we will check if any paths can be updated to match our env vars
    rt.callbacks.addScript(rt.Name('filePostOpen'), post_open_callback, id=rt.Name(callback_name))
    rt.callbacks.addScript(rt.Name('filePostMerge'), post_merge_callback, id=rt.Name(callback_name))

    print("SGTK env var callbacks registered")

def post_open_callback():
    print("post open callback called")
    update_and_resolve_paths()

def post_merge_callback():
    print("post merge callback called")
    update_and_resolve_paths()

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
        # SGTK_storage_lookup_12s3ch23r7yhf73491hdz = #("$path1", "c:/path1")
        for root in roots:
            mxs_script = '#("{0}", "{1}")'.format(root[0], root[1]).replace("\\", "\\\\")

            # generate a unique variable name using the path
            var_name = generate_variable_name(root[1])
            rt.execute('persistent global {0} = undefined'.format(var_name))
            rt.persistents.make(rt.name(var_name))

            # Now persistently store the roots to the unique variable name
            mxs_script = "{0} = {1}".format(var_name, mxs_script)
            rt.execute(mxs_script)

        print("persistent roots data stored")

def generate_variable_name(root_path):
    """
    Takes the persistent variable name template and applies the hash of the path to the variable name.
    :param root_path:
    :return:
    """
    #TODO might need to take into account the variable name as well.
    hash_object = hashlib.md5(root_path.encode())
    return persistent_variable_name + hash_object.hexdigest()

def retrieve_storage_lookup():
    """
    Retrieves a previously stored env var look up from the scene persistent variables.
    :return:
    """
    # return a dictionary where the root path maps to the environment variable.
    roots = {}
    # when merging the persistent variables from the merged file are added to the globalVars not the persistent vars.
    for variable in rt.globalVars.gather():
        if str(variable).startswith(persistent_variable_name):
            val = rt.globalVars.get(variable)
            # put the path as the key and the sg root name as the value
            roots[val[1]] = val[0]

    return roots

def _get_new_path(current_path, storage_roots):
    """
    Loops over the storage roots trying to see if the passed current_path
    starts with a path in the storage_root lookup. If it does then it
    will rebuild the path to match current environment variable path.
    If it can't match then None is returned.
    :param current_path:
    :param storage_roots:
    :return:
    """
    for previous_storage_path, raw_sg_root_path in storage_roots.items():
        if current_path.startswith(previous_storage_path):
            # take the previous path off so we can insert the new path on.
            relative_path = os.path.relpath(current_path, previous_storage_path)

            return os.path.join(os.path.expandvars(raw_sg_root_path), relative_path)


def update_and_resolve_paths():
    """
    Scans the scene and updates any paths that can be matched
     against the previous env var path, to the current env var path.
    :return:
    """
    storage_root_lookup = retrieve_storage_lookup()
    print("storage_root_lookup", storage_root_lookup)

    if not storage_root_lookup:
        return

    # repath all paths found in the asset manager
    for i in range(rt.AssetManager.GetNumAssets()):
        # Max is index 1 based.
        asset = rt.AssetManager.GetAssetByIndex(i + 1)
        a_file = asset.getfilename()

        new_path = _get_new_path(a_file, storage_root_lookup)

        if new_path is not None and new_path != a_file:
            print("repathing {0} to {1}".format(a_file, new_path))
            rt.atsops.RetargetAssets(rt.rootScene, a_file, new_path, CreateOutputFolder=False)
            # TODO: check if the repath failed, if it did we could try adding an external path.

            asset = rt.AssetManager.GetAssetByIndex(i + 1)
            if asset.getfilename() != new_path:
                print("failed to repath!")

    # now check for any configured external paths that might need repathing.
    for i in reversed(range(rt.mapPaths.count())):
        # Max is index 1 based.
        mapped_path = rt.mapPaths.get(i + 1)

        new_mapped_path = _get_new_path(mapped_path, storage_root_lookup)

        print(mapped_path)
        print(new_mapped_path)