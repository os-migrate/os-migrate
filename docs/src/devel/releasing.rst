Releasing the OS Migrate collection
===================================

Set env vars with old and new versions:

::

   OLD_VERSION=$(./toolbox/run bash -c 'cat /galaxy.yml | shyaml get-value version')
   echo "OLD_VERSION=$OLD_VERSION"

   NEW_VERSION="SOME.NEW.VERSION"

Edit the version in galaxy.yml and any hardcoded values in functional
tests:

.. code:: bash

   sed -i -e "s/^version: $OLD_VERSION/version: $NEW_VERSION/" .//galaxy.yml
   grep -lr "os_migrate_version: $OLD_VERSION" ./tests | xargs sed -i -e "s/^os_migrate_version: $OLD_VERSION/os_migrate_version: $NEW_VERSION/"

A build is required to update const.py:

::

   ./toolbox/run make

Create a pull request with these changes. Once it's merged, check out
the merge commit and release to galaxy:

::

   git checkout $MERGED_COMMIT
   ./toolbox/run ./scripts/publish.sh -k <YOUR_GALAXY_TOKEN>

After a successful release, create a tag on the commit you built the
release from, and push the tag to the upstream repo:

::

   git tag -m "$NEW_VERSION" "$NEW_VERSION"
   # assuming the os-migrate upstream repo is named 'upstream' in your repo clone
   git push upstream --tags

If you've incremented "X" or "Y" in "X.Y.Z" version scheme, create also
a stable branch to allow us to create ".Z" releases:

::

   STABLE_VERSION=$(awk -F. '{ print $1 "." $2; }' <<<"$NEW_VERSION")
   git checkout -b stable/$STABLE_VERSION
   git push upstream stable/$STABLE_VERSION
