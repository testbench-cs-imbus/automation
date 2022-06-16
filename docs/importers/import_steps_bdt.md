# **Importing Keywords from Gherkin/Behave**

The script `import_steps_bdt.py` is used to import steps from Behave `*.steps` files as Keywords into TestBech CS.

## **Setup (Behave Steps/Keyword Import)**

Fill in the variables in the config file in the "Behave" section:

```bash
    "base_dir"      # base directory - should be an absolute path
    "result_dir"    # relative to base_dir, the place to store results
    "scenario_dir"  # relative to base_dir, the place to store scenario files, 
                    # and for Behave, where to find them 
    "cleanup"       # if True, remove generated files; otherwise leave them for further reference
```

For import, actually only `base_dir` and `scenario_dir` are required; these seetimgs are shared with the adapter Behave.

## **How to use**

Call the importer script, e.g.:

```bash
python .\import_steps_bdt.py source_file 
```

The parameter `source_file` is either a feature folder (import all steps in the "steps"-folder), or the filename of the `*.feature` file to be imported.

(!) Mind: Also if you provide a folder name, Behave will only extract steps if at least one `.feature` file esists in the scenario folder.

The script will list all available products in your workspace and prompt to select one. Enter the ID of the product of your choice (leading number).

Import starts.

## **Command line flags**

| options | explanation |
| -------| --- |
  -h, --help  |          show this information and exit
  -x PREFIX, --prefix PREFIX |             prafix added to each Keyword name
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

## **How it works (Behave Steps/Keyword Import)**

This script takes advantage of  the capability of "behave" to list available steps. The steps in that list are in turn added to as Keywords to the selected product in TestBench CS. For each Keyword, this comprises:

* creating a new Keyword (unless it already exists)
* add a generic  `description` for that Keyword: "Import from Behave."
* adding the required `parameters` for that Keyword
* setting the flag `isImplemented` true
* set the value for `library` generically: "Behave"

## **Limitations**

* Behave will alway import each Keyword from any `*steps` file it can find in the "step"-folder.
