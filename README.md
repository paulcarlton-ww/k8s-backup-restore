# Kubernetes Namespaced Resources Backup and Restore

To run the command use the following:

```bash
python3 dr.py [command] [args]
```

There are currently 2 commands:

* backup - this will backup objects from a k8s cluster into a s3 bucket
* restore - this will restore objects from s3 into k8s

### Using Environment Variables

Environment variables can be used instead of using args. For example, the `restore` command has an argument to specify the bucket name to restore from. Normally you would supply this using `--bucket` but you could instead use an environment variable named: `DR_RESTORE_BUCKET`:

```bash
export DR_RESTORE_BUCKET=my-test-bucket
python3 dr.py restore
```

The naming convention for the environment variables is `DR_[COMMAND]_[OPTION]` where:

* [COMMAND] - is replaced by the command you are running in CAPS (i.e. backup or restore)
* [ARGUMENT] - is the name of the option in CAPS (as can be seen when running --help)
