from app.services.github.clone_service import CloneService

service = CloneService()

repo = service.clone_repository(
    "https://github.com/pallets/flask"
)

print(repo)

service.delete_repository(repo)