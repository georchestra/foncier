docker-build:
	TAG=$$(date +%Y%m%d%H%M%S) ;\
	docker pull python:3.4 ; \
	docker pull debian:stretch ; \
	docker build -t ppigenpdc/foncier-app:latest . ; \
	docker build -t ppigenpdc/foncier-worker:latest celery ; \
	#~ docker build -t ppigenpdc/foncier-app:$$TAG . ; \
	#~ docker build -t ppigenpdc/foncier-worker:$$TAG celery ; \
	#~ docker push ppigenpdc/foncier-app:$$TAG ; \
	#~ docker push ppigenpdc/foncier-app:latest ; \
	#~ docker push ppigenpdc/foncier-worker:$$TAG ; \
	#~ docker push ppigenpdc/foncier-worker:latest ; \

docker-stop-rm:
	docker-compose stop
	docker-compose rm -f

docker-clean-volumes:
	docker-compose down --volumes --remove-orphans

docker-clean-images:
	docker-compose down --rmi 'all' --remove-orphans

docker-clean-all:
	docker-compose down --volumes --rmi 'all' --remove-orphans

all: docker-build
