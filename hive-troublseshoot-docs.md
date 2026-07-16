# Development

## Clone Locally
```
git clone --filter=blob:limit=50k https://github.com/HiveLMS/Hive.git
```

### Install dev dependencies
```
cd core
uv sync
cd ..
pre-commit install
```

## Reset local DB
```pwsh
./manage_hive.py --env dev down
sudo rm -rf db
sudo rm -rf dummy/
./manage_hive.py --env dev init
```


## dev commands:

### Rebuild Orval apis
```pwsh
./manage_hive.py --env dev generate_api
```

### Setup Hive for the first time (dev)
```pwsh
./manage_hive.py --env dev build_deps
./manage_hive.py --env dev init
./manage_hive.py --env dev start
# Check if hive.org is the hosts file
# sudo bash -c 'echo "127.0.0.1 hive.org" >> /etc/hosts' # I'd rather not spam the user's hosts file
```

### Low level dev env update dockers (this shouldn't really be needed)
```pwsh
./manage_hive.py --env dev update
```

### Changes to DB Schema (explain WTF this means plz)
```
docker compose exec core python manage.py makemigrations
docker compose exec core python manage.py migrate
```

### Run all linters
```pwsh
uv run pre-commit run --all-files
```

### Run Backend (core) tests
```pwsh
docker compose exec core pytest
```


