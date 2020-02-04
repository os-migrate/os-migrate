Installation from source
========================

```bash
git clone https://github.com/os-migrate/os-migrate
cd os-migrate
# > Here you can checkout a specific commit/branch if desired <

make toolbox-build
./toolbox/run make

pushd releases
ansible-galaxy collection install --force os_migrate-os_migrate-latest.tar.gz
popd
```
