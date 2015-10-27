clean:
	@echo ---- Deleting old deploy dir
	rm -rf deploy/

web: clean
	@echo ---- Creating new deploy dir
	mkdir -p deploy/web
	cp -r web/tienda_ecuador_project/* deploy/web/
	python -m compileall deploy/web/
	#rm `find deploy/web | grep \\.py$$`

upload_web: web
	rsync -v -r --delete --force -z --progress -c deploy/web/ javcasas_dssti-facturacion@ssh.phx.nearlyfreespeech.net:/home/protected/django/

.PHONY: clean web upload_web
