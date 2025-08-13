docker-compose --env-file env.example up -d
docker-compose down --remove-orphans
docker-compose --env-file env.example up -d --build