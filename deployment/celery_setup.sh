#Thanks to Mike Lissner
#https://groups.google.com/forum/#!topic/celery-users/unOygQAjhSU

NOT TESTED!

     # I prefer init scripts to be checked into version control, so
        # they live in my django project and need to be linked.
        ln -s deployment/etc/init.d/celeryd /etc/init.d/celeryd
        ln -s deployment/etc/init.d/celerybeat /etc/init.d/celerybeat
        ln -s deployment/etc/idefault/celeryd /etc/default/celeryd
        ln -s deployment/etc/default/celerybeat /etc/default/celerybeat

        # The init script needs to be executable:
        chmod +x /etc/init.d/celeryd
        chmod +x /etc/init.d/celerybeat

        # Make an unprivileged, non-password-enabled user and group to run celery
        useradd celery

        # make a spot for the logs and the pid files
        mkdir /var/log/celery
        mkdir /var/run/celery
        chown celery:celery /var/log/celery
        chown celery:celery /var/run/celery

        # I also keep log scripts in version control, so they need to get linked as well.
        ln -s myproject/log-scripts/celery /etc/logrotate.d/celery