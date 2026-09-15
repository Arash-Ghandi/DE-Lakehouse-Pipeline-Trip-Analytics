up:
	docker-compose up -d
down:
	docker-compose down

push:
	git add . && git commit -m "update" && git push -u origin main