coverage erase
coverage run --source '.' manage.py test -v 2
coverage html
