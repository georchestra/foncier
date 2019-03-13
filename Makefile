docker-build-latest: docker-pull-deps
	docker build -t georchestra/foncier-app:18.12 foncier-docker ; \
	docker build -t georchestra/foncier-worker:18.12 celery ; \

docker-build-push: docker-build-latest
	TAG=18.12-$$(date +%Y%m%d%H%M%S) ;\
	docker tag georchestra/foncier-app:18.12 georchestra/foncier-app:$$TAG ; \
	docker tag georchestra/foncier-worker:18.12 georchestra/foncier-worker:$$TAG ; \
	docker push georchestra/foncier-app:$$TAG ; \
	docker push georchestra/foncier-app:18.12 ; \
	docker push georchestra/foncier-worker:$$TAG ; \
	docker push georchestra/foncier-worker:18.12 ; \

docker-pull-deps:
	docker pull python:3.5 ; \
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
