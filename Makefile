docker-build-latest: docker-pull-deps
	docker build -t ppigenpdc/foncier-app:latest . ; \
	docker build -t ppigenpdc/foncier-worker:latest celery ; \

docker-build-push: docker-build-latest
	TAG=$$(date +%Y%m%d%H%M%S) ;\
	docker tag ppigenpdc/foncier-app:latest ppigenpdc/foncier-app:$$TAG ; \
	docker tag ppigenpdc/foncier-worker:latest ppigenpdc/foncier-worker:$$TAG ; \
	docker push ppigenpdc/foncier-app:$$TAG ; \
	docker push ppigenpdc/foncier-app:latest ; \
	docker push ppigenpdc/foncier-worker:$$TAG ; \
	docker push ppigenpdc/foncier-worker:latest ; \

docker-pull-deps:
	docker pull python:3.4 ; \
	docker pull debian:stretch ; \

docker-stop-rm:
	docker-compose stop
	docker-compose rm -f

docker-clean-volumes:
	docker-compose down --volumes --remove-orphans

docker-clean-images:
	docker-compose down --rmi 'all' --remove-orphans

docker-clean-all:
	docker-compose down --volumes --rmi 'all' --remove-orphans

all: docker-build-latest
