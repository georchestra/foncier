BTAG=19.04

docker-build-latest: docker-pull-deps
	docker build -t georchestra/foncier-app:${BTAG} -f foncier-docker/Dockerfile . ; \
	docker build -t georchestra/foncier-worker:${BTAG} celery ; \

docker-build-push: docker-build-latest
	TAG=${BTAG}-$$(date +%Y%m%d%H%M%S) ;\
	echo $$TAG ;\
	docker tag georchestra/foncier-app:${BTAG} georchestra/foncier-app:$$TAG ; \
	docker tag georchestra/foncier-worker:${BTAG} georchestra/foncier-worker:$$TAG ; \
	docker push georchestra/foncier-app:$$TAG ; \
	docker push georchestra/foncier-app:${BTAG} ; \
	docker push georchestra/foncier-worker:$$TAG ; \
	docker push georchestra/foncier-worker:${BTAG} ; \

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
