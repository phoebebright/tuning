#run from deployment directory
rm /etc/init.d/celeryd
cp ./etc/init.d/celeryd /etc/init.d/celeryd
#chown celery:www-data /etc/init.d/celeryd

rm /etc/default/celeryd
cp ./etc/default/celeryd /etc/default/celeryd
#chown celery:www-data /etc/default/celeryd

rm /etc/init.d/celerybeat
cp ./etc/init.d/celerybeat /etc/init.d/celerybeat
#chown celery:www-data /etc/init.d/celerybeat

rm /etc/default/celerybeat
cp ./etc/default/celerybeat /etc/default/celerybeat
#chown celery:www-data /etc/default/celerybeat

ls /etc/init.d/celery*
ls /etc/default/celery*