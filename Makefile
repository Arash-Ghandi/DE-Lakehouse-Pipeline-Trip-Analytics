up:
	docker-compose up -d
down:
	docker-compose down --remove-orphans

push:
	git add . && git commit -m "update" && git push -u origin main

datasets:
	docker exec -it lakehouse-pipeline bash -c "cd /home/jovyan/work && python src/ingestion/generate_sample_data.py --rows 50000 --out data/raw && python src/bronze/ingest_to_bronze.py && python src/silver/clean_transform.py && python src/gold/aggregate.py"