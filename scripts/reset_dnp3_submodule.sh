# Note: deprecated
git rm --cached deps/dnp3
rm -rf .git/modules/deps/dnp3
rm -rf deps/dnp3
cd deps
git submodule add https://github.com/kefeimo/opendnp3.git
git submodule update --init --recursive
cd dnp3
git checkout 7d84673d165a4a075590a5f146ed1a4ba35d4e49
cd ../..