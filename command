docker-compose --env-file env.example up -d
docker-compose down --remove-orphans
docker-compose --env-file env.example up -d --build

docker run -d --name hill-mongodb-dev -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=example -e MONGO_INITDB_DATABASE=hill_ts mongo:latest