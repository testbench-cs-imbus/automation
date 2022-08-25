# **Importing Keywords from Robot Framework**

The script `import_kwd_rf.py` is used to import Keywords from Robot Framework (RF) libraries or `.resource` files into TestBech CS.

## **Setup (RF Keyword Import)**

Fill in the variables in the config file in the "ROBOT_KDT" section:

```bash
    "base_dir"      # base directory - should be an absolute path
    "script_dir"    # relative to base_dir, the place to store .robot files in, 
                    # and for Robot Framework, where to find them
    "result_dir"    # relative to base_dir, the place to store results
    "resource_dir"  # relative to base_dir, the place for .resource files
    "empty_string"  # used to indicate an empty a value for an argument
    "clean_up"      # True or False, whether to delete the created files
```

For import, actually only `base_dir` and `script_dir` are required; these seetimgs are shared with the adapter RFKdt.

## **How to use**

Call the importer script, e.g.:

```bash
python import_kwd_rf.py source_file 
```

The parameter `source_file` is either the name of an installed RF library, or the filename (possibly including the path) of an RF resource file. For a library, the name - e.g. "Browser" or "BuiltIn" - is sufficient.

The script will list all available products in your workspace and prompt to select one. Enter the ID of the product of your choice (leading number)

Import starts.

## **Command line flags**

| options | explanation |
| -------| --- |
  -h, --help  |          show this information and exit
  -x PREFIX, --prefix PREFIX |             prefix added to each Keyword name
  -w WORKSPACE, --workspace WORKSPACE |       your TestBench CS workspace
  -s SERVER, --server SERVER |                        base address for TestBench CS Server
  -u USER, --user USER | user name for accessing TestBench CS
  -p PASSWORD, --password PASSWORD |                        password for accessing TestBench CS
  -i, --insecure     |   for debugging only: ignore SSL warnings

## **Security issues**

You may want to avoid exposing your credentials (server, workspace, username, and password) to access TestBench CS. Depending on your requirements, for each of those you can chose between three option for a balance between comfort and confidentiality:

* Store your credentials in the file `config.py` you create based on `config.py.template`
* Provide your credentials on the command line (see above)
* If you leave one more credentials empty in the config file, and do not provide them in the command line, the script will prompt you.

## **How it works (RF Keyword Import)**

This script takes advantage of "libdoc", a component of Robot Framework. libdoc is called to create a list of Keywords in the provided source. The Keywords in that list are in turn added to the selected product in TestBench CS. For each Keyword, this comprises:

* creating a new Keyword (unless it already exists)
* if available, add the `description` for that Keyword
* adding the required `parameters` for that Keyword
* setting the flag `isImplemented` true
* set the proper value for `library`, depending if the source file is a library or a resource file

## **Limitations**

* Keyword descriptions longer than 3999 characters are truncated since this is a limit in TestBench CS.
* Links in Keyword descriptions (especially from libraries) will in most cases not work.
